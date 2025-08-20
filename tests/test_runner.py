#!/usr/bin/env python3
"""
Test runner for gitinspector tests with activity feature focus.

This script provides convenient ways to run tests and validates the activity feature
by creating test repositories on-demand when needed.
"""

import os
import subprocess
import sys
import unittest
import tempfile
import shutil

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the repository creation utilities
from .create_simple_test_repos import create_git_repo, add_commit
from datetime import datetime, timedelta


def create_test_repositories_on_demand():
    """Create test repositories in a temporary directory for testing."""
    print("🔧 Creating test repositories on-demand...")

    # Create temporary directory for test repositories
    temp_dir = tempfile.mkdtemp(prefix="gitinspector_test_")
    print(f"   📁 Using temporary directory: {temp_dir}")

    # Repository 1: Team Growth Repository
    print("   1. Creating team_growth_repo...")
    team_repo = os.path.join(temp_dir, "team_growth_repo")
    create_git_repo(team_repo)

    base_date = datetime(2024, 1, 1)

    # Month 1: Solo developer
    add_commit(
        team_repo,
        "core.py",
        'class Core:\n    def __init__(self):\n        self.version = "1.0"\n',
        "Founder Dev",
        "founder@company.com",
        "Initial core implementation",
        base_date,
    )

    # Month 2: Second developer joins
    add_commit(
        team_repo,
        "utils.py",
        "def helper_function():\n    return True\n\ndef format_data(data):\n    return str(data)\n",
        "Developer 2",
        "dev2@company.com",
        "Add utility functions",
        base_date + timedelta(days=32),
    )

    # Month 3: Team of 4
    add_commit(
        team_repo,
        "api.py",
        'from flask import Flask\n\napp = Flask(__name__)\n\n@app.route("/")\ndef home():\n    return "Hello World"\n',
        "Backend Dev",
        "backend@company.com",
        "Add API layer",
        base_date + timedelta(days=62),
    )

    add_commit(
        team_repo,
        "frontend.js",
        'function main() {\n    console.log("Frontend loaded");\n}\n',
        "Frontend Dev",
        "frontend@company.com",
        "Add frontend code",
        base_date + timedelta(days=65),
    )

    # Repository 2: Solo Productive Repository
    print("   2. Creating solo_productive_repo...")
    solo_repo = os.path.join(temp_dir, "solo_productive_repo")
    create_git_repo(solo_repo)

    solo_base = datetime(2024, 6, 1)
    features = ["authentication.py", "database.py", "config.py", "models.py", "views.py"]

    for i, feature in enumerate(features):
        content = f'# {feature.replace(".py", "").title()} Module\ndef {feature.replace(".py", "")}_function():\n    return "implemented"\n'
        add_commit(
            solo_repo,
            feature,
            content,
            "Solo Expert",
            "expert@company.com",
            f"Implement {feature}",
            solo_base + timedelta(days=i * 7),
        )

    # Repository 3: Seasonal Activity Repository
    print("   3. Creating seasonal_activity_repo...")
    seasonal_repo = os.path.join(temp_dir, "seasonal_activity_repo")
    create_git_repo(seasonal_repo)

    # Q1: High activity
    q1_base = datetime(2024, 1, 1)
    for i, feature in enumerate(["planning.py", "roadmap.py", "goals.py"]):
        content = f'# Q1 Planning\ndef {feature.replace(".py", "")}():\n    pass\n'
        add_commit(
            seasonal_repo,
            feature,
            content,
            "Planning Team",
            "planning@company.com",
            f"Q1 planning: {feature}",
            q1_base + timedelta(days=i * 7),
        )

    # Q4: High activity
    q4_base = datetime(2024, 1, 10, 1)
    for i, feature in enumerate(["optimization.py", "release.py"]):
        content = f'# Q4 Release\ndef {feature.replace(".py", "")}():\n    return "optimized"\n'
        add_commit(
            seasonal_repo,
            feature,
            content,
            "Release Team",
            "release@company.com",
            f"Q4 release: {feature}",
            q4_base + timedelta(days=i * 10),
        )

    # Repository 4: Mixed Project Repository
    print("   4. Creating mixed_project_repo...")
    mixed_repo = os.path.join(temp_dir, "mixed_project_repo")
    create_git_repo(mixed_repo)

    mixed_base = datetime(2024, 3, 1)

    # Python files
    add_commit(
        mixed_repo,
        "main.py",
        'def main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()\n',
        "Python Dev",
        "python@company.com",
        "Add Python main module",
        mixed_base,
    )

    # Test files
    add_commit(
        mixed_repo,
        "test_main.py",
        "import unittest\n\nclass TestMain(unittest.TestCase):\n    def test_main_runs(self):\n        pass\n",
        "QA Engineer",
        "qa@company.com",
        "Add Python tests",
        mixed_base + timedelta(days=10),
    )

    # Repository 5: Legacy Maintenance Repository
    print("   5. Creating legacy_maintenance_repo...")
    legacy_repo = os.path.join(temp_dir, "legacy_maintenance_repo")
    create_git_repo(legacy_repo)

    legacy_base = datetime(2020, 1, 1)

    # Legacy code
    add_commit(
        legacy_repo,
        "legacy.py",
        '# Legacy code from 2020\ndef old_function():\n    return "deprecated"\n',
        "Legacy Dev",
        "legacy@company.com",
        "Initial legacy implementation",
        legacy_base,
    )

    # Maintenance updates
    add_commit(
        legacy_repo,
        "legacy.py",
        '# Legacy code from 2020\ndef old_function():\n    return "deprecated"\n\ndef new_wrapper():\n    return old_function()\n',
        "Maintenance Dev",
        "maintenance@company.com",
        "Add wrapper for legacy function",
        legacy_base + timedelta(days=1460),
    )  # 4 years later

    print("   ✅ All test repositories created successfully!")
    return temp_dir, {
        "team_growth_repo": team_repo,
        "solo_productive_repo": solo_repo,
        "seasonal_activity_repo": seasonal_repo,
        "mixed_project_repo": mixed_repo,
        "legacy_maintenance_repo": legacy_repo,
    }


