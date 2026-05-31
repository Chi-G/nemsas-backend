import sys
import os
import importlib.util
from importlib.abc import Loader

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Custom import redirection finder to load src.* from app.* without duplicate execution
class SrcToAppFinder:
    def find_spec(self, fullname, path, target=None):
        if fullname == "src" or fullname.startswith("src."):
            # Map legacy namespaces to modern structure
            if fullname.startswith("src.db.models"):
                app_name = fullname.replace("src.db.models", "app.models", 1)
            elif fullname.startswith("src.db.schemas"):
                app_name = fullname.replace("src.db.schemas", "app.schemas", 1)
            else:
                app_name = fullname.replace("src", "app", 1)
            try:
                # If already imported under 'app', reuse it directly
                if app_name in sys.modules:
                    sys.modules[fullname] = sys.modules[app_name]
                    spec = importlib.util.find_spec(app_name)
                    if spec is not None:
                        spec.name = fullname
                        class DummyLoader(Loader):
                            def create_module(self, spec):
                                return sys.modules[app_name]
                            def exec_module(self, module):
                                pass
                        spec.loader = DummyLoader() # type: ignore
                        return spec
                
                # Otherwise, find the spec and delegate loading
                spec = importlib.util.find_spec(app_name)
                if spec is not None:
                    spec.name = fullname
                    class DelegatingLoader(Loader):
                        def create_module(self, spec):
                            mod = importlib.import_module(app_name)
                            sys.modules[fullname] = mod
                            return mod
                        def exec_module(self, module):
                            pass
                    spec.loader = DelegatingLoader() # type: ignore
                    return spec
            except Exception:
                pass
        return None

sys.meta_path.insert(0, SrcToAppFinder())

import pytest
import pytest_asyncio
from app.core.security import create_access_token
from app.models.user import User
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from app.db.session import Base, get_db
from app.core.config import settings
from app.main import app as fastapi_app

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

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(db: AsyncSession):
    yield
    # Cleanup logic
    from app.models.partner import Partner, Pledge, FacilityRequest
    from app.models.audit import SystemAuditLog
    from app.models.transfer_form import TransferForm
    
    await db.execute(delete(Pledge))
    await db.execute(delete(FacilityRequest))
    await db.execute(delete(Partner))
    await db.execute(delete(SystemAuditLog))
    await db.execute(delete(TransferForm))
    await db.execute(delete(User).where(User.email != "admin@test.com"))
    await db.commit()

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    fastapi_app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def get_user_token_headers():
    def _get_user_token_headers(user: User) -> dict:
        from typing import cast as tcast, Optional
        access_token = create_access_token(
            subject=str(user.id), 
            role=tcast(Optional[str], user.user_type),
            state_id=tcast(Optional[int], user.state_id)
        )
        return {"Authorization": f"Bearer {access_token}"}
    return _get_user_token_headers

@pytest_asyncio.fixture
async def admin_token_headers(db: AsyncSession, get_user_token_headers) -> dict:
    # Check if admin user exists
    result = await db.execute(select(User).where(User.email == "admin@test.com"))
    admin_user = result.scalars().first()
    
    if not admin_user:
        admin_user = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            user_name="admin",
            hashed_password="hash",
            is_active=True,
            user_type="SUPERADMINISTRATOR"
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
    
    return get_user_token_headers(admin_user)
