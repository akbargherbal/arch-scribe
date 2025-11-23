"""
File: tests/unit/test_coverage_calc.py
"""

import pytest
import os
import tempfile
import shutil
import json
from arch_state import StateManager

class TestCoverageCalculation:
    """Test suite for coverage calculation functions"""
    
    def setup_method(self):
        """Create temporary directory for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Initialize minimal state
        self.mgr = StateManager()
        self.mgr.data = {
            "schema_version": "2.2",
            "metadata": {
                "project_name": "test",
                "scan_stats": {}
            },
            "systems": {},
            "progress": {}
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_calculate_coverage_zero_files(self):
        """Coverage should be 0 when no files exist"""
        sig_paths = set()
        mapped = set()
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        assert quality == 0.0
    
    def test_calculate_coverage_partial(self):
        """Coverage should reflect partial mapping"""
        sig_paths = {'file1.py', 'file2.py', 'file3.py'}
        mapped = {'file1.py', 'file2.py'}
        
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        assert quality == 66.7  # 2/3 = 66.7%
    
    def test_calculate_coverage_quality_capped_at_100(self):
        """Coverage quality should never exceed 100% (FIX VERIFICATION)"""
        
        # Test 1: All files mapped (should be exactly 100%)
        sig_paths = {'file1.py', 'file2.py', 'file3.py'}
        mapped = {'file1.py', 'file2.py', 'file3.py'}
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        assert quality == 100.0
        
        # Test 2: Mapped set larger than sig_paths (THE BUG SCENARIO)
        # This was causing >100% in git-truck
        sig_paths = {'file1.py', 'file2.py'}
        mapped = {'file1.py', 'file2.py', 'file3.py', 'test.py', 'doc.py'}
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        
        # CRITICAL: Should cap at 100%, not return 250%
        assert quality == 100.0
        assert quality <= 100.0
    
    def test_calculate_coverage_quality_intersection_logic(self):
        """Verify set intersection logic works correctly"""
        
        # Only files in BOTH sets should count
        sig_paths = {'a.py', 'b.py', 'c.py', 'd.py'}
        mapped = {'b.py', 'c.py', 'e.py', 'f.py'}  # e.py, f.py not significant
        
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        
        # Only b.py and c.py are in both sets: 2/4 = 50%
        assert quality == 50.0
    
    def test_calculate_coverage_with_test_files(self):
        """Test/doc files are now included (no filtering)"""
        
        # Old behavior: filtered out test files, causing asymmetry
        # New behavior: counts all files consistently
        sig_paths = {'app.py', 'test_app.py', 'docs.py', 'utils.py'}
        mapped = {'app.py', 'test_app.py', 'docs.py', 'utils.py'}
        
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        
        # All 4 files mapped, including test/doc files
        assert quality == 100.0
    
    def test_update_stats_updates_all_metrics(self):
        """Verify update_stats() integrates with new calculation"""
        
        # Create test files
        os.makedirs('src', exist_ok=True)
        for i in range(3):
            with open(f'src/file{i}.py', 'w') as f:
                f.write('x' * 2000)  # >1KB = significant
        
        # Map some files to a system
        self.mgr.data["systems"]["TestSystem"] = {
            "key_files": ["src/file0.py", "src/file1.py"],
            "insights": []
        }
        
        # Update stats
        self.mgr.update_stats()
        
        stats = self.mgr.data["metadata"]["scan_stats"]
        
        # Verify all metrics updated
        assert stats["significant_files_total"] == 3
        assert stats["mapped_files_count"] == 2
        assert stats["coverage_percentage"] == 66.7  # 2/3
        assert stats["coverage_quality"] == 66.7  # Should match coverage_percentage
        assert stats["coverage_quality"] <= 100.0  # NEVER exceeds 100%
    
    def test_coverage_quality_matches_coverage_percentage(self):
        """After fix, quality should match coverage_percentage"""
        
        # Since we removed filtering, these should be identical
        sig_paths = {'a.py', 'b.py', 'c.py', 'd.py', 'e.py'}
        mapped = {'a.py', 'b.py', 'c.py'}
        
        quality = self.mgr.calculate_coverage_quality(sig_paths, mapped)
        expected_coverage = (3 / 5) * 100  # 60%
        
        assert quality == 60.0
        assert quality == round(expected_coverage, 1)


# ==============================================================================
# VERIFICATION SCRIPT
# ==============================================================================

"""
Run this to verify the fix on git-truck data:

python3 << 'EOF'
import json

# Simulate git-truck state
sig_paths = set([f'file{i}.py' for i in range(76)])  # 76 significant files
mapped = set([f'file{i}.py' for i in range(73)])      # 73 mapped files

# Old calculation (BROKEN)
def old_calc(sig_paths, mapped):
    core_mapped = [f for f in mapped if 'test' not in f.lower()]
    core_sig = [f for f in sig_paths if 'test' not in f.lower()]
    if not core_sig: return 0.0
    return round(len(core_mapped) / len(core_sig) * 100, 1)

# New calculation (FIXED)
def new_calc(sig_paths, mapped):
    if not sig_paths: return 0.0
    mapped_sig = sig_paths.intersection(mapped)
    return round(len(mapped_sig) / len(sig_paths) * 100, 1)

print("Git-truck simulation:")
print(f"  Old (broken): {old_calc(sig_paths, mapped)}%")  # Could be >100%
print(f"  New (fixed):  {new_calc(sig_paths, mapped)}%")  # Always ≤100%
print(f"  Coverage:     {round(73/76*100, 1)}%")          # Should match new calc
EOF
"""