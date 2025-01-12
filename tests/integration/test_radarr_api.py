"""Integration tests for the Radarr API client."""
import pytest
import pytest_asyncio
import aiohttp
from pydantic import HttpUrl
from judgarr.api.radarr.client import RadarrClient, Movie
from judgarr.config.models.core import RootConfig as Settings

@pytest_asyncio.fixture
async def radarr_client(settings: Settings, http_session: aiohttp.ClientSession) -> RadarrClient:
    """Create a Radarr client for testing."""
    client = RadarrClient(
        base_url=HttpUrl(str(settings.api.radarr.url)),
        api_key=settings.api.radarr.api_key
    )
    client._session = http_session  # Use the shared session
    return client

@pytest.mark.asyncio
async def test_get_movie(radarr_client: RadarrClient) -> None:
    """Test getting a movie from Radarr."""
    # Use a known test movie ID from your Radarr instance
    movie_id = 1  # Replace with a valid test movie ID
    movie = await radarr_client.get_movie(movie_id)
    
    # Check that we get a Movie object with the expected fields
    assert isinstance(movie, Movie)
    assert movie.id == movie_id
    assert isinstance(movie.title, str)
    assert isinstance(movie.size_on_disk, int)

@pytest.mark.asyncio
async def test_get_movies(radarr_client: RadarrClient) -> None:
    """Test getting all movies from Radarr."""
    movies = await radarr_client.get_all_movies()
    
    assert isinstance(movies, list)
    if movies:  # If there are any movies
        movie = movies[0]
        assert isinstance(movie, Movie)
        assert movie.id > 0
        assert isinstance(movie.title, str)
        assert movie.size_on_disk >= 0
