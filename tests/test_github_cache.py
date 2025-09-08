#!/usr/bin/env python3
"""
Tests for GitHub cache module.
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_cache import GitHubCache, GitHubCacheError


class TestGitHubCache(unittest.TestCase):
    """Test GitHub cache functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = GitHubCache(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_cache_initialization(self):
        """Test cache initialization."""
        self.assertEqual(self.cache.cache_dir, Path(self.temp_dir))
        self.assertTrue(self.cache.cache_dir.exists())

    def test_metadata_operations(self):
        """Test metadata operations."""
        # Initially no metadata
        metadata = self.cache.get_cache_metadata()
        self.assertEqual(metadata, {})

        # Update metadata for a repository
        repository = "test/repo"
        self.cache.update_cache_metadata(repository)

        metadata = self.cache.get_cache_metadata()
        self.assertIn("repositories", metadata)
        self.assertIn(repository, metadata["repositories"])
        self.assertIn("last_sync", metadata["repositories"][repository])
        self.assertIn("cached_at", metadata["repositories"][repository])

    def test_repository_cached_check(self):
        """Test repository cached check."""
        repository = "test/repo"

        # Initially not cached
        self.assertFalse(self.cache.is_repository_cached(repository))

        # After updating metadata
        self.cache.update_cache_metadata(repository)
        self.assertTrue(self.cache.is_repository_cached(repository))

    def test_last_sync_time(self):
        """Test last sync time retrieval."""
        repository = "test/repo"

        # Initially no sync time
        self.assertIsNone(self.cache.get_last_sync_time(repository))

        # After updating metadata
        sync_time = "2024-01-01T00:00:00Z"
        self.cache.update_cache_metadata(repository, sync_time)
        self.assertEqual(self.cache.get_last_sync_time(repository), sync_time)

    def test_pull_requests_caching(self):
        """Test pull requests caching."""
        repository = "test/repo"
        prs = [
            {"number": 1, "title": "Test PR 1", "state": "open"},
            {"number": 2, "title": "Test PR 2", "state": "closed"},
        ]

        # Cache PRs
        self.cache.cache_pull_requests(repository, prs)

        # Retrieve PRs
        cached_prs = self.cache.get_cached_pull_requests(repository)
        self.assertEqual(cached_prs, prs)

        # Test non-existent repository
        empty_prs = self.cache.get_cached_pull_requests("nonexistent/repo")
        self.assertEqual(empty_prs, [])

    def test_reviews_caching(self):
        """Test reviews caching."""
        repository = "test/repo"
        pr_number = 1
        reviews = [
            {"id": 1, "user": {"login": "user1"}, "state": "APPROVED"},
            {"id": 2, "user": {"login": "user2"}, "state": "COMMENTED"},
        ]

        # Cache reviews
        self.cache.cache_reviews(repository, pr_number, reviews)

        # Retrieve reviews
        cached_reviews = self.cache.get_cached_reviews(repository, pr_number)
        self.assertEqual(cached_reviews, reviews)

        # Test non-existent PR
        empty_reviews = self.cache.get_cached_reviews(repository, 999)
        self.assertEqual(empty_reviews, [])

    def test_comments_caching(self):
        """Test comments caching."""
        repository = "test/repo"
        pr_number = 1
        comments = [
            {"id": 1, "user": {"login": "user1"}, "body": "Great work!"},
            {"id": 2, "user": {"login": "user2"}, "body": "Needs improvement"},
        ]

        # Cache comments
        self.cache.cache_comments(repository, pr_number, comments)

        # Retrieve comments
        cached_comments = self.cache.get_cached_comments(repository, pr_number)
        self.assertEqual(cached_comments, comments)

        # Test non-existent PR
        empty_comments = self.cache.get_cached_comments(repository, 999)
        self.assertEqual(empty_comments, [])

    def test_review_comments_caching(self):
        """Test review comments caching."""
        repository = "test/repo"
        pr_number = 1
        review_comments = [
            {"id": 1, "user": {"login": "user1"}, "body": "Line 10 needs fixing"},
            {"id": 2, "user": {"login": "user2"}, "body": "Good catch!"},
        ]

        # Cache review comments
        self.cache.cache_review_comments(repository, pr_number, review_comments)

        # Retrieve review comments
        cached_review_comments = self.cache.get_cached_review_comments(repository, pr_number)
        self.assertEqual(cached_review_comments, review_comments)

        # Test non-existent PR
        empty_review_comments = self.cache.get_cached_review_comments(repository, 999)
        self.assertEqual(empty_review_comments, [])

    def test_clear_repository_cache(self):
        """Test clearing repository cache."""
        repository = "test/repo"

        # Add some data
        self.cache.update_cache_metadata(repository)
        self.cache.cache_pull_requests(repository, [{"number": 1}])
        self.cache.cache_reviews(repository, 1, [{"id": 1}])
        self.cache.cache_comments(repository, 1, [{"id": 1}])
        self.cache.cache_review_comments(repository, 1, [{"id": 1}])

        # Verify data exists
        self.assertTrue(self.cache.is_repository_cached(repository))
        self.assertEqual(len(self.cache.get_cached_pull_requests(repository)), 1)

        # Clear repository cache
        self.cache.clear_repository_cache(repository)

        # Verify data is cleared
        self.assertFalse(self.cache.is_repository_cached(repository))
        self.assertEqual(len(self.cache.get_cached_pull_requests(repository)), 0)

    def test_clear_all_cache(self):
        """Test clearing all cache."""
        # Add some data
        self.cache.update_cache_metadata("test/repo1")
        self.cache.update_cache_metadata("test/repo2")

        # Verify data exists
        self.assertEqual(len(self.cache.get_cached_repositories()), 2)

        # Clear all cache
        self.cache.clear_all_cache()

        # Verify all data is cleared
        self.assertEqual(len(self.cache.get_cached_repositories()), 0)

    def test_cache_size(self):
        """Test cache size calculation."""
        # Initially empty
        sizes = self.cache.get_cache_size()
        self.assertEqual(sizes["metadata"], 0)

        # Add some data
        self.cache.update_cache_metadata("test/repo")

        # Check sizes
        sizes = self.cache.get_cache_size()
        self.assertGreater(sizes["metadata"], 0)

    def test_cached_repositories(self):
        """Test getting cached repositories list."""
        # Initially empty
        self.assertEqual(self.cache.get_cached_repositories(), [])

        # Add repositories
        self.cache.update_cache_metadata("test/repo1")
        self.cache.update_cache_metadata("test/repo2")

        # Check list
        repos = self.cache.get_cached_repositories()
        self.assertEqual(set(repos), {"test/repo1", "test/repo2"})

    def test_json_file_errors(self):
        """Test handling of JSON file errors."""
        # Create invalid JSON file
        invalid_file = self.cache.cache_dir / "metadata.json"
        with open(invalid_file, "w") as f:
            f.write("invalid json content")

        # Should raise GitHubCacheError
        with self.assertRaises(GitHubCacheError):
            self.cache.get_cache_metadata()


if __name__ == "__main__":
    unittest.main()
