"""
Unit tests for schema validation logic.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager

class TestSchemaValidation:
    """Test validate_schema() function."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Test")
        return m
    
    def test_validate_empty_state(self, mgr):
        """Test validation of freshly initialized state."""
        # Fresh state has no systems, so no errors expected regarding systems
        # But might have orphaned files if we don't mock scan_files
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert len(errors) == 0
    
    def test_validate_missing_description(self, mgr):
        """Test detection of TODO descriptions."""
        mgr.add_system("BadSys")
        # Default description is "TODO"
        
        # Mock scan_files to avoid orphan errors
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("Missing or placeholder description" in e for e in errors)
    
    def test_validate_missing_files(self, mgr):
        """Test detection of systems with no key_files."""
        mgr.add_system("EmptySys")
        mgr.update_system("EmptySys", desc="Valid description")
        mgr.add_insight("EmptySys", "Valid insight")
        
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("No key_files listed" in e for e in errors)
    
    def test_validate_missing_insights(self, mgr):
        """Test detection of systems with no insights."""
        mgr.add_system("NoInsightSys")
        mgr.update_system("NoInsightSys", desc="Valid description")
        mgr.map_files("NoInsightSys", ["file.py"])
        
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("No insights recorded" in e for e in errors)
    
    def test_validate_broken_dependencies(self, mgr):
        """Test detection of dependencies to non-existent systems."""
        mgr.add_system("SysA")
        # Manually inject bad dependency to bypass add_dependency checks
        mgr.data["systems"]["SysA"]["dependencies"].append(
            {"system": "GhostSys", "reason": "Because"}
        )
        
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("References non-existent system" in e for e in errors)
    
    def test_validate_orphaned_files(self, mgr):
        """Test detection of unmapped significant files."""
        # Mock scan_files to return significant files that aren't mapped
        sig_paths = {f"orphan{i}.py" for i in range(10)}
        
        with patch.object(mgr, 'scan_files', return_value=(10, 10, sig_paths)):
            errors = mgr.validate_schema()
            assert any("unmapped significant files" in e for e in errors)