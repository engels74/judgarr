"""Configuration management for Judgarr."""

import os
from pathlib import Path
from typing import Optional
import yaml

from ..shared.constants import DEFAULT_CONFIG_PATH
from .models.core import RootConfig as Config

def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file.
    
    Args:
        config_path: Path to config file, defaults to DEFAULT_CONFIG_PATH
        
    Returns:
        Config: Loaded configuration object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    return Config.model_validate(config_dict)
