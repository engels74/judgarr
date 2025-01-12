"""
Radarr API client implementation.
"""
from typing import Optional, Sequence

from ..base import BaseAPIClient, APIError
from ...shared.constants import RADARR_MOVIE_ENDPOINT
from .models import Movie, MovieCollection

class RadarrClient(BaseAPIClient):
    """Client for interacting with the Radarr API."""
    
    async def get_movie(self, movie_id: int) -> Movie:
        """Get information about a specific movie.
        
        Args:
            movie_id: Radarr movie ID
            
        Returns:
            Movie object with details
            
        Raises:
            APIError: If the movie is not found or request fails
        """
        data = await self.get(f"{RADARR_MOVIE_ENDPOINT}/{movie_id}")
        return Movie.model_validate(data)
    
    async def get_movie_by_tmdb_id(self, tmdb_id: int) -> Optional[Movie]:
        """Get movie information using TMDB ID.
        
        Args:
            tmdb_id: TMDB ID of the movie
            
        Returns:
            Movie object if found, None otherwise
        """
        params = {"tmdbId": tmdb_id}
        data = await self.get(RADARR_MOVIE_ENDPOINT, params=params)
        
        if not data:
            return None
            
        # Radarr returns a list, but there should only be one match
        return Movie.model_validate(data[0])
    
    async def get_movies(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_key: str = "sortTitle",
        sort_dir: str = "asc",
    ) -> MovieCollection:
        """Get a list of movies with pagination.
        
        Args:
            page: Page number
            page_size: Number of items per page
            sort_key: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            
        Returns:
            MovieCollection containing paginated movie list
        """
        params = {
            "page": page,
            "pageSize": page_size,
            "sortKey": sort_key,
            "sortDir": sort_dir,
        }
        
        data = await self.get(RADARR_MOVIE_ENDPOINT, params=params)
        return MovieCollection.model_validate(data)
    
    async def get_all_movies(self) -> list[Movie]:
        """Get all movies in the Radarr library.
        
        Returns:
            List of all movies
        """
        data = await self.get(RADARR_MOVIE_ENDPOINT)
        return [Movie.model_validate(movie) for movie in data]
    
    async def calculate_movie_size(self, movie_id: int) -> int:
        """Calculate the size of a movie in bytes.
        
        Args:
            movie_id: Radarr movie ID
            
        Returns:
            Size in bytes
            
        Note:
            This returns the actual size on disk if the movie is downloaded,
            or 0 if the movie hasn't been downloaded yet.
        """
        movie = await self.get_movie(movie_id)
        return movie.size_on_disk
    
    async def calculate_movies_size(self, movie_ids: Sequence[int]) -> int:
        """Calculate the total size of multiple movies.
        
        Args:
            movie_ids: List of Radarr movie IDs
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        for movie_id in movie_ids:
            try:
                size = await self.calculate_movie_size(movie_id)
                total_size += size
            except APIError:
                # Skip movies that can't be found or have errors
                continue
                
        return total_size
