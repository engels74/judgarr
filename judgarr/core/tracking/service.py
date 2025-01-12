"""
User request tracking service.
"""
from datetime import datetime
from typing import Optional, Sequence

from ...api.overseerr.client import OverseerrClient
from ...api.radarr.client import RadarrClient
from ...api.sonarr.client import SonarrClient
from ...shared.types import UserId
from ...shared.utils import calculate_rolling_window
from ...database.models import UserStats
from .calculator import SizeCalculator

class UserTrackingService:
    """Service for tracking user request data usage."""
    
    def __init__(
        self,
        overseerr_client: OverseerrClient,
        radarr_client: RadarrClient,
        sonarr_client: SonarrClient,
        tracking_period_days: int = 30,
    ):
        """Initialize the tracking service.
        
        Args:
            overseerr_client: Client for Overseerr API
            radarr_client: Client for Radarr API
            sonarr_client: Client for Sonarr API
            tracking_period_days: Number of days to track
        """
        self.tracking_period_days = tracking_period_days
        self.calculator = SizeCalculator(
            overseerr_client,
            radarr_client,
            sonarr_client,
        )
    
    async def get_user_stats(
        self,
        user_id: UserId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> UserStats:
        """Get statistics for a user's requests.
        
        Args:
            user_id: User ID to get stats for
            start_date: Start of date range (default: tracking_period_days ago)
            end_date: End of date range (default: now)
            
        Returns:
            User statistics
        """
        if start_date is None or end_date is None:
            start_date, end_date = calculate_rolling_window(self.tracking_period_days)
        
        total_size, requests = await self.calculator.calculate_user_requests_size(
            user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return UserStats(
            user_id=user_id,
            username="unknown",  # Default username when not available
            total_data_usage=total_size,
            punishment_level=0,  # Default level
            cooldown_days=0,  # No cooldown by default
            request_limit=100,  # Default request limit
            total_requests=len(requests),
            current_punishment_id=None,
            last_request_date=requests[-1].request_date if requests else None,
        )
    
    async def get_all_user_stats(
        self,
        user_ids: Sequence[UserId],
    ) -> dict[UserId, UserStats]:
        """Get statistics for multiple users.
        
        Args:
            user_ids: List of user IDs to get stats for
            
        Returns:
            Dictionary mapping user IDs to their stats
        """
        stats = {}
        for user_id in user_ids:
            try:
                user_stats = await self.get_user_stats(user_id)
                stats[user_id] = user_stats
            except Exception as e:
                # Log error but continue with other users
                print(f"Error getting stats for user {user_id}: {str(e)}")
                continue
        return stats
    
    async def check_user_limits(
        self,
        user_id: UserId,
        size_limit: int,
    ) -> tuple[bool, Optional[UserStats]]:
        """Check if a user has exceeded their data limit.
        
        Args:
            user_id: User ID to check
            size_limit: Size limit in bytes
            
        Returns:
            Tuple of (limit exceeded, user stats if available)
        """
        try:
            stats = await self.get_user_stats(user_id)
            return stats.total_data_usage > size_limit, stats
        except Exception as e:
            print(f"Error checking limits for user {user_id}: {str(e)}")
            return False, None
