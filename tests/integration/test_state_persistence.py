"""
Integration tests for state file persistence.
"""
import pytest
import os
import json
import sys
import time
from unittest.mock import patch  # [FIX] Added missing import

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.arch_scribe.arch_state import StateManager, STATE_FILE, BACKUP_FILE

class TestSaveLoadCycle:
    """Test save/load integrity."""
    
    def test_save_and_load_preserves_data(self, temp_dir, monkeypatch):
        """Test that data survives save/load cycle."""
        monkeypatch.chdir(temp_dir)
        
        # 1. Create and save
        mgr1 = StateManager()
        mgr1.init_project("Persistence Test")
        mgr1.add_system("System A")
        good_insight = "Implements OAuth using JWT tokens with Redis session storage, which enables horizontal scaling"
        mgr1.add_insight("System A", "Insight 1", good_insight)
        # Save is automatic in add_system/add_insight
        
        # 2. Load new instance
        mgr2 = StateManager()
        assert mgr2.data["metadata"]["project_name"] == "Persistence Test"
        assert "System A" in mgr2.data["systems"]
        assert "Insight 1" in mgr2.data["systems"]["System A"]["insights"]
    
    def test_backup_file_created(self, temp_dir, monkeypatch):
        """Test that .backup file is created on save."""
        monkeypatch.chdir(temp_dir)
        
        mgr = StateManager()
        mgr.init_project("Backup Test")
        
        # Initial state exists, but backup might not yet (depends on logic)
        # Logic: if os.path.exists(STATE_FILE): shutil.copy(STATE_FILE, BACKUP_FILE)
        # So we need a second save to trigger backup of the first
        
        mgr.add_system("System A") # This triggers save, backing up the init state
        
        assert os.path.exists(BACKUP_FILE)
        
        # Verify backup contains previous state (without System A)
        with open(BACKUP_FILE) as f:
            backup_data = json.load(f)
            assert "System A" not in backup_data["systems"]


class TestCorruptionRecovery:
    """Test recovery from corrupted files."""
    
    def test_restore_from_backup_on_corruption(self, temp_dir, monkeypatch, capsys):
        """Test automatic backup restoration."""
        monkeypatch.chdir(temp_dir)
        
        # 1. Create valid state and backup
        mgr = StateManager()
        mgr.init_project("Recovery Test")
        mgr.add_system("Important System") # Creates backup of init state
        
        # Force a save to make sure backup has "Important System"
        # We'll manually copy current state to backup to simulate a recent backup
        import shutil
        shutil.copy(STATE_FILE, BACKUP_FILE)
        
        # 2. Corrupt the main file
        with open(STATE_FILE, "w") as f:
            f.write("{ I am broken json }")
            
        # 3. Try to load
        mgr_rec = StateManager()
        
        # 4. Verify recovery
        captured = capsys.readouterr()
        assert "Restoring from backup" in captured.out
        assert "Important System" in mgr_rec.data["systems"]

    def test_atomic_write_safety(self, temp_dir, monkeypatch):
        """Test that we don't lose data if write fails halfway."""
        monkeypatch.chdir(temp_dir)
        mgr = StateManager()
        mgr.init_project("Atomic Test")
        
        # We can't easily simulate a crash during write in Python without mocking open
        # But we can verify the temp file logic exists by mocking the rename
        
        with patch('os.replace') as mock_replace:
            mgr.save_state()
            
            # Verify it tried to replace .tmp with actual file
            args = mock_replace.call_args[0]
            assert args[0].endswith('.tmp')
            assert args[1] == STATE_FILE
            
            # Verify the temp file actually exists on disk (since we mocked the move)
            assert os.path.exists(STATE_FILE + ".tmp")