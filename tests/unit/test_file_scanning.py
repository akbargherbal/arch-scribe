"""
Unit tests for file scanning and ignore logic.
"""
import pytest
import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import StateManager, IGNORE_DIRS

class TestGitignoreLoading:
    """Test .gitignore parsing."""

    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global IGNORE_DIRS after each test to prevent side effects."""
        original = IGNORE_DIRS.copy()
        yield
        IGNORE_DIRS.clear()
        IGNORE_DIRS.update(original)
    
    def test_load_gitignore_missing_file(self, temp_dir, monkeypatch):
        """Test behavior when .gitignore doesn't exist."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        assert isinstance(mgr.ignore_patterns, set)
        assert len(mgr.ignore_patterns) == 0
    
    def test_load_gitignore_with_comments(self, temp_dir, monkeypatch):
        """Test that comments are ignored."""
        monkeypatch.chdir(temp_dir)
        with open(".gitignore", "w") as f:
            f.write("# This is a comment\n")
            f.write("*.log\n")
            f.write("\n") # Empty line
        
        mgr = StateManager()
        assert "*.log" in mgr.ignore_patterns
        assert "# This is a comment" not in mgr.ignore_patterns
    
    def test_load_gitignore_with_directories(self, temp_dir, monkeypatch):
        """Test directory patterns (trailing slash)."""
        monkeypatch.chdir(temp_dir)
        with open(".gitignore", "w") as f:
            f.write("temp_build/\n")
            
        mgr = StateManager()
        # Note: StateManager modifies the global IGNORE_DIRS set
        assert "temp_build" in IGNORE_DIRS


class TestIgnoreLogic:
    """Test is_ignored() function."""
    
    def test_ignore_default_dirs(self, temp_dir, monkeypatch):
        """Test that default dirs are ignored."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        assert mgr.is_ignored("node_modules", "node_modules") is True
        assert mgr.is_ignored(".git", ".git") is True
    
    def test_ignore_by_extension(self, temp_dir, monkeypatch):
        """Test ignoring by file extension."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        assert mgr.is_ignored("script.pyc", "script.pyc") is True
        assert mgr.is_ignored("image.png", "image.png") is True
        assert mgr.is_ignored("script.py", "script.py") is False
    
    def test_ignore_by_gitignore_pattern(self, temp_dir, monkeypatch):
        """Test gitignore pattern matching."""
        monkeypatch.chdir(temp_dir)
        with open(".gitignore", "w") as f:
            f.write("secret_*.txt\n")
            
        mgr = StateManager()
        assert mgr.is_ignored("secret_key.txt", "secret_key.txt") is True
        assert mgr.is_ignored("public_key.txt", "public_key.txt") is False


class TestFileScanning:
    """Test scan_files() function."""
    
    def test_scan_empty_directory(self, temp_dir, monkeypatch):
        """Test scanning empty directory."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        total, sig_total, sig_paths = mgr.scan_files()
        assert total == 0
        assert sig_total == 0
    
    def test_scan_with_ignored_dirs(self, temp_dir, monkeypatch):
        """Test that ignored directories are skipped."""
        monkeypatch.chdir(temp_dir)
        os.makedirs("node_modules")
        with open("node_modules/package.json", "w") as f:
            f.write("content" * 1000) # Make it significant size
            
        mgr = StateManager()
        total, sig_total, sig_paths = mgr.scan_files()
        assert total == 0 # Should be ignored
    
    def test_scan_respects_size_threshold(self, temp_dir, monkeypatch):
        """Test that only files >1KB are counted as significant."""
        monkeypatch.chdir(temp_dir)
        
        # Small file (under 1KB)
        with open("small.py", "w") as f:
            f.write("print('hello')")
            
        # Large file (over 1KB)
        with open("large.py", "w") as f:
            f.write("a" * 1025)
            
        mgr = StateManager()
        total, sig_total, sig_paths = mgr.scan_files()
        
        assert total == 2
        assert sig_total == 1
        assert "large.py" in sig_paths
        assert "small.py" not in sig_paths
    
    def test_scan_handles_permission_errors(self, temp_dir, monkeypatch):
        """Test graceful handling of unreadable files."""
        monkeypatch.chdir(temp_dir)
        
        # Create a file
        with open("locked.py", "w") as f:
            f.write("content")
            
        mgr = StateManager()
        
        # Mock os.path.getsize to raise OSError
        with patch('os.path.getsize', side_effect=OSError("Permission denied")):
            total, sig_total, sig_paths = mgr.scan_files()
            
        # Should count towards total but not crash, and likely not be significant
        assert total == 1
        assert sig_total == 0