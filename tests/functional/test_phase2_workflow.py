"""
Functional tests for Phase 2 synthesis workflow.
"""
import pytest
import sys
import os
import json
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager

@pytest.mark.functional
class TestPhase2DataConsumption:
    """Test Phase 2 data retrieval and formatting."""
    
    @pytest.fixture
    def populated_mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Phase2 Test")
        m.add_system("Auth")
        m.update_system("Auth", desc="Handles login", comp=100)
        m.add_insight("Auth", "Uses OAuth", force=True)
        m.add_system("DB")
        m.add_dependency("Auth", "DB", "Stores users")
        return m
    
    def test_show_summary_format(self, populated_mgr, capsys):
        """Test --summary flag produces condensed output."""
        populated_mgr.show_system("Auth", summary=True)
        captured = capsys.readouterr()
        
        data = json.loads(captured.out)
        assert "description" in data
        assert "completeness" in data
        assert "dependencies" in data
        assert "top_insights" in data
        # Summary should not include the full file list
        assert "key_files" not in data
        
    def test_graph_generation(self, populated_mgr, capsys):
        """Test Mermaid graph generation for dependencies."""
        populated_mgr.export_graph()
        captured = capsys.readouterr()
        
        assert "graph TD" in captured.out
        assert 'Auth["Auth"]' in captured.out
        assert 'Auth -->|Stores users| DB' in captured.out