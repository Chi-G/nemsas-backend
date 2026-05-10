from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# For Neon/asyncpg, we pass SSL requirement via connect_args
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    connect_args={
        "ssl": "require",
        "statement_cache_size": 0,
    },
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
