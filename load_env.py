#!/usr/bin/env python3
"""
Load environment variables from .env file.

This script loads environment variables from a .env file and makes them available
to the current process. This is useful for development and testing.
"""

import os
import sys
from pathlib import Path


def load_env_file(env_file=".env"):
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to the .env file (default: .env)
    """
    env_path = Path(env_file)

    if not env_path.exists():
        print(f"⚠️  {env_file} file not found")
        print("Please create a .env file with your GitHub credentials")
        return False

    print(f"📄 Loading environment variables from {env_file}", file=sys.stderr)

    with open(env_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE pairs
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable
                os.environ[key] = value
                print(f"  ✅ {key} = {'*' * len(value) if 'KEY' in key.upper() else value}", file=sys.stderr)
            else:
                print(f"  ⚠️  Skipping invalid line {line_num}: {line}")

    print("🎉 Environment variables loaded successfully!", file=sys.stderr)
    return True


if __name__ == "__main__":
    load_env_file()
