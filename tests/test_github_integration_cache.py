#!/usr/bin/env python3
"""
Tests for GitHub integration with cache functionality.
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_integration import GitHubIntegration, GitHubIntegrationError
from gitinspector.github_cache import GitHubCache


class TestGitHubIntegrationCache(unittest.TestCase):
    """Test GitHub integration with cache functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = GitHubCache(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_cache(self):
        """Test initialization with cache enabled."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        self.assertTrue(integration.use_cache)
        self.assertIsInstance(integration.cache, GitHubCache)
        self.assertEqual(integration.cache.cache_dir, self.cache.cache_dir)

    def test_initialization_without_cache(self):
        """Test initialization without cache."""
        with patch.dict(os.environ, {"GITHUB_APP_ID": "test_app", "GITHUB_PRIVATE_KEY": "test_key"}):
            integration = GitHubIntegration(app_id="test_app", private_key_content="test_key", use_cache=False)

            self.assertFalse(integration.use_cache)
            self.assertIsNone(integration.cache)
            self.assertEqual(integration.app_id, "test_app")

    def test_initialization_cache_only(self):
        """Test initialization in cache-only mode."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        self.assertTrue(integration.use_cache)
        self.assertIsNotNone(integration.cache)

    def test_get_pull_requests_from_cache(self):
        """Test getting pull requests from cache."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Add test data to cache
        repository = "test/repo"
        test_prs = [
            {"number": 1, "title": "Test PR 1", "state": "open", "created_at": "2024-01-01T00:00:00Z"},
            {"number": 2, "title": "Test PR 2", "state": "closed", "created_at": "2024-01-02T00:00:00Z"},
        ]

        integration.cache.cache_pull_requests(repository, test_prs)
        integration.cache.update_cache_metadata(repository)

        # Get PRs from cache
        prs = integration.get_pull_requests("test", "repo")
        self.assertEqual(prs, test_prs)

    def test_get_pull_requests_with_filtering(self):
        """Test getting pull requests with state and since filtering."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Add test data to cache
        repository = "test/repo"
        test_prs = [
            {"number": 1, "title": "Test PR 1", "state": "open", "created_at": "2024-01-01T00:00:00Z"},
            {
                "number": 2,
                "title": "Test PR 2",
                "state": "closed",
                "created_at": "2024-01-01T23:59:59Z",
            },  # Before since date
            {"number": 3, "title": "Test PR 3", "state": "open", "created_at": "2024-01-03T00:00:00Z"},
        ]

        integration.cache.cache_pull_requests(repository, test_prs)
        integration.cache.update_cache_metadata(repository)

        # Filter by state
        open_prs = integration.get_pull_requests("test", "repo", state="open")
        self.assertEqual(len(open_prs), 2)
        self.assertTrue(all(pr["state"] == "open" for pr in open_prs))

        # Filter by since
        recent_prs = integration.get_pull_requests("test", "repo", since="2024-01-02T00:00:00Z")
        self.assertEqual(len(recent_prs), 1)
        self.assertEqual(recent_prs[0]["number"], 3)

    def test_get_pull_requests_no_cache(self):
        """Test getting pull requests when no cache data available."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Try to get PRs for non-cached repository
        with self.assertRaises(GitHubIntegrationError) as cm:
            integration.get_pull_requests("test", "repo")

        self.assertIn("No cached data available", str(cm.exception))

    def test_get_pr_reviews_from_cache(self):
        """Test getting PR reviews from cache."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Add test data to cache
        repository = "test/repo"
        pr_number = 1
        test_reviews = [
            {"id": 1, "user": {"login": "user1"}, "state": "APPROVED"},
            {"id": 2, "user": {"login": "user2"}, "state": "COMMENTED"},
        ]

        integration.cache.cache_reviews(repository, pr_number, test_reviews)
        integration.cache.update_cache_metadata(repository)

        # Get reviews from cache
        reviews = integration.get_pr_reviews("test", "repo", pr_number)
        self.assertEqual(reviews, test_reviews)

    def test_get_pr_comments_from_cache(self):
        """Test getting PR comments from cache."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Add test data to cache
        repository = "test/repo"
        pr_number = 1
        test_comments = [
            {"id": 1, "user": {"login": "user1"}, "body": "Great work!"},
            {"id": 2, "user": {"login": "user2"}, "body": "Needs improvement"},
        ]

        integration.cache.cache_comments(repository, pr_number, test_comments)
        integration.cache.update_cache_metadata(repository)

        # Get comments from cache
        comments = integration.get_pr_comments("test", "repo", pr_number)
        self.assertEqual(comments, test_comments)

    def test_get_pr_review_comments_from_cache(self):
        """Test getting PR review comments from cache."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Add test data to cache
        repository = "test/repo"
        pr_number = 1
        test_review_comments = [
            {"id": 1, "user": {"login": "user1"}, "body": "Line 10 needs fixing"},
            {"id": 2, "user": {"login": "user2"}, "body": "Good catch!"},
        ]

        integration.cache.cache_review_comments(repository, pr_number, test_review_comments)
        integration.cache.update_cache_metadata(repository)

        # Get review comments from cache
        review_comments = integration.get_pr_review_comments("test", "repo", pr_number)
        self.assertEqual(review_comments, test_review_comments)

    def test_api_mode_without_cache(self):
        """Test API mode without cache."""
        with patch.dict(os.environ, {"GITHUB_APP_ID": "test_app", "GITHUB_PRIVATE_KEY": "test_key"}):
            integration = GitHubIntegration(app_id="test_app", private_key_content="test_key", use_cache=False)

            # Mock the entire API request method to prevent actual network requests
            # Return data on first call, empty list on second call to break the pagination loop
            with patch.object(integration, "_make_authenticated_request") as mock_request:
                mock_request.side_effect = [
                    [
                        {
                            "number": 1,
                            "title": "Test PR",
                            "state": "open",
                            "created_at": "2024-01-01T00:00:00Z",
                            "user": {"login": "testuser"},
                        }
                    ],  # First page
                    [],  # Second page (empty, breaks the loop)
                ]

                prs = integration.get_pull_requests("test", "repo")
                self.assertEqual(len(prs), 1)
                self.assertEqual(prs[0]["number"], 1)
                self.assertEqual(mock_request.call_count, 2)  # Called twice due to pagination

    def test_analyze_repository_prs_with_cache(self):
        """Test analyzing repository PRs with cache."""
        integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)

        # Add test data to cache
        repository = "test/repo"
        test_prs = [
            {
                "number": 1,
                "title": "Test PR 1",
                "state": "closed",
                "merged_at": "2024-01-02T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "user": {"login": "author1"},
            }
        ]

        test_reviews = [{"user": {"login": "reviewer1"}, "state": "APPROVED"}]

        test_comments = [{"user": {"login": "commenter1"}, "body": "Great work!"}]

        integration.cache.cache_pull_requests(repository, test_prs)
        integration.cache.cache_reviews(repository, 1, test_reviews)
        integration.cache.cache_comments(repository, 1, test_comments)
        integration.cache.cache_review_comments(repository, 1, [])
        integration.cache.update_cache_metadata(repository)

        # Analyze repository
        analysis = integration.analyze_repository_prs("test", "repo")

        self.assertEqual(analysis["repository"], repository)
        self.assertEqual(analysis["total_prs"], 1)
        self.assertEqual(analysis["closed_prs"], 0)  # Merged PRs are not counted as closed
        self.assertEqual(analysis["merged_prs"], 1)
        self.assertIn("author1", analysis["user_stats"])
        self.assertIn("reviewer1", analysis["review_stats"])
        self.assertIn("commenter1", analysis["comment_stats"])


if __name__ == "__main__":
    unittest.main()
