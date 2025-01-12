"""Unit tests for user management functionality."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from judgarr.core.user_management import UserStatus, UserManager
from judgarr.database.models import UserData, UserStats, UserPunishment
from judgarr.shared.types import UserId

@pytest.fixture(scope="function")
def mock_db_manager():
    """Create a mock database manager."""
    return AsyncMock()

@pytest.fixture(scope="function")
def mock_punishment_manager():
    """Create a mock punishment manager."""
    return AsyncMock()

@pytest.fixture(scope="function")
def user_manager(mock_db_manager, mock_punishment_manager):
    """Create a UserManager instance with mock dependencies."""
    return UserManager(
        db_manager=mock_db_manager,
        punishment_manager=mock_punishment_manager
    )

class TestUserStatus:
    """Test cases for UserStatus class."""
    
    def test_user_status_initialization(self):
        """Test UserStatus initialization with basic attributes."""
        user_id = UserId("test_user")
        status = UserStatus(
            user_id=user_id,
            total_requests=10,
            total_data_usage=1024,
            current_punishment=None,
            last_request_date=None
        )
        
        assert status.user_id == user_id
        assert status.total_requests == 10
        assert status.total_data_usage == 1024
        assert status.current_punishment is None
        assert status.last_request_date is None
        assert not status.is_punished
        assert status.remaining_cooldown_days == 0
    
    def test_is_punished_with_active_punishment(self):
        """Test is_punished property with an active punishment."""
        now = datetime.now()
        punishment = UserPunishment(
            id=1,
            user_id=UserId("test_user"),
            level=1,
            cooldown_days=5,
            request_reduction=2,
            data_usage=1024,
            start_date=now,
            end_date=now + timedelta(days=5),
            reason="Test punishment"
        )
        
        status = UserStatus(
            user_id=UserId("test_user"),
            total_requests=10,
            total_data_usage=1024,
            current_punishment=punishment
        )
        
        assert status.is_punished
        assert status.remaining_cooldown_days > 0

class TestUserManager:
    """Test cases for UserManager class."""
    
    @pytest.mark.asyncio
    async def test_get_user_status(self, user_manager, mock_db_manager):
        """Test getting user status."""
        user_id = UserId("test_user")
        now = datetime.now()
        mock_user_data = UserData(
            user_id=user_id,
            total_requests=10,
            request_frequency=1.0,
            movie_requests=5,
            tv_requests=5,
            last_processed=now
        )
        mock_user_stats = UserStats(
            user_id=user_id,
            username="test_user",
            total_requests=5,
            total_data_usage=2048,
            punishment_level=0,
            cooldown_days=0,
            request_limit=100,
            current_punishment_id=None,
            last_request_date=now
        )

        # Set get_active_punishment to return None
        mock_db_manager.get_user_data.return_value = mock_user_data
        mock_db_manager.get_user_stats.return_value = mock_user_stats
        user_manager.punishment_manager.get_active_punishment = AsyncMock(return_value=None)

        status = await user_manager.get_user_status(user_id)

        assert status.user_id == user_id
        assert status.total_requests == 5
        assert status.total_data_usage == 2048
        assert not status.is_punished
    
    @pytest.mark.asyncio
    async def test_reset_user_status(self, user_manager, mock_db_manager, mock_punishment_manager):
        """Test resetting user status."""
        user_id = UserId("test_user")
        reason = "Administrative reset"
        now = datetime.now()
        
        mock_stats = UserStats(
            user_id=user_id,
            username="test_user",
            total_requests=0,
            total_data_usage=0,
            punishment_level=0,
            cooldown_days=0,
            request_limit=100,
            current_punishment_id=None,
            last_request_date=now
        )
        
        mock_punishment_manager.override_punishment.return_value = None
        mock_db_manager.get_user_stats.return_value = mock_stats
        mock_db_manager.update_user_stats.return_value = None
        
        await user_manager.reset_user_status(user_id, reason)
        
        mock_db_manager.remove_user_punishments.assert_called_once_with(user_id)
        mock_db_manager.update_user_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_adjust_request_limit(self, user_manager, mock_db_manager, mock_punishment_manager):
        """Test adjusting user request limit."""
        user_id = UserId("test_user")
        adjustment = -5
        reason = "Test adjustment"
        now = datetime.now()
        
        mock_punishment = UserPunishment(
            id=1,
            user_id=user_id,
            level=1,
            cooldown_days=5,
            request_reduction=5,
            data_usage=0,
            start_date=now,
            end_date=now + timedelta(days=5),
            reason=reason
        )
        mock_stats = UserStats(
            user_id=user_id,
            username="test_user",
            total_requests=10,
            total_data_usage=1024,
            punishment_level=1,
            cooldown_days=5,
            request_limit=95,
            current_punishment_id=mock_punishment.id,
            last_request_date=now
        )
        
        mock_punishment_manager.process_user_behavior.return_value = mock_punishment
        mock_db_manager.get_user_stats.return_value = mock_stats
        mock_db_manager.update_user_stats.return_value = None
        
        await user_manager.adjust_request_limit(user_id, adjustment, reason)
        
        mock_db_manager.adjust_user_limit.assert_called_once_with(
            user_id, adjustment, reason
        )
    
    @pytest.mark.asyncio
    async def test_list_punished_users(self, user_manager, mock_db_manager):
        """Test listing punished users."""
        now = datetime.now()
        mock_punishments = [
            UserPunishment(
                id=1,
                user_id=UserId("user1"),
                level=1,
                cooldown_days=5,
                request_reduction=2,
                data_usage=1024,
                start_date=now,
                end_date=now + timedelta(days=5),
                reason="Test punishment 1"
            ),
            UserPunishment(
                id=2,
                user_id=UserId("user2"),
                level=2,
                cooldown_days=7,
                request_reduction=3,
                data_usage=2048,
                start_date=now,
                end_date=now + timedelta(days=7),
                reason="Test punishment 2"
            )
        ]
        
        mock_stats = UserStats(
            user_id=UserId("user1"),
            username="user1",
            total_requests=5,
            total_data_usage=2048,
            punishment_level=1,
            cooldown_days=5,
            request_limit=95,
            current_punishment_id=mock_punishments[0].id,
            last_request_date=now
        )
        
        mock_db_manager.get_punished_users.return_value = [mock_stats]
        mock_db_manager.get_punishment.return_value = mock_punishments[0]
        
        punished_users = await user_manager.list_punished_users()
        
        assert len(punished_users) > 0
        assert all(user.is_punished for user in punished_users)
