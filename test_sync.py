#!/usr/bin/env python3
"""
Test script for GitHub sync with environment loading.

This script loads environment variables from .env file and runs the sync.
"""

import sys
import subprocess
from load_env import load_env_file


def main():
    """Run GitHub sync test with environment loading."""
    print("🧪 GitHub Sync Test with Environment Loading")
    print("=" * 50)

    # Load environment variables
    if not load_env_file():
        print("\n❌ Failed to load environment variables")
        print("Please create a .env file with your GitHub credentials")
        return 1

    print("\n🚀 Running GitHub sync test...")

    # Run the sync script
    try:
        result = subprocess.run([sys.executable, "sync_github_cache.py", "--test-mode"], check=True)

        print("\n✅ Sync completed successfully!")

        # Show cache status
        print("\n📊 Cache status:")
        subprocess.run([sys.executable, "sync_github_cache.py", "--status"])

        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Sync failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Sync interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
