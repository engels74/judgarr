"""
User management system for handling user status and limits.
"""
from datetime import datetime, timezone
from typing import Optional, List

from ..shared.types import UserId
from ..database.models import UserData, UserStats, UserPunishment, UserRequest
from ..database.manager import DatabaseManager
from .punishments.manager import PunishmentManager

class UserStatus:
    """User status information."""
    
    def __init__(
        self,
        user_id: UserId,
        total_requests: int,
        total_data_usage: int,
        current_punishment: Optional[UserPunishment] = None,
        last_request_date: Optional[datetime] = None,
    ):
        """Initialize user status.
        
        Args:
            user_id: User's unique identifier
            total_requests: Total number of requests made
            total_data_usage: Total data requested in bytes
            current_punishment: Current active punishment if any
            last_request_date: Date of last request
        """
        self.user_id = user_id
        self.total_requests = total_requests
        self.total_data_usage = total_data_usage
        self.current_punishment = current_punishment
        self.last_request_date = last_request_date
        
    @property
    def is_punished(self) -> bool:
        """Check if user is currently punished."""
        if not self.current_punishment:
            return False
        return (
            self.current_punishment.is_active and
            datetime.now() < self.current_punishment.end_date
        )
        
    @property
    def remaining_cooldown_days(self) -> int:
        """Get remaining cooldown days if punished."""
        if not self.is_punished or not self.current_punishment:
            return 0
        delta = self.current_punishment.end_date - datetime.now()
        return max(0, delta.days)
        
    @property
    def current_request_limit(self) -> int:
        """Get current request limit accounting for any reductions."""
        if not self.is_punished or not self.current_punishment:
            return 100  # Default Overseerr limit
        return max(0, 100 - self.current_punishment.request_reduction)

