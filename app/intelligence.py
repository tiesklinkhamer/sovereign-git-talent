import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from anthropic import AsyncAnthropic
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TargetProfile, TrackedEvent, IntelligenceLog
from app.slack import send_slack_alert, SlackAlertData

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are a defense tech VC analyst. Review this engineer's recent GitHub activity. 
Are they likely exploring a new startup idea, working on dual-use technology (drones, cryptography, AI, autonomy), 
or is this standard hobby work? 
Return ONLY a valid JSON object with the following structure:
{
    "is_anomalous": boolean,
    "domain": string (or null),
    "summary": string
}
Do not wrap it in markdown block quotes, do not output any preamble. Just raw JSON."""

def _simplify_event_payload(event: TrackedEvent) -> Dict[str, Any]:
    """
    Extracts high-signal information from the raw GitHub API payload
    to reduce LLM token usage.
    """
    simple = {
        "event_type": event.event_type,
        "repo_name": event.repo_name,
        "created_at": event.event_created_at.isoformat()
    }
    
    payload = event.payload.get("payload", {})
    if event.event_type == "PushEvent":
        commits = payload.get("commits", [])
        simple["commit_messages"] = [c.get("message") for c in commits]
    elif event.event_type == "CreateEvent":
        simple["description"] = payload.get("description")
    elif event.event_type == "WatchEvent":
        simple["action"] = payload.get("action")
    elif event.event_type == "PullRequestEvent":
        pr = payload.get("pull_request", {})
        simple["action"] = payload.get("action")
        simple["title"] = pr.get("title")
        simple["body"] = pr.get("body")
        
    return simple

async def evaluate_user_events(session: AsyncSession, profile: TargetProfile, client: AsyncAnthropic):
    """
    Fetches unanalyzed events for a user, sends a prompt to Claude, 
    and saves the resulting intelligence log.
    """
    # Fetch events that don't have an intelligence log attached yet
    result = await session.execute(
        select(TrackedEvent)
        .outerjoin(IntelligenceLog, TrackedEvent.id == IntelligenceLog.event_id)
        .where(TrackedEvent.profile_id == profile.id)
        .where(IntelligenceLog.id == None)
        .order_by(TrackedEvent.event_created_at.asc())
    )
    unprocessed_events = result.scalars().all()

    if not unprocessed_events:
        return

    logger.info(f"Evaluating {len(unprocessed_events)} unprocessed events for {profile.github_username}")

    events_payload = [_simplify_event_payload(e) for e in unprocessed_events]
    
    prompt = f"Engineer GitHub Username: {profile.github_username}\n"
    if profile.known_affiliation:
        prompt += f"Known Affiliation: {profile.known_affiliation}\n"
    prompt += f"Recent Events JSON:\n{json.dumps(events_payload, default=str)}\n"

    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        content = response.content[0].text.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        analysis = json.loads(content.strip())
        
        is_anomalous = analysis.get("is_anomalous", False)
        domain = analysis.get("domain", None)
        summary = analysis.get("summary", "No summary provided.")

        # Attach the log to the LAST event in the current batch
        latest_event = unprocessed_events[-1]
        
        log_entry = IntelligenceLog(
            event_id=latest_event.id,
            is_anomalous=is_anomalous,
            domain=domain,
            summary=summary
        )
        session.add(log_entry)
        await session.commit()
        
        if is_anomalous:
            logger.warning(f"Anomaly detected for {profile.github_username} in domain '{domain}': {summary}")
            await send_slack_alert(SlackAlertData(
                github_username=profile.github_username,
                known_affiliation=profile.known_affiliation,
                event_type=latest_event.event_type,
                repo_name=latest_event.repo_name,
                domain=domain,
                summary=summary
            ))

    except json.JSONDecodeError:
        logger.error(f"Failed to parse Claude JSON response for {profile.github_username}: {content}")
    except Exception as e:
        logger.error(f"Failed to evaluate events for {profile.github_username}: {e}")

async def evaluate_discovery_snippet(client: AsyncAnthropic, snippet: str, keyword: str) -> bool:
    """
    Fast L1 filter to determine if a search result is relevant to defense tech.
    """
    prompt = f"""Evaluate if the following GitHub code/repo snippet is related to actual hardware, software, or research 
useful in defense or dual-use sectors (drones, robotics, AI, crypto, aerospace, security).

Keyword hit: {keyword}
Snippet: {snippet}

Return ONLY 'YES' or 'NO'."""

    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return "YES" in response.content[0].text.upper()
    except Exception as e:
        logger.error(f"Discovery filter error: {e}")
        return True # Default to True to avoid missing talent on API error

async def synthesize_talent_brief(session: AsyncSession, profile: TargetProfile, client: AsyncAnthropic):
    """
    Synthesizes all historical events and metadata for a profile 
    into a holistic Markdown talent brief.
    """
    # Fetch all events for this profile
    result = await session.execute(
        select(TrackedEvent)
        .where(TrackedEvent.profile_id == profile.id)
        .order_by(TrackedEvent.event_created_at.desc())
        .limit(50)  # Top 50 events for context
    )
    events = result.scalars().all()
    if not events:
        return

    events_payload = [_simplify_event_payload(e) for e in events]
    
    prompt = f"""Synthesize a professional 'Defense Tech Talent Brief' for the following engineer.
Username: {profile.github_username}
Bio: {profile.bio}
Location: {profile.location}
Affiliation: {profile.known_affiliation}

Recent Events:
{json.dumps(events_payload, default=str)}

Focus on:
1. Core technical competencies (languages, frameworks, niche domains).
2. Defense/Dual-use relevance (drones, AI, cryptography, etc.).
3. Recent trajectory (is their activity increasing or shifting towards a specific field?).

Format as a concise Markdown brief. Use headers and bullet points. No conversational filler."""

    try:
        response = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        
        brief = response.content[0].text.strip()
        profile.brief_summary = brief
        profile.last_brief_generated_at = datetime.now(timezone.utc)
        
        # Simple score calculation improvement: +1 per anomaly, +0.1 per event
        anomalies_result = await session.execute(
            select(IntelligenceLog).join(TrackedEvent).where(TrackedEvent.profile_id == profile.id).where(IntelligenceLog.is_anomalous == True)
        )
        anomalies_count = len(anomalies_result.scalars().all())
        profile.defense_relevance_score = (anomalies_count * 5.0) + (len(events) * 0.1)
        
        session.add(profile)
        await session.commit()
        logger.info(f"Synthesized talent brief for {profile.github_username}")

    except Exception as e:
        logger.error(f"Failed to synthesize brief for {profile.github_username}: {e}")

async def run_intelligence_pipeline(session: AsyncSession):
    """
    Runs the LLM evaluation for all profiles with unanalyzed events.
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY is missing. Cannot run intelligence pipeline.")
        return
        
    profiles_result = await session.execute(select(TargetProfile))
    profiles = profiles_result.scalars().all()
    
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    
    for profile in profiles:
        # 1. Evaluate new events (Haiku for speed/cost)
        await evaluate_user_events(session, profile, client)
        
        # 2. Re-synthesize brief if significant time has passed (Sonnet for quality)
        should_resynthesize = (
            profile.brief_summary is None or 
            (profile.last_brief_generated_at and 
             (datetime.now(timezone.utc) - profile.last_brief_generated_at).total_seconds() > 86400)
        )
        if should_resynthesize:
            await synthesize_talent_brief(session, profile, client)
