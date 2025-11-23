"""
Integration tests for CLI command execution.
"""
import pytest
import sys
import os
import json
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from arch_state import main, STATE_FILE

@pytest.fixture
def cli_runner(temp_dir, monkeypatch):
    """Helper to run CLI commands in temp dir."""
    monkeypatch.chdir(temp_dir)
    
    def run_cmd(args):
        with patch.object(sys, 'argv', ["arch_state.py"] + args):
            main()
            
    return run_cmd

class TestCLIInit:
    """Test 'init' command."""
    
    def test_init_creates_state_file(self, cli_runner):
        """Test that init creates architecture.json."""
        cli_runner(["init", "Test Project"])
        assert os.path.exists(STATE_FILE)
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["project_name"] == "Test Project"
    
    def test_init_detects_project_type(self, cli_runner, monkeypatch):
        """Test auto-detection of project type."""
        # Create a Django marker
        with open("manage.py", "w") as f: f.write("")
        
        cli_runner(["init", "Django Project"])
        
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["project_type"] == "Django Web Application"


class TestCLIStatus:
    """Test 'status' command."""
    
    def test_status_displays_metadata(self, cli_runner, capsys):
        """Test that status shows project info."""
        cli_runner(["init", "Status Project"])
        
        # Clear capture from init
        capsys.readouterr()
        
        cli_runner(["status"])
        captured = capsys.readouterr()
        
        assert "Status Project" in captured.out
        assert "Sessions:" in captured.out
        assert "Coverage:" in captured.out


class TestCLISystemCommands:
    """Test system manipulation commands."""
    
    @pytest.fixture(autouse=True)
    def setup_project(self, cli_runner):
        cli_runner(["init", "Sys Project"])
    
    def test_add_command(self, cli_runner, capsys):
        """Test 'add' command creates system."""
        cli_runner(["add", "New System"])
        captured = capsys.readouterr()
        assert "Added system: New System" in captured.out
        
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert "New System" in data["systems"]
    
    def test_map_command(self, cli_runner):
        """Test 'map' command adds files to system."""
        cli_runner(["add", "Core"])
        cli_runner(["map", "Core", "file1.py", "file2.py"])
        
        with open(STATE_FILE) as f:
            data = json.load(f)
            files = data["systems"]["Core"]["key_files"]
            assert "file1.py" in files
            assert "file2.py" in files
    def test_update_command(self, cli_runner):
            """Test 'update' command modifies system metadata."""
            cli_runner(["add", "Core"])
            cli_runner(["update", "Core", "--desc", "Core logic"])
            with open(STATE_FILE) as f:
                data = json.load(f)
                sys = data["systems"]["Core"]
                assert sys["description"] == "Core logic"
                # Completeness is now auto-computed (should be 0 with no files/insights)
                assert sys["completeness"] == 0    
    
    def test_insight_command(self, cli_runner):
            """Test 'insight' command adds insight."""
            cli_runner(["add", "Core"])
            # Use a valid insight to avoid interactive prompt
            valid_insight = "Implements critical core functionality using robust design patterns, which ensures high system stability and optimal performance under load"
            cli_runner(["insight", "Core", valid_insight])  



    def test_dep_command(self, cli_runner, monkeypatch):
        """Test 'dep' command creates dependency."""
        cli_runner(["add", "A"])
        cli_runner(["add", "B"])
        
        cli_runner(["dep", "A", "B", "Depends on it"])
        
        with open(STATE_FILE) as f:
            data = json.load(f)
            deps = data["systems"]["A"]["dependencies"]
            assert deps[0]["system"] == "B"


class TestCLIReporting:
    """Test reporting commands."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, cli_runner):
        cli_runner(["init", "Report Project"])
        cli_runner(["add", "Sys A"])
    
    def test_list_command(self, cli_runner, capsys):
        """Test 'list' command shows all systems."""
        cli_runner(["list"])
        captured = capsys.readouterr()
        assert "Sys A" in captured.out
        assert "0%" in captured.out
    
    def test_show_command(self, cli_runner, capsys):
        """Test 'show' command displays system details."""
        cli_runner(["show", "Sys A"])
        captured = capsys.readouterr()
        assert "\"completeness\": 0" in captured.out
    
    def test_graph_command(self, cli_runner, capsys):
        """Test 'graph' command generates Mermaid syntax."""
        cli_runner(["graph"])
        captured = capsys.readouterr()
        assert "graph TD" in captured.out
        assert "Sys_A[\"Sys A\"]" in captured.out