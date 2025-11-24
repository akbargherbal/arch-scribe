import pytest
from src.arch_scribe.scanning.classifier import FileClassifier

def test_classifier_matches_old_behavior():
    """Ensure Phase 1 classifier produces identical results to old logic"""
    classifier = FileClassifier()
    assert classifier.is_significant("test.py", 500) is False
    assert classifier.is_significant("test.py", 1024) is True
    assert classifier.is_significant("test.py", 2048) is True

def test_data_directory_detection():
    classifier = FileClassifier()
    assert classifier.is_significant("src/auth.py", 2048) is True
    assert classifier.is_significant("lib/utils.py", 3000) is True
    assert classifier.is_significant("data/words.json", 1000000) is False
    assert classifier.is_significant("static/themes/dark.json", 2048) is False
    assert classifier.is_significant("sounds/click.mp3", 50000) is False
    assert classifier.is_significant("src/assets/images/logo.png", 5000) is False

def test_custom_config_directories():
    classifier = FileClassifier()
    assert classifier.is_significant("wordlists/russian.txt", 5000) is False

def test_extension_classification():
    classifier = FileClassifier()
    
    # Code files
    assert classifier.is_significant("app.py", 2048) is True
    
    # Data files
    assert classifier.is_significant("export.csv", 100000) is False
    assert classifier.is_significant("data.sqlite", 50000) is False
    
    # Documentation (Now treated as Config/Significant)
    assert classifier.is_significant("README.md", 5000) is True  # <--- CHANGED to True
    
    # Config files
    assert classifier.is_significant("small.json", 2048) is True
    assert classifier.is_significant("huge.json", 100000) is False
    assert classifier.is_significant("Dockerfile", 1500) is True

def test_monkeytype_word_lists():
    classifier = FileClassifier()
    assert classifier.is_significant("static/wordlists/russian_50k.json", 1300000) is False
    assert classifier.is_significant("russian_50k.json", 1300000) is False
    assert classifier.is_significant("package.json", 2048) is True

def test_statistical_outlier_detection():
    classifier = FileClassifier()
    classifier.size_samples = [1024 * (i % 10 + 1) for i in range(100)]
    huge_size = 5 * 1024 * 1024
    classifier.size_samples.append(huge_size)
    
    threshold = classifier.calculate_outlier_threshold()
    classifier._outlier_threshold = threshold
    
    assert classifier.is_size_outlier(huge_size) is True
    assert classifier.is_significant("huge_logic.py", huge_size) is True
    assert classifier.is_significant("dump.unknown", huge_size) is False
