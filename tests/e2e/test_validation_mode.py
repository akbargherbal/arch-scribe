import pytest
import os
from unittest.mock import patch
from src.arch_scribe.core.state_manager import StateManager

class TestValidationMode:
    """End-to-end tests for the 'validate' command logic."""

    def test_validation_detects_errors(self, temp_dir, monkeypatch):
        """Test that validation catches issues in a workflow."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        mgr.init_project("Test Project")

        # Create a system but leave it incomplete
        mgr.add_system("IncompleteSys")
        # Missing description, files, insights

        # Mock scan_files to avoid orphan errors cluttering the result
        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()

        assert len(errors) > 0
        assert any("placeholder description" in e for e in errors)
        assert any("No key_files" in e for e in errors)
        assert any("No insights" in e for e in errors)

    def test_validation_passes_clean_state(self, temp_dir, monkeypatch):
        """Test that clean state passes validation."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        mgr.init_project("Good Project")

        mgr.add_system("GoodSys")
        mgr.update_system("GoodSys", desc="Valid description")
        mgr.map_files("GoodSys", ["file.py"])
        mgr.add_insight("GoodSys", "Valid insight", force=True)

        # Mock scan_files to avoid orphan errors since we didn't create real files
        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()

        assert errors == []