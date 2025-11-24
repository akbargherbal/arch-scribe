"""
arch-scribe: Cliff Notes for Code

LLM-guided architecture documentation generator.
"""

__version__ = "0.1.0"

from .core.state_manager import StateManager
from .arch_state import main

__all__ = ["StateManager", "main"]