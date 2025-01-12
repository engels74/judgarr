"""
Pydantic models for Overseerr API responses.
"""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class MediaInfo(BaseModel):
    """Media information from Overseerr."""
    id: int
    media_type: Literal["movie", "tv"] = Field(alias="mediaType")
    tmdb_id: int = Field(alias="tmdbId")
    status: int
    status4k: Optional[int] = Field(alias="status4k")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
class RequestMedia(BaseModel):
    """Request media details."""
    id: int
    media_type: Literal["movie", "tv"] = Field(alias="mediaType")
    tmdb_id: int = Field(alias="tmdbId")
    tvdb_id: Optional[int] = Field(alias="tvdbId")
    status: int
    status4k: Optional[int] = Field(alias="status4k")
    
class Request(BaseModel):
    """Overseerr request model."""
    id: int
    status: int
    media: RequestMedia
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    requested_by: dict = Field(alias="requestedBy")
    modified_by: Optional[dict] = Field(alias="modifiedBy")
    
class RequestResponse(BaseModel):
    """Response model for request endpoints."""
    page_info: dict = Field(alias="pageInfo")
    results: list[Request]
    
class UserQuota(BaseModel):
    """User quota information."""
    movie: Optional[int] = None
    tv: Optional[int] = None
