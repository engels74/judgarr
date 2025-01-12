"""
Database models for the Judgarr project.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from ...shared.types import UserId

class UserRequest(BaseModel):
    """Model representing a user's media request."""
    id: int
    user_id: UserId
    media_id: str
    media_type: str  # 'movie' or 'series'
    request_date: datetime
    size_bytes: int
    status: str

class UserPunishment(BaseModel):
    """Model representing a user's punishment record."""
    id: int
    user_id: UserId
    level: int
    start_date: datetime
    end_date: datetime
    cooldown_days: int
    request_reduction: int
    reason: Optional[str] = None
    data_usage: int  # in bytes
    is_active: bool = True

class UserStats(BaseModel):
    """Model representing user statistics."""
    user_id: UserId
    username: str
    total_data_usage: int  # in bytes
    punishment_level: int
    cooldown_days: int
    request_limit: int
    total_requests: int
    current_punishment_id: Optional[int] = None
    last_request_date: Optional[datetime] = None

class UserData(BaseModel):
    """Model representing processed user data and analysis."""
    user_id: UserId
    total_requests: int
    request_frequency: float
    movie_requests: int
    tv_requests: int
    last_processed: datetime
