"""
Shared pytest fixtures and configuration.
"""
import pytest
from pathlib import Path
import json
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that cleans up after test."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def empty_state_manager(temp_dir, monkeypatch):
    """Provide a fresh StateManager instance in a temp directory."""
    monkeypatch.chdir(temp_dir)
    # Import here to avoid circular imports
    # from arch_state import StateManager
    # return StateManager()
    pass


@pytest.fixture
def sample_state_data():
    """Provide sample architecture.json data."""
    return {
        "schema_version": "2.2",
        "metadata": {
            "project_name": "Test Project",
            "project_type": "Flask Web Application",
            "last_updated": "2024-01-01T00:00:00",
            "phase": "survey",
            "total_sessions": 1
        },
        "systems": {},
        "progress": {
            "systems_identified": 0,
            "systems_complete": 0,
            "estimated_overall_completeness": 0
        }
    }


@pytest.fixture
def populated_state_data():
    """Provide state data with several systems already defined."""
    pass
