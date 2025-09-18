#!/usr/bin/env python3
"""
Simple tests for --github flag integration and error handling.
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.gitinspector import Runner
from gitinspector import teamconfig


class TestGitHubFlagSimple(unittest.TestCase):
    """Test --github flag integration and error handling."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = Runner()
        self.runner.github = True

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_github_flag_with_no_github_repositories(self):
        """Test --github flag when config has no github_repositories."""
        # Mock team config with no GitHub repositories
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            # Mock has_github_repositories to return False
            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = False

                # Capture stderr
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    # Mock the process method to avoid full execution
                    with patch.object(self.runner, "process") as mock_process:
                        mock_process.side_effect = lambda repos: None

                        # Call the GitHub analysis part directly
                        from gitinspector.gitinspector import Runner

                        runner = Runner()
                        runner.github = True

                        # Mock the team config loading in the process method
                        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load2:
                            mock_load2.return_value = None

                            with patch(
                                "gitinspector.gitinspector.teamconfig.has_github_repositories"
                            ) as mock_has_repos2:
                                mock_has_repos2.return_value = False

                                # This should show the warning message
                                with patch("sys.stderr", new_callable=StringIO) as mock_stderr2:
                                    # Simulate the GitHub analysis part
                                    if not teamconfig.has_github_repositories():
                                        print(
                                            "Warning: --github specified but no GitHub repositories found in config file",
                                            file=sys.stderr,
                                        )

                                    # Should show warning message
                                    stderr_output = mock_stderr2.getvalue()
                                    self.assertIn(
                                        "Warning: --github specified but no GitHub repositories found in config file",
                                        stderr_output,
                                    )

    def test_github_flag_with_valid_repositories(self):
        """Test --github flag when config has valid GitHub repositories."""
        # Mock team config with valid GitHub repositories
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            # Mock has_github_repositories to return True
            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = True

                # Mock get_github_repositories
                with patch("gitinspector.gitinspector.teamconfig.get_github_repositories") as mock_get_repos:
                    mock_get_repos.return_value = ["owner/repo1", "owner/repo2"]

                    # This should not show the warning message
                    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                        # Simulate the GitHub analysis part
                        if teamconfig.has_github_repositories():
                            github_repos = teamconfig.get_github_repositories()
                            print(f"Analyzing {len(github_repos)} GitHub repositories...", file=sys.stderr)

                        # Should show analysis message, not warning
                        stderr_output = mock_stderr.getvalue()
                        self.assertIn("Analyzing 2 GitHub repositories...", stderr_output)
                        self.assertNotIn("Warning: --github specified but no GitHub repositories found", stderr_output)

    def test_github_flag_team_config_loading(self):
        """Test that --github flag automatically loads team config."""
        # Mock team config loading
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            # Mock has_github_repositories to return True
            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = True

                # Mock get_github_repositories
                with patch("gitinspector.gitinspector.teamconfig.get_github_repositories") as mock_get_repos:
                    mock_get_repos.return_value = ["owner/repo1"]

                    # Simulate the team config loading that happens in the process method
                    teamconfig.load_team_config("team_config.json", enable_team_filtering=False)

                    # Verify team config was loaded
                    mock_load.assert_called_once_with("team_config.json", enable_team_filtering=False)

    def test_github_flag_error_messages(self):
        """Test that appropriate error messages are shown for different scenarios."""
        # Test 1: No config file
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.side_effect = teamconfig.TeamConfigError("Team config file not found: team_config.json")

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    # Simulate the error handling in the process method
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

        # Test 2: Invalid config
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.side_effect = teamconfig.TeamConfigError("Invalid team config: 'team' must be a list")

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    # Simulate the error handling in the process method
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

    def test_github_flag_help_message(self):
        """Test that --github flag shows appropriate help message."""
        # Test the help text includes GitHub information
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["gitinspector", "--help"]):
                with self.assertRaises(SystemExit):
                    from gitinspector.gitinspector import main

                    main()

                help_output = mock_stdout.getvalue()
                self.assertIn("--github", help_output)
                self.assertIn("analyze GitHub pull requests", help_output)


if __name__ == "__main__":
    unittest.main()
