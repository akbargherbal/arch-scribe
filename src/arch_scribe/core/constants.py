import datetime

# --- CONFIGURATION ---
STATE_FILE = "architecture.json"
BACKUP_FILE = "architecture.json.backup"
SESSION_FILE = ".session_start"

# Legacy threshold - kept for backward compatibility in Phase 1
SIGNIFICANT_SIZE_KB = 1

# New classification config (Phase 1 preparation)
CLASSIFICATION_CONFIG = {
    "min_size_bytes": 100,  # Files under 100 bytes are never significant
    "size_threshold_kb": 1,  # Default fallback
}

# Base ignores - will be augmented by .gitignore
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".env",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "target",
    "bin",
    "obj",
}
IGNORE_EXTS = {
    ".pyc",
    ".o",
    ".exe",
    ".so",
    ".dll",
    ".class",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}

# --- COLORS ---
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

# --- DEFAULT SCHEMA ---
DEFAULT_STATE = {
    "schema_version": "2.2",
    "metadata": {
        "project_name": "",
        "project_type": "Unknown",
        "last_updated": "",
        "phase": "survey",
        "total_sessions": 0,
        "scan_stats": {
            "total_files_scanned": 0,
            "significant_files_total": 0,
            "mapped_files_count": 0,
            "coverage_percentage": 0.0,
            "coverage_quality": 0.0,
        },
        "session_history": [],
    },
    "systems": {},
    "progress": {
        "systems_identified": 0,
        "systems_complete": 0,
        "estimated_overall_completeness": 0,
    },
}
