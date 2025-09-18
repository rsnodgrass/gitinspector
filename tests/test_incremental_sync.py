#!/usr/bin/env python3
"""
Tests for incremental sync functionality.
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, timezone

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_cache import GitHubCache, GitHubCacheError


class TestIncrementalSync(unittest.TestCase):
    """Test incremental sync functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = GitHubCache(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_get_latest_pr_update_time(self):
        """Test getting latest PR update time."""
        repository = "test/repo"

        # Initially no data
        self.assertIsNone(self.cache.get_latest_pr_update_time(repository))

        # Add PRs with different timestamps
        prs = [
            {"number": 1, "title": "PR 1", "updated_at": "2024-01-01T10:00:00Z", "created_at": "2024-01-01T09:00:00Z"},
            {"number": 2, "title": "PR 2", "updated_at": "2024-01-02T15:30:00Z", "created_at": "2024-01-02T14:00:00Z"},
            {"number": 3, "title": "PR 3", "updated_at": "2024-01-01T20:00:00Z", "created_at": "2024-01-01T19:00:00Z"},
        ]

        self.cache.cache_pull_requests(repository, prs)

        # Should return the latest timestamp
        latest_time = self.cache.get_latest_pr_update_time(repository)
        self.assertEqual(latest_time, "2024-01-02T15:30:00Z")

    def test_get_latest_activity_time(self):
        """Test getting latest activity time from all data types."""
        repository = "test/repo"

        # Initially no data
        self.assertIsNone(self.cache.get_latest_activity_time(repository))

        # Add PRs
        prs = [{"number": 1, "title": "PR 1", "updated_at": "2024-01-01T10:00:00Z"}]
        self.cache.cache_pull_requests(repository, prs)

        # Add reviews with later timestamp
        reviews = [{"id": 1, "submitted_at": "2024-01-02T12:00:00Z", "state": "APPROVED"}]
        self.cache.cache_reviews(repository, 1, reviews)

        # Add comments with even later timestamp
        comments = [{"id": 1, "updated_at": "2024-01-03T14:00:00Z", "body": "Comment"}]
        self.cache.cache_comments(repository, 1, comments)

        # Should return the latest timestamp from comments
        latest_time = self.cache.get_latest_activity_time(repository)
        self.assertEqual(latest_time, "2024-01-03T14:00:00Z")

    def test_merge_pull_requests(self):
        """Test merging PRs with existing data."""
        repository = "test/repo"

        # Add initial PRs
        initial_prs = [
            {"number": 1, "title": "Original PR 1", "updated_at": "2024-01-01T10:00:00Z"},
            {"number": 2, "title": "Original PR 2", "updated_at": "2024-01-02T10:00:00Z"},
        ]
        self.cache.cache_pull_requests(repository, initial_prs)

        # Add new/updated PRs
        new_prs = [
            {"number": 1, "title": "Updated PR 1", "updated_at": "2024-01-03T10:00:00Z"},
            {"number": 3, "title": "New PR 3", "updated_at": "2024-01-04T10:00:00Z"},
        ]
        self.cache.merge_pull_requests(repository, new_prs)

        # Check merged result
        merged_prs = self.cache.get_cached_pull_requests(repository)
        self.assertEqual(len(merged_prs), 3)

        # Check that PR 1 was updated
        pr1 = next(pr for pr in merged_prs if pr["number"] == 1)
        self.assertEqual(pr1["title"], "Updated PR 1")
        self.assertEqual(pr1["updated_at"], "2024-01-03T10:00:00Z")

        # Check that PR 2 is unchanged
        pr2 = next(pr for pr in merged_prs if pr["number"] == 2)
        self.assertEqual(pr2["title"], "Original PR 2")

        # Check that PR 3 was added
        pr3 = next(pr for pr in merged_prs if pr["number"] == 3)
        self.assertEqual(pr3["title"], "New PR 3")

    def test_merge_reviews(self):
        """Test merging reviews with existing data."""
        repository = "test/repo"
        pr_number = 1

        # Add initial reviews
        initial_reviews = [
            {"id": 1, "state": "APPROVED", "submitted_at": "2024-01-01T10:00:00Z"},
            {"id": 2, "state": "COMMENTED", "submitted_at": "2024-01-02T10:00:00Z"},
        ]
        self.cache.cache_reviews(repository, pr_number, initial_reviews)

        # Add new/updated reviews
        new_reviews = [
            {"id": 1, "state": "CHANGES_REQUESTED", "submitted_at": "2024-01-03T10:00:00Z"},
            {"id": 3, "state": "APPROVED", "submitted_at": "2024-01-04T10:00:00Z"},
        ]
        self.cache.merge_reviews(repository, pr_number, new_reviews)

        # Check merged result
        merged_reviews = self.cache.get_cached_reviews(repository, pr_number)
        self.assertEqual(len(merged_reviews), 3)

        # Check that review 1 was updated
        review1 = next(r for r in merged_reviews if r["id"] == 1)
        self.assertEqual(review1["state"], "CHANGES_REQUESTED")

        # Check that review 2 is unchanged
        review2 = next(r for r in merged_reviews if r["id"] == 2)
        self.assertEqual(review2["state"], "COMMENTED")

        # Check that review 3 was added
        review3 = next(r for r in merged_reviews if r["id"] == 3)
        self.assertEqual(review3["state"], "APPROVED")

    def test_merge_comments(self):
        """Test merging comments with existing data."""
        repository = "test/repo"
        pr_number = 1

        # Add initial comments
        initial_comments = [{"id": 1, "body": "Original comment", "created_at": "2024-01-01T10:00:00Z"}]
        self.cache.cache_comments(repository, pr_number, initial_comments)

        # Add new/updated comments
        new_comments = [
            {"id": 1, "body": "Updated comment", "updated_at": "2024-01-02T10:00:00Z"},
            {"id": 2, "body": "New comment", "created_at": "2024-01-03T10:00:00Z"},
        ]
        self.cache.merge_comments(repository, pr_number, new_comments)

        # Check merged result
        merged_comments = self.cache.get_cached_comments(repository, pr_number)
        self.assertEqual(len(merged_comments), 2)

        # Check that comment 1 was updated
        comment1 = next(c for c in merged_comments if c["id"] == 1)
        self.assertEqual(comment1["body"], "Updated comment")

        # Check that comment 2 was added
        comment2 = next(c for c in merged_comments if c["id"] == 2)
        self.assertEqual(comment2["body"], "New comment")

    def test_merge_review_comments(self):
        """Test merging review comments with existing data."""
        repository = "test/repo"
        pr_number = 1

        # Add initial review comments
        initial_review_comments = [{"id": 1, "body": "Original review comment", "created_at": "2024-01-01T10:00:00Z"}]
        self.cache.cache_review_comments(repository, pr_number, initial_review_comments)

        # Add new/updated review comments
        new_review_comments = [
            {"id": 1, "body": "Updated review comment", "updated_at": "2024-01-02T10:00:00Z"},
            {"id": 2, "body": "New review comment", "created_at": "2024-01-03T10:00:00Z"},
        ]
        self.cache.merge_review_comments(repository, pr_number, new_review_comments)

        # Check merged result
        merged_review_comments = self.cache.get_cached_review_comments(repository, pr_number)
        self.assertEqual(len(merged_review_comments), 2)

        # Check that review comment 1 was updated
        review_comment1 = next(c for c in merged_review_comments if c["id"] == 1)
        self.assertEqual(review_comment1["body"], "Updated review comment")

        # Check that review comment 2 was added
        review_comment2 = next(c for c in merged_review_comments if c["id"] == 2)
        self.assertEqual(review_comment2["body"], "New review comment")

    def test_incremental_sync_scenario(self):
        """Test a complete incremental sync scenario."""
        repository = "test/repo"

        # Initial sync - add some data
        initial_prs = [
            {
                "number": 1,
                "title": "Initial PR",
                "updated_at": "2024-01-01T10:00:00Z",
                "created_at": "2024-01-01T09:00:00Z",
            }
        ]
        self.cache.cache_pull_requests(repository, initial_prs)
        self.cache.update_cache_metadata(repository)

        # Simulate incremental sync - add newer data
        new_prs = [
            {
                "number": 1,
                "title": "Updated PR",
                "updated_at": "2024-01-02T15:00:00Z",
                "created_at": "2024-01-01T09:00:00Z",
            },
            {
                "number": 2,
                "title": "New PR",
                "updated_at": "2024-01-02T16:00:00Z",
                "created_at": "2024-01-02T14:00:00Z",
            },
        ]

        # Get latest activity time (should be from initial PR)
        latest_time = self.cache.get_latest_activity_time(repository)
        self.assertEqual(latest_time, "2024-01-01T10:00:00Z")

        # Merge new data
        self.cache.merge_pull_requests(repository, new_prs)

        # Check final result
        final_prs = self.cache.get_cached_pull_requests(repository)
        self.assertEqual(len(final_prs), 2)

        # Check that we now have the latest timestamp
        new_latest_time = self.cache.get_latest_activity_time(repository)
        self.assertEqual(new_latest_time, "2024-01-02T16:00:00Z")


if __name__ == "__main__":
    unittest.main()
