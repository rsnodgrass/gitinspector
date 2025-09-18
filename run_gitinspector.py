#!/usr/bin/env python3
"""
Wrapper script to run GitInspector with proper module imports.

This script ensures GitInspector runs correctly with all its dependencies.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
try:
    from load_env import load_env_file

    load_env_file()
except ImportError:
    pass

# Import and run GitInspector
if __name__ == "__main__":
    # Import the main GitInspector module
    from gitinspector.gitinspector import main

    # Run GitInspector with command line arguments
    main()
