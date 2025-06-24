"""
Utility functions used across the Notion Task Runner project.

This module is intended to house reusable helpers that encapsulate common patterns,
such as logging and error handling, to promote consistency and reduce duplication.
"""

import os
from logging import Logger


def fail(log: Logger, message: str) -> None:
    log.error(message)
    exit(1)


def get_or_raise(log: Logger, key: str) -> str:
    """
    Retrieves the value of a configuration key or fails if not set.

    :param key: The environment variable key to retrieve.
    :param log: The logger to use for logging errors.
    :return: The value of the environment variable.
    """
    value = os.getenv(key)
    if not value:
        fail(log, f"Missing required environment variable: {key}")
    return value  # type: ignore[return-value]
