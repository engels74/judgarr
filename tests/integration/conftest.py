"""Shared fixtures for integration tests."""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
import aiohttp
from pydantic import HttpUrl
from judgarr.config.models.core import RootConfig as Settings, APISettings, APIConfig
from judgarr.config.models.punishment import PunishmentConfig
from judgarr.api.overseerr.client import OverseerrClient
from judgarr.api.radarr.client import RadarrClient
from judgarr.api.sonarr.client import SonarrClient
from judgarr.core.tracking.correlation import MediaCorrelationService

# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest-asyncio."""
    config.option.asyncio_mode = "strict"
    config.option.asyncio_default_fixture_loop_scope = "function"

TMDB_API_KEY = "tmdb_api_key"

@pytest.fixture
def settings() -> Settings:
    """Create settings for testing."""
    return Settings(
        api=APISettings(
            overseerr=APIConfig(
                url=HttpUrl("http://overseerr:5055"),
                api_key="overseerr_api_key"
            ),
            radarr=APIConfig(
                url=HttpUrl("http://radarr:7878"),  # Not configured yet
                api_key="radarr_api_key"
            ),
            sonarr=APIConfig(
                url=HttpUrl("http://sonarr:7878"),  # Not configured yet
                api_key="sonarr_api_key"
            )
        ),
        punishment=PunishmentConfig()  # Using default values for punishment config
    )

@pytest_asyncio.fixture
async def http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create a shared HTTP session for testing."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest_asyncio.fixture
async def overseerr_client(settings: Settings, http_session: aiohttp.ClientSession) -> AsyncGenerator[OverseerrClient, None]:
    """Create an Overseerr client for testing."""
    client = OverseerrClient(
        base_url=HttpUrl(str(settings.api.overseerr.url)),
        api_key=settings.api.overseerr.api_key
    )
    client._session = http_session  # Use the shared session
    yield client

@pytest_asyncio.fixture
async def radarr_client(settings: Settings, http_session: aiohttp.ClientSession) -> AsyncGenerator[RadarrClient, None]:
    """Create a Radarr client for testing."""
    client = RadarrClient(
        base_url=HttpUrl(str(settings.api.radarr.url)),
        api_key=settings.api.radarr.api_key
    )
    client._session = http_session  # Use the shared session
    yield client

@pytest_asyncio.fixture
async def sonarr_client(settings: Settings, http_session: aiohttp.ClientSession) -> AsyncGenerator[SonarrClient, None]:
    """Create a Sonarr client for testing."""
    client = SonarrClient(
        base_url=HttpUrl(str(settings.api.sonarr.url)),
        api_key=settings.api.sonarr.api_key
    )
    client._session = http_session  # Use the shared session
    yield client

@pytest_asyncio.fixture
async def correlation_service(http_session: aiohttp.ClientSession) -> AsyncGenerator[MediaCorrelationService, None]:
    """Create a media correlation service for testing."""
    service = MediaCorrelationService(api_key=TMDB_API_KEY)
    service._session = http_session  # Use the shared session
    yield service
    await service.close()
