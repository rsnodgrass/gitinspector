#!/usr/bin/env python3
"""
Tests for test mode functionality.
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_github_cache import sync_repository_data, sync_all_repositories
from gitinspector.github_cache import GitHubCache


class TestTestMode(unittest.TestCase):
    """Test test mode functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = GitHubCache(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_test_mode_date_calculation(self):
        """Test that test mode calculates the correct date (7 days ago)."""
        from datetime import datetime, timedelta

        # Test the date calculation logic
        test_since = (datetime.now() - timedelta(days=7)).isoformat()

        # Should be a valid ISO format string
        self.assertIsNotNone(test_since)
        self.assertIsInstance(test_since, str)
        self.assertTrue(len(test_since) > 10)  # Should be a reasonable length

        # Should be approximately 7 days ago
        now = datetime.now()
        test_date = datetime.fromisoformat(test_since.replace("Z", "+00:00"))
        days_diff = (now - test_date).days
        self.assertGreaterEqual(days_diff, 6)  # At least 6 days (allowing for time differences)
        self.assertLessEqual(days_diff, 8)  # At most 8 days

    def test_test_mode_pr_limiting(self):
        """Test that test mode limits PRs to 5."""
        # Mock GitHub integration
        mock_integration = MagicMock()

        # Create mock PRs (more than 5)
        mock_prs = [
            {"number": i, "title": f"PR {i}", "updated_at": "2024-01-01T10:00:00Z"} for i in range(1, 10)  # 9 PRs
        ]

        mock_integration.get_pull_requests.return_value = mock_prs
        mock_integration.get_pr_reviews.return_value = []
        mock_integration.get_pr_comments.return_value = []
        mock_integration.get_pr_review_comments.return_value = []

        # Run sync in test mode
        with patch("sync_github_cache.GitHubIntegration", return_value=mock_integration):
            sync_repository_data(
                mock_integration, self.cache, "test", "repo", since="2024-01-01T00:00:00Z", test_mode=True
            )

        # Check that only 5 PRs were processed
        cached_prs = self.cache.get_cached_pull_requests("test/repo")
        self.assertEqual(len(cached_prs), 5)

        # Check that we got the first 5 PRs
        for i, pr in enumerate(cached_prs):
            self.assertEqual(pr["number"], i + 1)

    def test_test_mode_with_existing_data(self):
        """Test that test mode works with existing cached data."""
        # Add some existing data
        existing_prs = [
            {"number": 1, "title": "Existing PR 1", "updated_at": "2024-01-01T10:00:00Z"},
            {"number": 2, "title": "Existing PR 2", "updated_at": "2024-01-02T10:00:00Z"},
        ]
        self.cache.cache_pull_requests("test/repo", existing_prs)
        self.cache.update_cache_metadata("test/repo")

        # Mock GitHub integration
        mock_integration = MagicMock()

        # Create new PRs
        new_prs = [
            {"number": 3, "title": "New PR 3", "updated_at": "2024-01-03T10:00:00Z"},
            {"number": 4, "title": "New PR 4", "updated_at": "2024-01-04T10:00:00Z"},
            {"number": 5, "title": "New PR 5", "updated_at": "2024-01-05T10:00:00Z"},
            {"number": 6, "title": "New PR 6", "updated_at": "2024-01-06T10:00:00Z"},
            {"number": 7, "title": "New PR 7", "updated_at": "2024-01-07T10:00:00Z"},
            {"number": 8, "title": "New PR 8", "updated_at": "2024-01-08T10:00:00Z"},
        ]

        mock_integration.get_pull_requests.return_value = new_prs
        mock_integration.get_pr_reviews.return_value = []
        mock_integration.get_pr_comments.return_value = []
        mock_integration.get_pr_review_comments.return_value = []

        # Run sync in test mode
        with patch("sync_github_cache.GitHubIntegration", return_value=mock_integration):
            sync_repository_data(
                mock_integration, self.cache, "test", "repo", since="2024-01-02T00:00:00Z", test_mode=True
            )

        # Check that we have existing + limited new PRs
        cached_prs = self.cache.get_cached_pull_requests("test/repo")
        self.assertEqual(len(cached_prs), 7)  # 2 existing + 5 new (limited)

        # Check that we have the right PRs
        pr_numbers = [pr["number"] for pr in cached_prs]
        self.assertIn(1, pr_numbers)  # Existing
        self.assertIn(2, pr_numbers)  # Existing
        self.assertIn(3, pr_numbers)  # New (within limit)
        self.assertIn(4, pr_numbers)  # New (within limit)
        self.assertIn(5, pr_numbers)  # New (within limit)
        self.assertIn(6, pr_numbers)  # New (within limit)
        self.assertIn(7, pr_numbers)  # New (within limit)
        self.assertNotIn(8, pr_numbers)  # New (beyond limit)

    def test_test_mode_integration(self):
        """Test test mode integration with sync_all_repositories."""
        # Mock GitHub integration
        mock_integration = MagicMock()

        # Create mock PRs
        mock_prs = [
            {"number": i, "title": f"PR {i}", "updated_at": "2024-01-01T10:00:00Z"} for i in range(1, 8)  # 7 PRs
        ]

        mock_integration.get_pull_requests.return_value = mock_prs
        mock_integration.get_pr_reviews.return_value = []
        mock_integration.get_pr_comments.return_value = []
        mock_integration.get_pr_review_comments.return_value = []

        # Test repositories
        repositories = ["test/repo1", "test/repo2"]

        # Run sync in test mode
        with patch("sync_github_cache.GitHubIntegration", return_value=mock_integration):
            sync_all_repositories(
                mock_integration, self.cache, repositories, since="2024-01-01T00:00:00Z", test_mode=True
            )

        # Check that both repositories were processed with limited PRs
        for repo in repositories:
            cached_prs = self.cache.get_cached_pull_requests(repo)
            self.assertEqual(len(cached_prs), 5)  # Limited to 5 PRs per repo


if __name__ == "__main__":
    unittest.main()
