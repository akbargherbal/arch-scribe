import pytest
from src.arch_scribe.scanning.classifier import FileClassifier

def test_classifier_matches_old_behavior():
    """Ensure Phase 1 classifier produces identical results to old logic"""
    classifier = FileClassifier()
    
    # 500 bytes < 1KB -> False
    assert classifier.is_significant("test.py", 500) is False
    
    # 1024 bytes = 1KB -> True
    assert classifier.is_significant("test.py", 1024) is True
    
    # 2048 bytes > 1KB -> True
    assert classifier.is_significant("test.py", 2048) is True

def test_data_directory_detection():
    classifier = FileClassifier()
    
    # Code files - should be significant
    assert classifier.is_significant("src/auth.py", 2048) is True
    assert classifier.is_significant("lib/utils.py", 3000) is True
    
    # Data directory files - should NOT be significant
    assert classifier.is_significant("data/words.json", 1000000) is False
    assert classifier.is_significant("static/themes/dark.json", 2048) is False
    assert classifier.is_significant("sounds/click.mp3", 50000) is False
    
    # Nested data directories
    assert classifier.is_significant("src/assets/images/logo.png", 5000) is False

def test_custom_config_directories():
    """Test that config-provided directories are respected"""
    # This implicitly tests the __init__ logic merging defaults with config
    classifier = FileClassifier()
    # 'wordlists' is in the config list we added to constants.py
    assert classifier.is_significant("wordlists/russian.txt", 5000) is False
