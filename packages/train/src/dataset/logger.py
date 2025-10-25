"""Logging configuration for the dataset module."""

import logging
import sys

# Create logger for the dataset module
logger = logging.getLogger("dataset")
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add handler to logger
if not logger.handlers:
    logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module within dataset."""
    return logging.getLogger(f"dataset.{name}")
