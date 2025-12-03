"""
Logging utilities for PolyMind Core.
"""
import logging
import sys
from typing import Optional
from config import settings


def setup_logger(name: str = "polymind", level: Optional[str] = None) -> logging.Logger:
    """
    Setup and configure logger for PolyMind Core.
    
    Args:
        name: Logger name
        level: Log level (INFO, DEBUG, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    log_level = level or settings.log_level
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


# Default logger instance
logger = setup_logger()

