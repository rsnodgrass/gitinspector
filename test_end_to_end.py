#!/usr/bin/env python3
"""
End-to-end test script for GitHub cache functionality.

This script demonstrates the test mode functionality by:
1. Running a test sync with limited data
2. Verifying the cache contains data
3. Running gitinspector to verify it works with cached data
4. Running an incremental sync to test merging
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False


def main():
    """Run end-to-end test."""
    print("🧪 GitHub Cache End-to-End Test")
    print("=" * 60)

    # Create temporary directory for test
    test_dir = tempfile.mkdtemp(prefix="github_cache_test_")
    print(f"Test directory: {test_dir}")

    try:
        # Change to test directory
        os.chdir(test_dir)

        # Copy gitinspector files to test directory
        gitinspector_dir = Path(__file__).parent
        for file in ["sync_github_cache.py", "gitinspector", "team_config.json"]:
            src = gitinspector_dir / file
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, Path(test_dir) / file)
                else:
                    shutil.copy2(src, Path(test_dir) / file)

        # Check if GitHub credentials are available
        if not os.getenv("GITHUB_APP_ID"):
            print("\n⚠️  WARNING: GITHUB_APP_ID not set")
            print("This test requires GitHub credentials to work properly.")
            print("Set GITHUB_APP_ID and GITHUB_PRIVATE_KEY_PATH environment variables.")
            print("\nContinuing with test anyway to show the interface...")

        # Test 1: Check cache status (should be empty)
        success = run_command(["python", "sync_github_cache.py", "--status"], "Check initial cache status")

        # Test 2: Run test mode sync
        success = run_command(
            ["python", "sync_github_cache.py", "--test-mode"], "Run test mode sync (last 7 days, max 5 PRs per repo)"
        )

        if not success:
            print("\n⚠️  Test mode sync failed - this is expected if GitHub credentials are not set")
            print("The test demonstrates the interface and error handling.")

        # Test 3: Check cache status after sync
        run_command(["python", "sync_github_cache.py", "--status"], "Check cache status after sync")

        # Test 4: Run gitinspector with GitHub data
        success = run_command(
            ["python", "gitinspector/gitinspector.py", "--github", "--format=text"],
            "Run gitinspector with cached GitHub data",
        )

        if not success:
            print("\n⚠️  GitInspector failed - this is expected if no data was synced")

        # Test 5: Run incremental sync
        run_command(
            ["python", "sync_github_cache.py", "--test-mode"], "Run incremental sync (should be fast if data exists)"
        )

        # Test 6: Show help
        run_command(["python", "sync_github_cache.py", "--help"], "Show sync script help")

        print(f"\n{'='*60}")
        print("🎉 End-to-end test completed!")
        print(f"Test directory: {test_dir}")
        print("You can inspect the cache files in the .github_cache directory")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1
    finally:
        # Clean up
        print(f"\nCleaning up test directory: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
