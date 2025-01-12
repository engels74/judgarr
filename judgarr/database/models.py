"""Database models for the application."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from ..shared.types import UserId

class UserData:
    """User data and request statistics."""
    
    def __init__(
        self,
        user_id: UserId,
        username: str,
        total_data_usage: int,  # in bytes
        total_requests: int,
        request_frequency: float,
        movie_requests: int,
        tv_requests: int,
        last_processed: datetime,
    ):
        self._user_id = user_id
        self._username = username
        self._total_data_usage = total_data_usage
        self._total_requests = total_requests
        self._request_frequency = request_frequency
        self._movie_requests = movie_requests
        self._tv_requests = tv_requests
        self._last_processed = last_processed

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def total_data_usage(self) -> int:
        return self._total_data_usage

    @property
    def total_requests(self) -> int:
        return self._total_requests

    @property
    def request_frequency(self) -> float:
        return self._request_frequency

    @property
    def movie_requests(self) -> int:
        return self._movie_requests

    @property
    def tv_requests(self) -> int:
        return self._tv_requests

    @property
    def last_processed(self) -> datetime:
        return self._last_processed


class UserRequest(BaseModel):
    """User request record."""
    id: int
    user_id: UserId
    media_id: str
    media_type: str
    request_date: datetime
    size_bytes: int
    status: str


class UserStats(BaseModel):
    """User statistics and current status."""
    user_id: UserId
    username: str
    total_data_usage: int
    total_requests: int = 0
    punishment_level: int
    cooldown_days: int
    request_limit: int


class UserPunishment(BaseModel):
    """User punishment record."""
    id: int
    user_id: UserId
    level: int
    start_date: datetime
    end_date: datetime
    cooldown_days: int
    request_reduction: int
    data_usage: int
    is_active: bool = True
    reason: Optional[str] = None
