"""
Unit tests for StateManager core functionality.
"""
import pytest
import os
import json
import sys
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
    
    def test_add_insight(self, initialized_mgr):
        """Test adding insights to a system."""
        initialized_mgr.add_system("Auth System")
        initialized_mgr.add_insight("Auth System", "Uses JWT")
        assert "Uses JWT" in initialized_mgr.data["systems"]["Auth System"]["insights"]
    
    def test_add_duplicate_insight_blocked(self, initialized_mgr, capsys):
        """Test that similar insights are detected and blocked."""
        initialized_mgr.add_system("Auth System")
        initialized_mgr.add_insight("Auth System", "Uses JWT tokens for auth")
        initialized_mgr.add_insight("Auth System", "uses jwt tokens for auth") # Case insensitive check
        
        captured = capsys.readouterr()
        assert "Similar insight already exists" in captured.out
        assert len(initialized_mgr.data["systems"]["Auth System"]["insights"]) == 1
    
    def test_add_dependency(self, initialized_mgr):
        """Test adding dependency between systems."""
        initialized_mgr.add_system("Frontend")
        initialized_mgr.add_system("Backend")
        
        initialized_mgr.add_dependency("Frontend", "Backend", "API calls")
        
        deps = initialized_mgr.data["systems"]["Frontend"]["dependencies"]
        assert len(deps) == 1
        assert deps[0]["system"] == "Backend"
        assert deps[0]["reason"] == "API calls"