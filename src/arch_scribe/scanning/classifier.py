import os
import statistics
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
    
    # Treated as significant if < max_config_size_kb (default 50KB)
    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini', '.xml', '.env',
        '.conf', '.config', '.properties', '.dockerfile',
        '.md', '.rst', '.txt'  # Documentation is significant!
    }
    
    # Never significant
    DATA_EXTENSIONS = {
        '.csv', '.tsv', '.parquet', '.db', '.sqlite', '.sql',
        '.log', '.lock'
    }
    
    def __init__(self):
        self.data_directories = self.DEFAULT_DATA_DIRECTORIES.union(
            set(CLASSIFICATION_CONFIG.get("data_directories", []))
        )
        self.max_config_size_kb = CLASSIFICATION_CONFIG.get("max_config_size_kb", 50)
        self.size_samples = []
        self._outlier_threshold = None
    
    def is_in_data_directory(self, file_path: str) -> bool:
        """Check if file is in a known data directory"""
        parts = file_path.replace('\\', '/').lower().split('/')
        return any(part in self.data_directories for part in parts)
    
    def classify_by_extension(self, file_path: str) -> str:
        """Returns: 'code', 'config', 'data', or 'unknown'"""
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
    
    def calculate_outlier_threshold(self) -> float:
        """Calculate IQR-based outlier threshold."""
        if len(self.size_samples) < 10:
            return float('inf')
        
        sorted_sizes = sorted(self.size_samples)
        n = len(sorted_sizes)
        
        q1 = sorted_sizes[n // 4]
        q3 = sorted_sizes[3 * n // 4]
        iqr = q3 - q1
        
        return q3 + (3 * iqr)

    def is_size_outlier(self, size_bytes: int) -> bool:
        """Check if file size is a statistical outlier"""
        if self._outlier_threshold is None:
            self._outlier_threshold = self.calculate_outlier_threshold()
        return size_bytes > self._outlier_threshold
    
    def is_significant(self, file_path: str, size_bytes: int) -> bool:
        """Determines if a file is significant based on heuristics."""
        # Phase 1: Size check (baseline filter)
        if size_bytes / 1024 < SIGNIFICANT_SIZE_KB:
            return False
        
        # Phase 2: Directory check
        if self.is_in_data_directory(file_path):
            return False
        
        # Phase 3: Extension-based rules
        file_type = self.classify_by_extension(file_path)
        
        # Phase 4: Statistical outlier check
        if self.is_size_outlier(size_bytes):
            if file_type != 'code':
                return False
        
        if file_type == 'code':
            return True
        
        if file_type == 'data':
            return False
        
        if file_type == 'config':
            return size_bytes / 1024 < self.max_config_size_kb
        
        return True
