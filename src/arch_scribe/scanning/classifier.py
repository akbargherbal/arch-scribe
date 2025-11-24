from ..core.constants import SIGNIFICANT_SIZE_KB, CLASSIFICATION_CONFIG

class FileClassifier:
    """Determines if a file is architecturally significant"""
    
    # Known data/asset directories that rarely contain significant code
    # These will be merged with config-provided directories
    DEFAULT_DATA_DIRECTORIES = {
        'data', 'assets', 'static', 'public', 'resources',
        'fixtures', 'samples', 'examples', 'wordlists',
        'locales', 'i18n', 'translations', 'sounds', 'audio',
        'themes', 'layouts', 'fonts', 'images', 'media',
        'node_modules', 'vendor', 'bower_components' # Redundant but safe
    }
    
    def __init__(self):
        self.data_directories = self.DEFAULT_DATA_DIRECTORIES.union(
            set(CLASSIFICATION_CONFIG.get("data_directories", []))
        )
    
    def is_in_data_directory(self, file_path: str) -> bool:
        """Check if file is in a known data directory"""
        # Normalize path separators
        parts = file_path.replace('\\', '/').lower().split('/')
        return any(part in self.data_directories for part in parts)
    
    def is_significant(self, file_path: str, size_bytes: int) -> bool:
        """
        Determines if a file is significant based on heuristics.
        """
        # Phase 1 logic (size check) - kept as baseline
        if size_bytes / 1024 < SIGNIFICANT_SIZE_KB:
            return False
        
        # NEW: Phase 2 logic (directory check)
        if self.is_in_data_directory(file_path):
            return False
        
        return True
