"""Integration tests for end-to-end workflows."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path

from judgarr.database.manager import DatabaseManager
from judgarr.core.user_management import UserManager
from judgarr.core.punishments import PunishmentManager
from judgarr.shared.types import UserId
from judgarr.database.models import UserStats, UserRequest

@pytest_asyncio.fixture
async def db():
    """Create a test database."""
    with tempfile.NamedTemporaryFile() as temp_db:
        db_path = Path(temp_db.name)
        manager = DatabaseManager(db_path)
        await manager.initialize()
        yield manager

@pytest_asyncio.fixture
async def punishment_manager(db: DatabaseManager):
    """Create a punishment manager for testing."""
    return PunishmentManager(db_manager=db)

@pytest_asyncio.fixture
async def user_manager(db: DatabaseManager, punishment_manager: PunishmentManager):
    """Create a user manager for testing."""
    return UserManager(db_manager=db, punishment_manager=punishment_manager)

@pytest.mark.asyncio
async def test_user_request_workflow(user_manager: UserManager):
    """Test complete user request workflow."""
    user_id = UserId("test_user")
    datetime.now(timezone.utc)
    
    # Create initial user stats
    stats = UserStats(
        user_id=user_id,
        username="test_user",
        total_data_usage=0,
        total_requests=0,
        punishment_level=0,
        cooldown_days=0,
        request_limit=10
    )
    await user_manager.db.create_user_stats(stats)
    
    # Add a request
    request = UserRequest(
        id=0,  # Will be set by database
        user_id=user_id,
        media_id="movie_123",
        media_type="movie",
        request_date=datetime.now(timezone.utc),
        size_bytes=1000000,
        status="pending"
    )
    request_id = await user_manager.db.add_request(request)
    assert request_id is not None
    
    # Verify request
    saved_request = await user_manager.db.get_request(request_id)
    assert saved_request is not None
    assert saved_request.user_id == user_id
    assert saved_request.media_id == "movie_123"
    
    # Check user stats were updated
    stats = await user_manager.db.get_user_stats(user_id)
    assert stats is not None
    assert stats.total_requests == 1
    assert stats.total_data_usage == 1000000

@pytest.mark.asyncio
async def test_punishment_workflow(user_manager: UserManager, punishment_manager: PunishmentManager):
    """Test complete punishment workflow."""
    user_id = UserId("test_user")
    now = datetime.now(timezone.utc)
    
    # Create initial user stats
    stats = UserStats(
        user_id=user_id,
        username="test_user",
        total_data_usage=0,
        total_requests=0,
        punishment_level=0,
        cooldown_days=0,
        request_limit=10
    )
    await user_manager.db.create_user_stats(stats)
    
    # Add a punishment
    end_date = now + timedelta(days=7)
    punishment = await punishment_manager.create_punishment(
        user_id=user_id,
        level=1,
        start_date=now,
        end_date=end_date,
        cooldown_days=7,
        request_reduction=50,
        data_usage=1000000000000,
        reason="Excessive usage"
    )
    assert punishment is not None
    assert punishment.user_id == user_id
    assert punishment.level == 1
    
    # Check user stats were updated
    stats = await user_manager.db.get_user_stats(user_id)
    assert stats is not None
    assert stats.punishment_level == 1
    assert stats.cooldown_days == 7
    assert stats.request_limit == 5  # Reduced by 50%
