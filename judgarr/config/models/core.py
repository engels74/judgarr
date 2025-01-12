"""Core configuration models."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
from .punishment import PunishmentConfig

class APIConfig(BaseModel):
    """API configuration settings."""
    url: HttpUrl
    api_key: str
    
    @field_validator("api_key")
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v.strip():
            raise ValueError("API key cannot be empty")
        return v

class APISettings(BaseModel):
    """Settings for all external APIs."""
    overseerr: APIConfig
    radarr: APIConfig
    sonarr: APIConfig

class NotificationConfig(BaseModel):
    """Base notification configuration."""
    enabled: bool = Field(default=True)

class DiscordConfig(NotificationConfig):
    """Discord notification settings."""
    webhook_url: str = ""

class SMTPConfig(BaseModel):
    """SMTP configuration for email notifications."""
    host: str
    port: int = Field(default=587, ge=1, le=65535)
    username: str
    password: str
    from_address: str
    use_tls: bool = Field(default=True)

class EmailConfig(NotificationConfig):
    """Email notification settings."""
    smtp: SMTPConfig | None = None

class NotificationSettings(BaseModel):
    """All notification settings."""
    discord: Optional[DiscordConfig] = None
    email: Optional[EmailConfig] = None

class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    file: str = "judgarr.log"
    max_size: int = Field(default=10, ge=1)  # MB
    backup_count: int = Field(default=5, ge=0)
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class DatabaseBackupConfig(BaseModel):
    """Database backup configuration."""
    enabled: bool = Field(default=True)
    interval_days: int = Field(default=7, ge=1)
    keep_backups: int = Field(default=4, ge=1)

class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "judgarr.db"
    backup: DatabaseBackupConfig = Field(default_factory=DatabaseBackupConfig)

class TrackingThresholds(BaseModel):
    """Data usage thresholds."""
    warning: float = Field(default=500)  # GB
    punishment: float = Field(default=1000)  # GB

class TrackingSettings(BaseModel):
    """User tracking configuration."""
    history_days: int = Field(default=30)
    check_interval: int = Field(default=60)  # minutes
    size_thresholds: TrackingThresholds = Field(default_factory=TrackingThresholds)

class RootConfig(BaseModel):
    """Root configuration model."""
    api: APISettings
    punishment: PunishmentConfig
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
