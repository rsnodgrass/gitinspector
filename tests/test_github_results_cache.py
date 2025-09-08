#!/usr/bin/env python3
"""
Tests for GitHub results cache functionality.
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_results_cache import GitHubResultsCache


class TestGitHubResultsCache(unittest.TestCase):
    """Test GitHub results cache functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = GitHubResultsCache(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_cache_initialization(self):
        """Test cache initialization."""
        self.assertEqual(str(self.cache.cache_dir), self.temp_dir)
        self.assertTrue(self.cache.cache_dir.exists())

    def test_cache_key_generation(self):
        """Test cache key generation."""
        repositories = ["owner/repo1", "owner/repo2"]
        since = "2024-01-01T00:00:00Z"
        cache_timestamps = {"owner/repo1": "2024-01-01T00:00:00Z", "owner/repo2": "2024-01-02T00:00:00Z"}
        
        key1 = self.cache._generate_cache_key(repositories, since, cache_timestamps)
        key2 = self.cache._generate_cache_key(repositories, since, cache_timestamps)
        
        # Same inputs should generate same key
        self.assertEqual(key1, key2)
        
        # Different inputs should generate different keys
        key3 = self.cache._generate_cache_key(["owner/repo3"], since, cache_timestamps)
        self.assertNotEqual(key1, key3)

    def test_cache_key_consistency(self):
        """Test that cache key generation is consistent regardless of order."""
        repositories1 = ["owner/repo1", "owner/repo2"]
        repositories2 = ["owner/repo2", "owner/repo1"]  # Different order
        
        key1 = self.cache._generate_cache_key(repositories1)
        key2 = self.cache._generate_cache_key(repositories2)
        
        # Should generate same key regardless of order
        self.assertEqual(key1, key2)

    def test_cache_results(self):
        """Test caching and retrieving results."""
        repositories = ["owner/repo1", "owner/repo2"]
        results = {
            "total_repositories": 2,
            "repositories": {"owner/repo1": {"total_prs": 5}, "owner/repo2": {"total_prs": 3}},
            "overall_stats": {"total_prs": 8}
        }
        cache_timestamps = {"owner/repo1": "2024-01-01T00:00:00Z", "owner/repo2": "2024-01-02T00:00:00Z"}
        
        # Cache results
        self.cache.cache_results(repositories, results, cache_timestamps=cache_timestamps)
        
        # Retrieve results
        cached_results = self.cache.get_cached_results(repositories, cache_timestamps=cache_timestamps)
        
        self.assertIsNotNone(cached_results)
        self.assertEqual(cached_results["total_repositories"], 2)
        self.assertEqual(cached_results["overall_stats"]["total_prs"], 8)

    def test_cache_invalidation(self):
        """Test that cache is invalidated when data changes."""
        repositories = ["owner/repo1", "owner/repo2"]
        results = {"total_repositories": 2, "overall_stats": {"total_prs": 8}}
        cache_timestamps = {"owner/repo1": "2024-01-01T00:00:00Z", "owner/repo2": "2024-01-02T00:00:00Z"}
        
        # Cache results
        self.cache.cache_results(repositories, results, cache_timestamps=cache_timestamps)
        
        # Try to retrieve with same timestamps - should work
        cached_results = self.cache.get_cached_results(repositories, cache_timestamps=cache_timestamps)
        self.assertIsNotNone(cached_results)
        
        # Try to retrieve with newer timestamps - should be invalid
        newer_timestamps = {"owner/repo1": "2024-01-03T00:00:00Z", "owner/repo2": "2024-01-02T00:00:00Z"}
        cached_results = self.cache.get_cached_results(repositories, cache_timestamps=newer_timestamps)
        self.assertIsNone(cached_results)

    def test_cache_without_timestamps(self):
        """Test cache behavior when no timestamps are provided."""
        repositories = ["owner/repo1", "owner/repo2"]
        results = {"total_repositories": 2, "overall_stats": {"total_prs": 8}}
        
        # Cache results without timestamps
        self.cache.cache_results(repositories, results)
        
        # Retrieve without timestamps - should work
        cached_results = self.cache.get_cached_results(repositories)
        self.assertIsNotNone(cached_results)
        
        # Retrieve with timestamps - should also work (no validation)
        # Note: This will create a different cache key, so it won't find the cached results
        # This is expected behavior - different parameters create different cache entries
        cache_timestamps = {"owner/repo1": "2024-01-01T00:00:00Z"}
        cached_results = self.cache.get_cached_results(repositories, cache_timestamps=cache_timestamps)
        # This should be None because it's a different cache key
        self.assertIsNone(cached_results)

    def test_clear_cache(self):
        """Test clearing cache."""
        repositories = ["owner/repo1"]
        results = {"total_repositories": 1}
        
        # Cache results
        self.cache.cache_results(repositories, results)
        
        # Verify cache exists
        cached_results = self.cache.get_cached_results(repositories)
        self.assertIsNotNone(cached_results)
        
        # Clear cache
        self.cache.clear_cache()
        
        # Verify cache is cleared
        cached_results = self.cache.get_cached_results(repositories)
        self.assertIsNone(cached_results)

    def test_get_cache_info(self):
        """Test getting cache information."""
        repositories = ["owner/repo1"]
        results = {"total_repositories": 1}
        
        # Get initial info
        info = self.cache.get_cache_info()
        self.assertEqual(info["total_entries"], 0)
        
        # Cache results
        self.cache.cache_results(repositories, results)
        
        # Get updated info
        info = self.cache.get_cache_info()
        self.assertEqual(info["total_entries"], 1)
        self.assertGreater(info["total_size_bytes"], 0)

    def test_cleanup_old_entries(self):
        """Test cleanup of old cache entries."""
        repositories = ["owner/repo1"]
        results = {"total_repositories": 1}
        
        # Cache results
        self.cache.cache_results(repositories, results)
        
        # Verify cache exists
        info = self.cache.get_cache_info()
        self.assertEqual(info["total_entries"], 1)
        
        # Cleanup with very short age (should remove everything)
        removed_count = self.cache.cleanup_old_entries(max_age_days=0)
        self.assertEqual(removed_count, 1)
        
        # Verify cache is cleared
        info = self.cache.get_cache_info()
        self.assertEqual(info["total_entries"], 0)

    def test_multiple_cache_entries(self):
        """Test multiple cache entries with different parameters."""
        repositories1 = ["owner/repo1"]
        repositories2 = ["owner/repo2"]
        results1 = {"total_repositories": 1, "repositories": {"owner/repo1": {"total_prs": 5}}}
        results2 = {"total_repositories": 1, "repositories": {"owner/repo2": {"total_prs": 3}}}
        
        # Cache different results
        self.cache.cache_results(repositories1, results1)
        self.cache.cache_results(repositories2, results2)
        
        # Verify both are cached
        info = self.cache.get_cache_info()
        self.assertEqual(info["total_entries"], 2)
        
        # Verify we can retrieve both
        cached1 = self.cache.get_cached_results(repositories1)
        cached2 = self.cache.get_cached_results(repositories2)
        
        self.assertIsNotNone(cached1)
        self.assertIsNotNone(cached2)
        self.assertEqual(cached1["total_repositories"], 1)
        self.assertEqual(cached2["total_repositories"], 1)

    def test_cache_with_since_parameter(self):
        """Test cache behavior with since parameter."""
        repositories = ["owner/repo1"]
        results = {"total_repositories": 1}
        since1 = "2024-01-01T00:00:00Z"
        since2 = "2024-01-02T00:00:00Z"
        
        # Cache with since parameter
        self.cache.cache_results(repositories, results, since=since1)
        
        # Retrieve with same since - should work
        cached_results = self.cache.get_cached_results(repositories, since=since1)
        self.assertIsNotNone(cached_results)
        
        # Retrieve with different since - should not work
        cached_results = self.cache.get_cached_results(repositories, since=since2)
        self.assertIsNone(cached_results)


if __name__ == "__main__":
    unittest.main()
