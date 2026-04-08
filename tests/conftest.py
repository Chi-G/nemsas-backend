import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from src.db.base import Base, get_db
from src.core.config import settings
from src.main import app

# Use an in-memory SQLite database for testing, or a separate test DB. Since we use asyncpg heavily, SQLite might have dialect issues with Enums or JSONB if we used them extensively.
# But for standard models, async sqlite is okay. Let's try to use a test postgres db if possible, or just standard sqlite for simplicity.
# Given potential dialect issues with asyncpg vs aiosqlite, we will use a dedicated test DB URL, defaulting to sqlite purely for speed if one isn't provided.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()
