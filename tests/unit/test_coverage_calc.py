import pytest
from unittest.mock import patch  # <--- Added this
from src.arch_scribe.metrics.coverage import calculate_coverage_quality
from src.arch_scribe.core.state_manager import StateManager

class TestCoverageCalculation:
    """Test coverage metric calculations."""

    def setup_method(self):
        self.mgr = StateManager()
        # Mock data structure
        self.mgr.data = {
            "metadata": {
                "scan_stats": {
                    "total_files_scanned": 0,
                    "significant_files_total": 0,
                    "mapped_files_count": 0,
                    "coverage_percentage": 0.0,
                    "coverage_quality": 0.0
                }
            },
            "systems": {},
            "progress": {}
        }

    def test_calculate_coverage_zero_files(self):
        """Coverage should be 0 when no files exist"""
        sig_paths = set()
        mapped = set()
        quality = calculate_coverage_quality(sig_paths, mapped)
        assert quality == 0.0

    def test_calculate_coverage_partial(self):
        """Coverage should reflect partial mapping"""
        sig_paths = {'file1.py', 'file2.py', 'file3.py'}
        mapped = {'file1.py', 'file2.py'}
        
        quality = calculate_coverage_quality(sig_paths, mapped)
        assert quality == 66.7

    def test_calculate_coverage_quality_capped_at_100(self):
        """Coverage quality should never exceed 100%"""
        
        # Test 1: All files mapped (should be exactly 100%)
        sig_paths = {'file1.py', 'file2.py', 'file3.py'}
        mapped = {'file1.py', 'file2.py', 'file3.py'}
        quality = calculate_coverage_quality(sig_paths, mapped)
        assert quality == 100.0

        # Test 2: More files mapped than exist (should not happen in practice, but logic should handle)
        # The intersection logic prevents >100% automatically
        sig_paths = {'file1.py'}
        mapped = {'file1.py', 'file2.py'}
        quality = calculate_coverage_quality(sig_paths, mapped)
        assert quality == 100.0

    def test_calculate_coverage_quality_intersection_logic(self):
        """Verify set intersection logic works correctly"""
        
        # Only files in BOTH sets should count
        sig_paths = {'a.py', 'b.py', 'c.py', 'd.py'}
        mapped = {'b.py', 'c.py', 'e.py', 'f.py'}  # e.py, f.py not significant
        
        quality = calculate_coverage_quality(sig_paths, mapped)
        
        # Should match b.py and c.py (2 files)
        # 2 / 4 = 50%
        assert quality == 50.0

    def test_calculate_coverage_with_test_files(self):
        """Test/doc files are now included (no filtering)"""
        
        # Old behavior: filtered out test files, causing asymmetry
        # New behavior: counts all files consistently
        sig_paths = {'app.py', 'test_app.py', 'docs.py', 'utils.py'}
        mapped = {'app.py', 'test_app.py', 'docs.py', 'utils.py'}
        
        quality = calculate_coverage_quality(sig_paths, mapped)
        assert quality == 100.0

    def test_update_stats_updates_all_metrics(self):
        """Test that update_stats updates all fields correctly"""
        
        # Mock scan_files on the scanner instance
        with patch.object(self.mgr.scanner, 'scan_files') as mock_scan:
            mock_scan.return_value = (10, 5, {'a.py', 'b.py', 'c.py', 'd.py', 'e.py'})
            
            # Setup mapped files
            self.mgr.data["systems"]["Sys1"] = {
                "key_files": ["a.py", "b.py"]
            }
            
            self.mgr.update_stats()
            
            stats = self.mgr.data["metadata"]["scan_stats"]
            assert stats["total_files_scanned"] == 10
            assert stats["significant_files_total"] == 5
            assert stats["mapped_files_count"] == 2  # a.py, b.py
            assert stats["coverage_percentage"] == 40.0  # 2/5
            assert stats["coverage_quality"] == 40.0

    def test_coverage_quality_matches_coverage_percentage(self):
        """After fix, quality should match coverage_percentage"""
        
        # Since we removed filtering, these should be identical
        sig_paths = {'a.py', 'b.py', 'c.py', 'd.py', 'e.py'}
        mapped = {'a.py', 'b.py', 'c.py'}
        
        quality = calculate_coverage_quality(sig_paths, mapped)
        
        # Manual calc: 3/5 = 60%
        assert quality == 60.0