"""
Service for correlating media IDs between different services.
"""
from typing import Optional, TypeVar
import aiohttp
from pydantic import BaseModel

T = TypeVar('T')

class MediaIdentifiers(BaseModel):
    """Model for storing different media identifiers."""
    tmdb_id: int
    tvdb_id: Optional[int] = None
    imdb_id: Optional[str] = None

class MediaCorrelationService:
    """Service for correlating media IDs between different services."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the correlation service.
        
        Args:
            api_key: TMDB API key for accessing their API
        """
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = api_key
        # Cache to store ID mappings (tmdb_id -> MediaIdentifiers)
        self._cache: dict[int, MediaIdentifiers] = {}
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure an aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the service's session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def get_tv_identifiers(self, tmdb_id: int) -> Optional[MediaIdentifiers]:
        """Get all identifiers for a TV show from TMDB ID.
        
        Args:
            tmdb_id: TMDB ID of the TV show
            
        Returns:
            MediaIdentifiers if found, None otherwise
        """
        # Check cache first
        if tmdb_id in self._cache:
            return self._cache[tmdb_id]
        
        # Use TMDB API to get other IDs
        session = await self._ensure_session()
        
        try:
            url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids"
            params = {"api_key": self._api_key} if self._api_key else None
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                identifiers = MediaIdentifiers(
                    tmdb_id=tmdb_id,
                    tvdb_id=data.get("tvdb_id"),
                    imdb_id=data.get("imdb_id"),
                )
                
                # Cache the result
                self._cache[tmdb_id] = identifiers
                return identifiers
                
        except aiohttp.ClientError:
            return None
    
    async def get_movie_identifiers(self, tmdb_id: int) -> Optional[MediaIdentifiers]:
        """Get all identifiers for a movie from TMDB ID.
        
        Args:
            tmdb_id: TMDB ID of the movie
            
        Returns:
            MediaIdentifiers if found, None otherwise
        """
        # For movies, we primarily use TMDB ID, but we can also get IMDb ID if needed
        if tmdb_id in self._cache:
            return self._cache[tmdb_id]
        
        # Use TMDB API to get other IDs
        session = await self._ensure_session()
        
        try:
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/external_ids"
            params = {"api_key": self._api_key} if self._api_key else None
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                identifiers = MediaIdentifiers(
                    tmdb_id=tmdb_id,
                    imdb_id=data.get("imdb_id"),
                )
                
                # Cache the result
                self._cache[tmdb_id] = identifiers
                return identifiers
                
        except aiohttp.ClientError:
            return None
