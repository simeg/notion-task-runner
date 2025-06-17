"""
Utility functions used across the Notion Task Runner project.

This module is intended to house reusable helpers that encapsulate common patterns,
such as logging and error handling, to promote consistency and reduce duplication.
"""

from logging import Logger


def fail(logger: Logger, message: str) -> None:
    logger.error(message)
    exit(1)
