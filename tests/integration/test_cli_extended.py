"""
Integration tests for extended CLI commands (coverage, sessions).
"""
import pytest
import sys
import os
import json
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import main, STATE_FILE

@pytest.fixture
def cli_runner(temp_dir, monkeypatch):
    """Helper to run CLI commands in temp dir."""
    monkeypatch.chdir(temp_dir)
    
    def run_cmd(args):
        with patch.object(sys, 'argv', ["arch_state.py"] + args):
            main()
            
    return run_cmd

class TestCLICoverage:
    """Test the 'coverage' command and visual reporting."""
    
    def test_coverage_command_output(self, cli_runner, capsys):
        """Test that coverage command produces the visual bar chart."""
        # 1. Init
        cli_runner(["init", "CovProject"])
        
        # 2. Create some files
        os.makedirs("src/utils")
        with open("src/main.py", "w") as f: f.write("content"*200) # >1KB
        with open("src/utils/helper.py", "w") as f: f.write("content"*200) # >1KB
        
        # 3. Map one file
        cli_runner(["add", "Core"])
        cli_runner(["map", "Core", "src/main.py"])
        
        # 4. Run coverage
        # Clear previous output
        capsys.readouterr()
        cli_runner(["coverage"])
        captured = capsys.readouterr()
        
        # Verify output elements
        assert "COVERAGE BY DIRECTORY" in captured.out
        assert "src" in captured.out
        assert "src/utils" in captured.out
        assert "TOP UNMAPPED FILES" in captured.out
        assert "helper.py" in captured.out
        # Check for the bar chart characters
        assert "█" in captured.out or "░" in captured.out

class TestCLISessions:
    """Test session commands via CLI dispatch."""
    
    def test_session_lifecycle_cli(self, cli_runner, capsys):
        """Test session-start and session-end via CLI."""
        cli_runner(["init", "SessProject"])
        
        # Start
        cli_runner(["session-start"])
        captured = capsys.readouterr()
        assert "Session 1 started" in captured.out
        
        # End
        cli_runner(["session-end"])
        captured = capsys.readouterr()
        assert "Session 1 recorded" in captured.out
        
        # Verify persistence
        with open(STATE_FILE) as f:
            data = json.load(f)
            assert data["metadata"]["total_sessions"] == 1