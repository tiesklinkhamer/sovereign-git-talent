from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class TargetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class TargetProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    github_username: str = Field(index=True, unique=True, description="The GitHub handle of the target")
    known_affiliation: Optional[str] = Field(default=None, description="e.g., Anduril, Palantir")
    status: TargetStatus = Field(default=TargetStatus.ACTIVE)
    last_etag: Optional[str] = Field(default=None, description="Last ETag for GitHub API conditional requests")
    last_polled_at: Optional[datetime] = Field(default=None)
    
    # Identity & Community
    github_id: Optional[str] = Field(default=None, index=True, description="Unique GitHub User ID for OAuth")
    is_claimed: bool = Field(default=False, index=True, description="Whether the profile has been claimed by a user")
    last_login: Optional[datetime] = Field(default=None)
    
    # Intelligence Synthesis
    brief_summary: Optional[str] = Field(default=None, description="Claude-synthesized holistic talent brief")
    last_brief_generated_at: Optional[datetime] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Enriched Profile Data
    bio: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    company: Optional[str] = Field(default=None)
    blog: Optional[str] = Field(default=None)
    defense_relevance_score: float = Field(default=0.0, description="Cumulative score prioritizing defense utility")
    open_to_work: bool = Field(default=False)
    
    events: List["TrackedEvent"] = Relationship(back_populates="profile")

class TrackedEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="targetprofile.id")
    event_type: str = Field(index=True, description="PushEvent, StarEvent, CreateEvent, etc.")
    repo_name: Optional[str] = Field(default=None)
    github_event_id: str = Field(unique=True, index=True)
    event_created_at: datetime = Field(index=True)
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    
    profile: "TargetProfile" = Relationship(back_populates="events")
    intelligence_logs: List["IntelligenceLog"] = Relationship(back_populates="event")

class IntelligenceLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="trackedevent.id")
    is_anomalous: bool = Field(default=False, index=True)
    domain: Optional[str] = Field(default=None, description="E.g., drone-swarms, cryptography")
    summary: str = Field(description="Claude's reasoning and summary of the event")
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    event: "TrackedEvent" = Relationship(back_populates="intelligence_logs")
