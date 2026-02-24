"""
Logging configuration for the BookAPI application.
"""
import logging
import sys
from typing import Optional


def setup_logging(
        level: str = "INFO",
        log_format: Optional[str] = None
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
    """
    if log_format is None:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Configure specific loggers

    # BookAPI logger - main application logger
    bookapi_logger = logging.getLogger("bookapi")
    bookapi_logger.setLevel(logging.INFO)

    # SQLAlchemy logger - reduce verbosity
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # Uvicorn loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Reduce noise from other libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"bookapi.{name}")
