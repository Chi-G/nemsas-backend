import pytest
import pytest_asyncio
from src.core.security import create_access_token
from src.db.models.user import User, Role
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from src.db.base import Base, get_db
from src.core.config import settings
from src.core.rbac import RoleName
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
    
    # Seed roles
    async with TestingSessionLocal() as db:
        for role_name in RoleName:
            result = await db.execute(select(Role).where(Role.name == role_name))
            if not result.scalars().first():
                db.add(Role(name=role_name))
        await db.commit()
        
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(db: AsyncSession):
    yield
    # Cleanup logic
    from sqlalchemy import delete
    from src.db.models.user import User, Role
    from src.db.models.partner import Partner, Pledge, FacilityRequest, Facility
    from src.db.models.auth import UserToken
    from src.db.models.reference import SystemAuditLog
    
    await db.execute(delete(Pledge))
    await db.execute(delete(FacilityRequest))
    await db.execute(delete(Partner))
    await db.execute(delete(UserToken))
    await db.execute(delete(SystemAuditLog))
    await db.execute(delete(User).where(User.email != "admin@test.com")) # Keep admin seeded for speed
    await db.commit()

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def get_user_token_headers():
    def _get_user_token_headers(user: User) -> dict:
        access_token = create_access_token(subject=str(user.id))
        return {"Authorization": f"Bearer {access_token}"}
    return _get_user_token_headers

@pytest_asyncio.fixture
async def admin_token_headers(db: AsyncSession, get_user_token_headers) -> dict:
    # Check if admin role exists
    result = await db.execute(select(Role).where(Role.name == RoleName.NEMSAS_ADMIN))
    admin_role = result.scalars().first()
    if not admin_role:
        admin_role = Role(name=RoleName.NEMSAS_ADMIN, description="NEMSAS Administrator")
        db.add(admin_role)
        await db.flush()
        
    # Check if admin user exists
    result = await db.execute(select(User).where(User.email == "admin@test.com"))
    admin_user = result.scalars().first()
    
    if not admin_user:
        admin_user = User(
            email="admin@test.com",
            name="Admin",
            hashed_password="hash",
            is_active=True,
            role_id=admin_role.id
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
    
    return get_user_token_headers(admin_user)