class UserManager:
    """Manager for user status and limits."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        punishment_manager: Optional[PunishmentManager] = None,
    ):
        """Initialize the manager.
        
        Args:
            db_manager: Database manager instance
            punishment_manager: Optional custom punishment manager
        """
        self.db = db_manager
        self.punishment_manager = punishment_manager or PunishmentManager(db_manager=db_manager)
        
    async def get_user_status(self, user_id: UserId) -> UserStatus:
        """Get current status for a user.
        
        Args:
            user_id: User to get status for
            
        Returns:
            User status information
        """
        stats = await self.db.get_user_stats(user_id)
        if not stats:
            # Create new stats record for user
            user_data = UserData(
                user_id=user_id,
                total_requests=0,
                request_frequency=0.0,
                movie_requests=0,
                tv_requests=0,
                last_processed=datetime.now(timezone.utc)
            )
            stats = UserStats(
                user_id=user_id,
                username="unknown",  # Set directly
                total_data_usage=0,  # Set directly
                punishment_level=0,  # Default level
                cooldown_days=0,  # No cooldown by default
                request_limit=100,  # Default Overseerr limit
                total_requests=user_data.total_requests,
                current_punishment_id=None,
                last_request_date=user_data.last_processed
            )
            await self.db.create_user_stats(stats)
            
        # Get active punishment if any
        punishment = await self.punishment_manager.get_active_punishment(user_id)
            
        # Get latest request date
        requests = await self.db.get_user_requests(user_id)
        last_request_date = None
        if requests and len(requests) > 0:
            last_request_date = max(r.request_date for r in requests)
            
        return UserStatus(
            user_id=user_id,
            total_requests=stats.total_requests,
            total_data_usage=stats.total_data_usage,
            current_punishment=punishment,
            last_request_date=last_request_date or stats.last_request_date,
        )
        
    async def reset_user_status(
        self,
        user_id: UserId,
        reason: str = "Administrative reset",
    ) -> None:
        """Reset a user's status and remove punishments.
        
        Args:
            user_id: User to reset
            reason: Reason for the reset
        """
        # Remove active punishment if any
        await self.punishment_manager.override_punishment(
            user_id=user_id,
            action="remove",
            reason=reason,
        )
        
        # Remove all punishments from history
        await self.db.remove_user_punishments(user_id)
        
        # Reset user stats
        user_data = UserData(
            user_id=user_id,
            total_requests=0,
            request_frequency=0.0,
            movie_requests=0,
            tv_requests=0,
            last_processed=datetime.now()
        )
        stats = UserStats(
            user_id=user_id,
            username="unknown",  # Set directly
            total_data_usage=0,  # Set directly
            punishment_level=0,  # Default level
            cooldown_days=0,  # No cooldown by default
            request_limit=100,  # Default Overseerr limit
            total_requests=user_data.total_requests,
            current_punishment_id=None,
            last_request_date=user_data.last_processed
        )
        await self.db.update_user_stats(stats)
        
    async def adjust_request_limit(
        self,
        user_id: UserId,
        adjustment: int,
        reason: str,
    ) -> None:
        """Adjust a user's request limit.
        
        Args:
            user_id: User to adjust limit for
            adjustment: Number of requests to add/remove (positive/negative)
            reason: Reason for the adjustment
        """
        # First adjust the user's limit
        await self.db.adjust_user_limit(user_id, adjustment, reason)
        
        if adjustment < 0:
            # Create user data for punishment calculation
            user_data = UserData(
                user_id=user_id,
                total_requests=0,  # Not relevant for manual adjustment
                request_frequency=0.0,  # Not relevant for manual adjustment
                movie_requests=0,
                tv_requests=0,
                last_processed=datetime.now()
            )
            
            # Process as mild punishment
            punishment = await self.punishment_manager.process_user_behavior(
                user_data=user_data,
                total_data_bytes=0,  # Not data-based punishment
                current_punishment=None,
            )
            
            if punishment:
                # Update user stats with new punishment
                stats = await self.db.get_user_stats(user_id)
                if stats:
                    stats.current_punishment_id = punishment.id
                    await self.db.update_user_stats(stats)
        else:
            # Remove any existing punishment
            punishment = await self.punishment_manager.override_punishment(
                user_id=user_id,
                action="remove",
                reason=reason,
            )
            
    async def list_punished_users(self) -> List[UserStatus]:
        """Get a list of all currently punished users.
        
        Returns:
            List of user status objects for punished users
        """
        punished_stats = await self.db.get_punished_users()
        
        statuses = []
        for stats in punished_stats:
            punishment = None
            if stats.current_punishment_id:
                punishment = await self.db.get_punishment(stats.current_punishment_id)
                
            status = UserStatus(
                user_id=stats.user_id,
                total_requests=stats.total_requests,
                total_data_usage=stats.total_data_usage,
                current_punishment=punishment,
                last_request_date=stats.last_request_date,
            )
            if status.is_punished:
                statuses.append(status)
                
        return statuses

    async def create_user(
        self,
        user_id: UserId,
        username: str,
        total_data_usage: int = 0,
        total_requests: int = 0,
    ) -> UserStats:
        """Create a new user with initial stats.
        
        Args:
            user_id: User's unique identifier
            username: User's display name
            total_data_usage: Initial data usage in bytes
            total_requests: Initial request count
            
        Returns:
            Created user stats
        """
        stats = UserStats(
            user_id=user_id,
            username=username,
            total_data_usage=total_data_usage,
            total_requests=total_requests,
            last_request_date=datetime.now(),
            punishment_level=0,
            cooldown_days=0,
            request_limit=10  # Default limit
        )
        await self.db.save_user_stats(stats)
        return stats

    async def add_request(
        self,
        user_id: UserId,
        media_id: str,
        media_type: str,
        size_bytes: int,
    ) -> Optional[UserRequest]:
        """Add a new media request for a user.
        
        Args:
            user_id: User making the request
            media_id: ID of requested media
            media_type: Type of media (movie/tv)
            size_bytes: Size of media in bytes
            
        Returns:
            Created request object if successful
            
        Raises:
            ValueError: If user has active punishment
        """
        # Check for active punishment
        punishment = await self.punishment_manager.get_active_punishment(user_id)
        if punishment and punishment.is_active:
            raise ValueError("User has active punishment")
            
        # Create initial request object
        request = UserRequest(
            id=0,  # Will be set by database
            user_id=user_id,
            media_id=media_id,
            media_type=media_type,
            request_date=datetime.now(timezone.utc),
            size_bytes=size_bytes,
            status="pending"
        )
        
        # Add request to database first
        request_id = await self.db.add_request(request)
        if request_id is None:
            return None
            
        # Update user stats
        stats = await self.get_user_stats(user_id)
        if stats:
            stats.total_requests += 1
            stats.total_data_usage += size_bytes
            await self.db.save_user_stats(stats)
            
        # Return the created request
        return UserRequest(
            id=request_id,
            user_id=request.user_id,
            media_id=request.media_id,
            media_type=request.media_type,
            size_bytes=request.size_bytes,
            request_date=request.request_date,
            status=request.status
        )

    async def get_user_stats(self, user_id: UserId) -> Optional[UserStats]:
        """Get current stats for a user.
        
        Args:
            user_id: User to get stats for
            
        Returns:
            User stats if found
        """
        return await self.db.get_user_stats(user_id)
