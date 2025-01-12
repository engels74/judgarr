"""
Pydantic models for Sonarr API responses.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class EpisodeFile(BaseModel):
    """Model representing an episode file in Sonarr."""
    id: int
    series_id: int = Field(alias="seriesId")
    season_number: int = Field(alias="seasonNumber")
    relative_path: str = Field(alias="relativePath")
    path: str
    size: int  # in bytes
    date_added: datetime = Field(alias="dateAdded")
    quality: dict
    media_info: dict = Field(alias="mediaInfo")
    
class Season(BaseModel):
    """Model representing a TV show season."""
    season_number: int = Field(alias="seasonNumber")
    monitored: bool
    statistics: Optional[dict] = None
    
class Series(BaseModel):
    """Model representing a TV series in Sonarr."""
    id: int
    title: str
    sort_title: str = Field(alias="sortTitle")
    status: str
    overview: Optional[str] = None
    network: Optional[str] = None
    air_time: Optional[str] = Field(alias="airTime", default=None)
    monitored: bool
    quality_profile_id: int = Field(alias="qualityProfileId")
    season_folder: bool = Field(alias="seasonFolder")
    size_on_disk: int = Field(alias="sizeOnDisk", default=0)  # in bytes
    seasons: List[Season]
    path: str
    tvdb_id: Optional[int] = Field(alias="tvdbId")
    tv_maze_id: Optional[int] = Field(alias="tvMazeId")
    tv_rage_id: Optional[int] = Field(alias="tvRageId")
    added: datetime
    
class Episode(BaseModel):
    """Model representing a TV episode."""
    id: int
    series_id: int = Field(alias="seriesId")
    episode_file_id: Optional[int] = Field(alias="episodeFileId")
    season_number: int = Field(alias="seasonNumber")
    episode_number: int = Field(alias="episodeNumber")
    title: str
    air_date: Optional[datetime] = Field(alias="airDate")
    air_date_utc: Optional[datetime] = Field(alias="airDateUtc")
    overview: Optional[str] = None
    monitored: bool
    has_file: bool = Field(alias="hasFile")
    size_on_disk: Optional[int] = Field(alias="sizeOnDisk", default=0)  # in bytes if downloaded
    
class SeriesCollection(BaseModel):
    """Model for a collection of TV series."""
    page: int
    page_size: int = Field(alias="pageSize")
    total_records: int = Field(alias="totalRecords")
    records: List[Series]
    
class SeasonStatistics(BaseModel):
    """Statistics for a TV season."""
    previous_airing: Optional[datetime] = Field(alias="previousAiring")
    size_on_disk: int = Field(alias="sizeOnDisk")
    episode_file_count: int = Field(alias="episodeFileCount")
    episode_count: int = Field(alias="episodeCount")
    total_episode_count: int = Field(alias="totalEpisodeCount")
    percent_of_episodes: float = Field(alias="percentOfEpisodes")
