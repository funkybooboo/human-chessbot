"""Pytest configuration and shared fixtures."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_save_dir(temp_dir):
    """Create a temporary save directory for games."""
    save_dir = os.path.join(temp_dir, "games")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    import logging

    # Clear all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # Set to WARNING to reduce noise during tests
    logging.basicConfig(level=logging.WARNING)
    yield
    # Cleanup after test
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
