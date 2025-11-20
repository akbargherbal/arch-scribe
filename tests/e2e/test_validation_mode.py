"""
End-to-end tests for Phase 1.5 validation workflow.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager

@pytest.mark.e2e
class TestValidationMode:
    """Test validation mode workflow."""
    
    def test_validation_detects_errors(self, temp_dir, monkeypatch):
        """Test that validation catches data quality issues."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        mgr.init_project("Bad Project")
        
        # Create invalid state
        mgr.add_system("BadSys") # Default desc is TODO
        
        errors = mgr.validate_schema()
        assert len(errors) > 0
        assert any("placeholder description" in e for e in errors)
    
    def test_validation_passes_clean_state(self, temp_dir, monkeypatch):
        """Test that clean state passes validation."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        mgr.init_project("Good Project")
        
        mgr.add_system("GoodSys")
        mgr.update_system("GoodSys", desc="Valid description")
        mgr.map_files("GoodSys", ["file.py"])
        mgr.add_insight("GoodSys", "Valid insight")
        
        # Mock scan_files to avoid orphan errors since we didn't create real files
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            
        assert len(errors) == 0