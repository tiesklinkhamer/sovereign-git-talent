import os
import asyncio
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models import TargetProfile, TargetStatus
from app.github import fetch_user_profile

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"

# High-value dual-use or defense-adjacent open source repositories
TARGET_REPOS = [
    "PX4/PX4-Autopilot", # Drones / Autonomy
    "ArduPilot/ardupilot", # Drones / Autonomy
    "ros2/ros2", # Robotics
]

async def discover_contributors(session: AsyncSession, repo_full_name: str, client: httpx.AsyncClient):
    """
    Fetches the most active contributors from a given repository.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/contributors?per_page=10"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = await client.get(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to fetch contributors for {repo_full_name}: {response.status_code}")
        return

    contributors = response.json()
    new_targets = 0
    
    for contributor in contributors:
        if contributor.get("type") != "User":
            continue
            
        username = contributor.get("login")
        if not username:
            continue
            
        # Check if we already track them
        existing = await session.execute(
            select(TargetProfile).where(TargetProfile.github_username == username)
        )
        if existing.first():
            continue
            
        # Fetch their profile
        prof_data = await fetch_user_profile(client, username)
        bio = prof_data.get("bio") if prof_data else None
        location = prof_data.get("location") if prof_data else None
        company = prof_data.get("company") if prof_data else None
        blog = prof_data.get("blog") if prof_data else None
        
        target = TargetProfile(
            github_username=username,
            known_affiliation=f"Discovered via {repo_full_name}",
            bio=bio,
            location=location,
            company=company,
            blog=blog
        )
        session.add(target)
        new_targets += 1
        
        # Respect rate limits
        await asyncio.sleep(0.5)
        
    await session.commit()
    logger.info(f"Discovered {new_targets} new targets from {repo_full_name}")

async def run_discovery_pipeline(session: AsyncSession):
    """
    Runs the automated discovery process across target repositories.
    """
    logger.info("Starting active discovery pipeline...")
    async with httpx.AsyncClient() as client:
        for repo in TARGET_REPOS:
            await discover_contributors(session, repo, client)
            await asyncio.sleep(1.0)
    logger.info("Discovery pipeline completed.")
