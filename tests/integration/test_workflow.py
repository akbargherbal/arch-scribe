"""
Integration tests for multi-command workflows.
"""
import pytest
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager, STATE_FILE

class TestSystemCreationWorkflow:
    """Test complete system creation workflow."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Workflow Test")
        return m

    def test_create_and_populate_system(self, mgr):
        """Test add → map → update → insight sequence."""
        # 1. Add System
        mgr.add_system("Auth")

        # 2. Map Files
        mgr.map_files("Auth", ["src/auth/login.py", "src/auth/logout.py"])

        # 3. Update Metadata (REMOVED: clarity parameter - now auto-computed)
        mgr.update_system("Auth", desc="Handles user login", comp=20)

        # 4. Add Insight (with force=True to skip validation in tests)
        mgr.add_insight("Auth", "Implements session management using JWT tokens with Redis backend, which reduces database queries by 50%", force=True)

        # Verify system exists and has expected data
        sys = mgr.data["systems"]["Auth"]
        assert sys["description"] == "Handles user login"
        assert sys["completeness"] == 20
        assert len(sys["key_files"]) == 2
        assert len(sys["insights"]) == 1
        # Note: clarity is auto-computed, will be "low" (20% completeness, 1 insight)
        assert sys["clarity"] == "low"

    def test_create_multiple_systems_with_dependencies(self, mgr):
        """Test creating interconnected systems."""
        mgr.add_system("Frontend")
        mgr.add_system("Backend")
        mgr.add_system("Database")
        
        mgr.add_dependency("Frontend", "Backend", "API calls")
        mgr.add_dependency("Backend", "Database", "SQL queries")
        
        # Verify dependencies
        fe_deps = mgr.data["systems"]["Frontend"]["dependencies"]
        assert len(fe_deps) == 1
        assert fe_deps[0]["system"] == "Backend"
        
        be_deps = mgr.data["systems"]["Backend"]["dependencies"]
        assert len(be_deps) == 1
        assert be_deps[0]["system"] == "Database"


class TestStateUpdates:
    """Test that state updates persist correctly."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Update Test")
        return m


    def test_multiple_updates_to_same_system(self, mgr):
        """Test sequential updates to one system and verify auto-computed clarity."""
        mgr.add_system("Core")

        # First update
        mgr.update_system("Core", desc="Initial description", comp=10)
        assert mgr.data["systems"]["Core"]["description"] == "Initial description"
        assert mgr.data["systems"]["Core"]["completeness"] == 10
        assert mgr.data["systems"]["Core"]["clarity"] == "low"  # <40% completeness

        # Second update (overwrite completeness to 50%)
        mgr.update_system("Core", desc="Updated description", comp=50)
        assert mgr.data["systems"]["Core"]["description"] == "Updated description"
        assert mgr.data["systems"]["Core"]["completeness"] == 50
        assert mgr.data["systems"]["Core"]["clarity"] == "low"  # 50% but 0 insights = low

        # Partial update - just triggers recomputation
        mgr.update_system("Core")
        assert mgr.data["systems"]["Core"]["description"] == "Updated description"  # Unchanged
        assert mgr.data["systems"]["Core"]["clarity"] == "low"  # Still low (0 insights)

        # Add insights to test clarity progression
        mgr.add_insight("Core", "Implements core functionality using modular design, which enables extension", force=True)
        mgr.add_insight("Core", "Provides event bus for component communication, which reduces coupling", force=True)
        mgr.add_insight("Core", "Manages lifecycle hooks using observer pattern, which enables plugins", force=True)
        
        # Now with 3 insights and 50% completeness, should be medium
        assert mgr.data["systems"]["Core"]["clarity"] == "medium"

    def test_updates_across_multiple_sessions(self, mgr):
        """Test that changes persist across sessions."""
        # Session 1
        mgr.start_session()
        mgr.add_system("Legacy")
        mgr.update_system("Legacy", desc="Old code")
        mgr.end_session()
        
        # Reload state (simulate new run)
        mgr2 = StateManager()
        assert "Legacy" in mgr2.data["systems"]
        assert mgr2.data["systems"]["Legacy"]["description"] == "Old code"
        
        # Session 2
        mgr2.start_session()
        mgr2.update_system("Legacy", desc="Refactored code", comp=100)
        mgr2.end_session()
        
        # Verify final state
        mgr3 = StateManager()
        assert mgr3.data["systems"]["Legacy"]["description"] == "Refactored code"
        assert mgr3.data["systems"]["Legacy"]["completeness"] == 100
        assert mgr3.data["metadata"]["total_sessions"] == 2