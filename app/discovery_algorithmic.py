import os
import logging
import httpx
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from anthropic import AsyncAnthropic
from app.models import TargetProfile, DiscoveryKeyword
from app.intelligence import evaluate_discovery_snippet, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def search_github_code(keyword: str):
    """
    Search GitHub code for the given keyword.
    """
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN missing for algorithmic discovery.")
        return []
        
    async with httpx.AsyncClient() as client:
        # We search specifically for the keyword in dual-use related topics or just general code
        # GitHub Code search is rate limited to 30 reqs/min for authenticated users.
        url = f"https://api.github.com/search/code?q={keyword}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.error(f"GitHub Search API failed: {resp.status_code} - {resp.text}")
            return []
            
        return resp.json().get("items", [])

async def run_algorithmic_discovery(session: AsyncSession):
    """
    Core loop to poll for high-value keywords and ingest new users.
    """
    # 1. Fetch active keywords
    res = await session.execute(select(DiscoveryKeyword).where(DiscoveryKeyword.is_active == True))
    keywords = res.scalars().all()
    
    if not keywords:
        logger.info("No active discovery keywords found.")
        return

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    for kw in keywords:
        logger.info(f"Polling GitHub for keyword: {kw.keyword}")
        items = await search_github_code(kw.keyword)
        
        for item in items:
            owner = item.get("repository", {}).get("owner", {}).get("login")
            if not owner:
                continue
                
            # Check if exists
            exists = await session.execute(select(TargetProfile).where(TargetProfile.github_username == owner))
            if exists.scalars().first():
                continue
                
            # 2. L1 Intelligence Filter
            snippet = f"Repo: {item.get('repository', {}).get('full_name')}\nPath: {item.get('path')}"
            is_relevant = True
            if client:
                is_relevant = await evaluate_discovery_snippet(client, snippet, kw.keyword)
                
            if is_relevant:
                new_target = TargetProfile(
                    github_username=owner,
                    known_affiliation=f"Discovered via: {kw.keyword}",
                    defense_relevance_score=1.0 
                )
                session.add(new_target)
                logger.info(f"Ingested qualified talent: {owner}")
            else:
                logger.info(f"Discarded low-relevance lead: {owner}")
        
        # 3. Update keyword last_polled
        kw.last_polled_at = datetime.now(timezone.utc)
        session.add(kw)
        await session.commit()
