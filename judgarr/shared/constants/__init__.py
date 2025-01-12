"""
Global constants used across the Judgarr project.
"""
from pathlib import Path

# Default paths
DEFAULT_CONFIG_PATH = Path("config.yml")
DEFAULT_DATABASE_PATH = Path("judgarr.db")
DEFAULT_LOG_PATH = Path("judgarr.log")

# Time constants
SECONDS_PER_DAY = 86400
DEFAULT_TRACKING_PERIOD_DAYS = 30

# Size constants (in bytes)
GB = 1024 * 1024 * 1024
TB = GB * 1024

# API endpoints
OVERSEERR_API_PREFIX = "/api/v1"
OVERSEERR_REQUESTS_ENDPOINT = f"{OVERSEERR_API_PREFIX}/request"
OVERSEERR_USER_ENDPOINT = f"{OVERSEERR_API_PREFIX}/user"
RADARR_MOVIE_ENDPOINT = "/api/v3/movie"
SONARR_SERIES_ENDPOINT = "/api/v3/series"

# Default limits
MAX_COOLDOWN_DAYS = 100
MAX_REQUEST_REDUCTION = 100
