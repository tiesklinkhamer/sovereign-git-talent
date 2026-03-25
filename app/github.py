import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import TargetProfile, TrackedEvent, TargetStatus

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"

# The events considered signal vs noise
HIGH_SIGNAL_EVENTS = {"PushEvent", "WatchEvent", "CreateEvent", "PullRequestEvent"}

class GitHubRateLimitError(Exception):
    pass

async def fetch_user_profile(client: httpx.AsyncClient, username: str) -> Optional[dict]:
    """
    Fetches the enriched user profile metadata from GitHub.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        
    url = f"{GITHUB_API_BASE}/users/{username}"
    response = await client.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

async def fetch_user_events(
    client: httpx.AsyncClient, 
    username: str, 
    last_etag: Optional[str]
) -> tuple[List[dict], Optional[str]]:
    """
    Fetches events for a single user, handling pagination and 304 Not Modified.
    Returns a tuple of (events, new_etag).
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    if last_etag:
        headers["If-None-Match"] = last_etag
        
    all_events = []
    url = f"{GITHUB_API_BASE}/users/{username}/events/public"
    new_etag = last_etag
    
    while url:
        response = await client.get(url, headers=headers)
        
        # Handle Rate Limiting
        if response.status_code == 403 and "rate limit" in response.text.lower():
            reset_time = response.headers.get("X-RateLimit-Reset")
            logger.warning(f"Rate limit exceeded. Resets at {reset_time}")
            raise GitHubRateLimitError("GitHub API rate limit exceeded.")
            
        if response.status_code == 304:
            logger.info(f"No new events for {username} (304 Not Modified).")
            break
            
        if response.status_code == 404:
            logger.warning(f"User {username} not found.")
            break
            
        response.raise_for_status()
        
        if not new_etag or url == f"{GITHUB_API_BASE}/users/{username}/events/public":
            # Caputure ETag strictly from the first page
            new_etag = response.headers.get("ETag")
            
        page_events = response.json()
        if not page_events:
            break
            
        all_events.extend(page_events)
        
        # Handle Pagination via the 'Link' header
        link_header = response.headers.get("Link", "")
        if 'rel="next"' in link_header:
            links = link_header.split(",")
            next_link = next((link for link in links if 'rel="next"' in link), None)
            if next_link:
                url = next_link.split(";")[0].strip("<> ")
            else:
                url = None
        else:
            url = None
            
        # Optional: respect rate limits gracefully between pages
        await asyncio.sleep(0.5)
        
    return all_events, new_etag

async def process_user_events(session: AsyncSession, profile: TargetProfile, client: httpx.AsyncClient):
    """
    Fetches and stores high-signal events for a given target profile.
    """
    try:
        raw_events, new_etag = await fetch_user_events(client, profile.github_username, profile.last_etag)
    except GitHubRateLimitError:
        logger.error(f"Stopping ingestion for {profile.github_username} due to rate limits.")
        return
    except Exception as e:
        logger.error(f"Error fetching events for {profile.github_username}: {e}")
        return

    # Filter and save new events
    new_tracked_events = []
    for event in raw_events:
        event_type = event.get("type")
        if event_type not in HIGH_SIGNAL_EVENTS:
            continue
            
        event_id = event.get("id")
        
        # Parse the event created_at time
        created_at_str = event.get("created_at")
        event_time = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        
        repo_name = event.get("repo", {}).get("name")
        
        # Check if we already have this event. Events are returned latest first. 
        existing_event = await session.execute(
            select(TrackedEvent).where(TrackedEvent.github_event_id == event_id)
        )
        if existing_event.first():
            continue
            
        tracked_event = TrackedEvent(
            profile_id=profile.id,
            event_type=event_type,
            repo_name=repo_name,
            github_event_id=event_id,
            event_created_at=event_time,
            payload=event
        )
        session.add(tracked_event)
        new_tracked_events.append(tracked_event)
        
    # Update profile polling metadata
    profile.last_etag = new_etag
    profile.last_polled_at = datetime.now(timezone.utc)
    
    # Try fetching profile enrichments if missing
    if not profile.bio and not profile.company:
        prof_data = await fetch_user_profile(client, profile.github_username)
        if prof_data:
            profile.bio = prof_data.get("bio")
            profile.location = prof_data.get("location")
            profile.company = prof_data.get("company")
            profile.blog = prof_data.get("blog")
            
    session.add(profile)
    
    await session.commit()
    logger.info(f"Ingested {len(new_tracked_events)} high-signal events for {profile.github_username}.")

async def run_ingestion_pipeline(session: AsyncSession):
    """
    Polls GitHub for all active target profiles.
    """
    profiles_result = await session.execute(
        select(TargetProfile).where(TargetProfile.status == TargetStatus.ACTIVE)
    )
    profiles = profiles_result.scalars().all()
    
    if not profiles:
        logger.info("No active profiles to ingest.")
        return

    # Use a single httpx client to pool connections
    async with httpx.AsyncClient() as client:
        for profile in profiles:
            logger.info(f"Starting ingestion for target: {profile.github_username}")
            await process_user_events(session, profile, client)
            # Add a small delay between users to avoid slamming GitHub API
            await asyncio.sleep(1.0)
