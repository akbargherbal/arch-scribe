"""
Integration tests for session tracking.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager

class TestSessionLifecycle:
    """Test session start/end tracking."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("SessionTest")
        return m
    
    def test_session_start_increments_counter(self, mgr):
        """Test that session-start increments total_sessions."""
        assert mgr.data["metadata"]["total_sessions"] == 0
        mgr.start_session()
        assert mgr.data["metadata"]["total_sessions"] == 1
    
    def test_session_end_records_history(self, mgr):
        """Test that session-end adds to session_history."""
        mgr.start_session()
        mgr.end_session()
        
        history = mgr.data["metadata"]["session_history"]
        assert len(history) == 1
        assert history[0]["session_id"] == 1
    
    def test_session_tracks_changes(self, mgr):
        """Test that session delta is calculated correctly."""
        mgr.start_session()
        
        # Make changes
        mgr.add_system("NewSys")
        mgr.map_files("NewSys", ["a.py", "b.py"])
        mgr.add_insight("NewSys", "Insight 1")
        
        mgr.end_session()
        
        entry = mgr.data["metadata"]["session_history"][0]
        assert entry["new_systems_found"] == 1
        assert entry["new_files_mapped"] == 2
        assert entry["insights_added"] == 1


class TestStoppingCriteria:
    """Test stopping condition detection."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("GateTest")
        return m
    
    def test_gate_a_detected(self, mgr, capsys):
        """Test Gate A: 90%+ coverage detection."""
        # Mock stats to 95% coverage
        mgr.data["metadata"]["scan_stats"]["coverage_percentage"] = 95.0
        
        # [FIX] Patch update_stats to prevent it from overwriting our manual 95% with 0%
        with patch.object(mgr, 'update_stats'):
            mgr.print_status()
        
        captured = capsys.readouterr()
        assert "Gate A: Coverage threshold met" in captured.out
    
    def test_gate_b_detected(self, mgr, capsys):
        """Test Gate B: 3 low-yield sessions detection."""
        # Add 3 low yield sessions
        history = []
        for i in range(1, 4):
            history.append({
                "session_id": i,
                "new_systems_found": 0,
                "new_files_mapped": 1, # < 3
                "insights_added": 0
            })
        mgr.data["metadata"]["session_history"] = history
        
        mgr.print_status()
        
        captured = capsys.readouterr()
        assert "Gate B: Diminishing returns detected" in captured.out