"""Punishment calculation logic."""

from typing import Optional
from datetime import datetime, timedelta

from ...database.models import UserData, UserPunishment
from ...config.models.punishment import PunishmentConfig
from . import PunishmentLevel

class PunishmentCalculator:
    """Calculator for determining user punishments based on data usage."""
    
    def __init__(self, config: Optional[PunishmentConfig] = None):
        """Initialize the calculator with configuration.
        
        Args:
            config: Punishment configuration, or use defaults if None
        """
        self.config = config or PunishmentConfig()
        
        # Convert GB thresholds to bytes
        bytes_per_gb = 1024 * 1024 * 1024
        self.thresholds = {
            PunishmentLevel.WARNING: self.config.thresholds.warning * bytes_per_gb,
            PunishmentLevel.MILD: self.config.thresholds.mild * bytes_per_gb,
            PunishmentLevel.SEVERE: self.config.thresholds.severe * bytes_per_gb,
            PunishmentLevel.MAXIMUM: self.config.thresholds.maximum * bytes_per_gb,
        }
        
        # Map cooldown periods
        self.cooldowns = {
            PunishmentLevel.WARNING: self.config.cooldowns.warning,
            PunishmentLevel.MILD: self.config.cooldowns.mild,
            PunishmentLevel.SEVERE: self.config.cooldowns.severe,
            PunishmentLevel.MAXIMUM: self.config.cooldowns.maximum,
        }
        
        # Map request limit reductions
        self.reductions = {
            PunishmentLevel.WARNING: self.config.request_limits.warning,
            PunishmentLevel.MILD: self.config.request_limits.mild,
            PunishmentLevel.SEVERE: self.config.request_limits.severe,
            PunishmentLevel.MAXIMUM: self.config.request_limits.maximum,
        }
        
        self.tracking_period_days = self.config.tracking_period_days
        
    def determine_punishment_level(
        self,
        total_data_bytes: int,
        current_level: Optional[PunishmentLevel] = None,
    ) -> PunishmentLevel:
        """Determine appropriate punishment level based on data usage.
        
        Args:
            total_data_bytes: Total data requested in bytes
            current_level: Current punishment level, if any
            
        Returns:
            Appropriate punishment level
        """
        # If already at maximum, stay there
        if current_level == PunishmentLevel.MAXIMUM:
            return PunishmentLevel.MAXIMUM
            
        # Find the highest threshold exceeded
        new_level = PunishmentLevel.NONE
        for level, threshold in self.thresholds.items():
            if total_data_bytes >= threshold:
                new_level = level
                
        # Never decrease level
        if current_level and current_level > new_level:
            return current_level
            
        return new_level
        
    def calculate_punishment(
        self,
        user_data: UserData,
        total_data_bytes: int,
        current_punishment: Optional[UserPunishment] = None,
    ) -> Optional[UserPunishment]:
        """Calculate punishment based on user's data usage.
        
        Args:
            user_data: Processed user data and analysis
            total_data_bytes: Total data requested in bytes over rolling window
            current_punishment: Current active punishment, if any
            
        Returns:
            New punishment if needed, None otherwise
        """
        current_level = None
        if current_punishment and current_punishment.is_active:
            current_level = PunishmentLevel(current_punishment.level)
            
        new_level = self.determine_punishment_level(total_data_bytes, current_level)
        if new_level == PunishmentLevel.NONE:
            return None
            
        # Get punishment parameters
        cooldown_days = self.cooldowns[new_level]
        request_reduction = self.reductions[new_level]
        
        # Convert threshold to GB for message
        threshold_gb = self.thresholds[new_level] / (1024 * 1024 * 1024)
        
        return UserPunishment(
            id=0,  # Will be set by database
            user_id=user_data.user_id,
            level=new_level,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=cooldown_days),
            cooldown_days=cooldown_days,
            request_reduction=request_reduction,
            reason=(
                f"Exceeded {new_level.value} data usage threshold "
                f"(threshold: {threshold_gb:.1f}GB)"
            ),
            data_usage=total_data_bytes,
            is_active=True,
        )
