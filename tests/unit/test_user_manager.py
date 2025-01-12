import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock

from judgarr.core.user_management import UserManager, UserStatus
from judgarr.database.models import UserRequest, UserPunishment, UserId, UserStats
from judgarr.database.manager import DatabaseManager
from judgarr.core.punishments.manager import PunishmentManager

@pytest.fixture
def db_manager():
    """Create a mock database manager."""
    mock_db = Mock(spec=DatabaseManager)
    mock_db.get_user_stats = AsyncMock()
    mock_db.get_user_requests = AsyncMock()
    mock_db.add_request = AsyncMock()
    return mock_db

@pytest.fixture
def punishment_manager():
    """Create a mock punishment manager."""
    mock_pm = Mock(spec=PunishmentManager)
    mock_pm.process_user_behavior = AsyncMock()
    mock_pm.get_active_punishment = AsyncMock()
    return mock_pm

@pytest.fixture
def user_manager(db_manager, punishment_manager):
    """Create a UserManager instance with mock dependencies."""
    return UserManager(db_manager=db_manager, punishment_manager=punishment_manager)

@pytest.mark.asyncio
async def test_get_user_status_no_requests(user_manager, db_manager):
    """Test getting status for user with no requests."""
    user_id = UserId("test_user")
    db_manager.get_user_stats.return_value = None
    db_manager.get_user_requests.return_value = []
    user_manager.punishment_manager.get_active_punishment.return_value = None
    
    status = await user_manager.get_user_status(user_id)
    
    assert isinstance(status, UserStatus)
    assert status.user_id == user_id
    assert status.total_requests == 0
    assert status.total_data_usage == 0
    assert status.current_punishment is None

@pytest.mark.asyncio
async def test_get_user_status_with_requests(user_manager, db_manager):
    """Test getting status for user with existing requests."""
    user_id = UserId("test_user")
    now = datetime.now(timezone.utc)
    
    # Mock user stats
    stats = UserStats(
        user_id=user_id,
        username="test_user",
        total_data_usage=3000000,
        total_requests=2,
        punishment_level=0,
        cooldown_days=0,
        request_limit=100
    )
    db_manager.get_user_stats.return_value = stats
    
    # Mock requests in database
    requests = [
        UserRequest(
            id=1,
            user_id=user_id,
            media_id="movie1",
            media_type="movie",
            request_date=now - timedelta(days=1),
            size_bytes=1000000,
            status="pending"
        ),
        UserRequest(
            id=2,
            user_id=user_id,
            media_id="series1",
            media_type="series",
            request_date=now,
            size_bytes=2000000,
            status="approved"
        )
    ]
    
    db_manager.get_user_requests.return_value = requests
    user_manager.punishment_manager.get_active_punishment.return_value = None
    
    status = await user_manager.get_user_status(user_id)
    
    assert isinstance(status, UserStatus)
    assert status.user_id == user_id
    assert status.total_requests == 2
    assert status.total_data_usage == 3000000  # From user stats
    assert status.last_request_date == now

@pytest.mark.asyncio
async def test_get_user_status_with_punishment(user_manager, db_manager):
    """Test getting status for user with active punishment."""
    user_id = UserId("test_user")
    now = datetime.now(timezone.utc)
    
    # Mock user stats
    stats = UserStats(
        user_id=user_id,
        username="test_user",
        total_data_usage=1000000,
        total_requests=1,
        punishment_level=1,
        cooldown_days=1,
        request_limit=50
    )
    db_manager.get_user_stats.return_value = stats
    
    punishment = UserPunishment(
        id=1,
        user_id=user_id,
        level=1,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=1),
        cooldown_days=1,
        request_reduction=50,
        data_usage=1000000,
        is_active=True
    )
    
    db_manager.get_user_requests.return_value = []
    user_manager.punishment_manager.get_active_punishment.return_value = punishment
    
    status = await user_manager.get_user_status(user_id)
    
    assert isinstance(status, UserStatus)
    assert status.current_punishment == punishment

@pytest.mark.asyncio
async def test_add_request_success(user_manager, db_manager):
    """Test successfully adding a new request."""
    user_id = UserId("test_user")
    media_id = "movie1"
    media_type = "movie"
    size_bytes = 1000000
    
    # Mock that there is no active punishment
    user_manager.punishment_manager.get_active_punishment.return_value = None
    
    # Mock database to return request ID
    db_manager.add_request.return_value = 1
    
    result = await user_manager.add_request(
        user_id=user_id,
        media_id=media_id,
        media_type=media_type,
        size_bytes=size_bytes
    )
    
    assert isinstance(result, UserRequest)
    assert result.id == 1
    assert result.user_id == user_id
    assert result.media_id == media_id
    assert result.media_type == media_type
    assert result.size_bytes == size_bytes
    assert result.status == "pending"
    db_manager.add_request.assert_called_once()

@pytest.mark.asyncio
async def test_add_request_with_active_punishment(user_manager, db_manager, punishment_manager):
    """Test adding request when user has active punishment."""
    user_id = UserId("test_user")
    now = datetime.now(timezone.utc)
    
    # Setup active punishment
    punishment = UserPunishment(
        id=1,
        user_id=user_id,
        level=1,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=1),
        cooldown_days=1,
        request_reduction=50,
        data_usage=1000000,
        is_active=True
    )
    
    user_manager.punishment_manager.get_active_punishment.return_value = punishment
    
    # Attempt to add request
    with pytest.raises(ValueError, match="User has active punishment"):
        await user_manager.add_request(
            user_id=user_id,
            media_id="movie1",
            media_type="movie",
            size_bytes=1000000
        )
    
    # Verify no request was added
    db_manager.add_request.assert_not_called()
