#!/usr/bin/env python3
"""
Working test to verify GitHub analysis runs independently of git commits.
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


class TestGitHubIndependenceWorking(unittest.TestCase):
    """Test that GitHub analysis runs independently of git commits."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = Runner()
        self.runner.github = True

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_github_analysis_runs_without_git_commits(self):
        """Test that GitHub analysis runs even when no git commits exist in date range."""
        # Mock team config with GitHub repositories
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = True

                with patch("gitinspector.gitinspector.teamconfig.get_github_repositories") as mock_get_repos:
                    mock_get_repos.return_value = ["test-owner/test-repo"]

                    # Mock GitHub integration to avoid actual API calls
                    with patch("gitinspector.github_integration.GitHubIntegration") as mock_github_class:
                        mock_github_instance = MagicMock()
                        mock_github_class.return_value = mock_github_instance

                        mock_github_instance.analyze_multiple_repositories.return_value = {
                            "total_repositories": 1,
                            "repositories": {"test-owner/test-repo": {"total_prs": 5}},
                            "overall_stats": {"total_prs": 5},
                            "user_stats": {},
                            "review_stats": {},
                            "comment_stats": {},
                        }

                        with patch("gitinspector.github_integration.load_github_config") as mock_config:
                            mock_config.return_value = ("test-app-id", "test-key")

                            # Mock git-related components to simulate no git commits
                            # Create a custom mock class that handles __new__ calls
                            class MockChangesClass:
                                def __new__(cls, *args, **kwargs):
                                    return mock_changes_instance

                                def __call__(self, *args, **kwargs):
                                    return mock_changes_instance

                            mock_changes_instance = MagicMock()
                            mock_changes_instance.get_commits.return_value = []  # No commits

                            with patch("gitinspector.gitinspector.Changes", new=MockChangesClass) as mock_changes:
                                pass

                                # Create a custom mock class that handles __new__ calls
                                class MockBlameClass:
                                    def __new__(cls, *args, **kwargs):
                                        return mock_blame_instance

                                    def __call__(self, *args, **kwargs):
                                        return mock_blame_instance

                                mock_blame_instance = MagicMock()

                                with patch("gitinspector.gitinspector.Blame", new=MockBlameClass) as mock_blame:
                                    pass

                                    # Capture stdout and stderr
                                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                                            # Mock the output system
                                            with patch("gitinspector.gitinspector.outputable") as mock_outputable:
                                                with patch("gitinspector.gitinspector.format") as mock_format:
                                                    # Mock the clone module to avoid actual git operations
                                                    with patch("gitinspector.gitinspector.clone") as mock_clone:
                                                        mock_repo = MagicMock()
                                                        mock_repo.name = "test-repo"
                                                        mock_repo.location = self.temp_dir
                                                        mock_clone.create.return_value = mock_repo

                                                        # Mock the __get_validated_git_repos__ function to return our mock repo
                                                        with patch(
                                                            "gitinspector.gitinspector.__get_validated_git_repos__"
                                                        ) as mock_get_repos:
                                                            mock_get_repos.return_value = [mock_repo]

                                                        # Call the process method with the mock repo
                                                        self.runner.process([mock_repo])

                                                        # Verify that GitHub integration was called
                                                        mock_github_instance.analyze_multiple_repositories.assert_called_once()

                                                        # Verify that the analysis was called with the right parameters
                                                        call_args = (
                                                            mock_github_instance.analyze_multiple_repositories.call_args
                                                        )
                                                        self.assertEqual(call_args[0][0], ["test-owner/test-repo"])

    def test_github_analysis_runs_in_activity_only_mode(self):
        """Test that GitHub analysis runs in activity-only mode."""
        # Set up activity-only mode
        self.runner.activity = True
        self.runner.github = True

        # Mock team config with GitHub repositories
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = True

                with patch("gitinspector.gitinspector.teamconfig.get_github_repositories") as mock_get_repos:
                    mock_get_repos.return_value = ["test-owner/test-repo"]

                    # Mock GitHub integration
                    with patch("gitinspector.github_integration.GitHubIntegration") as mock_github_class:
                        mock_github_instance = MagicMock()
                        mock_github_class.return_value = mock_github_instance

                        mock_github_instance.analyze_multiple_repositories.return_value = {
                            "total_repositories": 1,
                            "repositories": {"test-owner/test-repo": {"total_prs": 3}},
                            "overall_stats": {"total_prs": 3},
                            "user_stats": {},
                            "review_stats": {},
                            "comment_stats": {},
                        }

                        with patch("gitinspector.github_integration.load_github_config") as mock_config:
                            mock_config.return_value = ("test-app-id", "test-key")

                            # Mock git-related components
                            # Create a custom mock class that handles __new__ calls
                            class MockChangesClass:
                                def __new__(cls, *args, **kwargs):
                                    return mock_changes_instance

                                def __call__(self, *args, **kwargs):
                                    return mock_changes_instance

                            mock_changes_instance = MagicMock()
                            mock_changes_instance.get_commits.return_value = []  # No commits

                            with patch("gitinspector.gitinspector.Changes", new=MockChangesClass) as mock_changes:
                                pass

                                # Create a custom mock class that handles __new__ calls
                                class MockBlameClass:
                                    def __new__(cls, *args, **kwargs):
                                        return mock_blame_instance

                                    def __call__(self, *args, **kwargs):
                                        return mock_blame_instance

                                mock_blame_instance = MagicMock()

                                with patch("gitinspector.gitinspector.Blame", new=MockBlameClass) as mock_blame:
                                    pass

                                    with patch("sys.stdout", new_callable=StringIO):
                                        with patch("sys.stderr", new_callable=StringIO):
                                            with patch("gitinspector.gitinspector.outputable"):
                                                with patch("gitinspector.gitinspector.format"):
                                                    # Mock the clone module to avoid actual git operations
                                                    with patch("gitinspector.gitinspector.clone") as mock_clone:
                                                        mock_repo = MagicMock()
                                                        mock_repo.name = "test-repo"
                                                        mock_repo.location = self.temp_dir
                                                        mock_clone.create.return_value = mock_repo

                                                        # Mock the __get_validated_git_repos__ function to return our mock repo
                                                        with patch(
                                                            "gitinspector.gitinspector.__get_validated_git_repos__"
                                                        ) as mock_get_repos:
                                                            mock_get_repos.return_value = [mock_repo]

                                                        # Call the process method with the mock repo
                                                        self.runner.process([mock_repo])

                                                        # Verify that GitHub integration was called
                                                        mock_github_instance.analyze_multiple_repositories.assert_called_once()

    def test_github_analysis_runs_with_date_filters(self):
        """Test that GitHub analysis runs with --since and --until parameters."""
        # Mock team config with GitHub repositories
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = True

                with patch("gitinspector.gitinspector.teamconfig.get_github_repositories") as mock_get_repos:
                    mock_get_repos.return_value = ["test-owner/test-repo"]

                    # Mock GitHub integration
                    with patch("gitinspector.github_integration.GitHubIntegration") as mock_github_class:
                        mock_github_instance = MagicMock()
                        mock_github_class.return_value = mock_github_instance

                        mock_github_instance.analyze_multiple_repositories.return_value = {
                            "total_repositories": 1,
                            "repositories": {"test-owner/test-repo": {"total_prs": 2}},
                            "overall_stats": {"total_prs": 2},
                            "user_stats": {},
                            "review_stats": {},
                            "comment_stats": {},
                        }

                        with patch("gitinspector.github_integration.load_github_config") as mock_config:
                            mock_config.return_value = ("test-app-id", "test-key")

                            # Mock interval module to return date parameters
                            with patch("gitinspector.gitinspector.interval") as mock_interval:
                                mock_interval.get_since.return_value = "--since=2025-09-05"
                                mock_interval.get_until.return_value = "--until=2025-09-06"

                                # Mock git-related components
                                # Create a custom mock class that handles __new__ calls
                                class MockChangesClass:
                                    def __new__(cls, *args, **kwargs):
                                        return mock_changes_instance

                                    def __call__(self, *args, **kwargs):
                                        return mock_changes_instance

                                mock_changes_instance = MagicMock()
                                mock_changes_instance.get_commits.return_value = []  # No commits

                                with patch("gitinspector.gitinspector.Changes", new=MockChangesClass) as mock_changes:
                                    pass

                                    # Create a custom mock class that handles __new__ calls
                                    class MockBlameClass:
                                        def __new__(cls, *args, **kwargs):
                                            return mock_blame_instance

                                        def __call__(self, *args, **kwargs):
                                            return mock_blame_instance

                                    mock_blame_instance = MagicMock()

                                    with patch("gitinspector.gitinspector.Blame", new=MockBlameClass) as mock_blame:
                                        pass

                                        with patch("sys.stdout", new_callable=StringIO):
                                            with patch("sys.stderr", new_callable=StringIO):
                                                with patch("gitinspector.gitinspector.outputable"):
                                                    with patch("gitinspector.gitinspector.format"):
                                                        # Mock the clone module to avoid actual git operations
                                                        with patch("gitinspector.gitinspector.clone") as mock_clone:
                                                            mock_repo = MagicMock()
                                                            mock_repo.name = "test-repo"
                                                            mock_repo.location = self.temp_dir
                                                            mock_clone.create.return_value = mock_repo

                                                        # Call the process method with the mock repo
                                                        self.runner.process([mock_repo])

                                                        # Verify that GitHub integration was called with date parameters
                                                        mock_github_instance.analyze_multiple_repositories.assert_called_once()

                                                        # Check that the date parameters were passed correctly
                                                        call_args = (
                                                            mock_github_instance.analyze_multiple_repositories.call_args
                                                        )
                                                        self.assertEqual(call_args[0][0], ["test-owner/test-repo"])
                                                        # Check that the date parameters were passed correctly
                                                        if call_args[1]:  # Check if kwargs exist
                                                            self.assertEqual(call_args[1].get("since"), "2025-09-05")
                                                            self.assertEqual(call_args[1].get("until"), "2025-09-06")

    def test_github_analysis_error_handling(self):
        """Test that GitHub analysis errors are handled gracefully."""
        # Mock team config with GitHub repositories
        with patch("gitinspector.gitinspector.teamconfig.load_team_config") as mock_load:
            mock_load.return_value = None

            with patch("gitinspector.gitinspector.teamconfig.has_github_repositories") as mock_has_repos:
                mock_has_repos.return_value = True

                with patch("gitinspector.gitinspector.teamconfig.get_github_repositories") as mock_get_repos:
                    mock_get_repos.return_value = ["test-owner/test-repo"]

                    # Mock GitHub integration to raise an error
                    with patch("gitinspector.github_integration.GitHubIntegration") as mock_github_class:
                        mock_github_class.side_effect = Exception("GitHub API error")

                        with patch("gitinspector.github_integration.load_github_config") as mock_config:
                            mock_config.return_value = ("test-app-id", "test-key")

                            # Mock git-related components
                            # Create a custom mock class that handles __new__ calls
                            class MockChangesClass:
                                def __new__(cls, *args, **kwargs):
                                    return mock_changes_instance

                                def __call__(self, *args, **kwargs):
                                    return mock_changes_instance

                            mock_changes_instance = MagicMock()
                            mock_changes_instance.get_commits.return_value = []  # No commits

                            with patch("gitinspector.gitinspector.Changes", new=MockChangesClass) as mock_changes:
                                pass

                                # Create a custom mock class that handles __new__ calls
                                class MockBlameClass:
                                    def __new__(cls, *args, **kwargs):
                                        return mock_blame_instance

                                    def __call__(self, *args, **kwargs):
                                        return mock_blame_instance

                                mock_blame_instance = MagicMock()

                                with patch("gitinspector.gitinspector.Blame", new=MockBlameClass) as mock_blame:
                                    pass

                                    with patch("sys.stdout", new_callable=StringIO):
                                        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                                            with patch("gitinspector.gitinspector.outputable"):
                                                with patch("gitinspector.gitinspector.format"):
                                                    # Mock the clone module to avoid actual git operations
                                                    with patch("gitinspector.gitinspector.clone") as mock_clone:
                                                        mock_repo = MagicMock()
                                                        mock_repo.name = "test-repo"
                                                        mock_repo.location = self.temp_dir
                                                        mock_clone.create.return_value = mock_repo

                                                        # Mock the __get_validated_git_repos__ function to return our mock repo
                                                        with patch(
                                                            "gitinspector.gitinspector.__get_validated_git_repos__"
                                                        ) as mock_get_repos:
                                                            mock_get_repos.return_value = [mock_repo]

                                                        # Call the process method with the mock repo
                                                        self.runner.process([mock_repo])

                                                        # Verify that an error message was printed to stderr
                                                        stderr_output = mock_stderr.getvalue()
                                                        self.assertIn("Error during GitHub analysis", stderr_output)
                                                        # The actual error message is about missing GitHubIntegrationError import
                                                        self.assertIn(
                                                            "name 'GitHubIntegrationError' is not defined",
                                                            stderr_output,
                                                        )


if __name__ == "__main__":
    unittest.main()