#!/usr/bin/env python3
"""
Test runner for gitinspector tests with activity feature focus.

This script provides convenient ways to run tests and validate the activity feature
using the permanent test repositories.
"""

import os
import subprocess
import sys
import unittest

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running GitInspector Unit Tests")
    print("=" * 50)
    
    test_dir = os.path.dirname(__file__)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = test_dir
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return False


def run_activity_integration_tests():
    """Run activity feature tests against permanent test repositories."""
    print("\n🔄 Running Activity Integration Tests")
    print("=" * 50)
    
    test_repos_dir = os.path.join(os.path.dirname(__file__), 'test_repositories')
    
    if not os.path.exists(test_repos_dir):
        print("❌ Test repositories not found. Run create_test_repos.py first.")
        return False
    
    gitinspector_dir = os.path.dirname(os.path.dirname(__file__))
    gitinspector_script = os.path.join(gitinspector_dir, 'gitinspector.py')
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Single Repository Analysis',
            'repos': ['team_growth_repo'],
            'args': ['-A']
        },
        {
            'name': 'Multi-Repository Analysis', 
            'repos': ['team_growth_repo', 'solo_productive_repo'],
            'args': ['-A']
        },
        {
            'name': 'Normalized Analysis',
            'repos': ['team_growth_repo', 'solo_productive_repo'],
            'args': ['-A', '--activity-normalize']
        },
        {
            'name': 'Weekly Analysis',
            'repos': ['seasonal_activity_repo'],
            'args': ['-A', '-w']
        },
        {
            'name': 'HTML Output',
            'repos': ['mixed_project_repo'],
            'args': ['-A', '-F', 'html']
        }
    ]
    
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        print(f"\n📊 Testing: {scenario['name']}")
        
        repo_paths = [os.path.join(test_repos_dir, repo) for repo in scenario['repos']]
        cmd = ['python', gitinspector_script] + scenario['args'] + repo_paths
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=gitinspector_dir)
            
            if result.returncode == 0:
                print(f"   ✅ {scenario['name']} - PASSED")
                
                # Basic output validation
                output = result.stdout
                if '-A' in scenario['args']:
                    if 'Activity by repository' in output:
                        print("   📈 Activity data found")
                    else:
                        print("   ⚠️  Activity data not found in output")
                
                if '--activity-normalize' in scenario['args']:
                    if 'normalized per contributor' in output or 'Per Contributor' in output:
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
    
    print(f"\n📊 Integration Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    
    return failed == 0


def run_performance_tests():
    """Run performance tests on larger datasets."""
    print("\n⚡ Running Performance Tests")
    print("=" * 50)
    
    test_repos_dir = os.path.join(os.path.dirname(__file__), 'test_repositories')
    gitinspector_dir = os.path.dirname(os.path.dirname(__file__))
    gitinspector_script = os.path.join(gitinspector_dir, 'gitinspector.py')
    
    # Test with all repositories at once
    all_repos = [
        'team_growth_repo',
        'solo_productive_repo', 
        'seasonal_activity_repo',
        'mixed_project_repo',
        'legacy_maintenance_repo'
    ]
    
    repo_paths = [os.path.join(test_repos_dir, repo) for repo in all_repos]
    
    import time
    
    print("📊 Testing performance with all 5 repositories...")
    start_time = time.time()
    
    cmd = ['python', gitinspector_script, '-A', '--activity-normalize'] + repo_paths
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=gitinspector_dir)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"   ✅ Analysis completed in {duration:.2f} seconds")
            
            # Count lines of output
            output_lines = len(result.stdout.split('\n'))
            print(f"   📝 Generated {output_lines} lines of output")
            
            # Check for expected content
            if 'TOTAL' in result.stdout:
                print("   📊 Summary statistics generated")
            
            return True
        else:
            print(f"   ❌ Performance test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        return False


def validate_test_repositories():
    """Validate that test repositories are properly structured."""
    print("\n🔍 Validating Test Repositories")
    print("=" * 50)
    
    test_repos_dir = os.path.join(os.path.dirname(__file__), 'test_repositories')
    
    expected_repos = [
        'team_growth_repo',
        'solo_productive_repo',
        'seasonal_activity_repo', 
        'mixed_project_repo',
        'legacy_maintenance_repo'
    ]
    
    all_valid = True
    
    for repo_name in expected_repos:
        repo_path = os.path.join(test_repos_dir, repo_name)
        
        if not os.path.exists(repo_path):
            print(f"   ❌ {repo_name} - Missing")
            all_valid = False
            continue
        
        # Check if it's a git repository
        git_dir = os.path.join(repo_path, '.git')
        if not os.path.exists(git_dir):
            print(f"   ❌ {repo_name} - Not a git repository")
            all_valid = False
            continue
        
        # Check for commits
        try:
            result = subprocess.run(['git', 'log', '--oneline'], 
                                  capture_output=True, text=True, cwd=repo_path)
            if result.returncode == 0 and result.stdout.strip():
                commit_count = len(result.stdout.strip().split('\n'))
                print(f"   ✅ {repo_name} - {commit_count} commits")
            else:
                print(f"   ❌ {repo_name} - No commits found")
                all_valid = False
        except Exception as e:
            print(f"   ❌ {repo_name} - Git error: {e}")
            all_valid = False
    
    return all_valid


def main():
    """Main test runner."""
    print("🚀 GitInspector Test Suite")
    print("=" * 50)
    
    # Validate test repositories first
    if not validate_test_repositories():
        print("\n⚠️  Test repository validation failed. Run create_test_repos.py to recreate them.")
        return False
    
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


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
