"""Integration tests for CLI functionality."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile

from judgarr.cli.main import cli

# Use Overseerr user ID 2 since ID 1 is admin with no limits
TEST_USER_ID = "2"

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile() as temp_db:
        yield Path(temp_db.name)

def test_init_command(runner: CliRunner, db_path: Path):
    """Test database initialization command."""
    result = runner.invoke(cli, ['init', '--db', str(db_path)])
    assert result.exit_code == 0
    assert "Database initialized" in result.output
    assert db_path.exists()

def test_user_stats_command(runner: CliRunner, db_path: Path):
    """Test user stats command."""
    # First initialize the database
    runner.invoke(cli, ['init', '--db', str(db_path)])
    
    # Test getting stats for user that hasn't made any requests yet
    result = runner.invoke(cli, ['user', 'stats', '--user-id', TEST_USER_ID, '--db', str(db_path)])
    assert result.exit_code == 0
    assert "No stats found" in result.output

def test_request_tracking(runner: CliRunner, db_path: Path):
    """Test request tracking functionality."""
    # Initialize database
    runner.invoke(cli, ['init', '--db', str(db_path)])
    
    # Track a new request
    result = runner.invoke(cli, [
        'request', 'add',
        '--user-id', TEST_USER_ID,
        '--media-id', 'movie_123',
        '--media-type', 'movie',
        '--size', '1000000',
        '--db', str(db_path)
    ])
    assert result.exit_code == 0
    assert "Request added successfully" in result.output
    
    # Verify request is tracked
    result = runner.invoke(cli, [
        'request', 'list',
        '--user-id', TEST_USER_ID,
        '--db', str(db_path)
    ])
    assert result.exit_code == 0
    assert "movie_123 (movie) - 1000000 bytes" in result.output
    
    # Check updated user stats
    result = runner.invoke(cli, ['user', 'stats', '--user-id', TEST_USER_ID, '--db', str(db_path)])
    assert result.exit_code == 0
    assert TEST_USER_ID in result.output
    assert "1000000" in result.output  # Total data usage should be updated

def test_punishment_management(runner: CliRunner, db_path: Path):
    """Test punishment management functionality."""
    # Initialize database
    runner.invoke(cli, ['init', '--db', str(db_path)])
    
    # Add a punishment for excessive usage
    result = runner.invoke(cli, [
        'punishment', 'add',
        '--user-id', TEST_USER_ID,
        '--level', '1',
        '--days', '7',
        '--reason', 'Excessive usage',
        '--db', str(db_path)
    ])
    assert result.exit_code == 0
    assert "Punishment added successfully" in result.output
    
    # Verify punishment is tracked
    result = runner.invoke(cli, [
        'punishment', 'list',
        '--user-id', TEST_USER_ID,
        '--db', str(db_path)
    ])
    assert result.exit_code == 0
    assert "Level 1 - Excessive usage (7 days)" in result.output
    
    # Remove punishment
    result = runner.invoke(cli, [
        'punishment', 'remove',
        '--user-id', TEST_USER_ID,
        '--reason', 'Testing removal',
        '--db', str(db_path)
    ])
    assert result.exit_code == 0
    assert "Punishment removed successfully" in result.output
    
    # Verify punishment removal reflects in user stats
    result = runner.invoke(cli, ['user', 'stats', '--user-id', TEST_USER_ID, '--db', str(db_path)])
    assert result.exit_code == 0
    assert TEST_USER_ID in result.output
