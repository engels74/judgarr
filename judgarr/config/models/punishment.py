"""Configuration models for punishment settings."""

from pydantic import BaseModel, Field, field_validator

class ThresholdsConfig(BaseModel):
    """Configuration for punishment thresholds in GB."""
    warning: float = Field(
        default=500,
        description="Data usage threshold in GB for warning level",
    )
    mild: float = Field(
        default=750,
        description="Data usage threshold in GB for mild punishment",
    )
    severe: float = Field(
        default=1000,
        description="Data usage threshold in GB for severe punishment",
    )
    maximum: float = Field(
        default=1500,
        description="Data usage threshold in GB for maximum punishment",
    )
    
    @field_validator("*")
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold values are positive."""
        if v <= 0:
            raise ValueError("Threshold must be positive")
        return v

class CooldownConfig(BaseModel):
    """Configuration for punishment cooldown periods in days."""
    warning: int = Field(
        default=3,
        description="Cooldown period in days for warning level",
    )
    mild: int = Field(
        default=5,
        description="Cooldown period in days for mild punishment",
    )
    severe: int = Field(
        default=7,
        description="Cooldown period in days for severe punishment",
    )
    maximum: int = Field(
        default=14,
        description="Cooldown period in days for maximum punishment",
    )
    
    @field_validator("*")
    def validate_cooldown(cls, v: int) -> int:
        """Validate cooldown values are positive."""
        if v <= 0:
            raise ValueError("Cooldown period must be positive")
        return v

class RequestLimitConfig(BaseModel):
    """Configuration for request limit reductions."""
    warning: int = Field(
        default=0,
        description="Request limit reduction for warning level",
    )
    mild: int = Field(
        default=-5,
        description="Request limit reduction for mild punishment",
    )
    severe: int = Field(
        default=-10,
        description="Request limit reduction for severe punishment",
    )
    maximum: int = Field(
        default=-15,
        description="Request limit reduction for maximum punishment",
    )
    
    @field_validator("*")
    def validate_limit(cls, v: int) -> int:
        """Validate limit reduction values."""
        if v > 0:
            raise ValueError("Request limit reduction must be non-positive")
        if v < -100:
            raise ValueError("Request limit reduction cannot exceed -100")
        return v

class PunishmentConfig(BaseModel):
    """Configuration for the punishment system."""
    tracking_period_days: int = Field(
        default=30,
        description="Rolling period in days for data usage tracking",
    )
    thresholds: ThresholdsConfig = Field(
        default_factory=ThresholdsConfig,
        description="Data usage thresholds for different punishment levels",
    )
    cooldowns: CooldownConfig = Field(
        default_factory=CooldownConfig,
        description="Cooldown periods for different punishment levels",
    )
    request_limits: RequestLimitConfig = Field(
        default_factory=RequestLimitConfig,
        description="Request limit reductions for different punishment levels",
    )
    
    @field_validator("tracking_period_days")
    def validate_tracking_period(cls, v: int) -> int:
        """Validate tracking period is positive."""
        if v <= 0:
            raise ValueError("Tracking period must be positive")
        return v
