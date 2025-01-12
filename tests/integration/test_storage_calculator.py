"""Integration tests for the storage calculator functionality."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from judgarr.core.tracking.calculator import SizeCalculator
from judgarr.shared.types import UserId
from judgarr.shared.constants import GB, TB
from judgarr.api.base import APIError

@pytest_asyncio.fixture
async def calculator(overseerr_client, radarr_client, sonarr_client, correlation_service):
    """Create a size calculator instance for testing."""
    calc = SizeCalculator(
        overseerr_client=overseerr_client,
        radarr_client=radarr_client,
        sonarr_client=sonarr_client,
    )
    calc.correlation = correlation_service
    yield calc
    await calc.close()

@pytest.mark.asyncio
async def test_calculate_movie_size(calculator):
    """Test calculating the size of a movie request."""
    # Use a known movie from the production environment
    tmdb_id = 572802  # Aquaman and the Lost Kingdom
    size = await calculator.calculate_movie_request_size(tmdb_id)
    
    # Size should be reasonable for a movie (between 10GB and 100GB)
    assert size > 10 * GB
    assert size < 100 * GB
    print(f"Movie size: {size / GB:.2f} GB")

@pytest.mark.asyncio
async def test_calculate_series_size(calculator):
    """Test calculating the size of a TV series request."""
    # Use a known TV series from the production environment
    tmdb_id = 84958  # Loki
    size = await calculator.calculate_series_request_size(tmdb_id)
    
    # Size should be reasonable for a TV series
    assert isinstance(size, int)
    assert size >= 0  # Some series might not have episodes yet
    print(f"Series size: {size / GB:.2f} GB")

@pytest.mark.asyncio
async def test_calculate_user_requests_size(calculator, overseerr_client):
    """Test calculating total size of user requests in a date range."""
    # Get a real user from Overseerr
    users = await overseerr_client.get_all_users()
    test_user = next((user for user in users if not user.get("isAdmin", False)), None)
    assert test_user is not None, "No non-admin user found for testing"
    
    user_id = UserId(test_user["id"])
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        total_size, requests = await calculator.calculate_user_requests_size(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Verify the results
        assert isinstance(total_size, int)
        assert isinstance(requests, list)
        print(f"Total user requests size: {total_size / GB:.2f} GB")
        print(f"Number of requests: {len(requests)}")
        
        # Size should be reasonable (less than 10TB for a month)
        assert total_size < 10 * TB
    except APIError as e:
        if e.status_code == 405:
            pytest.skip("Overseerr API endpoint not available in this environment")
        raise

@pytest.mark.asyncio
async def test_invalid_movie_id(calculator):
    """Test calculating size with an invalid movie ID."""
    with pytest.raises(APIError):
        await calculator.calculate_movie_request_size(-1)

@pytest.mark.asyncio
async def test_invalid_series_id(calculator):
    """Test calculating size with an invalid series ID."""
    with pytest.raises(APIError):
        await calculator.calculate_series_request_size(-1)
