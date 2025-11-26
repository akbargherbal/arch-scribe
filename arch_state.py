#!/usr/bin/env python3
import sys
import os

# Add 'src' to Python path so we can import the package
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

try:
    # Import the main entry point from our new package structure
    from arch_scribe.arch_state import main
except ImportError as e:
    print(f"Error importing arch-scribe: {e}")
    sys.exit(1)

if __name__ == "__main__":
    main()
