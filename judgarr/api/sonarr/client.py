"""
Sonarr API client implementation.
"""
from typing import Optional, Sequence

from ..base import BaseAPIClient, APIError
from ...shared.constants import SONARR_SERIES_ENDPOINT
from .models import Series, Episode, SeasonStatistics

class SonarrClient(BaseAPIClient):
    """Client for interacting with the Sonarr API."""
    
    async def get_series(self, series_id: int) -> Series:
        """Get information about a specific TV series.
        
        Args:
            series_id: Sonarr series ID
            
        Returns:
            Series object with details
            
        Raises:
            APIError: If the series is not found or request fails
        """
        data = await self.get(f"{SONARR_SERIES_ENDPOINT}/{series_id}")
        return Series.model_validate(data)
    
    async def get_series_by_tvdb_id(self, tvdb_id: int) -> Optional[Series]:
        """Get series information using TVDB ID.
        
        Args:
            tvdb_id: TVDB ID of the series
            
        Returns:
            Series object if found, None otherwise
        """
        params = {"tvdbId": tvdb_id}
        data = await self.get(SONARR_SERIES_ENDPOINT, params=params)
        
        if not data:
            return None
            
        # Sonarr returns a list, but there should only be one match
        return Series.model_validate(data[0])
    
    async def get_all_series(self) -> list[Series]:
        """Get all TV series in the Sonarr library.
        
        Returns:
            List of all series
        """
        data = await self.get(SONARR_SERIES_ENDPOINT)
        return [Series.model_validate(series) for series in data]
    
    async def get_episodes(self, series_id: int) -> list[Episode]:
        """Get all episodes for a TV series.
        
        Args:
            series_id: Sonarr series ID
            
        Returns:
            List of episodes
        """
        data = await self.get("/api/v3/episode", params={"seriesId": series_id})
        return [Episode.model_validate(episode) for episode in data]
    
    async def get_season_statistics(
        self,
        series_id: int,
        season_number: int
    ) -> SeasonStatistics:
        """Get statistics for a specific season.
        
        Args:
            series_id: Sonarr series ID
            season_number: Season number
            
        Returns:
            Season statistics
        """
        series = await self.get_series(series_id)
        for season in series.seasons:
            if season.season_number == season_number and season.statistics:
                return SeasonStatistics.model_validate(season.statistics)
        raise APIError(f"Season {season_number} not found for series {series_id}")
    
    async def calculate_series_size(self, series_id: int) -> int:
        """Calculate the total size of a TV series in bytes.
        
        Args:
            series_id: Sonarr series ID
            
        Returns:
            Size in bytes
            
        Note:
            This returns the actual size on disk for all downloaded episodes.
        """
        series = await self.get_series(series_id)
        return series.size_on_disk
    
    async def calculate_season_size(
        self,
        series_id: int,
        season_number: int
    ) -> int:
        """Calculate the size of a specific season in bytes.
        
        Args:
            series_id: Sonarr series ID
            season_number: Season number
            
        Returns:
            Size in bytes
        """
        try:
            stats = await self.get_season_statistics(series_id, season_number)
            return stats.size_on_disk
        except APIError:
            return 0
    
    async def calculate_series_sizes(self, series_ids: Sequence[int]) -> int:
        """Calculate the total size of multiple TV series.
        
        Args:
            series_ids: List of Sonarr series IDs
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        for series_id in series_ids:
            try:
                size = await self.calculate_series_size(series_id)
                total_size += size
            except APIError:
                # Skip series that can't be found or have errors
                continue
                
        return total_size
