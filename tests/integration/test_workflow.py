"""
Integration tests for multi-command workflows.
"""
import pytest
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import StateManager

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
        mgr.update_system("Auth", desc="Handles user login")

        # 4. Add Insight (with force=True to skip validation in tests)
        mgr.add_insight("Auth", "Implements session management using JWT tokens with Redis backend, which reduces database queries by 50%", force=True)

        # Verify system exists and has expected data
        sys = mgr.data["systems"]["Auth"]
        assert sys["description"] == "Handles user login"
        assert sys["completeness"] == 15
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

        # First update - set initial description
        mgr.update_system("Core", desc="Initial description")
        assert mgr.data["systems"]["Core"]["description"] == "Initial description"
        assert mgr.data["systems"]["Core"]["completeness"] == 0  # No files, insights, or deps yet
        assert mgr.data["systems"]["Core"]["clarity"] == "low"

        # Second update - change description
        mgr.update_system("Core", desc="Updated description")
        assert mgr.data["systems"]["Core"]["description"] == "Updated description"
        assert mgr.data["systems"]["Core"]["completeness"] == 0  # Still no content
        assert mgr.data["systems"]["Core"]["clarity"] == "low"

        # Add insights to test clarity progression
        mgr.add_insight("Core", "Implements core functionality using modular design, which enables extension", force=True)
        mgr.add_insight("Core", "Provides event bus for component communication, which reduces coupling", force=True)
        mgr.add_insight("Core", "Manages lifecycle hooks using observer pattern, which enables plugins", force=True)

        # Now with 3 insights, completeness should be 21% (3/5 * 35 = 21)
        # But 21% < 40%, so clarity stays "low" (need 40%+ for medium)
        assert mgr.data["systems"]["Core"]["completeness"] == 21
        assert mgr.data["systems"]["Core"]["clarity"] == "low"
        
        # To reach medium clarity, need 40%+ completeness
        # Add 2 more insights to get 35 points (5/5 * 35)
        mgr.add_insight("Core", "Handles plugin loading using dynamic imports, which supports extensibility", force=True)
        mgr.add_insight("Core", "Validates configurations using schema checks, which prevents errors", force=True)
        
        # With 5 insights: 35 points = 35% (still < 40%, but close)
        # Add dependency to push over 40%: 35 + 15 = 50%
        mgr.add_system("Config")
        mgr.add_dependency("Core", "Config", "Loads settings")
        
        # Now: 0 (files) + 35 (5 insights) + 15 (dep) + 0 (clarity) = 50%
        # With 50% and 5 insights, clarity should be "medium"
        assert mgr.data["systems"]["Core"]["completeness"] == 55  # 50 base + 5 medium clarity
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

        # Session 2 - Update description and add content
        mgr2.start_session()
        mgr2.update_system("Legacy", desc="Refactored code")
        
        # Add content to reach 100% completeness
        # Need: 40 (files) + 35 (insights) + 15 (dep) + 10 (high clarity) = 100
        
        # Create dummy files for testing
        for i in range(10):
            with open(f"file{i}.py", "w") as f:
                f.write("# " + "x" * 2000)
        
        # Map 10 files (40 points)
        mgr2.map_files("Legacy", [f"file{i}.py" for i in range(10)])
        
        # Add 5 insights (35 points)
        insights = [
            "Refactored to use dependency injection pattern, which improves testability and modularity",
            "Extracted business logic into service layer, which separates concerns and enables reuse",
            "Implemented caching strategy using Redis, which reduces latency by 60 percent",
            "Added comprehensive error handling with retry logic, which improves reliability",
            "Migrated to async/await pattern, which increases throughput and scalability"
        ]
        for insight in insights:
            mgr2.add_insight("Legacy", insight, force=True)
        
        # Add dependency (15 points)
        mgr2.add_system("Cache")
        mgr2.add_dependency("Legacy", "Cache", "Stores computed results")
        
        mgr2.end_session()

        # Verify final state
        mgr3 = StateManager()
        assert mgr3.data["systems"]["Legacy"]["description"] == "Refactored code"
        assert mgr3.data["systems"]["Legacy"]["completeness"] == 100
        assert mgr3.data["systems"]["Legacy"]["clarity"] == "high"
        assert mgr3.data["metadata"]["total_sessions"] == 2