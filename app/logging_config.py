"""Structured JSON logging configuration."""

import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # JSON handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        rename_fields={
            "asctime": "timestamp",
            "name": "logger",
            "levelname": "level",
        },
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
