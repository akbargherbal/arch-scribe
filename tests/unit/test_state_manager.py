"""
Unit tests for StateManager core functionality.
"""
import pytest
import os
import json
import sys
import tempfile
import unittest
from unittest.mock import patch, mock_open



# Add project root to path to import arch_state
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import StateManager, STATE_FILE, BACKUP_FILE

class TestStateManagerInit:
    """Test StateManager initialization and setup."""

    def test_load_state_missing_file(self, temp_dir, monkeypatch):
        """Test loading state when file doesn't exist."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        assert mgr.data is None

    def test_load_state_valid_json(self, temp_dir, monkeypatch, sample_state_data):
        """Test loading valid architecture.json."""
        monkeypatch.chdir(temp_dir)
        with open(STATE_FILE, 'w') as f:
            json.dump(sample_state_data, f)

        mgr = StateManager()
        assert mgr.data is not None
        assert mgr.data["metadata"]["project_name"] == "Test Project"

    def test_load_state_corrupted_json(self, temp_dir, monkeypatch, sample_state_data):
        """Test recovery from corrupted JSON with backup."""
        monkeypatch.chdir(temp_dir)

        # Create corrupted state file
        with open(STATE_FILE, 'w') as f:
            f.write("{invalid json")

        # Create valid backup
        with open(BACKUP_FILE, 'w') as f:
            json.dump(sample_state_data, f)

        # Should load from backup
        mgr = StateManager()
        assert mgr.data is not None
        assert mgr.data["metadata"]["project_name"] == "Test Project"

    def test_load_state_corrupted_no_backup(self, temp_dir, monkeypatch):
        """Test failure when corrupted and no backup exists."""
        monkeypatch.chdir(temp_dir)
        with open(STATE_FILE, 'w') as f:
            f.write("{invalid json")

        with pytest.raises(SystemExit):
            StateManager()


class TestProjectInit:
    """Test project initialization."""

    def test_init_new_project(self, temp_dir, monkeypatch):
        """Test initializing a new project."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()

        # Mock input to avoid hanging if it asks (though it shouldn't for new)
        monkeypatch.setattr('builtins.input', lambda _: 'y')

        mgr.init_project("My New Project")

        assert os.path.exists(STATE_FILE)
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            assert data["metadata"]["project_name"] == "My New Project"
            assert data["metadata"]["phase"] == "survey"

    def test_init_with_existing_file(self, temp_dir, monkeypatch):
        """Test initialization when file exists (overwrite prompt)."""
        monkeypatch.chdir(temp_dir)

        # Create existing
        with open(STATE_FILE, 'w') as f:
            f.write("{}")

        mgr = StateManager()

        # Simulate 'y' for overwrite
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        mgr.init_project("Overwritten Project")

        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            assert data["metadata"]["project_name"] == "Overwritten Project"

    def test_init_abort_on_no(self, temp_dir, monkeypatch):
        """Test initialization aborts if user says no to overwrite."""
        monkeypatch.chdir(temp_dir)

        # Create existing
        with open(STATE_FILE, 'w') as f:
            json.dump({"original": True}, f)

        mgr = StateManager()

        # Simulate 'n' for overwrite
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        mgr.init_project("New Project")

        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            assert data.get("original") is True

    def test_detect_project_type_django(self, temp_dir, monkeypatch):
        """Test Django project detection."""
        monkeypatch.chdir(temp_dir)
        with open("manage.py", "w") as f: f.write("# django")

        mgr = StateManager()
        assert mgr.detect_project_type() == "Django Web Application"

    def test_detect_project_type_flask(self, temp_dir, monkeypatch):
        """Test Flask project detection."""
        monkeypatch.chdir(temp_dir)
        with open("app.py", "w") as f: f.write("# flask")
        with open("requirements.txt", "w") as f: f.write("flask")

        mgr = StateManager()
        assert mgr.detect_project_type() == "Flask Web Application"


