import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.user import UserService
from src.db.models.user import User
from src.db.models.auth import TokenType

@pytest.fixture
def user_service():
    return UserService()

@pytest.mark.asyncio
async def test_create_activation_token(user_service):
    """Verifies that create_activation_token correctly calls auth_service."""
    db = AsyncMock()
    user_id = 1
    
    with patch("src.services.auth.auth_service.create_token", new_callable=AsyncMock) as mock_create_token:
        mock_token_obj = MagicMock()
        mock_token_obj.token = "secure_token_123"
        mock_create_token.return_value = mock_token_obj
        
        token = await user_service.create_activation_token(db, user_id=user_id)
        
        assert token == "secure_token_123"
        mock_create_token.assert_called_once_with(
            db, user_id=user_id, token_type=TokenType.ACTIVATION, expires_in_minutes=2880
        )

@pytest.mark.asyncio
async def test_deactivate_invalidates_tokens(user_service):
    """Verifies that deactivating a user also invalidates their tokens."""
    db = AsyncMock()
    user = User(id=1, email="test@example.com", is_active=True)
    
    # We expect an UPDATE statement to be executed on UserToken
    with patch("src.services.user.update") as mock_update:
        await user_service.deactivate(db, db_obj=user)
        
        assert user.is_active is False
        db.execute.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

@pytest.mark.asyncio
async def test_reactivate(user_service):
    """Verifies that reactivating a user sets is_active to True."""
    db = AsyncMock()
    user = User(id=1, is_active=False)
    
    await user_service.reactivate(db, db_obj=user)
    
    assert user.is_active is True
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)
