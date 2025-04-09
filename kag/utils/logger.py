"""
Logging utilities for the KAG system.

This module provides functions for setting up and using logging throughout
the KAG system.
"""

import logging
import os
import sys
from typing import Optional

from kag.config import get_settings

# Get settings
settings = get_settings()

def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Setup logging for the KAG system.
    
    Args:
        log_level: Optional log level override
    """
    # Get log level from settings or override
    log_level = log_level or settings.log_level
    
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure logging format
    log_format = settings.log_format
    
    # Configure handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Configure log file if specified
    log_dir = os.environ.get("KAG_LOG_DIR")
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "kag.log")
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers
    )
    
    # Set log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log startup
    logger = logging.getLogger("kag")
    logger.info(f"Logging setup with level {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.
    
    Args:
        name: Name of the module
        
    Returns:
        Logger for the module
    """
    # Check if main logger has been configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        setup_logging()
    
    # Add kag prefix for internal modules
    if not name.startswith("kag.") and not name == "kag":
        if name.startswith("__main__"):
            name = "kag"
        else:
            name = f"kag.{name}"
    
    return logging.getLogger(name) 