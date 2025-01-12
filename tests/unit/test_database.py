"""Unit tests for database functionality."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path

from judgarr.database.manager import DatabaseManager, UserRequest, UserStats
from judgarr.core.punishments import PunishmentLevel
from judgarr.shared.types import UserId

@pytest_asyncio.fixture
async def db():
    """Create a test database."""
    with tempfile.NamedTemporaryFile() as temp_db:
        db_path = Path(temp_db.name)
        manager = DatabaseManager(db_path)
        await manager.initialize()
        yield manager
        await manager.close()

@pytest.mark.asyncio
async def test_database_initialization(db: DatabaseManager):
    """Test database initialization."""
    # Database should already be initialized by fixture
    # Just verify it exists and has the expected tables
    tables = await db.get_tables()
    assert "users" in tables
    assert "requests" in tables
    assert "punishments" in tables

@pytest.mark.asyncio
async def test_user_request_management(db: DatabaseManager):
    """Test user request management functions."""
    user_id = UserId("test_user")
    now = datetime.now(timezone.utc)

    # Test creating request
    request = UserRequest(
        id=0,  # Will be set by database
        user_id=user_id,
        media_id="movie_123",
        media_type="movie",
        request_date=now,
        size_bytes=1000000,
        status="pending"
    )
    request_id = await db.add_request(request)
    assert request_id is not None

    # Get the request
    request = await db.get_request(request_id)
    assert request is not None
    assert request.user_id == user_id
    assert request.media_id == "movie_123"
    assert request.size_bytes == 1000000

    # Update request size
    await db.update_request_size(request_id, 2000000)
    updated_request = await db.get_request(request_id)
    assert updated_request is not None, "Failed to retrieve updated request"
    assert updated_request.size_bytes == 2000000

@pytest.mark.asyncio
async def test_user_punishment_management(db: DatabaseManager):
    """Test user punishment management functions."""
    user_id = UserId("test_user")
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=7)

    # Test creating punishment
    punishment = await db.create_punishment(
        user_id=user_id,
        level=PunishmentLevel.WARNING.value,
        start_date=now,
        end_date=end_date,
        cooldown_days=7,
        request_reduction=50,
        data_usage=5000000000,
        reason="Excessive usage"
    )
    assert punishment is not None
    assert punishment.user_id == user_id
    assert punishment.level == PunishmentLevel.WARNING.value

    # Test getting active punishment
    active = await db.get_active_punishment(user_id)
    assert active is not None
    assert active.user_id == user_id
    assert active.level == PunishmentLevel.WARNING.value

    # Test deactivating punishment
    await db.deactivate_punishment(user_id, reason="Test complete")
    active = await db.get_active_punishment(user_id)
    assert active is None

@pytest.mark.asyncio
async def test_user_stats_management(db: DatabaseManager):
    """Test user statistics management functions."""
    user_id = UserId("test_user")

    # Test creating user stats
    stats = UserStats(
        user_id=user_id,
        username="test_user",
        total_data_usage=0,
        total_requests=0,
        punishment_level=0,
        cooldown_days=0,
        request_limit=10
    )
    await db.create_user_stats(stats)

    # Get user stats
    saved_stats = await db.get_user_stats(user_id)
    assert saved_stats is not None
    assert saved_stats.user_id == user_id
    assert saved_stats.username == "test_user"
    assert saved_stats.total_requests == 0
    assert saved_stats.request_limit == 10

    # Update user stats
    stats.total_requests = 5
    stats.total_data_usage = 1000000
    await db.update_user_stats(stats)

    # Verify updates
    updated_stats = await db.get_user_stats(user_id)
    assert updated_stats is not None
    assert updated_stats.total_requests == 5
    assert updated_stats.total_data_usage == 1000000

@pytest.mark.asyncio
async def test_user_limit_adjustment(db: DatabaseManager):
    """Test user request limit adjustment."""
    user_id = UserId("test_user")

    # Create initial stats
    stats = UserStats(
        user_id=user_id,
        username="test_user",
        total_data_usage=0,
        total_requests=0,
        punishment_level=0,
        cooldown_days=0,
        request_limit=10
    )
    await db.create_user_stats(stats)
    
    # Get initial stats
    saved_stats = await db.get_user_stats(user_id)
    assert saved_stats is not None
    assert saved_stats.request_limit == 10

    # Adjust limit up
    await db.adjust_user_limit(user_id, 5, "Testing increase")
    updated_stats = await db.get_user_stats(user_id)
    assert updated_stats is not None
    assert updated_stats.request_limit == 15

    # Adjust limit down
    await db.adjust_user_limit(user_id, -3, "Testing decrease")
    final_stats = await db.get_user_stats(user_id)
    assert final_stats is not None
    assert final_stats.request_limit == 12