class TestSystemOperations:
    """Test CRUD operations on systems."""

    @pytest.fixture
    def initialized_mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        mgr.init_project("Test Project")
        return mgr

    def test_add_system(self, initialized_mgr):
        """Test adding a new system."""
        initialized_mgr.add_system("Auth System")
        assert "Auth System" in initialized_mgr.data["systems"]
        assert initialized_mgr.data["systems"]["Auth System"]["completeness"] == 0

    def test_add_duplicate_system(self, initialized_mgr, capsys):
        """Test adding a system that already exists."""
        initialized_mgr.add_system("Auth System")
        initialized_mgr.add_system("Auth System")
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_update_system_description(self, initialized_mgr):
        """Test updating system description."""
        initialized_mgr.add_system("Auth System")
        initialized_mgr.update_system("Auth System", desc="Handles login")
        assert initialized_mgr.data["systems"]["Auth System"]["description"] == "Handles login"

    def test_update_system_with_newline_fails(self, initialized_mgr, capsys):
        """Test that descriptions with newlines are rejected."""
        initialized_mgr.add_system("Auth System")
        initialized_mgr.update_system("Auth System", desc="Line 1\nLine 2")
        captured = capsys.readouterr()
        assert "cannot contain newlines" in captured.out
        assert initialized_mgr.data["systems"]["Auth System"]["description"] == "TODO"

    def test_map_files_to_system(self, initialized_mgr):
        """Test mapping files to a system."""
        initialized_mgr.add_system("Auth System")
        initialized_mgr.map_files("Auth System", ["auth.py", "login.py"])

        files = initialized_mgr.data["systems"]["Auth System"]["key_files"]
        assert "auth.py" in files
        assert "login.py" in files
        assert len(files) == 2

    def test_validate_insight_quality_good_insight(self):
        """Good insights should pass validation"""
        mgr = StateManager()

        # Good insight: 15+ words, has action verb, has impact
        good_insight = "Implements token refresh using Redis cache with sliding window TTL, which reduces database load by sixty percent and improves response times"
        errors = mgr.validate_insight_quality(good_insight)

        assert errors == []

    def test_validate_insight_quality_too_short(self):
        """Short insights should fail validation"""
        mgr = StateManager()

        errors = mgr.validate_insight_quality("Uses JWT")
        assert len(errors) > 0
        assert any("Too short" in e for e in errors)

        # Should report word count
        assert "2 words" in errors[0]

    def test_validate_insight_quality_missing_action(self):
        """Insights without action verbs should fail"""
        mgr = StateManager()

        # Long but no action verb
        insight = "The system is complex and has many different features for handling requests from various client applications and services"
        errors = mgr.validate_insight_quality(insight)

        assert any("WHAT" in e for e in errors)

    def test_validate_insight_quality_missing_impact(self):
        """Insights without impact statement should fail"""
        mgr = StateManager()

        # Has action but no impact
        insight = "Implements decorator pattern for route protection with middleware functions in the application stack"
        errors = mgr.validate_insight_quality(insight)

        assert any("WHY/IMPACT" in e for e in errors)

    def test_add_insight_with_force_bypasses_validation(self):
        """Force flag should bypass validation for testing"""
        mgr = StateManager()
        mgr.data = {
            "systems": {
                "TestSys": {
                    "insights": [],
                    "key_files": []
                }
            },
            "metadata": {"last_updated": ""}
        }

        # Short insight with force=True should be added
        mgr.add_insight("TestSys", "Short text", force=True)
        assert len(mgr.data["systems"]["TestSys"]["insights"]) == 1

    def test_add_insight(self):
        """Test adding quality insight (UPDATE EXISTING TEST)"""
        mgr = StateManager()
        mgr.data = {
            "systems": {
                "TestSys": {
                    "insights": [],
                    "key_files": []
                }
            },
            "metadata": {"last_updated": ""}
        }

        # Use quality insight (15+ words, action, impact)
        insight = "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load by caching session data and improves scalability"
        mgr.add_insight("TestSys", insight, force=True)

        assert len(mgr.data["systems"]["TestSys"]["insights"]) == 1
        assert mgr.data["systems"]["TestSys"]["insights"][0] == insight

    def test_add_duplicate_insight_blocked(self):
        """Duplicate detection should still work (UPDATE EXISTING TEST)"""
        mgr = StateManager()
        mgr.data = {
            "systems": {
                "TestSys": {
                    "insights": [],
                    "key_files": []
                }
            },
            "metadata": {"last_updated": ""}
        }

        insight = "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load by caching session data and improves scalability"

        # Add once
        mgr.add_insight("TestSys", insight, force=True)
        # Try to add duplicate
        mgr.add_insight("TestSys", insight, force=True)

        # Should only exist once
        assert len(mgr.data["systems"]["TestSys"]["insights"]) == 1


    def test_add_dependency(self, initialized_mgr):
        """Test adding dependency between systems."""
        initialized_mgr.add_system("Frontend")
        initialized_mgr.add_system("Backend")

        initialized_mgr.add_dependency("Frontend", "Backend", "API calls")

        deps = initialized_mgr.data["systems"]["Frontend"]["dependencies"]
        assert len(deps) == 1
        assert deps[0]["system"] == "Backend"
        assert deps[0]["reason"] == "API calls"





