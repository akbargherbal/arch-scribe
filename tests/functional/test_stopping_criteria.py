"""
Functional tests for stopping condition detection.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager

@pytest.mark.functional
class TestGateDetection:
    """Test automated stopping criteria detection."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Gate Test")
        return m
    
    def test_gate_a_90_percent_coverage(self, mgr, capsys):
        """Test that Gate A is detected at 90%+ coverage."""
        # Mock stats directly
        mgr.data["metadata"]["scan_stats"]["coverage_percentage"] = 91.0
        
        # Prevent update_stats from overwriting our mock
        with patch.object(mgr, 'update_stats'):
            mgr.print_status()
            
        captured = capsys.readouterr()
        assert "Gate A: Coverage threshold met" in captured.out
    
    def test_gate_b_diminishing_returns(self, mgr, capsys):
        """Test Gate B detection after 3 low-yield sessions."""
        # Inject 3 low yield sessions
        history = []
        for i in range(3):
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
    
    def test_both_gates_simultaneously(self, mgr, capsys):
        """Test behavior when both gates trigger."""
        mgr.data["metadata"]["scan_stats"]["coverage_percentage"] = 95.0
        
        history = [{"session_id": i, "new_systems_found": 0, "new_files_mapped": 0, "insights_added": 0} for i in range(3)]
        mgr.data["metadata"]["session_history"] = history
        
        with patch.object(mgr, 'update_stats'):
            mgr.print_status()
            
        captured = capsys.readouterr()
        assert "Gate A" in captured.out
        assert "Gate B" in captured.out