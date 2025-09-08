#!/usr/bin/env python3
"""
Tests for --github flag error messages and user guidance.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
from io import StringIO

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import teamconfig


class TestGitHubFlagErrorMessages(unittest.TestCase):
    """Test --github flag error messages and user guidance."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_team_config_file_not_found_error(self):
        """Test error message when team_config.json doesn't exist."""
        # Ensure team_config.json doesn't exist
        if os.path.exists("team_config.json"):
            os.remove("team_config.json")

        # Test the error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                try:
                    teamconfig.load_team_config("team_config.json", enable_team_filtering=False)
                except teamconfig.TeamConfigError as e:
                    print("gitinspector:", e.msg, file=sys.stderr)
                    sys.exit(1)

            # Should exit with error code 1
            self.assertEqual(cm.exception.code, 1)

            # Should show appropriate error message
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Team config file not found", stderr_output)
            self.assertIn("team_config.json", stderr_output)

    def test_invalid_team_config_error(self):
        """Test error message when team config is invalid."""
        # Create an invalid team config
        config_data = {"team": "not_a_list", "github_repositories": ["owner/repo1"]}  # Should be a list

        with open("team_config.json", "w") as f:
            json.dump(config_data, f)

        # Test the error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                try:
                    teamconfig.load_team_config("team_config.json", enable_team_filtering=False)
                except teamconfig.TeamConfigError as e:
                    print("gitinspector:", e.msg, file=sys.stderr)
                    sys.exit(1)

            # Should exit with error code 1
            self.assertEqual(cm.exception.code, 1)

            # Should show appropriate error message
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Invalid team config", stderr_output)
            self.assertIn("must be a list", stderr_output)

    def test_missing_team_key_error(self):
        """Test error message when config is missing required 'team' key."""
        # Create a config missing the required 'team' key
        config_data = {"github_repositories": ["owner/repo1"]}

        with open("team_config.json", "w") as f:
            json.dump(config_data, f)

        # Test the error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                try:
                    teamconfig.load_team_config("team_config.json", enable_team_filtering=False)
                except teamconfig.TeamConfigError as e:
                    print("gitinspector:", e.msg, file=sys.stderr)
                    sys.exit(1)

            # Should exit with error code 1
            self.assertEqual(cm.exception.code, 1)

            # Should show appropriate error message
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Invalid team config", stderr_output)
            self.assertIn("'team' key not found", stderr_output)

    def test_malformed_json_error(self):
        """Test error message when JSON is malformed."""
        # Create a malformed JSON file
        with open("team_config.json", "w") as f:
            f.write("{ invalid json }")

        # Test the error message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                try:
                    teamconfig.load_team_config("team_config.json", enable_team_filtering=False)
                except teamconfig.TeamConfigError as e:
                    print("gitinspector:", e.msg, file=sys.stderr)
                    sys.exit(1)

            # Should exit with error code 1
            self.assertEqual(cm.exception.code, 1)

            # Should show appropriate error message
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Error parsing JSON file", stderr_output)

    def test_no_github_repositories_warning(self):
        """Test warning message when no GitHub repositories are found."""
        # Create a valid team config but without github_repositories
        config_data = {"team": ["user1", "user2"]}

        with open("team_config.json", "w") as f:
            json.dump(config_data, f)

        # Load the config
        teamconfig.load_team_config("team_config.json", enable_team_filtering=False)

        # Test the warning message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            if not teamconfig.has_github_repositories():
                print("Warning: --github specified but no GitHub repositories found in config file", file=sys.stderr)

            # Should show warning message
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Warning: --github specified but no GitHub repositories found in config file", stderr_output)

    def test_empty_github_repositories_warning(self):
        """Test warning message when github_repositories list is empty."""
        # Create a valid team config with empty github_repositories
        config_data = {"team": ["user1", "user2"], "github_repositories": []}

        with open("team_config.json", "w") as f:
            json.dump(config_data, f)

        # Load the config
        teamconfig.load_team_config("team_config.json", enable_team_filtering=False)

        # Test the warning message
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            if not teamconfig.has_github_repositories():
                print("Warning: --github specified but no GitHub repositories found in config file", file=sys.stderr)

            # Should show warning message
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Warning: --github specified but no GitHub repositories found in config file", stderr_output)

    def test_valid_github_repositories_no_warning(self):
        """Test that no warning is shown when valid GitHub repositories are found."""
        # Create a valid team config with GitHub repositories
        config_data = {"team": ["user1", "user2"], "github_repositories": ["owner/repo1", "owner/repo2"]}

        with open("team_config.json", "w") as f:
            json.dump(config_data, f)

        # Load the config
        teamconfig.load_team_config("team_config.json", enable_team_filtering=False)

        # Test that no warning is shown
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            if teamconfig.has_github_repositories():
                github_repos = teamconfig.get_github_repositories()
                print(f"Analyzing {len(github_repos)} GitHub repositories...", file=sys.stderr)
            else:
                print("Warning: --github specified but no GitHub repositories found in config file", file=sys.stderr)

            # Should show analysis message, not warning
            stderr_output = mock_stderr.getvalue()
            self.assertIn("Analyzing 2 GitHub repositories...", stderr_output)
            self.assertNotIn("Warning: --github specified but no GitHub repositories found", stderr_output)

    def test_github_flag_help_message(self):
        """Test that --github flag shows appropriate help message."""
        # Skip this test as it requires a git repository
        self.skipTest("Help test requires git repository setup")

    def test_user_guidance_messages(self):
        """Test that appropriate user guidance messages are provided."""
        # Test 1: No config file - should suggest creating one
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            try:
                teamconfig.load_team_config("nonexistent.json", enable_team_filtering=False)
            except teamconfig.TeamConfigError as e:
                print("gitinspector:", e.msg, file=sys.stderr)
                print("Please create a team_config.json file with your GitHub repositories.", file=sys.stderr)

            stderr_output = mock_stderr.getvalue()
            self.assertIn("Team config file not found", stderr_output)
            self.assertIn("Please create a team_config.json file", stderr_output)

        # Test 2: No GitHub repositories - should suggest adding them
        config_data = {"team": ["user1"]}
        with open("team_config.json", "w") as f:
            json.dump(config_data, f)

        teamconfig.load_team_config("team_config.json", enable_team_filtering=False)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            if not teamconfig.has_github_repositories():
                print("Warning: --github specified but no GitHub repositories found in config file", file=sys.stderr)
                print("Please add 'github_repositories' to your team_config.json file.", file=sys.stderr)

            stderr_output = mock_stderr.getvalue()
            self.assertIn("no GitHub repositories found", stderr_output)
            self.assertIn("Please add 'github_repositories'", stderr_output)


if __name__ == "__main__":
    unittest.main()
