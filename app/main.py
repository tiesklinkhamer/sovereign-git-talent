import os
import json
import logging
import httpx
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from anthropic import AsyncAnthropic
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import get_async_session, AsyncSessionLocal, init_db
from app.models import TargetProfile, TargetStatus, TrackedEvent, IntelligenceLog
from app.github import run_ingestion_pipeline
from app.intelligence import run_intelligence_pipeline
from app.discovery import run_discovery_pipeline
from app.discovery_algorithmic import run_algorithmic_discovery
from app.auth import create_access_token, get_github_user, get_current_user, TokenData
from app.models import TargetProfile, TargetStatus, TrackedEvent, IntelligenceLog, DiscoveryKeyword

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_sync_job():
    """
    Background job triggered by APScheduler every 12 hours.
    """
    logger.info("Starting scheduled sync job...")
    async with AsyncSessionLocal() as session:
        try:
            await run_discovery_pipeline(session)
            await run_algorithmic_discovery(session)
            await run_ingestion_pipeline(session)
            await run_intelligence_pipeline(session)
            logger.info("Scheduled sync job completed successfully.")
        except Exception as e:
            logger.error(f"Error during scheduled sync job: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (Synchronous setup)
    init_db()
    
    # Start APScheduler
    scheduler.add_job(scheduled_sync_job, "interval", hours=12, id="daily_sync_job")
    scheduler.start()
    logger.info("APScheduler started. Sync job scheduled every 12 hours.")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("APScheduler stopped.")

app = FastAPI(
    title="Sovereign Git: Talent Sonar API",
    description="Automated defense tech talent intelligence engine.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TargetCreate(BaseModel):
    github_username: str
    known_affiliation: str | None = None

@app.post("/targets", summary="Add a new target profile")
async def add_target(target: TargetCreate, session: AsyncSession = Depends(get_async_session)):
    """
    Adds a new GitHub username to the tracking list.
    """
    existing_target = await session.execute(
        select(TargetProfile).where(TargetProfile.github_username == target.github_username)
    )
    if existing_target.first():
        raise HTTPException(status_code=400, detail="Target already exists")
        
    db_target = TargetProfile(
        github_username=target.github_username,
        known_affiliation=target.known_affiliation
    )
    session.add(db_target)
    await session.commit()
    await session.refresh(db_target)
    
    return {"message": "Target added successfully", "target_id": db_target.id}

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@app.get("/auth/github/login")
async def github_login():
    """
    Redirects to GitHub OAuth consent screen.
    """
    scope = "user:email read:user"
    return {
        "url": f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope={scope}"
    }

@app.get("/auth/github/callback")
async def github_callback(code: str, session: AsyncSession = Depends(get_async_session)):
    """
    Exchanges GitHub code for access token, gets user, then issues JWT.
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get GitHub access token")
            
        # Get user info
        github_user = await get_github_user(access_token)
        if not github_user:
            raise HTTPException(status_code=400, detail="Failed to fetch user from GitHub")
            
        github_id = str(github_user["id"])
        username = github_user["login"]
        
        # Check for existing profile by github_username or github_id
        result = await session.execute(
            select(TargetProfile).where(
                (TargetProfile.github_id == github_id) | 
                (TargetProfile.github_username == username)
            )
        )
        profile = result.scalars().first()
        
        if not profile:
            # Create a new profile if they don't exist yet
            profile = TargetProfile(
                github_username=username,
                github_id=github_id,
                is_claimed=True,
                last_login=datetime.now(timezone.utc),
                bio=github_user.get("bio"),
                location=github_user.get("location"),
                company=github_user.get("company")
            )
            session.add(profile)
        else:
            # Update existing profile
            profile.github_id = github_id
            profile.is_claimed = True
            profile.last_login = datetime.now(timezone.utc)
            session.add(profile)
            
        await session.commit()
        
        # Create JWT
        jwt_token = create_access_token({"sub": github_id, "username": username})
        return {"access_token": jwt_token, "token_type": "bearer"}

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    open_to_work: Optional[bool] = None

@app.get("/profile/me", summary="Get current user profile")
async def get_my_profile(
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Returns the TargetProfile associated with the logged-in user.
    """
    result = await session.execute(
        select(TargetProfile).where(TargetProfile.github_id == user.github_id)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.patch("/profile/me", summary="Update current user profile")
async def update_my_profile(
    update: ProfileUpdate,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Updates the TargetProfile associated with the logged-in user.
    """
    result = await session.execute(
        select(TargetProfile).where(TargetProfile.github_id == user.github_id)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile

class MatchmakingQuery(BaseModel):
    capability_query: str

@app.post("/matchmaking/suggest", summary="Suggest talent based on technical capability")
async def suggest_talent(
    query: MatchmakingQuery,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Uses LLM to rank profiles based on a specific capability request 
    (e.g., 'Need someone who knows PX4 and ROS2').
    """
    # Fetch top 50 profiles by score
    res = await session.execute(
        select(TargetProfile)
        .where(TargetProfile.brief_summary != None)
        .order_by(TargetProfile.defense_relevance_score.desc())
        .limit(50)
    )
    profiles = res.scalars().all()
    if not profiles:
        return {"suggestions": []}

    # Prepare context for Claude to rank
    candidates_data = [
        {
            "username": p.github_username,
            "brief": p.brief_summary[:500], # Snippets for context
            "score": p.defense_relevance_score,
            "open_to_work": p.open_to_work
        } for p in profiles
    ]

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Capability Request: {query.capability_query}

Candidates:
{json.dumps(candidates_data, default=str)}

Rank the top 5 candidates that best match the capability request. 
Return ONLY a JSON list of usernames in order of relevance. 
Example: ["user1", "user2"]"""

    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()
        
        # Simple JSON extraction
        if "[" in content and "]" in content:
            ranked_usernames = json.loads(content[content.find("["):content.rfind("]")+1])
            
            # Map back to full profile objects
            suggestions = []
            profile_map = {p.github_username: p for p in profiles}
            for uname in ranked_usernames:
                if uname in profile_map:
                    suggestions.append(profile_map[uname])
            
            return {"suggestions": suggestions}
        
        return {"suggestions": []}
    except Exception as e:
        logger.error(f"Matchmaking error: {e}")
        return {"suggestions": []}

@app.post("/sync", summary="Manually trigger a sync job")
async def trigger_sync(background_tasks: BackgroundTasks):
    """
    Manually triggers the ingestion and intelligence pipeline in the background.
    """
    async def manual_sync():
        async with AsyncSessionLocal() as session:
            try:
                await run_discovery_pipeline(session)
                await run_algorithmic_discovery(session)
                await run_ingestion_pipeline(session)
                await run_intelligence_pipeline(session)
                logger.info("Manual sync job completed.")
            except Exception as e:
                logger.error(f"Error during manual sync job: {e}")

    background_tasks.add_task(manual_sync)
    return {"message": "Sync job has been pushed to background tasks."}

@app.post("/discovery/keywords", summary="Add a new discovery keyword")
async def add_keyword(
    keyword: str, 
    category: str = "general",
    session: AsyncSession = Depends(get_async_session)
):
    """
    Adds a new technical keyword to the algorithmic discovery engine.
    """
    db_kw = DiscoveryKeyword(keyword=keyword, category=category)
    session.add(db_kw)
    await session.commit()
    return {"message": "Keyword added successfully"}

@app.get("/discovery/keywords/list", summary="List all active discovery keywords")
async def list_keywords(session: AsyncSession = Depends(get_async_session)):
    """
    Returns the list of active technical keywords used for algorithmic discovery.
    """
    res = await session.execute(select(DiscoveryKeyword))
    keywords = res.scalars().all()
    return {"keywords": keywords}

@app.get("/search/profiles", summary="Search and filter discovered talent")
async def search_profiles(
    domain: str | None = None,
    location: str | None = None,
    min_score: float = 0.0,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Search engineers by domain, location, and defense relevance score.
    """
    query = select(TargetProfile).where(TargetProfile.status == TargetStatus.ACTIVE)
    
    if location:
        query = query.where(TargetProfile.location.ilike(f"%{location}%"))
    if min_score > 0:
        query = query.where(TargetProfile.defense_relevance_score >= min_score)
        
    result = await session.execute(query.order_by(TargetProfile.defense_relevance_score.desc()).limit(100))
    profiles = result.scalars().all()
    
    # In a real app we'd join on IntelligenceLog to filter by domain properly.
    return {"profiles": profiles}

@app.get("/feed", summary="Get the real-time anomaly signal feed")
async def get_signal_feed(session: AsyncSession = Depends(get_async_session)):
    """
    Returns the latest anomalous events analyzed by Claude.
    """
    query = (
        select(IntelligenceLog, TrackedEvent, TargetProfile)
        .join(TrackedEvent, TrackedEvent.id == IntelligenceLog.event_id)
        .join(TargetProfile, TargetProfile.id == TrackedEvent.profile_id)
        .where(IntelligenceLog.is_anomalous == True)
        .order_by(IntelligenceLog.analyzed_at.desc())
        .limit(50)
    )
    result = await session.execute(query)
    feed = []
    for log, event, profile in result.all():
        feed.append({
            "log_id": log.id,
            "username": profile.github_username,
            "domain": log.domain,
            "summary": log.summary,
            "analyzed_at": log.analyzed_at,
            "repo_name": event.repo_name,
            "event_type": event.event_type
        })
        
    return {"feed": feed}
