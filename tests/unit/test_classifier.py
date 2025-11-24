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
