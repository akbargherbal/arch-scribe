import os
import fnmatch
from ..core.constants import IGNORE_DIRS, IGNORE_EXTS
from .classifier import FileClassifier

class FileScanner:
    def __init__(self):
        self.ignore_patterns = self.load_gitignore()
        self.classifier = FileClassifier()

    def load_gitignore(self):
        """Parses .gitignore to augment IGNORE_DIRS"""
        patterns = set()
        if os.path.exists(".gitignore"):
            try:
                with open(".gitignore", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if line.endswith("/"):
                                IGNORE_DIRS.add(line.rstrip("/"))
                            patterns.add(line)
            except Exception:
                pass
        return patterns

    def is_ignored(self, path, name):
        if name in IGNORE_DIRS:
            return True
        if os.path.splitext(name)[1] in IGNORE_EXTS:
            return True
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def scan_files(self):
        total, sig_total, sig_paths = 0, 0, set()
        
        # Pass 1: Collect all valid files and their sizes
        valid_files = []
        self.classifier.size_samples = []
        
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if not self.is_ignored(os.path.join(root, d), d)]

            for file in files:
                if self.is_ignored(os.path.join(root, file), file):
                    continue

                path = os.path.join(root, file)
                rel = os.path.relpath(path, ".").replace("\\", "/")
                if rel.startswith("./"):
                    rel = rel[2:]

                total += 1
                try:
                    size = os.path.getsize(path)
                    valid_files.append((rel, size))
                    self.classifier.size_samples.append(size)
                except OSError:
                    pass
        
        # Pass 2: Classify with statistical context
        # Calculate threshold once after collecting all samples
        self.classifier._outlier_threshold = self.classifier.calculate_outlier_threshold()
        
        for rel, size in valid_files:
            if self.classifier.is_significant(rel, size):
                sig_total += 1
                sig_paths.add(rel)
                
        return total, sig_total, sig_paths