def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running GitInspector Unit Tests")
    print("=" * 50)

    test_dir = os.path.dirname(__file__)

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = test_dir
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return False


def run_activity_integration_tests():
    """Run activity feature tests against on-demand test repositories."""
    print("\n🔄 Running Activity Integration Tests")
    print("=" * 50)

    # Create test repositories on-demand
    temp_dir, repo_paths = create_test_repositories_on_demand()

    try:
        gitinspector_dir = os.path.dirname(os.path.dirname(__file__))
        gitinspector_script = os.path.join(gitinspector_dir, "gitinspector.py")

        # Test scenarios
        scenarios = [
            {"name": "Single Repository Analysis", "repos": ["team_growth_repo"], "args": ["-A"]},
            {
                "name": "Multi-Repository Analysis",
                "repos": ["team_growth_repo", "solo_productive_repo"],
                "args": ["-A"],
            },
            {
                "name": "Normalized Analysis",
                "repos": ["team_growth_repo", "solo_productive_repo"],
                "args": ["-A", "--activity-normalize"],
            },
            {"name": "Weekly Analysis", "repos": ["seasonal_activity_repo"], "args": ["-A", "-w"]},
            {"name": "HTML Output", "repos": ["mixed_project_repo"], "args": ["-A", "-F", "html"]},
        ]

        passed = 0
        failed = 0

        for scenario in scenarios:
            print(f"\n📊 Testing: {scenario['name']}")

            scenario_repo_paths = [repo_paths[repo] for repo in scenario["repos"]]
            cmd = ["python", gitinspector_script] + scenario["args"] + scenario_repo_paths

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=gitinspector_dir)

                if result.returncode == 0:
                    print(f"   ✅ {scenario['name']} - PASSED")

                    # Basic output validation
                    output = result.stdout
                    if "-A" in scenario["args"]:
                        if "Activity by repository" in output:
                            print("   📈 Activity data found")
                        else:
                            print("   ⚠️  Activity data not found in output")

                    if "--activity-normalize" in scenario["args"]:
                        if "normalized per contributor" in output or "Per Contributor" in output:
                            print("   📊 Normalization detected")
                        else:
                            print("   ⚠️  Normalization not detected in output")

                    passed += 1
                else:
                    print(f"   ❌ {scenario['name']} - FAILED")
                    print(f"   Error: {result.stderr}")
                    failed += 1

            except Exception as e:
                print(f"   ❌ {scenario['name']} - ERROR: {e}")
                failed += 1

    except Exception as e:
        print(f"   ❌ Integration test setup error: {e}")
        return False

    print(f"\n📊 Integration Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")

    return failed == 0


def run_performance_tests():
    """Run performance tests on on-demand test repositories."""
    print("\n⚡ Running Performance Tests")
    print("=" * 50)

    # Create test repositories on-demand
    temp_dir, repo_paths = create_test_repositories_on_demand()

    try:
        gitinspector_dir = os.path.dirname(os.path.dirname(__file__))
        gitinspector_script = os.path.join(gitinspector_dir, "gitinspector.py")

        # Test with all repositories at once
        all_repos = [
            "team_growth_repo",
            "solo_productive_repo",
            "seasonal_activity_repo",
            "mixed_project_repo",
            "legacy_maintenance_repo",
        ]

        scenario_repo_paths = [repo_paths[repo] for repo in all_repos]

        import time

        print("📊 Testing performance with all 5 repositories...")
        start_time = time.time()

        cmd = ["python", gitinspector_script, "-A", "--activity-normalize"] + scenario_repo_paths

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=gitinspector_dir)
            end_time = time.time()

            duration = end_time - start_time

            if result.returncode == 0:
                print(f"   ✅ Analysis completed in {duration:.2f} seconds")

                # Count lines of output
                output_lines = len(result.stdout.split("\n"))
                print(f"   📝 Generated {output_lines} lines of output")

                # Check for expected content
                if "TOTAL" in result.stdout:
                    print("   📊 Summary statistics generated")

                return True
            else:
                print(f"   ❌ Performance test failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"   ❌ Performance test error: {e}")
            return False

    finally:
        # Clean up temporary test repositories
        print(f"\n🧹 Cleaning up temporary test repositories...")
        try:
            shutil.rmtree(temp_dir)
            print(f"   ✅ Cleaned up: {temp_dir}")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")


def main():
    """Main test runner."""
    print("🚀 GitInspector Test Suite")
    print("=" * 50)

    success = True

    # Run unit tests
    if not run_unit_tests():
        success = False

    # Run integration tests
    if not run_activity_integration_tests():
        success = False

    # Run performance tests
    if not run_performance_tests():
        success = False

    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
