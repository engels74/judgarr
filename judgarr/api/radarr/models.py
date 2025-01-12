"""
Pydantic models for Radarr API responses.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class MovieFile(BaseModel):
    """Model representing a movie file in Radarr."""
    id: int
    movie_id: int = Field(alias="movieId")
    relative_path: str = Field(alias="relativePath")
    path: str
    size: int  # in bytes
    date_added: datetime = Field(alias="dateAdded")
    quality: dict
    media_info: dict = Field(alias="mediaInfo")
    
class Quality(BaseModel):
    """Quality profile information."""
    id: int
    name: str
    source: str
    resolution: int
    
class MovieQualityProfile(BaseModel):
    """Movie quality profile settings."""
    quality: Quality
    allowed: bool
    
class Movie(BaseModel):
    """Model representing a movie in Radarr."""
    id: int
    title: str
    original_title: Optional[str] = Field(alias="originalTitle")
    year: int
    size_on_disk: int = Field(alias="sizeOnDisk", default=0)  # in bytes
    status: str
    monitored: bool
    has_file: bool = Field(alias="hasFile")
    movie_file: Optional[MovieFile] = Field(alias="movieFile", default=None)
    added: datetime
    quality_profile_id: int = Field(alias="qualityProfileId")
    tmdb_id: int = Field(alias="tmdbId")
    imdb_id: Optional[str] = Field(alias="imdbId", default=None)
    
class MovieCollection(BaseModel):
    """Model for a collection of movies."""
    page: int
    page_size: int = Field(alias="pageSize")
    total_records: int = Field(alias="totalRecords")
    records: List[Movie]
