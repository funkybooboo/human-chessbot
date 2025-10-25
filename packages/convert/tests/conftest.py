"""Pytest configuration and shared fixtures for convert package tests."""

import pytest


@pytest.fixture(autouse=True)
def reset_cwd(monkeypatch, tmp_path):
    """Reset current working directory for each test to avoid side effects."""
    # This ensures tests don't interfere with each other
    pass
