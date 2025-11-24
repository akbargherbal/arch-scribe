import os
from ..core.constants import SIGNIFICANT_SIZE_KB, CLASSIFICATION_CONFIG

class FileClassifier:
    """Determines if a file is architecturally significant"""
    
    # Known data/asset directories that rarely contain significant code
    DEFAULT_DATA_DIRECTORIES = {
        'data', 'assets', 'static', 'public', 'resources',
        'fixtures', 'samples', 'examples', 'wordlists',
        'locales', 'i18n', 'translations', 'sounds', 'audio',
        'themes', 'layouts', 'fonts', 'images', 'media',
        'node_modules', 'vendor', 'bower_components'
    }
    
    # File extensions by category
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.swift',
        '.kt', '.scala', '.clj', '.ex', '.exs', '.erl', '.hs', '.lua',
        '.sh', '.bash', '.zsh', '.pl', '.pm', '.r', '.m', '.mm'
    }
    
    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini', '.xml', '.env',
        '.conf', '.config', '.properties', '.dockerfile'
    }
    
    DATA_EXTENSIONS = {
        '.csv', '.tsv', '.parquet', '.db', '.sqlite', '.sql',
        '.txt', '.md', '.rst', '.log', '.lock'
    }
    
    def __init__(self):
        self.data_directories = self.DEFAULT_DATA_DIRECTORIES.union(
            set(CLASSIFICATION_CONFIG.get("data_directories", []))
        )
        self.max_config_size_kb = CLASSIFICATION_CONFIG.get("max_config_size_kb", 50)
    
    def is_in_data_directory(self, file_path: str) -> bool:
        """Check if file is in a known data directory"""
        parts = file_path.replace('\\', '/').lower().split('/')
        return any(part in self.data_directories for part in parts)
    
    def classify_by_extension(self, file_path: str) -> str:
        """Returns: 'code', 'config', 'data', or 'unknown'"""
        # Handle Dockerfile special case (no extension)
        if os.path.basename(file_path).lower() == 'dockerfile':
            return 'config'
            
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.CODE_EXTENSIONS:
            return 'code'
        elif ext in self.CONFIG_EXTENSIONS:
            return 'config'
        elif ext in self.DATA_EXTENSIONS:
            return 'data'
        return 'unknown'
    
    def is_significant(self, file_path: str, size_bytes: int) -> bool:
        """
        Determines if a file is significant based on heuristics.
        """
        # Phase 1: Size check (baseline filter)
        if size_bytes / 1024 < SIGNIFICANT_SIZE_KB:
            return False
        
        # Phase 2: Directory check
        if self.is_in_data_directory(file_path):
            return False
        
        # NEW: Phase 3: Extension-based rules
        file_type = self.classify_by_extension(file_path)
        
        # Code files: always significant if >1KB (already checked above)
        if file_type == 'code':
            return True
        
        # Data files: never significant (unless we want to track schemas, but usually noise)
        if file_type == 'data':
            return False
        
        # Config files: only if reasonably sized
        if file_type == 'config':
            return size_bytes / 1024 < self.max_config_size_kb
        
        # Unknown: use size heuristic (stay conservative)
        return True
