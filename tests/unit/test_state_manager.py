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
                
                # Set low completeness
                mgr.update_system("Test System", comp=30)
                
                # Add only 2 insights
                mgr.add_insight("Test System", "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load", force=True)
                mgr.add_insight("Test System", "Provides role-based access control using decorator pattern, which simplifies authorization checks", force=True)
                
                # Verify clarity is low
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "low")
                self.assertEqual(len(sys["insights"]), 2)
                self.assertEqual(sys["completeness"], 30)
            finally:
                os.chdir(orig_dir)
    
    def test_compute_clarity_medium_partial_understanding(self):
        """Medium clarity: 3-4 insights, 40-69% completeness"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                
                # Set medium completeness
                mgr.update_system("Test System", comp=55)
                
                # Add 3 insights
                mgr.add_insight("Test System", "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load", force=True)
                mgr.add_insight("Test System", "Provides role-based access control using decorator pattern, which simplifies authorization checks", force=True)
                mgr.add_insight("Test System", "Handles session management using sliding window expiration, which improves security without frequent re-authentication", force=True)
                
                # Verify clarity is medium
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "medium")
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
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Auth System")
                mgr.add_system("Database")
                
                # Set high completeness
                mgr.update_system("Auth System", comp=80)
                
                # Add 5 insights
                insights = [
                    "Implements authentication using JWT tokens with Redis-backed refresh logic, which reduces database load",
                    "Provides role-based access control using decorator pattern, which simplifies authorization checks",
                    "Handles session management using sliding window expiration, which improves security without frequent re-authentication",
                    "Manages password hashing using bcrypt with adaptive work factor, which provides future-proof security",
                    "Integrates with OAuth providers using PKCE flow, which enables secure third-party authentication"
                ]
                for insight in insights:
                    mgr.add_insight("Auth System", insight, force=True)
                
                # Add dependency (required for high clarity)
                mgr.add_dependency("Auth System", "Database", "Stores user credentials and session tokens")
                
                # Verify clarity is high
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
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                
                # Set high completeness
                mgr.update_system("Test System", comp=80)
                
                # Add 5 insights
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
                
                # Verify clarity is medium (not high) due to missing dependencies
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "medium")  # Not high without deps
                self.assertEqual(len(sys["dependencies"]), 0)
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
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Test System")
                
                # Set medium completeness
                mgr.update_system("Test System", comp=50)
                
                # Initial clarity: low (0 insights)
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "low")
                
                # Add 3 insights to reach medium clarity
                mgr.add_insight("Test System", "Implements authentication using JWT tokens with Redis cache, which reduces DB load", force=True)
                mgr.add_insight("Test System", "Provides role-based access control using decorators, which simplifies checks", force=True)
                mgr.add_insight("Test System", "Handles session management using sliding expiration, which improves security", force=True)
                
                # Verify clarity updated to medium
                sys = mgr.data["systems"]["Test System"]
                self.assertEqual(sys["clarity"], "medium")
            finally:
                os.chdir(orig_dir)
    
    def test_clarity_recomputed_after_add_dependency(self):
        """Verify clarity is recomputed after adding dependencies"""
        with tempfile.TemporaryDirectory() as tmp:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmp)
                mgr = StateManager()
                mgr.init_project("TestProject")
                mgr.add_system("Auth System")
                mgr.add_system("Database")
                
                # Set high completeness and add 5 insights
                mgr.update_system("Auth System", comp=75)
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
                sys = mgr.data["systems"]["Auth System"]
                self.assertEqual(sys["clarity"], "medium")
                
                # Add dependency
                mgr.add_dependency("Auth System", "Database", "Stores user data")
                
                # After dependency: should be high
                sys = mgr.data["systems"]["Auth System"]
                self.assertEqual(sys["clarity"], "high")
            finally:
                os.chdir(orig_dir)