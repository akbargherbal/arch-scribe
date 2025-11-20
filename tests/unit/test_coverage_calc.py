"""
Unit tests for coverage calculation logic.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager

class TestCoverageCalculation:
    """Test coverage metrics calculation."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Test")
        return m

    def test_calculate_coverage_zero_files(self, mgr):
        """Test coverage calculation with no files."""
        # Mock scan_files to return 0
        with patch.object(mgr, 'scan_files', return_value=(0, 0, set())):
            mgr.update_stats()
            stats = mgr.data["metadata"]["scan_stats"]
            assert stats["coverage_percentage"] == 0.0
            assert stats["coverage_quality"] == 0.0
    
    def test_calculate_coverage_partial(self, mgr):
        """Test coverage calculation with some files mapped."""
        # 10 significant files, 5 mapped
        sig_paths = {f"file{i}.py" for i in range(10)}
        mapped_files = {f"file{i}.py" for i in range(5)}
        
        # Setup system with mapped files
        mgr.add_system("Sys1")
        mgr.map_files("Sys1", list(mapped_files))
        
        with patch.object(mgr, 'scan_files', return_value=(20, 10, sig_paths)):
            mgr.update_stats()
            stats = mgr.data["metadata"]["scan_stats"]
            assert stats["coverage_percentage"] == 50.0
            assert stats["mapped_files_count"] == 5
    
    def test_calculate_coverage_quality(self, mgr):
        """Test quality metric excluding test/doc files."""
        # 4 significant files: 2 core, 1 test, 1 doc
        # [FIX] Use 'documentation.md' to ensure it hits the 'doc' filter (README.md doesn't match 'doc')
        sig_paths = {"core.py", "utils.py", "test_core.py", "documentation.md"}
        
        # Map only the core files
        mapped = {"core.py", "utils.py"}
        
        quality = mgr.calculate_coverage_quality(sig_paths, mapped)
        
        # Core significant: core.py, utils.py (2 files)
        # Core mapped: core.py, utils.py (2 files)
        # Quality should be 100%
        assert quality == 100.0
        
        # Now map a test file but miss a core file
        mapped_bad = {"test_core.py", "core.py"}
        quality_bad = mgr.calculate_coverage_quality(sig_paths, mapped_bad)
        
        # Core significant: 2
        # Core mapped: 1 (core.py)
        # Quality should be 50%
        assert quality_bad == 50.0
    
    def test_update_stats_updates_all_metrics(self, mgr):
        """Test that update_stats() refreshes all metrics."""
        sig_paths = {"a.py", "b.py"}
        with patch.object(mgr, 'scan_files', return_value=(10, 2, sig_paths)):
            mgr.update_stats()
            
            stats = mgr.data["metadata"]["scan_stats"]
            assert "total_files_scanned" in stats
            assert "significant_files_total" in stats
            assert "mapped_files_count" in stats
            assert "coverage_percentage" in stats
            assert "coverage_quality" in stats
            
            prog = mgr.data["progress"]
            assert "systems_identified" in prog
            assert "systems_complete" in prog