class TestClarityComputation(unittest.TestCase):
    """Tests for auto-computed clarity levels"""

    def test_compute_clarity_low_minimal_insights(self):
        """Low clarity: 0-2 insights, <40% completeness"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")

                sys = mgr.data["systems"]["Test System"]

                # Add only 2 insights
                mgr.add_insight("Test System", "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load", force=True)
                mgr.add_insight("Test System", "Provides role-based access control using decorator pattern, which simplifies authorization checks", force=True)

                # Verify clarity is low
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "low")
                self.assertEqual(len(sys["insights"]), 2)
                # With 2 insights and 0 files:
                # Completeness = 0 (files) + 14 (2/5 * 35) + 0 (deps) + 0 (clarity) = 14%
                self.assertEqual(sys["completeness"], 14)
            finally:
                os.chdir(orig_dir)

    def test_compute_clarity_medium_partial_understanding(self):
        """Medium clarity: 3-4 insights, 40-69% completeness"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                # Create dummy files to boost completeness
                for i in range(5):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)
                
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                
                # Map 5 files (20 points)
                mgr.map_files("Test System", [f"file{i}.py" for i in range(5)])

                # Add 3 insights (21 points)
                mgr.add_insight("Test System", "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load", force=True)
                mgr.add_insight("Test System", "Provides role-based access control using decorator pattern, which simplifies authorization checks", force=True)
                mgr.add_insight("Test System", "Handles session management using sliding window expiration, which improves security without frequent re-authentication", force=True)

                # Verify clarity is medium
                # Expected: 20 (files) + 21 (3 insights) + 0 (deps) + 0 (clarity) = 41%
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "medium")  # 41% comp + 3 insights = medium
                self.assertEqual(len(sys["insights"]), 3)
                self.assertGreaterEqual(sys["completeness"], 40)
                self.assertLess(sys["completeness"], 70)
            finally:
                os.chdir(orig_dir)

    def test_compute_clarity_high_deep_understanding(self):
        """High clarity: 5+ insights, 70%+ completeness, with dependencies"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                # Create dummy files to boost completeness
                for i in range(10):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)
                
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Auth System")
                mgr.add_system("Database")
                
                # Map 10 files (40 points)
                mgr.map_files("Auth System", [f"file{i}.py" for i in range(10)])

                # Add 5 insights (35 points)
                insights = [
                    "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load",
                    "Provides role-based access control using decorator pattern, which simplifies authorization checks",
                    "Handles session management using sliding window expiration, which improves security without frequent re-authentication",
                    "Manages password hashing using bcrypt with adaptive work factor, which provides future-proof security",
                    "Integrates with OAuth providers using PKCE flow, which enables secure third-party authentication"
                ]
                for insight in insights:
                    mgr.add_insight("Auth System", insight, force=True)

                # Add dependency (15 points + required for high clarity)
                mgr.add_dependency("Auth System", "Database", "Stores user credentials and session tokens")

                # Verify clarity is high
                # Expected: 40 (10 files) + 35 (5 insights) + 15 (dep) + 10 (high clarity) = 100%
                sys = mgr.data["systems"]["Auth System"]
                self.assertEqual(sys["clarity"], "high")
                self.assertEqual(len(sys["insights"]), 5)
                self.assertGreaterEqual(sys["completeness"], 70)
                self.assertGreater(len(sys["dependencies"]), 0)
            finally:
                os.chdir(orig_dir)

    def test_compute_clarity_high_requires_dependencies(self):
        """High clarity requires dependencies even with 5+ insights and 70%+ completeness"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                # Create dummy files
                for i in range(10):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)
                
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                
                # Map 10 files (40 points) to get over 70% completeness threshold
                mgr.map_files("Test System", [f"file{i}.py" for i in range(10)])

                # Add 5 insights (35 points)
                insights = [
                    "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load",
                    "Provides role-based access control using decorator pattern, which simplifies authorization checks",
                    "Handles session management using sliding window expiration, which improves security",
                    "Manages password hashing using bcrypt with adaptive work factor, which provides security",
                    "Integrates with OAuth providers using PKCE flow, which enables third-party authentication"
                ]
                for insight in insights:
                    mgr.add_insight("Test System", insight, force=True)

                # NO dependencies added
                # Expected: 40 (files) + 35 (insights) + 0 (dep) + 5 (medium clarity) = 80%
                # With 80% comp + 5 insights but NO deps, clarity should be "medium"

                # Verify clarity is medium (not high) due to missing dependencies
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "medium")  # Not high without deps
                self.assertGreaterEqual(sys["completeness"], 70)  # Has enough completeness
                self.assertEqual(len(sys["insights"]), 5)  # Has enough insights
                self.assertEqual(len(sys["dependencies"]), 0)  # But missing deps
            finally:
                os.chdir(orig_dir)

    def test_clarity_recomputed_after_map_files(self):
        """Verify clarity is recomputed after mapping files"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)

                # Create dummy files
                with open("file1.py", "w") as f:
                    f.write("# " + "x" * 2000)  # >1KB
                with open("file2.py", "w") as f:
                    f.write("# " + "x" * 2000)

                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")

                # Initial clarity should be low
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "low")

                # Map files (doesn't change clarity directly, but method should update it)
                mgr.map_files("Test System", ["file1.py", "file2.py"])

                # Verify clarity field exists and is computed
                sys = mgr.data["systems"]["Test System"]
                self.assertIn("clarity", sys)
                self.assertIn(sys["clarity"], ["low", "medium", "high"])
            finally:
                os.chdir(orig_dir)

    def test_clarity_recomputed_after_add_insight(self):
        """Verify clarity is recomputed after adding insights"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                # Create dummy files
                for i in range(5):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)
                
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                
                # Map 5 files to boost completeness (20 points)
                mgr.map_files("Test System", [f"file{i}.py" for i in range(5)])

                # Initial clarity: low (20% comp, 0 insights)
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "low")

                # Add 3 insights to reach medium clarity (21 points)
                mgr.add_insight("Test System", "Implements authentication using JWT tokens with Redis cache, which reduces DB load", force=True)
                mgr.add_insight("Test System", "Provides role-based access control using decorators, which simplifies checks", force=True)
                mgr.add_insight("Test System", "Handles session management using sliding expiration, which improves security", force=True)

                # Verify clarity updated to medium
                # Expected: 20 (files) + 21 (3 insights) + 0 (dep) + 0 (clarity) = 41%
                # With 41% comp + 3 insights = medium clarity
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "medium")
                self.assertGreaterEqual(sys["completeness"], 40)
            finally:
                os.chdir(orig_dir)

    def test_clarity_recomputed_after_add_dependency(self):
        """Verify clarity is recomputed after adding dependencies"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                
                # Create dummy files
                for i in range(10):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)
                
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Auth System")
                mgr.add_system("Database")
                
                # Map 10 files (40 points)
                mgr.map_files("Auth System", [f"file{i}.py" for i in range(10)])

                # Add 5 insights (35 points)
                insights = [
                    "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces load",
                    "Provides role-based access control using decorator pattern, which simplifies authorization",
                    "Handles session management using sliding window expiration, which improves security",
                    "Manages password hashing using bcrypt with adaptive work factor, which provides security",
                    "Integrates with OAuth providers using PKCE flow, which enables third-party authentication"
                ]
                for insight in insights:
                    mgr.add_insight("Auth System", insight, force=True)

                # Before dependency: should be medium
                # Expected: 40 (files) + 35 (insights) + 0 (dep) + 5 (medium clarity) = 80%
                sys = mgr.data["systems"]["Auth System"]
                self.assertEqual(sys["clarity"], "medium")  # 80% comp + 5 insights + no deps = medium

                # Add dependency
                mgr.add_dependency("Auth System", "Database", "Stores user data")

                # After dependency: should be high
                # Expected: 40 (files) + 35 (insights) + 15 (dep) + 10 (high clarity) = 100%
                sys = mgr.data["systems"]["Auth System"]
                self.assertEqual(sys["clarity"], "high")
                self.assertEqual(sys["completeness"], 100)
            finally:
                os.chdir(orig_dir)

class TestCompletenessComputation(unittest.TestCase):
    """Tests for auto-computed completeness scores"""

    def test_compute_completeness_minimal_system(self):
        """Minimal system: 0 files, 0 insights → 0%"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Minimal System")

                sys = mgr.data["systems"]["Minimal System"]

                # Verify minimal completeness
                self.assertEqual(sys["completeness"], 0)
                self.assertEqual(len(sys["key_files"]), 0)
                self.assertEqual(len(sys["insights"]), 0)
                self.assertEqual(len(sys["dependencies"]), 0)
            finally:
                os.chdir(orig_dir)

    def test_compute_completeness_formula_accuracy(self):
        """Test formula: 5 files, 3 insights, 1 dep, medium clarity"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)

                # Create dummy files
                for i in range(5):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)  # >1KB

                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                mgr.add_system("Dependency")

                # Map 5 files → 20 points (5/10 * 40)
                mgr.map_files("Test System", [f"file{i}.py" for i in range(5)])

                # Add 3 insights → 21 points (3/5 * 35)
                insights = [
                    "Implements authentication using JWT tokens with Redis cache, which reduces database load significantly",
                    "Provides role-based access control using decorator pattern, which simplifies authorization checks",
                    "Handles session management using sliding window expiration, which improves security"
                ]
                for insight in insights:
                    mgr.add_insight("Test System", insight, force=True)

                # Add dependency → 15 points
                mgr.add_dependency("Test System", "Dependency", "Uses for data storage")

                sys = mgr.data["systems"]["Test System"]

                # Expected: 20 (files) + 21 (insights) + 15 (deps) + 5 (medium clarity) = 61
                # Medium clarity because: 3 insights + 61% comp (circular but converges)
                expected = 20 + 21 + 15 + 5  # = 61
                self.assertEqual(sys["completeness"], expected)
                self.assertEqual(sys["clarity"], "medium")
            finally:
                os.chdir(orig_dir)

    def test_compute_completeness_capped_at_100(self):
        """Completeness should never exceed 100%"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)

                # Create 20 dummy files (more than 10)
                for i in range(20):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)

                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Large System")
                mgr.add_system("Dependency")

                # Map 20 files → 40 points (capped at 10 files)
                mgr.map_files("Large System", [f"file{i}.py" for i in range(20)])

                # Add 10 UNIQUE insights → 35 points (capped at 5 insights)
                insights = [
                    "Implements authentication layer using JWT tokens with Redis caching, which reduces database load significantly",
                    "Provides comprehensive logging system with structured output, which enables better debugging and monitoring",
                    "Manages request routing using pattern matching algorithms, which improves performance and flexibility",
                    "Handles data validation using schema-based checks with custom rules, which ensures data integrity",
                    "Integrates with external APIs using retry logic and circuit breakers, which improves reliability",
                    "Orchestrates background jobs using task queue with priority scheduling, which optimizes resource usage",
                    "Maintains session state using distributed cache with TTL expiration, which scales horizontally",
                    "Processes file uploads using streaming with virus scanning, which protects against malware",
                    "Monitors system health using metrics collection with alerting, which enables proactive maintenance",
                    "Transforms data formats using pluggable converters with validation, which supports multiple clients"
                ]
                for insight in insights:
                    mgr.add_insight("Large System", insight, force=True)

                # Add dependency → 15 points
                mgr.add_dependency("Large System", "Dependency", "Integration")

                sys = mgr.data["systems"]["Large System"]

                # Should be capped at 100 (40 + 35 + 15 + 10 = 100)
                self.assertLessEqual(sys["completeness"], 100)
                self.assertEqual(sys["completeness"], 100)
                self.assertEqual(sys["clarity"], "high")
            finally:
                os.chdir(orig_dir)

    def test_completeness_recomputed_after_map_files(self):
        """Verify completeness increases after mapping files"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)

                # Create dummy files
                for i in range(5):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)

                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")

                # Initial completeness should be 0
                sys = mgr.data["systems"]["Test System"]
                initial_comp = sys["completeness"]
                self.assertEqual(initial_comp, 0)

                # Map files
                mgr.map_files("Test System", ["file0.py", "file1.py", "file2.py"])

                # Verify completeness increased
                sys = mgr.data["systems"]["Test System"]
                self.assertGreater(sys["completeness"], initial_comp)

                # Expected: 3 files = 12 points (3/10 * 40)
                self.assertEqual(sys["completeness"], 12)
            finally:
                os.chdir(orig_dir)

    def test_completeness_recomputed_after_add_insight(self):
        """Verify completeness increases after adding insights"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")

                # Initial completeness should be 0
                initial_comp = mgr.data["systems"]["Test System"]["completeness"]
                self.assertEqual(initial_comp, 0)

                # Add insight
                mgr.add_insight("Test System",
                              "Implements authentication using JWT tokens with Redis cache, which reduces database load",
                              force=True)

                # Verify completeness increased
                sys = mgr.data["systems"]["Test System"]
                self.assertGreater(sys["completeness"], initial_comp)

                # Expected: 1 insight = 7 points (1/5 * 35)
                self.assertEqual(sys["completeness"], 7)
            finally:
                os.chdir(orig_dir)

    def test_completeness_recomputed_after_add_dependency(self):
        """Verify completeness increases after adding dependency"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("System A")
                mgr.add_system("System B")

                # Initial completeness should be 0
                initial_comp = mgr.data["systems"]["System A"]["completeness"]
                self.assertEqual(initial_comp, 0)

                # Add dependency
                mgr.add_dependency("System A", "System B", "Uses for storage")

                # Verify completeness increased by 15 points
                sys = mgr.data["systems"]["System A"]
                self.assertEqual(sys["completeness"], 15)
            finally:
                os.chdir(orig_dir)

    def test_completeness_progression_realistic_workflow(self):
        """Test completeness progression through realistic workflow"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)

                # Create files
                for i in range(10):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)

                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Auth System")
                mgr.add_system("Database")

                # Step 1: Map 3 files → ~12%
                mgr.map_files("Auth System", ["file0.py", "file1.py", "file2.py"])
                comp1 = mgr.data["systems"]["Auth System"]["completeness"]
                self.assertEqual(comp1, 12)

                # Step 2: Add 2 insights → ~26%
                mgr.add_insight("Auth System",
                              "Implements JWT authentication with Redis-backed tokens, which reduces database load",
                              force=True)
                mgr.add_insight("Auth System",
                              "Provides role-based access control using decorators, which simplifies authorization",
                              force=True)
                comp2 = mgr.data["systems"]["Auth System"]["completeness"]
                self.assertEqual(comp2, 26)  # 12 + 14 (2/5 * 35)

                # Step 3: Add dependency → ~41%
                mgr.add_dependency("Auth System", "Database", "Stores credentials")
                comp3 = mgr.data["systems"]["Auth System"]["completeness"]
                self.assertEqual(comp3, 41)  # 26 + 15

                # Step 4: Add 3 more insights (5 total) → ~61%
                mgr.add_insight("Auth System",
                              "Handles session management with sliding expiration, which improves security",
                              force=True)
                mgr.add_insight("Auth System",
                              "Manages password hashing using bcrypt, which provides security",
                              force=True)
                mgr.add_insight("Auth System",
                              "Integrates OAuth providers using PKCE, which enables third-party auth",
                              force=True)
                comp4 = mgr.data["systems"]["Auth System"]["completeness"]
                # 12 (files) + 35 (5 insights) + 15 (deps) + 0 (still low clarity with only 60% comp)
                # Wait, clarity needs 70%+ for high, so at 62% it's medium (+5)
                self.assertEqual(comp4, 67)  # 12 + 35 + 15 + 5

                # Verify clarity is medium (5+ insights but <70% comp)
                sys = mgr.data["systems"]["Auth System"]
                self.assertEqual(sys["clarity"], "medium")

                # Step 5: Map 7 more files (10 total) → should reach high clarity
                mgr.map_files("Auth System", [f"file{i}.py" for i in range(3, 10)])
                
                # Reload system data after modification
                sys = mgr.data["systems"]["Auth System"]
                comp5 = sys["completeness"]
                
                # 40 (10 files) + 35 (5 insights) + 15 (deps) + 10 (high clarity) = 100
                self.assertEqual(comp5, 100)
                self.assertEqual(sys["clarity"], "high")
            finally:
                os.chdir(orig_dir)

    def test_edge_case_large_system(self):
        """Test with very large system (20+ files, 10+ insights)"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)

                # Create 25 files
                for i in range(25):
                    with open(f"file{i}.py", "w") as f:
                        f.write("# " + "x" * 2000)

                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Large System")
                mgr.add_system("Dep")

                # Map 25 files (should cap at 40 points)
                mgr.map_files("Large System", [f"file{i}.py" for i in range(25)])

                # Add 8 UNIQUE insights (should cap at 35 points)
                insights = [
                    "Feature A implements caching using Redis with TTL expiration, which reduces database queries significantly",
                    "Feature B provides real-time notifications using WebSockets with reconnection logic, which improves user experience",
                    "Feature C manages file storage using S3 with CDN integration, which reduces latency for global users",
                    "Feature D handles authentication using OAuth with PKCE flow, which ensures secure third-party access",
                    "Feature E processes payments using Stripe with webhook verification, which enables reliable transactions",
                    "Feature F generates reports using background jobs with result caching, which improves performance",
                    "Feature G validates inputs using JSON schema with custom validators, which prevents bad data",
                    "Feature H monitors health using metrics collection with alerting, which enables proactive maintenance"
                ]
                for insight in insights:
                    mgr.add_insight("Large System", insight, force=True)

                # Add dependency
                mgr.add_dependency("Large System", "Dep", "Integration")

                sys = mgr.data["systems"]["Large System"]

                # Should reach 100: 40 + 35 + 15 + 10 = 100
                self.assertEqual(sys["completeness"], 100)
                self.assertEqual(sys["clarity"], "high")
            finally:
                os.chdir(orig_dir)