#!/usr/bin/env python3
"""
Test helpers for GitHub integration tests.
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_integration import GitHubIntegration
from gitinspector.github_cache import GitHubCache


class GitHubTestHelper:
    """Helper class for GitHub integration tests."""

    def __init__(self, test_case):
        """Initialize the test helper."""
        self.test_case = test_case
        self.temp_dir = None
        self.cache = None
        self.integration = None

    def setup(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = GitHubCache(self.temp_dir)
        self.integration = GitHubIntegration(use_cache=True, cache_dir=self.temp_dir)
        return self

    def teardown(self):
        """Clean up test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_pr(
        self,
        number: int,
        state: str = "closed",
        merged: bool = True,
        author: str = "testuser",
        created_days_ago: int = 1,
    ) -> Dict:
        """Create a test PR with standard structure."""
        created_at = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        created_at = created_at.replace(day=created_at.day - created_days_ago)

        pr = {
            "number": number,
            "title": f"Test PR {number}",
            "state": state,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "user": {"login": author},
        }

        if merged and state == "closed":
            merged_at = created_at.replace(hour=12, minute=0, second=0, microsecond=0)
            pr["merged_at"] = merged_at.isoformat().replace("+00:00", "Z")
        else:
            pr["merged_at"] = None

        return pr

    def create_test_review(self, reviewer: str = "reviewer1", state: str = "APPROVED") -> Dict:
        """Create a test review."""
        return {
            "id": 1,
            "user": {"login": reviewer},
            "state": state,
        }

    def create_test_comment(self, commenter: str = "commenter1", body: str = "Great work!") -> Dict:
        """Create a test comment."""
        return {
            "id": 1,
            "user": {"login": commenter},
            "body": body,
        }

    def setup_cached_data(
        self,
        repository: str,
        prs: List[Dict],
        reviews: Dict = None,
        comments: Dict = None,
        review_comments: Dict = None,
        general_comments: Dict = None,
    ):
        """Set up cached data for testing."""
        self.integration.cache.cache_pull_requests(repository, prs)

        if reviews:
            for pr_number, pr_reviews in reviews.items():
                self.integration.cache.cache_reviews(repository, pr_number, pr_reviews)

        if comments:
            for pr_number, pr_comments in comments.items():
                self.integration.cache.cache_comments(repository, pr_number, pr_comments)

        if review_comments:
            for pr_number, pr_review_comments in review_comments.items():
                self.integration.cache.cache_review_comments(repository, pr_number, pr_review_comments)

        if general_comments:
            for pr_number, pr_general_comments in general_comments.items():
                self.integration.cache.cache_general_comments(repository, pr_number, pr_general_comments)

        self.integration.cache.update_cache_metadata(repository)

    def create_standard_test_data(self, repository: str = "test/repo") -> Dict:
        """Create standard test data for common test scenarios."""
        prs = [
            self.create_test_pr(1, "closed", True, "author1", 2),
            self.create_test_pr(2, "open", False, "author2", 1),
            self.create_test_pr(3, "closed", False, "author3", 3),
        ]

        reviews = {
            1: [self.create_test_review("reviewer1", "APPROVED")],
            2: [self.create_test_review("reviewer2", "COMMENTED")],
        }

        comments = {
            1: [self.create_test_comment("commenter1", "Great work!")],
            2: [self.create_test_comment("commenter2", "Needs improvement")],
        }

        review_comments = {
            1: [self.create_test_comment("reviewer1", "Line 10 needs fixing")],
            2: [self.create_test_comment("reviewer2", "Good catch!")],
        }

        self.setup_cached_data(repository, prs, reviews, comments, review_comments)

        return {
            "prs": prs,
            "reviews": reviews,
            "comments": comments,
            "review_comments": review_comments,
        }

    def assert_analysis_structure(self, analysis: Dict, repository: str, expected_prs: int = None):
        """Assert that analysis has the correct basic structure."""
        self.test_case.assertEqual(analysis["repository"], repository)
        self.test_case.assertIn("total_prs", analysis)
        self.test_case.assertIn("open_prs", analysis)
        self.test_case.assertIn("closed_prs", analysis)
        self.test_case.assertIn("merged_prs", analysis)
        self.test_case.assertIn("pr_durations", analysis)
        self.test_case.assertIn("user_stats", analysis)
        self.test_case.assertIn("review_stats", analysis)
        self.test_case.assertIn("comment_stats", analysis)

        if expected_prs is not None:
            self.test_case.assertEqual(analysis["total_prs"], expected_prs)

    def assert_user_stats(self, analysis: Dict, user: str, expected_stats: Dict):
        """Assert that user stats match expected values."""
        self.test_case.assertIn(user, analysis["user_stats"])
        user_stats = analysis["user_stats"][user]

        for key, expected_value in expected_stats.items():
            self.test_case.assertEqual(
                user_stats[key],
                expected_value,
                f"User {user} {key} mismatch: expected {expected_value}, got {user_stats[key]}",
            )

    def assert_review_stats(self, analysis: Dict, reviewer: str, expected_reviews: int):
        """Assert that review stats match expected values."""
        self.test_case.assertIn(reviewer, analysis["review_stats"])
        self.test_case.assertEqual(analysis["review_stats"][reviewer]["reviews_given"], expected_reviews)

    def assert_comment_stats(self, analysis: Dict, commenter: str, expected_comments: int):
        """Assert that comment stats match expected values."""
        self.test_case.assertIn(commenter, analysis["comment_stats"])
        self.test_case.assertEqual(analysis["comment_stats"][commenter]["comments_given"], expected_comments)


class GitHubTestContext:
    """Context manager for GitHub test setup and teardown."""

    def __init__(self, test_case):
        """Initialize the context manager."""
        self.helper = GitHubTestHelper(test_case)

    def __enter__(self):
        """Set up test environment."""
        return self.helper.setup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up test environment."""
        self.helper.teardown()


def create_test_integration(cache_dir: str = None) -> GitHubIntegration:
    """Create a test GitHubIntegration instance."""
    if cache_dir is None:
        cache_dir = tempfile.mkdtemp()
    return GitHubIntegration(use_cache=True, cache_dir=cache_dir)


def create_test_cache(cache_dir: str = None) -> GitHubCache:
    """Create a test GitHubCache instance."""
    if cache_dir is None:
        cache_dir = tempfile.mkdtemp()
    return GitHubCache(cache_dir)
