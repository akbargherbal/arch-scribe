import pytest
from unittest.mock import patch
from src.arch_scribe.core.state_manager import StateManager

class TestSchemaValidation:
    """Test validation logic."""

    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        manager = StateManager()
        manager.init_project("Test")
        return manager

    def test_validate_empty_state(self, mgr):
        """Test validation of freshly initialized state."""
        # Fresh state has no systems, so no errors expected regarding systems
        # But might have orphaned files if we don't mock scan_files
        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert errors == []

    def test_validate_missing_description(self, mgr):
        """Test detection of TODO descriptions."""
        mgr.add_system("BadSys")
        # Default description is "TODO"

        # Mock scan_files to avoid orphan errors
        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("placeholder description" in e for e in errors)

    def test_validate_missing_files(self, mgr):
        """Test detection of systems with no key_files."""
        mgr.add_system("EmptySys")
        mgr.update_system("EmptySys", desc="Valid description")
        mgr.add_insight("EmptySys", "Valid insight", force=True)

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("No key_files" in e for e in errors)

    def test_validate_missing_insights(self, mgr):
        """Test detection of systems with no insights."""
        mgr.add_system("NoInsightSys")
        mgr.update_system("NoInsightSys", desc="Valid description")
        mgr.map_files("NoInsightSys", ["file.py"])

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("No insights" in e for e in errors)

    def test_validate_broken_dependencies(self, mgr):
        """Test detection of dependencies to non-existent systems."""
        mgr.add_system("SysA")
        # Manually inject bad dependency to bypass add_dependency checks
        mgr.data["systems"]["SysA"]["dependencies"].append(
            {"system": "GhostSys", "reason": "Because"}
        )

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("non-existent system" in e for e in errors)

    def test_validate_orphaned_files(self, mgr):
        """Test detection of unmapped significant files."""
        # Mock scan_files to return significant files that aren't mapped
        sig_paths = {f"orphan{i}.py" for i in range(10)}
        
        with patch.object(mgr.scanner, 'scan_files', return_value=(10, 10, sig_paths)):
            errors = mgr.validate_schema()
            assert any("unmapped significant files" in e for e in errors)


class TestInsightThresholds:
    """Test validation rules for insight count vs completeness."""

    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        manager = StateManager()
        manager.init_project("Test")
        return manager

    def test_validate_insight_threshold_50_percent(self, mgr):
        """Systems >50% complete need 3+ insights."""
        mgr.add_system("Sys50")
        mgr.update_system("Sys50", desc="Valid")
        mgr.map_files("Sys50", ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py"]) # ~20%
        
        # Only 1 insight
        mgr.add_insight("Sys50", "Insight 1", force=True)
        
        # Force completeness to 55% AFTER adding insight (so it's not overwritten)
        mgr.data["systems"]["Sys50"]["completeness"] = 55

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("need 3+ for 50%+" in e for e in errors)

    def test_validate_insight_threshold_80_percent(self, mgr):
        """Systems >80% complete need 5+ insights."""
        mgr.add_system("Sys80")
        mgr.update_system("Sys80", desc="Valid")
        mgr.map_files("Sys80", ["f1.py"])
        
        # Only 3 insights
        for i in range(3):
            mgr.add_insight("Sys80", f"Insight {i}", force=True)
            
        # Force completeness to 85% AFTER adding insights
        mgr.data["systems"]["Sys80"]["completeness"] = 85

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert any("need 5+ for 80%+" in e for e in errors)

    def test_validate_insight_threshold_sufficient(self, mgr):
        """Validation passes when insight count is sufficient."""
        mgr.add_system("GoodSys")
        mgr.update_system("GoodSys", desc="Valid")
        mgr.map_files("GoodSys", ["f1.py"])
        
        # 5 insights (sufficient)
        for i in range(5):
            mgr.add_insight("GoodSys", f"Insight {i}", force=True)
            
        # 85% complete
        mgr.data["systems"]["GoodSys"]["completeness"] = 85

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert errors == []

    def test_validate_low_completeness_accepts_few_insights(self, mgr):
        """Low completeness systems don't need many insights."""
        mgr.add_system("LowSys")
        mgr.update_system("LowSys", desc="Valid")
        mgr.map_files("LowSys", ["f1.py"])
        
        # 1 insight (sufficient for low completeness)
        mgr.add_insight("LowSys", "Insight 1", force=True)
        
        # 20% complete
        mgr.data["systems"]["LowSys"]["completeness"] = 20

        with patch.object(mgr.scanner, 'scan_files', return_value=(0, 0, set())):
            errors = mgr.validate_schema()
            assert errors == []