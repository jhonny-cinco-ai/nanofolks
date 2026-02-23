"""Centralized logging configuration for nanofolks."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def configure_logging(
    level: str = "SUCCESS",
    log_file: Optional[Path] = None,
    verbose: bool = False
) -> None:
    """
    Configure global logging sinks.
    
    Args:
        level: Minimum level for console output (default: SUCCESS)
        log_file: Optional path for the persistent log file
        verbose: If True, set console level to DEBUG
    """
    # Remove default loguru sink
    logger.remove()

    # Determine paths
    if log_file is None:
        log_file = Path.home() / ".nanofolks" / "nanofolks.log"
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Console Sink (Clean Terminal)
    # Only show SUCCESS, WARNING, ERROR, CRITICAL by default
    console_level = "DEBUG" if verbose else level
    
    logger.add(
        sys.stderr,
        level=console_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )

    # 2. File Sink (Complete History)
    # Always capture everything (DEBUG and above) in the file
    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        enqueue=True,  # Safe for multi-threaded/async
    )

    logger.debug(f"Logging initialized. Console level: {console_level}, File: {log_file}")
