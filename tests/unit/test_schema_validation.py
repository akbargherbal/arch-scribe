"""
Unit tests for schema validation logic.
"""
import pytest
import sys
import os
import unittest
import copy
from src.arch_scribe.arch_state import StateManager, DEFAULT_STATE
import tempfile
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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
        mgr.add_insight("EmptySys", "Valid insight", force=True)
        
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


class TestInsightThresholds(unittest.TestCase):
    """Tests for Fix #5: Minimum insight requirements"""
    
    def test_validate_insight_threshold_50_percent(self):
        """System at 50%+ completeness requires 3+ insights"""
        with tempfile.TemporaryDirectory() as tmp:
            original_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                mgr = StateManager()
                mgr.data = copy.deepcopy(DEFAULT_STATE)
                mgr.data["systems"]["TestSystem"] = {
                    "description": "Valid description",
                    "completeness": 60,
                    "clarity": "medium",
                    "key_files": ["file1.py", "file2.py"],
                    "insights": ["Insight 1", "Insight 2"],  # Only 2 insights
                    "dependencies": [],
                    "complexities": []
                }
                
                errors = mgr.validate_schema()
                
                # Should have error about insufficient insights
                self.assertTrue(any("need 3+" in e for e in errors))
                self.assertTrue(any("60% complete but only 2 insights" in e for e in errors))
            finally:
                os.chdir(original_dir)
    
    def test_validate_insight_threshold_80_percent(self):
        """System at 80%+ completeness requires 5+ insights"""
        with tempfile.TemporaryDirectory() as tmp:
            original_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                mgr = StateManager()
                mgr.data = copy.deepcopy(DEFAULT_STATE)
                mgr.data["systems"]["TestSystem"] = {
                    "description": "Valid description",
                    "completeness": 85,
                    "clarity": "high",
                    "key_files": ["file1.py", "file2.py"],
                    "insights": ["I1", "I2", "I3", "I4"],  # Only 4 insights
                    "dependencies": [],
                    "complexities": []
                }
                
                errors = mgr.validate_schema()
                
                # Should have error about insufficient insights
                self.assertTrue(any("need 5+" in e for e in errors))
                self.assertTrue(any("85% complete but only 4 insights" in e for e in errors))
            finally:
                os.chdir(original_dir)
    
    def test_validate_insight_threshold_sufficient(self):
        """System with sufficient insights passes validation"""
        with tempfile.TemporaryDirectory() as tmp:
            original_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                mgr = StateManager()
                mgr.data = copy.deepcopy(DEFAULT_STATE)
                mgr.data["systems"]["TestSystem"] = {
                    "description": "Valid description",
                    "completeness": 85,
                    "clarity": "high",
                    "key_files": ["file1.py", "file2.py"],
                    "insights": ["I1", "I2", "I3", "I4", "I5"],  # 5 insights = OK
                    "dependencies": [],
                    "complexities": []
                }
                
                errors = mgr.validate_schema()
                
                # Should NOT have insight threshold errors
                insight_errors = [e for e in errors if "insights" in e.lower() and "need" in e]
                self.assertEqual(len(insight_errors), 0)
            finally:
                os.chdir(original_dir)
    
    def test_validate_low_completeness_accepts_few_insights(self):
        """System below 50% completeness can have fewer insights"""
        with tempfile.TemporaryDirectory() as tmp:
            original_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                mgr = StateManager()
                mgr.data = copy.deepcopy(DEFAULT_STATE)
                mgr.data["systems"]["TestSystem"] = {
                    "description": "Valid description",
                    "completeness": 30,
                    "clarity": "low",
                    "key_files": ["file1.py"],
                    "insights": ["Just one insight"],
                    "dependencies": [],
                    "complexities": []
                }
                
                errors = mgr.validate_schema()
                
                # Should NOT have insight threshold errors
                threshold_errors = [e for e in errors if "need 3+" in e or "need 5+" in e]
                self.assertEqual(len(threshold_errors), 0)
            finally:
                os.chdir(original_dir)

