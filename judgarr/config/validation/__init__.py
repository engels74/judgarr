"""Configuration validation utilities."""

from pydantic import ValidationError

def validate_punishment_settings(settings: dict) -> None:
    """Validate punishment settings.
    
    Args:
        settings: Punishment settings to validate
        
    Raises:
        ValidationError: If settings are invalid
    """
    if settings["cooldown_increment"] <= 0:
        raise ValidationError("Cooldown increment must be positive")
    
    if settings["request_limit_decrement"] < 0:
        raise ValidationError("Request limit decrement must be non-negative")
    
    if settings["max_cooldown_days"] <= 0:
        raise ValidationError("Maximum cooldown days must be positive")
    
    if settings["min_request_limit"] < 0:
        raise ValidationError("Minimum request limit must be non-negative")
    
    if settings["exponential_factor"] <= 1:
        raise ValidationError("Exponential factor must be greater than 1")
    
    if settings["cooldown_reset_days"] <= 0:
        raise ValidationError("Cooldown reset days must be positive")
