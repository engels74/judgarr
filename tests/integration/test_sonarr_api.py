"""Integration tests for the Sonarr API client."""
import pytest
import pytest_asyncio
import aiohttp
from pydantic import HttpUrl
from judgarr.api.sonarr.client import SonarrClient
from judgarr.config.models.core import RootConfig as Settings
from judgarr.api.sonarr.models import Series, Episode

@pytest_asyncio.fixture
async def sonarr_client(settings: Settings, http_session: aiohttp.ClientSession) -> SonarrClient:
    """Create a Sonarr client for testing."""
    client = SonarrClient(
        base_url=HttpUrl(str(settings.api.sonarr.url)),
        api_key=settings.api.sonarr.api_key
    )
    client._session = http_session  # Use the shared session
    return client

@pytest.mark.asyncio
async def test_get_series(sonarr_client: SonarrClient) -> None:
    """Test getting a series from Sonarr."""
    # Use a known test series ID from your Sonarr instance
    series_id = 1  # Replace with a valid test series ID
    series = await sonarr_client.get_series(series_id)
    
    assert series is not None
    assert isinstance(series, Series)
    assert series.id == series_id
    assert hasattr(series, 'title')
    assert hasattr(series, 'size_on_disk')
    assert series.size_on_disk is None or series.size_on_disk >= 0  # Size can be 0 for new/undownloaded series

@pytest.mark.asyncio
async def test_get_all_series(sonarr_client: SonarrClient) -> None:
    """Test getting all series from Sonarr."""
    series_list = await sonarr_client.get_all_series()
    
    assert isinstance(series_list, list)
    if series_list:  # If there are any series
        series = series_list[0]
        assert series is not None
        assert isinstance(series, Series)
        assert hasattr(series, 'id')
        assert hasattr(series, 'title')
        assert hasattr(series, 'size_on_disk')
        assert series.size_on_disk is None or series.size_on_disk >= 0  # Size can be 0 for new/undownloaded series

@pytest.mark.asyncio
async def test_get_episodes(sonarr_client: SonarrClient) -> None:
    """Test getting episodes for a series from Sonarr."""
    # Get all series first
    series_list = await sonarr_client.get_all_series()
    
    if series_list:  # If there are any series
        series = series_list[0]
        episodes = await sonarr_client.get_episodes(series.id)
        
        assert isinstance(episodes, list)
        if episodes:  # If there are any episodes
            episode = episodes[0]
            assert episode is not None
            assert isinstance(episode, Episode)
            assert episode.series_id == series.id
            assert episode.season_number >= 0
            assert episode.episode_number > 0
            assert episode.size_on_disk is None or episode.size_on_disk >= 0

@pytest.mark.asyncio
async def test_calculate_series_size(sonarr_client: SonarrClient) -> None:
    """Test calculating series size."""
    # Get all series
    series_list = await sonarr_client.get_all_series()
    
    if series_list:  # If there are any series
        # Calculate total size (handle None values)
        total_size = sum(series.size_on_disk or 0 for series in series_list)
        assert total_size >= 0
        
        # Calculate size for a specific series
        series = series_list[0]
        assert series.size_on_disk is None or series.size_on_disk >= 0
        
        # Get episodes and verify their sizes
        episodes = await sonarr_client.get_episodes(series.id)
        if episodes:
            # Handle None values in episode sizes
            episode_sizes = [episode.size_on_disk or 0 for episode in episodes]
            assert all(size >= 0 for size in episode_sizes)
            total_episode_size = sum(episode_sizes)
            assert total_episode_size >= 0
