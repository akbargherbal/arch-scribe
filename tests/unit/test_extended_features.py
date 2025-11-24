"""
Unit tests for extended features (edge cases, interactivity).
"""
import pytest
import sys
import os
import json
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import StateManager 

class TestProjectDetectionExtended:
    """Test detection of less common project types."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        return StateManager()
        
    def test_detect_rust(self, mgr):
        with open("Cargo.toml", "w") as f: f.write("")
        assert mgr.detect_project_type() == "Rust Project"
        
    def test_detect_go(self, mgr):
        with open("go.mod", "w") as f: f.write("")
        assert mgr.detect_project_type() == "Go Project"
        
    def test_detect_python_pkg(self, mgr):
        with open("setup.py", "w") as f: f.write("")
        assert mgr.detect_project_type() == "Python Package/Library"
        
    def test_detect_container(self, mgr):
        with open("Dockerfile", "w") as f: f.write("")
        assert mgr.detect_project_type() == "Containerized Application"

class TestInteractiveDependency:
    """Test interactive prompts in dependency creation."""
    
    @pytest.fixture
    def mgr(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        m = StateManager()
        m.init_project("Interactivity")
        m.add_system("Source")
        return m
        
    def test_add_dependency_create_target_yes(self, mgr, monkeypatch):
        """Test answering 'y' to create a missing target system."""
        # Mock input to return 'y'
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        
        mgr.add_dependency("Source", "NewTarget", "Needs it")
        
        # Verify target was created
        assert "NewTarget" in mgr.data["systems"]
        # Verify dependency exists
        deps = mgr.data["systems"]["Source"]["dependencies"]
        assert deps[0]["system"] == "NewTarget"
        
    def test_add_dependency_create_target_no(self, mgr, monkeypatch):
        """Test answering 'n' to abort dependency creation."""
        # Mock input to return 'n'
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        
        mgr.add_dependency("Source", "GhostTarget", "Needs it")
        
        # Verify target was NOT created
        assert "GhostTarget" not in mgr.data["systems"]
        # Verify dependency was NOT added
        deps = mgr.data["systems"]["Source"]["dependencies"]
        assert len(deps) == 0