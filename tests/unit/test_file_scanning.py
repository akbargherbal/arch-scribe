"""
Unit tests for file scanning and ignore logic.
"""
import pytest


class TestGitignoreLoading:
    """Test .gitignore parsing."""
    
    def test_load_gitignore_missing_file(self):
        """Test behavior when .gitignore doesn't exist."""
        pass
    
    def test_load_gitignore_with_comments(self):
        """Test that comments are ignored."""
        pass
    
    def test_load_gitignore_with_directories(self):
        """Test directory patterns (trailing slash)."""
        pass


class TestIgnoreLogic:
    """Test is_ignored() function."""
    
    def test_ignore_default_dirs(self):
        """Test that default dirs are ignored."""
        pass
    
    def test_ignore_by_extension(self):
        """Test ignoring by file extension."""
        pass
    
    def test_ignore_by_gitignore_pattern(self):
        """Test gitignore pattern matching."""
        pass


class TestFileScanning:
    """Test scan_files() function."""
    
    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        pass
    
    def test_scan_with_ignored_dirs(self):
        """Test that ignored directories are skipped."""
        pass
    
    def test_scan_respects_size_threshold(self):
        """Test that only files >1KB are counted as significant."""
        pass
    
    def test_scan_handles_permission_errors(self):
        """Test graceful handling of unreadable files."""
        pass
