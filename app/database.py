import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Default to a local postgres instance if not provided
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:secret@localhost:5432/sovereign_git")

# Synchronous Engine (used for setup, metadata creation, and simple scripts)
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    from app.models import TargetProfile, TrackedEvent, IntelligenceLog
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Asynchronous Engine (used primarily in FastAPI endpoints for better performance)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2", "postgresql+asyncpg", 1) \
                                 if "postgresql+psycopg2" in DATABASE_URL \
                                 else DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
