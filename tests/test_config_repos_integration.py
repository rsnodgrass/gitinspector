#!/usr/bin/env python3
"""
Integration tests for the --config-repos functionality.

Tests the complete workflow of using repositories from config files
with the --config-repos flag.
"""

import os
import sys
import unittest
import tempfile
import json
import subprocess

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import teamconfig


class TestConfigReposIntegration(unittest.TestCase):
    """Integration tests for --config-repos functionality."""

    def setUp(self):
        """Set up test environment."""
        teamconfig.clear_team_config()
        
        # Create a temporary directory for test repositories
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a simple git repository for testing
        self.create_test_repo("test-repo-1")
        self.create_test_repo("test-repo-2")

    def tearDown(self):
        """Clean up after tests."""
        teamconfig.clear_team_config()
        os.chdir(self.original_cwd)
        
        # Clean up test repositories
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_repo(self, repo_name):
        """Create a simple test git repository."""
        repo_path = os.path.join(self.test_dir, repo_name)
        os.makedirs(repo_path)
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
        
        # Create a test file and commit
        test_file = os.path.join(repo_path, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content\n")
        
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], 
            cwd=repo_path, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], 
            cwd=repo_path, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], 
            cwd=repo_path, capture_output=True, check=True
        )

    def test_config_repos_with_valid_config(self):
        """Test --config-repos with a valid config file containing repositories."""
        config_data = {
            "team": ["Test User"],
            "repositories": [
                os.path.join(self.test_dir, "test-repo-1"),
                os.path.join(self.test_dir, "test-repo-2")
            ]
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that the config loads correctly
        teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertTrue(teamconfig.has_repositories())
        repositories = teamconfig.get_repositories()
        self.assertEqual(len(repositories), 2)
        
        # Test that repositories exist and are valid
        for repo_path in repositories:
            self.assertTrue(os.path.exists(repo_path))
            self.assertTrue(os.path.exists(os.path.join(repo_path, ".git")))

    def test_config_repos_without_repositories_in_config(self):
        """Test --config-repos when config file has no repositories field."""
        config_data = {
            "team": ["Test User"]
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that the config loads correctly but has no repositories
        teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertFalse(teamconfig.has_repositories())
        repositories = teamconfig.get_repositories()
        self.assertEqual(len(repositories), 0)

    def test_config_repos_with_empty_repositories_list(self):
        """Test --config-repos with empty repositories list in config."""
        config_data = {
            "team": ["Test User"],
            "repositories": []
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that the config loads correctly
        teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertTrue(teamconfig.has_repositories())
        repositories = teamconfig.get_repositories()
        self.assertEqual(len(repositories), 0)

    def test_config_repos_with_invalid_repositories_type(self):
        """Test --config-repos with invalid repositories type in config."""
        config_data = {
            "team": ["Test User"],
            "repositories": "not_a_list"
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that loading fails with appropriate error
        with self.assertRaises(teamconfig.TeamConfigError) as context:
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertIn("repositories' must be a list", str(context.exception))

    def test_config_repos_with_missing_team_field(self):
        """Test --config-repos with config file missing required team field."""
        config_data = {
            "repositories": ["/path/to/repo"]
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that loading fails with appropriate error
        with self.assertRaises(teamconfig.TeamConfigError) as context:
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertIn("'team' key not found", str(context.exception))

    def test_config_repos_with_empty_config(self):
        """Test --config-repos with empty config file."""
        config_file = os.path.join(self.test_dir, "empty_config.json")
        with open(config_file, "w") as f:
            json.dump({}, f)
        
        # Test that loading fails with appropriate error
        with self.assertRaises(teamconfig.TeamConfigError) as context:
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertIn("empty file", str(context.exception))

    def test_config_repos_with_malformed_json(self):
        """Test --config-repos with malformed JSON in config file."""
        config_file = os.path.join(self.test_dir, "malformed_config.json")
        with open(config_file, "w") as f:
            f.write('{"team": ["user1", "repositories": ["repo1"]}')
        
        # Test that loading fails with appropriate error
        with self.assertRaises(teamconfig.TeamConfigError) as context:
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertIn("Error parsing JSON file", str(context.exception))

    def test_config_repos_with_nonexistent_config_file(self):
        """Test --config-repos with non-existent config file."""
        config_file = os.path.join(self.test_dir, "nonexistent.json")
        
        # Test that loading fails with appropriate error
        with self.assertRaises(teamconfig.TeamConfigError) as context:
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertIn("not found", str(context.exception))

    def test_config_repos_with_relative_paths(self):
        """Test --config-repos with relative repository paths in config."""
        config_data = {
            "team": ["Test User"],
            "repositories": [
                "test-repo-1",
                "test-repo-2"
            ]
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that the config loads correctly with relative paths
        teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertTrue(teamconfig.has_repositories())
        repositories = teamconfig.get_repositories()
        self.assertEqual(len(repositories), 2)
        
        # Verify relative paths are preserved
        self.assertIn("test-repo-1", repositories)
        self.assertIn("test-repo-2", repositories)

    def test_config_repos_with_absolute_paths(self):
        """Test --config-repos with absolute repository paths in config."""
        config_data = {
            "team": ["Test User"],
            "repositories": [
                os.path.abspath(os.path.join(self.test_dir, "test-repo-1")),
                os.path.abspath(os.path.join(self.test_dir, "test-repo-2"))
            ]
        }
        
        config_file = os.path.join(self.test_dir, "team_config.json")
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Test that the config loads correctly with absolute paths
        teamconfig.load_team_config(config_file, enable_team_filtering=True)
        
        self.assertTrue(teamconfig.has_repositories())
        repositories = teamconfig.get_repositories()
        self.assertEqual(len(repositories), 2)
        
        # Verify absolute paths are preserved
        for repo_path in repositories:
            self.assertTrue(os.path.isabs(repo_path))
            self.assertTrue(os.path.exists(repo_path))


if __name__ == "__main__":
    unittest.main()
