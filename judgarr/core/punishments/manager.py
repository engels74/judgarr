"""Manager for handling user punishments."""

from typing import Optional
from datetime import datetime, timedelta
from ...database.manager import DatabaseManager
from ...shared.types import UserId
from ...database.models import UserData, UserPunishment
from .levels import PunishmentLevel
from .calculator import PunishmentCalculator

class PunishmentManager:
    """Manager for handling user punishments."""
    
    def __init__(
        self,
        calculator: Optional[PunishmentCalculator] = None,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        """Initialize the manager.
        
        Args:
            calculator: Custom calculator instance, or use default if None
            db_manager: Database manager instance for persistence
        """
        self.calculator = calculator or PunishmentCalculator()
        if db_manager is None:
            raise ValueError("Database manager is required")
        self.db = db_manager
        
    async def process_user_behavior(
        self,
        user_data: UserData,
        total_data_bytes: int,
        current_punishment: Optional[UserPunishment] = None,
    ) -> Optional[UserPunishment]:
        """Process user behavior and determine if punishment is needed.
        
        Args:
            user_data: Processed user data and analysis
            total_data_bytes: Total data requested in bytes over rolling window
            current_punishment: Current active punishment, if any
            
        Returns:
            New punishment if needed, None otherwise
        """
        punishment = self.calculator.calculate_punishment(
            user_data,
            total_data_bytes,
            current_punishment,
        )
        
        if punishment and self.db:
            # Persist the punishment
            await self.db.create_punishment(
                user_id=punishment.user_id,
                level=punishment.level,
                start_date=punishment.start_date,
                end_date=punishment.end_date,
                cooldown_days=punishment.cooldown_days,
                request_reduction=punishment.request_reduction,
                reason=punishment.reason,
                data_usage=punishment.data_usage,
                is_active=punishment.is_active,
            )
            
        return punishment
        
    async def override_punishment(
        self,
        user_id: UserId,
        action: str,
        reason: str,
    ) -> Optional[UserPunishment]:
        """Override a user's punishment (admin action).
        
        Args:
            user_id: ID of user to override punishment for
            action: Override action ('remove' or 'escalate')
            reason: Reason for the override
            
        Returns:
            New punishment if escalating, None if removing
        """
        if not self.db:
            return None
            
        if action == "remove":
            # Get current punishment if any
            current = await self.db.get_active_punishment(user_id)
            if current:
                # Deactivate it
                current.is_active = False
                await self.db.update_punishment(current)
            return None
            
        elif action == "escalate":
            # Create a severe punishment
            punishment = UserPunishment(
                id=0,  # Will be set by database
                user_id=user_id,
                level=PunishmentLevel.SEVERE,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7),  # 1 week
                cooldown_days=7,
                request_reduction=50,  # Significant reduction
                reason=f"Administrative override: {reason}",
                data_usage=0,  # Not data-based
                is_active=True,
            )
            
            # Create punishment in database
            await self.db.create_punishment(
                user_id=punishment.user_id,
                level=punishment.level,
                start_date=punishment.start_date,
                end_date=punishment.end_date,
                cooldown_days=punishment.cooldown_days,
                request_reduction=punishment.request_reduction,
                reason=punishment.reason,
                data_usage=punishment.data_usage,
                is_active=punishment.is_active,
            )
            return punishment
            
        return None

    async def get_active_punishment(self, user_id: UserId) -> Optional[UserPunishment]:
        """Get active punishment for a user if any.
        
        Args:
            user_id: User to get punishment for
            
        Returns:
            Active punishment if exists, None otherwise
        """
        if not self.db:
            return None
            
        return await self.db.get_active_punishment(user_id)

    async def reset_punishment(self, user_id: UserId, reason: Optional[str] = None) -> bool:
        """Reset a user's punishment status.
        
        Args:
            user_id: ID of user to reset
            reason: Optional reason for the reset
            
        Returns:
            bool: True if reset was successful, False otherwise
        """
        try:
            # Get current punishment if any
            current = await self.db.get_active_punishment(user_id)
            if not current:
                # No active punishment to reset
                return True
                
            # Deactivate current punishment
            await self.db.deactivate_punishment(
                user_id=user_id,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to reset punishment for {user_id}: {str(e)}")
            return False

    async def create_punishment(
        self,
        user_id: UserId,
        level: int,
        start_date: datetime,
        end_date: datetime,
        cooldown_days: int,
        request_reduction: int,
        data_usage: int,
        reason: str,
    ) -> Optional[UserPunishment]:
        """Create a new punishment for a user.
        
        Args:
            user_id: User to punish
            level: Punishment severity level
            start_date: When punishment starts
            end_date: When punishment ends
            cooldown_days: Days of cooldown after punishment
            request_reduction: Percentage to reduce requests by
            data_usage: Data usage that triggered punishment
            reason: Reason for punishment
            
        Returns:
            Created punishment if successful
        """
        # Update user stats with punishment
        stats = await self.db.get_user_stats(user_id)
        if stats:
            stats.punishment_level = level
            stats.cooldown_days = cooldown_days
            stats.request_limit = max(5, stats.request_limit - (stats.request_limit * request_reduction // 100))
            await self.db.save_user_stats(stats)
            
        # Create punishment in database and return it
        return await self.db.create_punishment(
            user_id=user_id,
            level=level,
            start_date=start_date,
            end_date=end_date,
            cooldown_days=cooldown_days,
            request_reduction=request_reduction,
            reason=reason,
            data_usage=data_usage,
            is_active=True,
        )
