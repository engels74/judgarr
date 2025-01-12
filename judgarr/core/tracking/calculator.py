"""
Size calculation logic for user requests.
"""
from datetime import datetime
from typing import Optional

from ...api.overseerr.client import OverseerrClient
from ...api.radarr.client import RadarrClient
from ...api.sonarr.client import SonarrClient
from ...api.base import APIError
from ...shared.types import UserId
from ...database.models import UserRequest
from .correlation import MediaCorrelationService

class SizeCalculator:
    """Calculator for user request sizes."""
    
    def __init__(
        self,
        overseerr_client: OverseerrClient,
        radarr_client: RadarrClient,
        sonarr_client: SonarrClient,
    ):
        """Initialize the calculator.
        
        Args:
            overseerr_client: Client for Overseerr API
            radarr_client: Client for Radarr API
            sonarr_client: Client for Sonarr API
        """
        self.overseerr = overseerr_client
        self.radarr = radarr_client
        self.sonarr = sonarr_client
        self.correlation = MediaCorrelationService()
    
    async def calculate_movie_request_size(self, tmdb_id: int) -> int:
        """Calculate the size of a movie request.
        
        Args:
            tmdb_id: TMDB ID of the movie
            
        Returns:
            Size in bytes
            
        Raises:
            APIError: If the movie is not found or request fails
        """
        # For movies, we can use TMDB ID directly with Radarr
        movie = await self.radarr.get_movie_by_tmdb_id(tmdb_id)
        if not movie:
            raise APIError(f"Movie with TMDB ID {tmdb_id} not found")
        return movie.size_on_disk
    
    async def calculate_series_request_size(self, tmdb_id: int) -> int:
        """Calculate the size of a TV series request.
        
        Args:
            tmdb_id: TMDB ID of the series from Overseerr
            
        Returns:
            Size in bytes
            
        Raises:
            APIError: If the series is not found or request fails
        """
        # Get TVDB ID for Sonarr
        identifiers = await self.correlation.get_tv_identifiers(tmdb_id)
        if not identifiers or not identifiers.tvdb_id:
            raise APIError(f"Series with TMDB ID {tmdb_id} not found")
            
        # Use TVDB ID with Sonarr
        series = await self.sonarr.get_series_by_tvdb_id(identifiers.tvdb_id)
        if not series:
            raise APIError(f"Series with TVDB ID {identifiers.tvdb_id} not found")
        return series.size_on_disk
    
    async def calculate_request_size(self, request: UserRequest) -> int:
        """Calculate the size of a user request.
        
        Args:
            request: User request to calculate size for
            
        Returns:
            Size in bytes
            
        Raises:
            APIError: If the media is not found or request fails
        """
        tmdb_id = int(request.media_id)  # Overseerr always provides TMDB ID
        
        if request.media_type == "movie":
            return await self.calculate_movie_request_size(tmdb_id)
        elif request.media_type == "tv":
            return await self.calculate_series_request_size(tmdb_id)
        raise APIError(f"Unknown media type: {request.media_type}")
    
    async def calculate_user_requests_size(
        self,
        user_id: UserId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[int, list[UserRequest]]:
        """Calculate total size of user requests in a date range.
        
        Args:
            user_id: User ID to calculate for
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Tuple of (total size in bytes, list of requests)
            
        Raises:
            APIError: If any request fails
        """
        requests = await self.overseerr.get_all_user_requests(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        total_size = 0
        processed_requests = []
        
        for request_data in requests:
            # Convert Overseerr request to our model
            request = UserRequest(
                id=request_data["id"],
                user_id=UserId(str(user_id)),  # Properly convert to UserId type
                media_id=str(request_data["media"]["tmdbId"]),  # Always TMDB ID from Overseerr
                media_type=request_data["media"]["mediaType"],
                request_date=datetime.fromisoformat(request_data["createdAt"]),
                size_bytes=0,  # Will be updated below
                status=str(request_data["status"]),
            )
            
            try:
                # Calculate size
                size = await self.calculate_request_size(request)
                request.size_bytes = size
                total_size += size
            except APIError as e:
                # Skip failed requests but continue processing others
                request.status = str(e)
                
            processed_requests.append(request)
            
        return total_size, processed_requests
    
    async def close(self) -> None:
        """Close the calculator's resources."""
        await self.correlation.close()
