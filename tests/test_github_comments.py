#!/usr/bin/env python3
"""
Tests for GitHub comments functionality including general comments, review comments, and comment statistics.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone, timedelta

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_integration import GitHubIntegration, GitHubIntegrationError
from tests.github_test_helpers import GitHubTestContext


class TestGitHubComments(unittest.TestCase):
    """Test GitHub comments functionality including general comments and comment statistics."""

    def setUp(self):
        """Set up test environment."""
        self.test_context = GitHubTestContext(self)
        self.helper = self.test_context.__enter__()
        self.integration = self.helper.integration

    def tearDown(self):
        """Clean up test environment."""
        self.test_context.__exit__(None, None, None)

    def test_get_pr_general_comments_with_cache(self):
        """Test getting general PR comments from cache."""
        repository = "test/repo"
        pr_number = 123
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "This is a general comment",
                "created_at": "2025-09-05T10:00:00Z",
            },
            {
                "id": 2,
                "user": {"login": "reviewer2"},
                "body": "Another general comment",
                "created_at": "2025-09-05T11:00:00Z",
            },
        ]

        # Set up cache with general comments and mark repository as cached
        self.helper.cache.cache_general_comments(repository, pr_number, general_comments)
        self.helper.cache.update_cache_metadata(repository)

        result = self.integration.get_pr_general_comments("test", "repo", pr_number)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["user"]["login"], "reviewer1")
        self.assertEqual(result[1]["id"], 2)
        self.assertEqual(result[1]["user"]["login"], "reviewer2")

    def test_get_pr_general_comments_without_cache(self):
        """Test getting general PR comments without cache (API call)."""
        repository = "test/repo"
        pr_number = 123
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "This is a general comment",
                "created_at": "2025-09-05T10:00:00Z",
            }
        ]

        # Mock the API call
        with patch.object(self.integration, "_make_authenticated_request") as mock_request:
            mock_request.return_value = general_comments

            # Set use_cache to False to force API call
            self.integration.use_cache = False

            result = self.integration.get_pr_general_comments("test", "repo", pr_number)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["user"]["login"], "reviewer1")
        mock_request.assert_called_once_with("test", "repo", "issues/123/comments")

    def test_get_pr_general_comments_404_error(self):
        """Test handling 404 error when no general comments exist."""
        repository = "test/repo"
        pr_number = 123

        # Mock the API call to raise 404 error
        with patch.object(self.integration, "_make_authenticated_request") as mock_request:
            mock_request.side_effect = GitHubIntegrationError("404 Not Found")

            # Set use_cache to False to force API call
            self.integration.use_cache = False

            result = self.integration.get_pr_general_comments("test", "repo", pr_number)

        self.assertEqual(result, [])
        mock_request.assert_called_once_with("test", "repo", "issues/123/comments")

    def test_get_pr_general_comments_no_cache_available(self):
        """Test error when no cache is available and use_cache is True."""
        repository = "test/repo"
        pr_number = 123

        # Ensure repository is not cached
        self.integration.use_cache = True

        with self.assertRaises(GitHubIntegrationError) as cm:
            self.integration.get_pr_general_comments("test", "repo", pr_number)

        self.assertIn("No cached data available for test/repo", str(cm.exception))

    def test_comment_stats_with_general_comments(self):
        """Test comment statistics processing with general comments."""
        repository = "test/repo"
        pr = self.helper.create_test_pr(1, "closed", True, "author1")

        # Set up different types of comments
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "General comment 1",
                "created_at": "2025-09-05T10:00:00Z",
            },
            {
                "id": 2,
                "user": {"login": "reviewer2"},
                "body": "General comment 2",
                "created_at": "2025-09-05T11:00:00Z",
            },
        ]

        review_comments = [
            {
                "id": 3,
                "user": {"login": "reviewer1"},
                "body": "Review comment 1",
                "created_at": "2025-09-05T12:00:00Z",
                "pull_request_review_id": 100,
            }
        ]

        # Mock the old comments (which are actually review comments)
        old_comments = [
            {
                "id": 4,
                "user": {"login": "reviewer3"},
                "body": "Old comment (review comment)",
                "created_at": "2025-09-05T13:00:00Z",
                "pull_request_review_id": 101,
            }
        ]

        # Set up cache data using the helper method
        self.helper.setup_cached_data(
            repository,
            [pr],
            general_comments={1: general_comments},
            review_comments={1: review_comments},
            comments={1: old_comments},
        )

        # Mock the methods to return our test data
        with patch.object(self.integration, "get_pr_general_comments") as mock_general, patch.object(
            self.integration, "get_pr_review_comments"
        ) as mock_review, patch.object(self.integration, "get_pr_comments") as mock_old:

            mock_general.return_value = general_comments
            mock_review.return_value = review_comments
            mock_old.return_value = old_comments

            analysis = self.integration.analyze_repository_prs("test", "repo")

        # Check that all comment types are counted
        self.assertIn("comment_stats", analysis)

        # reviewer1 should have 2 comments (1 general + 1 review)
        self.assertEqual(analysis["comment_stats"]["reviewer1"]["comments_given"], 2)

        # reviewer2 should have 1 comment (1 general)
        self.assertEqual(analysis["comment_stats"]["reviewer2"]["comments_given"], 1)

        # reviewer3 should have 1 comment (1 old/review comment)
        self.assertEqual(analysis["comment_stats"]["reviewer3"]["comments_given"], 1)

    def test_review_stats_with_comments(self):
        """Test review statistics include comments given by reviewers."""
        repository = "test/repo"
        pr = self.helper.create_test_pr(1, "closed", True, "author1")

        # Set up reviews
        reviews = [
            {"id": 1, "user": {"login": "reviewer1"}, "state": "APPROVED", "submitted_at": "2025-09-05T10:00:00Z"},
            {
                "id": 2,
                "user": {"login": "reviewer2"},
                "state": "CHANGES_REQUESTED",
                "submitted_at": "2025-09-05T11:00:00Z",
            },
        ]

        # Set up comments by reviewers
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "General comment by reviewer1",
                "created_at": "2025-09-05T10:00:00Z",
            }
        ]

        review_comments = [
            {
                "id": 2,
                "user": {"login": "reviewer2"},
                "body": "Review comment by reviewer2",
                "created_at": "2025-09-05T11:00:00Z",
                "pull_request_review_id": 100,
            }
        ]

        # Set up cache data using the helper method
        self.helper.setup_cached_data(
            repository,
            [pr],
            reviews={1: reviews},
            general_comments={1: general_comments},
            review_comments={1: review_comments},
        )

        # Mock the methods to return our test data
        with patch.object(self.integration, "get_pr_reviews") as mock_reviews, patch.object(
            self.integration, "get_pr_general_comments"
        ) as mock_general, patch.object(self.integration, "get_pr_review_comments") as mock_review, patch.object(
            self.integration, "get_pr_comments"
        ) as mock_old:

            mock_reviews.return_value = reviews
            mock_general.return_value = general_comments
            mock_review.return_value = review_comments
            mock_old.return_value = []

            analysis = self.integration.analyze_repository_prs("test", "repo")

        # Check review statistics
        self.assertIn("review_stats", analysis)

        # reviewer1 should have 1 review and 1 comment
        self.assertEqual(analysis["review_stats"]["reviewer1"]["reviews_given"], 1)
        self.assertEqual(analysis["review_stats"]["reviewer1"]["comments_given"], 1)

        # reviewer2 should have 1 review and 1 comment
        self.assertEqual(analysis["review_stats"]["reviewer2"]["reviews_given"], 1)
        self.assertEqual(analysis["review_stats"]["reviewer2"]["comments_given"], 1)

    def test_comment_stats_received_by_author(self):
        """Test that PR authors receive comments correctly."""
        repository = "test/repo"
        pr = self.helper.create_test_pr(1, "closed", True, "author1")

        # Set up comments on the PR
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "Comment on author1's PR",
                "created_at": "2025-09-05T10:00:00Z",
            },
            {
                "id": 2,
                "user": {"login": "reviewer2"},
                "body": "Another comment on author1's PR",
                "created_at": "2025-09-05T11:00:00Z",
            },
        ]

        review_comments = [
            {
                "id": 3,
                "user": {"login": "reviewer1"},
                "body": "Review comment on author1's PR",
                "created_at": "2025-09-05T12:00:00Z",
                "pull_request_review_id": 100,
            }
        ]

        # Set up cache data using the helper method
        self.helper.setup_cached_data(
            repository, [pr], general_comments={1: general_comments}, review_comments={1: review_comments}
        )

        # Mock the methods to return our test data
        with patch.object(self.integration, "get_pr_general_comments") as mock_general, patch.object(
            self.integration, "get_pr_review_comments"
        ) as mock_review, patch.object(self.integration, "get_pr_comments") as mock_old, patch.object(
            self.integration, "get_pr_reviews"
        ) as mock_reviews:

            mock_general.return_value = general_comments
            mock_review.return_value = review_comments
            mock_old.return_value = []
            mock_reviews.return_value = []

            analysis = self.integration.analyze_repository_prs("test", "repo")

        # Check that author1 received the comments
        self.assertIn("user_stats", analysis)
        self.assertIn("author1", analysis["user_stats"])
        self.assertEqual(analysis["user_stats"]["author1"]["total_comments_received"], 3)  # 2 general + 1 review

    def test_cache_general_comments_methods(self):
        """Test GitHub cache methods for general comments."""
        repository = "test/repo"
        pr_number = 123
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "Test general comment",
                "created_at": "2025-09-05T10:00:00Z",
            }
        ]

        # Test caching
        self.helper.cache.cache_general_comments(repository, pr_number, general_comments)

        # Test retrieval
        cached_comments = self.helper.cache.get_cached_general_comments(repository, pr_number)
        self.assertEqual(len(cached_comments), 1)
        self.assertEqual(cached_comments[0]["id"], 1)
        self.assertEqual(cached_comments[0]["user"]["login"], "reviewer1")

        # Test retrieval for non-existent PR
        empty_comments = self.helper.cache.get_cached_general_comments(repository, 999)
        self.assertEqual(empty_comments, [])

    def test_clear_repository_cache_includes_general_comments(self):
        """Test that clearing repository cache also clears general comments."""
        repository = "test/repo"
        pr_number = 123
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "Test general comment",
                "created_at": "2025-09-05T10:00:00Z",
            }
        ]

        # Cache some general comments
        self.helper.cache.cache_general_comments(repository, pr_number, general_comments)

        # Verify they exist
        cached_comments = self.helper.cache.get_cached_general_comments(repository, pr_number)
        self.assertEqual(len(cached_comments), 1)

        # Clear the repository cache
        self.helper.cache.clear_repository_cache(repository)

        # Verify general comments are cleared
        cleared_comments = self.helper.cache.get_cached_general_comments(repository, pr_number)
        self.assertEqual(cleared_comments, [])

    def test_fetch_pr_related_data_includes_general_comments(self):
        """Test that _fetch_pr_related_data includes general comments."""
        repository = "test/repo"
        pr_number = 123
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "Test general comment",
                "created_at": "2025-09-05T10:00:00Z",
            }
        ]

        # Set up cache data and mark repository as cached
        self.helper.cache.cache_general_comments(repository, pr_number, general_comments)
        self.helper.cache.update_cache_metadata(repository)

        # Mock other methods
        with patch.object(self.integration, "get_pr_reviews") as mock_reviews, patch.object(
            self.integration, "get_pr_comments"
        ) as mock_comments, patch.object(self.integration, "get_pr_review_comments") as mock_review_comments:

            mock_reviews.return_value = []
            mock_comments.return_value = []
            mock_review_comments.return_value = []

            # Call the method
            result = self.integration._fetch_pr_related_data("test", "repo", pr_number)

        # Check that general comments are included
        self.assertIn("general_comments", result)
        self.assertEqual(len(result["general_comments"]), 1)
        self.assertEqual(result["general_comments"][0]["id"], 1)

    def test_process_pr_related_data_handles_general_comments(self):
        """Test that _process_pr_related_data correctly handles general comments."""
        repository = "test/repo"
        pr = self.helper.create_test_pr(1, "closed", True, "author1")

        general_comments = [
            {"id": 1, "user": {"login": "reviewer1"}, "body": "General comment", "created_at": "2025-09-05T10:00:00Z"}
        ]

        pr_data = {"reviews": [], "comments": [], "review_comments": [], "general_comments": general_comments}

        analysis = {"comment_stats": {}, "user_stats": {}, "review_stats": {}}

        # Call the method
        self.integration._process_pr_related_data(pr, pr_data, analysis)

        # Check that general comments are processed
        self.assertIn("reviewer1", analysis["comment_stats"])
        self.assertEqual(analysis["comment_stats"]["reviewer1"]["comments_given"], 1)

    def test_integration_with_mixed_comment_types(self):
        """Test integration with all types of comments mixed together."""
        repository = "test/repo"
        pr = self.helper.create_test_pr(1, "closed", True, "author1")

        # Set up all types of comments
        general_comments = [
            {
                "id": 1,
                "user": {"login": "reviewer1"},
                "body": "General comment 1",
                "created_at": "2025-09-05T10:00:00Z",
            },
            {
                "id": 2,
                "user": {"login": "reviewer2"},
                "body": "General comment 2",
                "created_at": "2025-09-05T11:00:00Z",
            },
        ]

        review_comments = [
            {
                "id": 3,
                "user": {"login": "reviewer1"},
                "body": "Review comment 1",
                "created_at": "2025-09-05T12:00:00Z",
                "pull_request_review_id": 100,
            }
        ]

        old_comments = [
            {
                "id": 4,
                "user": {"login": "reviewer3"},
                "body": "Old comment (review comment)",
                "created_at": "2025-09-05T13:00:00Z",
                "pull_request_review_id": 101,
            }
        ]

        # Set up cache data using the helper method
        self.helper.setup_cached_data(
            repository,
            [pr],
            general_comments={1: general_comments},
            review_comments={1: review_comments},
            comments={1: old_comments},
        )

        # Mock the methods
        with patch.object(self.integration, "get_pr_general_comments") as mock_general, patch.object(
            self.integration, "get_pr_review_comments"
        ) as mock_review, patch.object(self.integration, "get_pr_comments") as mock_old, patch.object(
            self.integration, "get_pr_reviews"
        ) as mock_reviews:

            mock_general.return_value = general_comments
            mock_review.return_value = review_comments
            mock_old.return_value = old_comments
            mock_reviews.return_value = []

            analysis = self.integration.analyze_repository_prs("test", "repo")

        # Verify total comment count (this is calculated in the overall stats)
        total_comments = sum(stats["comments_given"] for stats in analysis["comment_stats"].values())
        self.assertEqual(total_comments, 4)  # 2 general + 1 review + 1 old

        # Verify individual comment counts
        self.assertEqual(analysis["comment_stats"]["reviewer1"]["comments_given"], 2)  # 1 general + 1 review
        self.assertEqual(analysis["comment_stats"]["reviewer2"]["comments_given"], 1)  # 1 general
        self.assertEqual(analysis["comment_stats"]["reviewer3"]["comments_given"], 1)  # 1 old

        # Verify author received all comments
        self.assertEqual(analysis["user_stats"]["author1"]["total_comments_received"], 4)


if __name__ == "__main__":
    unittest.main()
