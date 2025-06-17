import logging

import coloredlogs


def get_logger(name: str) -> logging.Logger:
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
