"""Configuration parsing utilities."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

def parse_config_file(config_path: Path) -> Dict[str, Any]:
    """Parse configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict containing parsed configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse configuration file: {e}")
        raise
    
    return config

def create_default_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Create default configuration.
    
    Args:
        config_path: Optional path to write config to
        
    Returns:
        Dict containing default configuration
    """
    default_config = {
        "api": {
            "overseerr": {
                "url": "http://localhost:5055",
                "api_key": ""
            },
            "radarr": {
                "url": "http://localhost:7878",
                "api_key": ""
            },
            "sonarr": {
                "url": "http://localhost:8989",
                "api_key": ""
            }
        },
        "notifications": {
            "discord": {
                "enabled": True,
                "webhook_url": ""
            },
            "email": {
                "enabled": False,
                "smtp_host": "",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_pass": "",
                "from_address": "",
                "use_tls": True
            }
        },
        "punishment": {
            "cooldown_increment": 3,
            "request_limit_decrement": 5,
            "max_cooldown_days": 100,
            "min_request_limit": 0,
            "exponential_factor": 1.5,
            "cooldown_reset_days": 30
        },
        "tracking": {
            "history_days": 30,
            "check_interval": 60,
            "size_thresholds": {
                "warning": 500,
                "punishment": 1000
            }
        }
    }
    
    if config_path:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.safe_dump(default_config, f, default_flow_style=False)
    
    return default_config
