"""
Unified logging configuration using structlog.

Provides structured JSON output for production and colored console output
for development with proper formatting and third-party log suppression.
"""

import logging
import sys
from typing import Any, cast

import structlog


def configure_logging(json_logs: bool = False, log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Args:
        json_logs: Whether to output logs in JSON format
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # JSON output for production - include format_exc_info for JSON logs
        shared_processors.insert(-1, structlog.processors.format_exc_info)
        shared_processors.append(structlog.processors.JSONRenderer())
        formatter = None
    else:
        # Human-readable output for development - exclude format_exc_info for pretty exceptions
        shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
        )

    # Configure structlog
    structlog.configure(
        processors=cast(Any, shared_processors),
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    if formatter:
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
