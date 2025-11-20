"""
End-to-end tests for multi-session exploration.
"""
import pytest
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager, STATE_FILE

@pytest.mark.e2e
@pytest.mark.slow
class TestMultiSessionWorkflow:
    """Test complete multi-session exploration workflow."""
    
    def test_three_session_survey(self, temp_dir, monkeypatch):
        """Test 3 complete sessions with state persistence."""
        monkeypatch.chdir(temp_dir)
        
        # Session 1: Init and Discovery
        mgr = StateManager()
        mgr.init_project("E2E Project")
        mgr.start_session()
        mgr.add_system("Core")
        mgr.end_session()
        
        # Session 2: Mapping
        mgr = StateManager() # Reload
        mgr.start_session()
        mgr.map_files("Core", ["main.py"]) 
        mgr.end_session()
        
        # Session 3: Refinement
        mgr = StateManager() # Reload
        mgr.start_session()
        mgr.add_insight("Core", "It works")
        mgr.end_session()
        
        # Verify
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["total_sessions"] == 3
            assert len(data["metadata"]["session_history"]) == 3
            assert "Core" in data["systems"]
            assert "It works" in data["systems"]["Core"]["insights"]
    
    def test_coverage_progression(self, temp_dir, monkeypatch):
        """Test that coverage increases session to session."""
        monkeypatch.chdir(temp_dir)
        
        # Create files
        with open("f1.py", "w") as f: f.write("x"*2000)
        with open("f2.py", "w") as f: f.write("x"*2000)
        
        # Session 1
        mgr = StateManager()
        mgr.init_project("Cov Test")
        mgr.start_session()
        mgr.add_system("Sys")
        mgr.map_files("Sys", ["f1.py"])
        mgr.end_session()
        
        cov1 = mgr.data["metadata"]["scan_stats"]["coverage_percentage"]
        
        # Session 2
        mgr = StateManager()
        mgr.start_session()
        mgr.map_files("Sys", ["f2.py"])
        mgr.end_session()
        
        cov2 = mgr.data["metadata"]["scan_stats"]["coverage_percentage"]
        
        assert cov2 > cov1