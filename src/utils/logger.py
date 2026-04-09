"""Logging configuration"""
import sys
from pathlib import Path
from loguru import logger


def get_yaml_config():
    """Get yaml config with fallback"""
    try:
        from utils.config import yaml_config
        return yaml_config
    except:
        return {
            "logging": {
                "level": "INFO",
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                "file": "logs/chatgpt_register_{time}.log",
                "save_to_database": True
            }
        }


def database_sink(message):
    """Custom sink to save logs to database"""
    try:
        # Parse loguru record
        record = message.record
        level = record["level"].name
        module = record["name"]
        msg = record["message"]
        
        # Only save important logs (INFO and above) to database
        if level in ["INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]:
            # Import here to avoid circular dependency
            from database.repository import LogRepository
            
            # Extract extra data if available
            extra_data = record.get("extra", {})
            
            # Save to database (async, don't block)
            LogRepository.create(
                level=level,
                module=module,
                message=msg[:2000],  # Truncate long messages
                extra_data=extra_data if extra_data else None
            )
    except Exception as e:
        # Don't crash if database logging fails
        pass


def setup_logger():
    """Setup loguru logger with file, console, and database output"""
    
    # Remove default handler
    logger.remove()
    
    # Get config
    yaml_config = get_yaml_config()
    log_config = yaml_config.get("logging", {})
    log_level = log_config.get("level", "INFO")
    log_format = log_config.get("format", "{time} | {level} | {message}")
    log_file = log_config.get("file", "logs/chatgpt_register_{time}.log")
    save_to_db = log_config.get("save_to_database", True)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Add console handler with colors
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True
    )
    
    # Add file handler
    logger.add(
        log_file,
        format=log_format,
        level=log_level,
        rotation="1 day",
        retention="7 days",
        compression="zip"
    )
    
    # Add database handler if enabled
    if save_to_db:
        logger.add(
            database_sink,
            format="{message}",
            level="INFO",  # Only save INFO and above to database
            enqueue=True  # Async logging to avoid blocking
        )
    
    return logger


# Initialize logger
log = setup_logger()
