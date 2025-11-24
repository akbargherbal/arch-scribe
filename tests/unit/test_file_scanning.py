import pytest
import os
from unittest.mock import patch
from src.arch_scribe.scanning.file_scanner import FileScanner

class TestGitignoreLoading:
    """Test .gitignore parsing logic."""

    def test_load_gitignore_missing_file(self, temp_dir, monkeypatch):
        """Test behavior when .gitignore doesn't exist."""
        monkeypatch.chdir(temp_dir)
        scanner = FileScanner()
        assert isinstance(scanner.ignore_patterns, set)
        assert len(scanner.ignore_patterns) == 0

    def test_load_gitignore_with_comments(self, temp_dir, monkeypatch):
        """Test that comments are ignored."""
        monkeypatch.chdir(temp_dir)
        with open(".gitignore", "w") as f:
            f.write("# This is a comment\n")
            f.write("*.log\n")
            f.write("\n") # Empty line

        scanner = FileScanner()
        assert "*.log" in scanner.ignore_patterns

    def test_load_gitignore_with_directories(self, temp_dir, monkeypatch):
        """Test that directory patterns are handled."""
        monkeypatch.chdir(temp_dir)
        with open(".gitignore", "w") as f:
            f.write("node_modules/\n")
            f.write("dist/\n")

        # We need to check if IGNORE_DIRS was updated
        # Since IGNORE_DIRS is a global constant imported in the module, 
        # we check the module's copy or the scanner's behavior
        scanner = FileScanner()
        # The scanner updates the global set, so we check behavior
        assert scanner.is_ignored("node_modules", "node_modules")


class TestIgnoreLogic:
    """Test file ignoring logic."""

    def test_ignore_default_dirs(self, temp_dir, monkeypatch):
        """Test that default dirs are ignored."""
        monkeypatch.chdir(temp_dir)
        scanner = FileScanner()
        assert scanner.is_ignored("node_modules", "node_modules") is True
        assert scanner.is_ignored(".git", ".git") is True
        assert scanner.is_ignored("src", "src") is False

    def test_ignore_by_extension(self, temp_dir, monkeypatch):
        """Test ignoring by file extension."""
        monkeypatch.chdir(temp_dir)
        scanner = FileScanner()
        assert scanner.is_ignored("script.pyc", "script.pyc") is True
        assert scanner.is_ignored("image.png", "image.png") is True
        assert scanner.is_ignored("script.py", "script.py") is False

    def test_ignore_by_gitignore_pattern(self, temp_dir, monkeypatch):
        """Test gitignore pattern matching."""
        monkeypatch.chdir(temp_dir)
        with open(".gitignore", "w") as f:
            f.write("secret_*.txt\n")

        scanner = FileScanner()
        assert scanner.is_ignored("secret_key.txt", "secret_key.txt") is True
        assert scanner.is_ignored("public_key.txt", "public_key.txt") is False


class TestFileScanning:
    """Test file system scanning."""

    def test_scan_empty_directory(self, temp_dir, monkeypatch):
        """Test scanning empty directory."""
        monkeypatch.chdir(temp_dir)
        scanner = FileScanner()
        total, sig_total, sig_paths = scanner.scan_files()
        assert total == 0
        assert sig_total == 0
        assert len(sig_paths) == 0

    def test_scan_with_ignored_dirs(self, temp_dir, monkeypatch):
        """Test that ignored directories are skipped."""
        monkeypatch.chdir(temp_dir)
        os.makedirs("node_modules")
        with open("node_modules/package.json", "w") as f:
            f.write("content" * 1000) # Make it significant size

        scanner = FileScanner()
        total, sig_total, sig_paths = scanner.scan_files()
        assert total == 0  # Should be ignored

    def test_scan_respects_size_threshold(self, temp_dir, monkeypatch):
        """Test that only files >1KB are counted as significant."""
        monkeypatch.chdir(temp_dir)

        # Small file (under 1KB)
        with open("small.py", "w") as f:
            f.write("print('hello')")

        # Large file (over 1KB)
        with open("large.py", "w") as f:
            f.write("a" * 1025)

        scanner = FileScanner()
        total, sig_total, sig_paths = scanner.scan_files()

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

        scanner = FileScanner()

        # Mock os.path.getsize to raise OSError
        with patch('os.path.getsize', side_effect=OSError("Permission denied")):
            total, sig_total, sig_paths = scanner.scan_files()
            
            # Should count towards total but not crash
            assert total == 1
            assert sig_total == 0
    def test_scan_ignores_data_directories(self, temp_dir, monkeypatch):
        """Test that files in data directories aren't counted as significant"""
        monkeypatch.chdir(temp_dir)
        
        os.makedirs("src")
        os.makedirs("data")
        
        # Real code file
        with open("src/main.py", "w") as f:
            f.write("a" * 2048)  # 2KB
        
        # Large data file
        with open("data/words.txt", "w") as f:
            f.write("a" * 100000)  # 100KB
        
        scanner = FileScanner()
        total, sig_total, sig_paths = scanner.scan_files()
        
        assert total == 2
        assert sig_total == 1  # Only main.py
        assert "src/main.py" in sig_paths
        assert "data/words.txt" not in sig_paths
