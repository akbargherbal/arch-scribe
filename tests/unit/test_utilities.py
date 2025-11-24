"""
End-to-end tests for new project initialization.
"""
import pytest
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import StateManager, STATE_FILE

@pytest.mark.e2e
class TestProjectInitialization:
    """Test initialization in different project types."""
    
    def test_init_django_project(self, temp_dir, monkeypatch):
        """Test initialization and detection of Django project."""
        monkeypatch.chdir(temp_dir)
        
        # Create Django signature
        with open("manage.py", "w") as f:
            f.write("# Django manage.py")
            
        # Run init
        mgr = StateManager()
        # Mock input to accept overwrite if needed (though shouldn't be for new)
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        mgr.init_project("Django App")
        
        # Verify
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["project_name"] == "Django App"
            assert data["metadata"]["project_type"] == "Django Web Application"
    
    def test_init_flask_project(self, temp_dir, monkeypatch):
        """Test initialization and detection of Flask project."""
        monkeypatch.chdir(temp_dir)
        
        # Create Flask signature
        with open("app.py", "w") as f: f.write("# Flask app")
        with open("requirements.txt", "w") as f: f.write("flask")
        
        mgr = StateManager()
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        mgr.init_project("Flask App")
        
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["project_type"] == "Flask Web Application"
    
    def test_init_nodejs_project(self, temp_dir, monkeypatch):
        """Test initialization and detection of Node.js project."""
        monkeypatch.chdir(temp_dir)
        
        # Create Node.js signature (Express)
        with open("package.json", "w") as f:
            json.dump({"dependencies": {"express": "^4.0.0"}}, f)
            
        mgr = StateManager()
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        mgr.init_project("Node App")
        
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["project_type"] == "Node.js/Express Application"