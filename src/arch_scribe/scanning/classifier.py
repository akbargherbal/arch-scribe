from ..core.constants import SIGNIFICANT_SIZE_KB

class FileClassifier:
    """Determines if a file is architecturally significant"""
    
    def __init__(self):
        pass
    
    def is_significant(self, file_path: str, size_bytes: int) -> bool:
        """
        Determines if a file is significant based on heuristics.
        
        Args:
            file_path: Relative path to the file
            size_bytes: Size of the file in bytes
            
        Returns:
            True if the file should be counted as significant
        """
        # Phase 1: Just delegate to old logic (size >= 1KB)
        # This ensures 100% backward compatibility during refactor
        return size_bytes / 1024 >= SIGNIFICANT_SIZE_KB
