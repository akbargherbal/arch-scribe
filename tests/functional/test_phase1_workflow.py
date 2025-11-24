"""
Functional tests for Phase 1 exploration workflow.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import StateManager

@pytest.mark.functional
class TestCompletePhase1Session:
    """Test complete Phase 1 exploration workflow."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Phase1 Test")
        return m

    def test_initial_discovery_session(self, mgr):
        """Test first session: orientation and initial systems."""
        mgr.start_session()
        
        # Simulate finding 2 systems
        mgr.add_system("Auth")
        mgr.update_system("Auth", desc="Login logic")
        
        mgr.add_system("Database")
        mgr.update_system("Database", desc="Postgres wrapper")
        
        mgr.end_session()
        
        # Force stats update to calculate systems_identified
        mgr.update_stats()
        
        assert mgr.data["progress"]["systems_identified"] == 2
        assert mgr.data["metadata"]["total_sessions"] == 1
        
    def test_progressive_coverage_increase(self, mgr):
        """Test that coverage increases over multiple sessions."""
        # [FIX] Create files larger than 1KB (1024 bytes) to be "significant"
        # "content" is 7 bytes. 7 * 200 = 1400 bytes > 1KB
        with open("a.py", "w") as f: f.write("content"*200)
        with open("b.py", "w") as f: f.write("content"*200)
        
        # Session 1: Map a.py
        mgr.start_session()
        mgr.add_system("Sys A")
        mgr.map_files("Sys A", ["a.py"])
        mgr.end_session()
        
        cov1 = mgr.data["metadata"]["scan_stats"]["coverage_percentage"]
        
        # Session 2: Map b.py
        mgr.start_session()
        mgr.map_files("Sys A", ["b.py"])
        mgr.end_session()
        
        cov2 = mgr.data["metadata"]["scan_stats"]["coverage_percentage"]
        
        # Should go from 50% (1/2) to 100% (2/2)
        assert cov1 == 50.0
        assert cov2 == 100.0
        assert cov2 > cov1
    def test_system_completeness_tracking(self, mgr):
        """Test that completeness scores are computed from files and insights."""
        mgr.add_system("Core")
        assert mgr.data["systems"]["Core"]["completeness"] == 0
        
        # Map some files to increase completeness
        mgr.map_files("Core", ["core.py", "utils.py", "config.py"])
        # 3 files = 12 points (3/10 * 40)
        assert mgr.data["systems"]["Core"]["completeness"] == 12
        
        # Add insights to further increase completeness
        mgr.add_insight("Core", "Implements core functionality using modular design, which enables easy extension", force=True)
        mgr.add_insight("Core", "Provides configuration management using YAML files, which simplifies deployment", force=True)
        # 3 files (12) + 2 insights (14) = 26 points
        assert mgr.data["systems"]["Core"]["completeness"] == 26
        
        # Check aggregate progress
        mgr.update_stats()
        assert mgr.data["progress"]["estimated_overall_completeness"] == 26.0
