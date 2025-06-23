import logging

import coloredlogs


def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a configured logger instance with colored output.

    If the logger has no handlers, it installs coloredlogs with a specific format
    and sets the logger's name to the final segment of the provided name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        short_name = name.split(".")[-1]
        coloredlogs.install(
            level="INFO",
            logger=logger,
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        logger.name = short_name
    return logger
