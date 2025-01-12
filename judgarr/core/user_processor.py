"""
User data processing service for analyzing Overseerr request data.
"""
from datetime import datetime, timedelta
from typing import Sequence

from ..api.overseerr.client import OverseerrClient
from ..api.overseerr.models import Request
from ..shared.types import UserId
from ..database.models import UserData

class UserDataProcessor:
    """Service for processing and analyzing user request data."""
    
    def __init__(self, overseerr_client: OverseerrClient):
        """Initialize the processor.
        
        Args:
            overseerr_client: Client for interacting with Overseerr API
        """
        self.overseerr_client = overseerr_client
        
    async def get_user_request_history(
        self,
        user_id: UserId,
        days: int = 30,
    ) -> list[Request]:
        """Get a user's request history for the specified period.
        
        Args:
            user_id: ID of the user to get history for
            days: Number of days to look back
            
        Returns:
            List of requests made by the user
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        requests = await self.overseerr_client.get_all_user_requests(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return [Request.model_validate(req) for req in requests]
        
    def analyze_request_patterns(
        self,
        requests: Sequence[Request],
        window_days: int = 30,
    ) -> dict:
        """Analyze request patterns to identify potential abuse.
        
        Args:
            requests: List of user requests to analyze
            window_days: Time window to analyze in days
            
        Returns:
            Dict containing analysis results:
            - total_requests: Total number of requests in window
            - request_frequency: Average requests per day
            - media_types: Count of each media type requested
        """
        if not requests:
            return {
                "total_requests": 0,
                "request_frequency": 0.0,
                "media_types": {"movie": 0, "tv": 0}
            }
            
        # Get date range
        dates = [req.created_at for req in requests]
        start_date = min(dates)
        end_date = max(dates)
        date_range = (end_date - start_date).days or 1  # Avoid division by zero
        
        # Count media types
        media_types = {"movie": 0, "tv": 0}
        for req in requests:
            media_types[req.media.media_type] += 1
            
        return {
            "total_requests": len(requests),
            "request_frequency": len(requests) / date_range,
            "media_types": media_types
        }
        
    async def process_user_data(
        self,
        user_id: UserId,
        window_days: int = 30,
    ) -> UserData:
        """Process all user data and generate insights.
        
        Args:
            user_id: ID of the user to process
            window_days: Time window to analyze in days
            
        Returns:
            Processed user data with analysis
        """
        # Get request history
        requests = await self.get_user_request_history(
            user_id=user_id,
            days=window_days,
        )
        
        # Analyze patterns
        analysis = self.analyze_request_patterns(
            requests=requests,
            window_days=window_days,
        )
        
        # Create user data object
        return UserData(
            user_id=user_id,
            total_requests=analysis["total_requests"],
            request_frequency=analysis["request_frequency"],
            movie_requests=analysis["media_types"]["movie"],
            tv_requests=analysis["media_types"]["tv"],
            last_processed=datetime.now(),
        )
