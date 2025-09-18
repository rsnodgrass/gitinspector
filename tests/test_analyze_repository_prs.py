#!/usr/bin/env python3
"""
Comprehensive tests for analyze_repository_prs function and related methods.
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


class TestAnalyzeRepositoryPRs(unittest.TestCase):
    """Test the analyze_repository_prs function and related methods."""

    def setUp(self):
        """Set up test environment."""
        self.test_context = GitHubTestContext(self)
        self.helper = self.test_context.__enter__()
        self.integration = self.helper.integration

    def tearDown(self):
        """Clean up test environment."""
        self.test_context.__exit__(None, None, None)

    def test_analyze_repository_prs_basic_functionality(self):
        """Test basic functionality of analyze_repository_prs."""
        repository = "test/repo"
        prs = [
            self.helper.create_test_pr(1, "closed", True, "author1"),
            self.helper.create_test_pr(2, "open", False, "author2"),
        ]

        self.helper.setup_cached_data(repository, prs)

        analysis = self.integration.analyze_repository_prs("test", "repo")

        self.helper.assert_analysis_structure(analysis, repository, 2)
        self.assertEqual(analysis["open_prs"], 1)
        self.assertEqual(analysis["closed_prs"], 0)  # Merged PRs are not counted as closed
        self.assertEqual(analysis["merged_prs"], 1)
        self.assertIn("author1", analysis["user_stats"])
        self.assertIn("author2", analysis["user_stats"])

    def test_analyze_repository_prs_with_reviews_and_comments(self):
        """Test analyze_repository_prs with reviews and comments."""
        repository = "test/repo"
        prs = [self.helper.create_test_pr(1, "closed", True, "author1")]
        reviews = {1: [self.helper.create_test_review("reviewer1", "APPROVED")]}
        comments = {1: [self.helper.create_test_comment("commenter1", "Great work!")]}
        review_comments = {1: [self.helper.create_test_comment("reviewer2", "Line 10 needs fixing")]}

        self.helper.setup_cached_data(repository, prs, reviews, comments, review_comments)

        analysis = self.integration.analyze_repository_prs("test", "repo")

        # Check review stats
        self.helper.assert_review_stats(analysis, "reviewer1", 1)

        # Check comment stats
        self.helper.assert_comment_stats(analysis, "commenter1", 1)
        self.helper.assert_comment_stats(analysis, "reviewer2", 1)

        # Check author received comments
        self.helper.assert_user_stats(analysis, "author1", {"total_comments_received": 2, "total_reviews_received": 1})

    def test_analyze_repository_prs_duration_calculation(self):
        """Test PR duration calculation for merged PRs."""
        repository = "test/repo"
        prs = [self.helper.create_test_pr(1, "closed", True, "author1", created_days_ago=2)]

        self.helper.setup_cached_data(repository, prs)

        analysis = self.integration.analyze_repository_prs("test", "repo")

        self.assertEqual(analysis["merged_prs"], 1)
        self.assertEqual(len(analysis["pr_durations"]), 1)
        self.assertGreater(analysis["pr_durations"][0], 0)  # Should be positive duration
        self.assertEqual(analysis["avg_pr_duration_hours"], analysis["pr_durations"][0])
        self.assertEqual(analysis["median_pr_duration_hours"], analysis["pr_durations"][0])

    def test_analyze_repository_prs_with_date_filters(self):
        """Test analyze_repository_prs with since and until filters."""
        repository = "test/repo"
        prs = [
            self.helper.create_test_pr(1, "closed", True, "author1", created_days_ago=5),
            self.helper.create_test_pr(2, "closed", True, "author2", created_days_ago=2),
        ]

        self.helper.setup_cached_data(repository, prs)

        # Test with since filter
        since_date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
        analysis = self.integration.analyze_repository_prs("test", "repo", since=since_date)

        self.assertEqual(analysis["total_prs"], 1)  # Only the recent PR should be included
        self.assertEqual(analysis["user_stats"]["author2"]["prs_created"], 1)

    def test_analyze_repository_prs_empty_repository(self):
        """Test analyze_repository_prs with empty repository."""
        repository = "test/repo"
        self.helper.setup_cached_data(repository, [])

        analysis = self.integration.analyze_repository_prs("test", "repo")

        self.helper.assert_analysis_structure(analysis, repository, 0)
        self.assertEqual(analysis["open_prs"], 0)
        self.assertEqual(analysis["closed_prs"], 0)
        self.assertEqual(analysis["merged_prs"], 0)
        self.assertEqual(analysis["avg_pr_duration_hours"], 0)
        self.assertEqual(analysis["median_pr_duration_hours"], 0)

    def test_analyze_repository_prs_multiple_authors(self):
        """Test analyze_repository_prs with multiple authors."""
        repository = "test/repo"
        prs = [
            self.helper.create_test_pr(1, "closed", True, "author1"),
            self.helper.create_test_pr(2, "closed", True, "author1"),
            self.helper.create_test_pr(3, "open", False, "author2"),
        ]

        self.helper.setup_cached_data(repository, prs)

        analysis = self.integration.analyze_repository_prs("test", "repo")

        # Check author stats
        self.helper.assert_user_stats(analysis, "author1", {"prs_created": 2, "prs_merged": 2})
        self.helper.assert_user_stats(analysis, "author2", {"prs_created": 1, "prs_merged": 0})

    def test_analyze_repository_prs_error_handling(self):
        """Test error handling in analyze_repository_prs."""
        # Test with non-cached repository
        with self.assertRaises(GitHubIntegrationError) as cm:
            self.integration.analyze_repository_prs("nonexistent", "repo")

        self.assertIn("No cached data available", str(cm.exception))

    @patch("gitinspector.github_integration.print")
    def test_log_analysis_start(self, mock_print):
        """Test the _log_analysis_start method."""
        self.integration._log_analysis_start("test", "repo")
        mock_print.assert_called_once_with("Analyzing PRs for test/repo...", file=sys.stderr)

    def test_initialize_analysis_structure(self):
        """Test the _initialize_analysis_structure method."""
        repository = "test/repo"
        analysis = self.integration._initialize_analysis_structure(repository)

        expected_structure = {
            "repository": repository,
            "total_prs": 0,
            "open_prs": 0,
            "closed_prs": 0,
            "merged_prs": 0,
            "pr_durations": [],
            "user_stats": {},
            "review_stats": {},
            "comment_stats": {},
        }

        self.assertEqual(analysis, expected_structure)

    def test_process_prs(self):
        """Test the _process_prs method."""
        repository = "test/repo"
        prs = [
            self.helper.create_test_pr(1, "closed", True, "author1"),
            self.helper.create_test_pr(2, "open", False, "author2"),
        ]

        self.helper.setup_cached_data(repository, prs)

        analysis = self.integration._initialize_analysis_structure(repository)
        self.integration._process_prs("test", "repo", prs, analysis)

        self.assertEqual(analysis["total_prs"], 2)
        self.assertEqual(analysis["open_prs"], 1)
        self.assertEqual(analysis["merged_prs"], 1)

    @patch("gitinspector.github_integration.print")
    def test_show_progress(self, mock_print):
        """Test the _show_progress method."""
        # Test progress at 10th item
        self.integration._show_progress(10, 100)
        mock_print.assert_called_with("  Processing PR 10/100 (10.0%)", file=sys.stderr)

        # Test progress at last item
        self.integration._show_progress(100, 100)
        mock_print.assert_called_with("  Processing PR 100/100 (100.0%)", file=sys.stderr)

        # Test no progress for non-milestone items
        mock_print.reset_mock()
        self.integration._show_progress(5, 100)
        mock_print.assert_not_called()

    @patch("time.sleep")
    def test_apply_rate_limiting(self, mock_sleep):
        """Test the _apply_rate_limiting method."""
        self.integration._apply_rate_limiting()
        mock_sleep.assert_called_once_with(0.1)

    def test_fetch_pr_related_data(self):
        """Test the _fetch_pr_related_data method."""
        repository = "test/repo"
        prs = [self.helper.create_test_pr(1, "closed", True, "author1")]
        reviews = {1: [self.helper.create_test_review("reviewer1")]}
        comments = {1: [self.helper.create_test_comment("commenter1")]}
        review_comments = {1: [self.helper.create_test_comment("reviewer2")]}

        self.helper.setup_cached_data(repository, prs, reviews, comments, review_comments)

        pr_data = self.integration._fetch_pr_related_data("test", "repo", 1)

        self.assertIn("reviews", pr_data)
        self.assertIn("comments", pr_data)
        self.assertIn("review_comments", pr_data)
        self.assertEqual(len(pr_data["reviews"]), 1)
        self.assertEqual(len(pr_data["comments"]), 1)
        self.assertEqual(len(pr_data["review_comments"]), 1)

    def test_process_pr_related_data(self):
        """Test the _process_pr_related_data method."""
        pr = self.helper.create_test_pr(1, "closed", True, "author1")
        pr_data = {
            "reviews": [self.helper.create_test_review("reviewer1")],
            "comments": [self.helper.create_test_comment("commenter1")],
            "review_comments": [self.helper.create_test_comment("reviewer2")],
            "general_comments": [self.helper.create_test_comment("reviewer3")],
        }

        analysis = self.integration._initialize_analysis_structure("test/repo")
        self.integration._process_pr_related_data(pr, pr_data, analysis)

        # Check that all data was processed
        self.assertIn("reviewer1", analysis["review_stats"])
        self.assertIn("commenter1", analysis["comment_stats"])
        self.assertIn("reviewer2", analysis["comment_stats"])
        self.assertIn("reviewer3", analysis["comment_stats"])
        self.assertEqual(analysis["user_stats"]["author1"]["total_reviews_received"], 1)
        self.assertEqual(analysis["user_stats"]["author1"]["total_comments_received"], 3)

    def test_process_pr_basic_info(self):
        """Test the _process_pr_basic_info method."""
        analysis = self.integration._initialize_analysis_structure("test/repo")

        # Test open PR
        open_pr = self.helper.create_test_pr(1, "open", False, "author1")
        self.integration._process_pr_basic_info(open_pr, analysis)
        self.assertEqual(analysis["open_prs"], 1)
        self.assertEqual(analysis["merged_prs"], 0)
        self.assertEqual(analysis["closed_prs"], 0)

        # Test merged PR
        merged_pr = self.helper.create_test_pr(2, "closed", True, "author2")
        self.integration._process_pr_basic_info(merged_pr, analysis)
        self.assertEqual(analysis["open_prs"], 1)
        self.assertEqual(analysis["merged_prs"], 1)
        self.assertEqual(analysis["closed_prs"], 0)

        # Test closed (not merged) PR
        closed_pr = self.helper.create_test_pr(3, "closed", False, "author3")
        self.integration._process_pr_basic_info(closed_pr, analysis)
        self.assertEqual(analysis["open_prs"], 1)
        self.assertEqual(analysis["merged_prs"], 1)
        self.assertEqual(analysis["closed_prs"], 1)

    def test_calculate_pr_duration(self):
        """Test the _calculate_pr_duration method."""
        pr = self.helper.create_test_pr(1, "closed", True, "author1", created_days_ago=1)
        duration = self.integration._calculate_pr_duration(pr)

        # Should be approximately 12 hours (created at midnight, merged at noon)
        self.assertAlmostEqual(duration, 12.0, delta=0.1)

    def test_process_pr_user_stats(self):
        """Test the _process_pr_user_stats method."""
        analysis = self.integration._initialize_analysis_structure("test/repo")

        # Test merged PR
        merged_pr = self.helper.create_test_pr(1, "closed", True, "author1")
        self.integration._process_pr_user_stats(merged_pr, analysis)

        self.assertIn("author1", analysis["user_stats"])
        self.assertEqual(analysis["user_stats"]["author1"]["prs_created"], 1)
        self.assertEqual(analysis["user_stats"]["author1"]["prs_merged"], 1)

        # Test non-merged PR
        open_pr = self.helper.create_test_pr(2, "open", False, "author2")
        self.integration._process_pr_user_stats(open_pr, analysis)

        self.assertIn("author2", analysis["user_stats"])
        self.assertEqual(analysis["user_stats"]["author2"]["prs_created"], 1)
        self.assertEqual(analysis["user_stats"]["author2"]["prs_merged"], 0)

    def test_ensure_user_in_stats(self):
        """Test the _ensure_user_in_stats method."""
        analysis = self.integration._initialize_analysis_structure("test/repo")

        # Test new user
        self.integration._ensure_user_in_stats("newuser", analysis["user_stats"])

        self.assertIn("newuser", analysis["user_stats"])
        expected_stats = {
            "prs_created": 0,
            "prs_merged": 0,
            "total_comments_received": 0,
            "total_reviews_received": 0,
        }
        self.assertEqual(analysis["user_stats"]["newuser"], expected_stats)

        # Test existing user (should not change)
        analysis["user_stats"]["newuser"]["prs_created"] = 5
        self.integration._ensure_user_in_stats("newuser", analysis["user_stats"])
        self.assertEqual(analysis["user_stats"]["newuser"]["prs_created"], 5)

    def test_process_review_stats(self):
        """Test the _process_review_stats method."""
        analysis = self.integration._initialize_analysis_structure("test/repo")

        reviews = [
            self.helper.create_test_review("reviewer1", "APPROVED"),
            self.helper.create_test_review("reviewer2", "COMMENTED"),
            self.helper.create_test_review("reviewer1", "CHANGES_REQUESTED"),
        ]

        # Add some comment stats to test the comments_given integration
        analysis["comment_stats"] = {
            "reviewer1": {"comments_given": 3, "comments_received": 0},
            "reviewer2": {"comments_given": 1, "comments_received": 0},
        }

        self.integration._process_review_stats(reviews, analysis)

        self.assertIn("reviewer1", analysis["review_stats"])
        self.assertIn("reviewer2", analysis["review_stats"])
        self.assertEqual(analysis["review_stats"]["reviewer1"]["reviews_given"], 2)
        self.assertEqual(analysis["review_stats"]["reviewer2"]["reviews_given"], 1)

        # Check that comments_given is also set
        self.assertEqual(analysis["review_stats"]["reviewer1"]["comments_given"], 3)
        self.assertEqual(analysis["review_stats"]["reviewer2"]["comments_given"], 1)

    def test_process_comment_stats(self):
        """Test the _process_comment_stats method."""
        analysis = self.integration._initialize_analysis_structure("test/repo")

        pr = self.helper.create_test_pr(1, "closed", True, "author1")
        comments = [self.helper.create_test_comment("commenter1", "Great work!")]
        review_comments = [self.helper.create_test_comment("reviewer1", "Line 10 needs fixing")]
        general_comments = [self.helper.create_test_comment("reviewer2", "General comment on PR")]

        self.integration._process_comment_stats(pr, comments, review_comments, general_comments, analysis)

        # Check commenter stats
        self.assertIn("commenter1", analysis["comment_stats"])
        self.assertEqual(analysis["comment_stats"]["commenter1"]["comments_given"], 1)
        self.assertIn("reviewer1", analysis["comment_stats"])
        self.assertEqual(analysis["comment_stats"]["reviewer1"]["comments_given"], 1)
        self.assertIn("reviewer2", analysis["comment_stats"])
        self.assertEqual(analysis["comment_stats"]["reviewer2"]["comments_given"], 1)

        # Check author received comments (3 total: 1 comment + 1 review + 1 general)
        self.assertEqual(analysis["user_stats"]["author1"]["total_comments_received"], 3)
        self.assertEqual(analysis["comment_stats"]["author1"]["comments_received"], 3)

    def test_calculate_final_statistics(self):
        """Test the _calculate_final_statistics method."""
        analysis = self.integration._initialize_analysis_structure("test/repo")
        analysis["pr_durations"] = [12.0, 24.0, 6.0]

        self.integration._calculate_final_statistics(analysis)

        self.assertEqual(analysis["avg_pr_duration_hours"], 14.0)  # (12+24+6)/3
        self.assertEqual(analysis["median_pr_duration_hours"], 12.0)  # Middle value when sorted

        self._test_empty_durations(analysis)

    def _test_empty_durations(self, analysis):
        """Test calculation with empty durations."""
        analysis["pr_durations"] = []
        self.integration._calculate_final_statistics(analysis)

        self.assertEqual(analysis["avg_pr_duration_hours"], 0)
        self.assertEqual(analysis["median_pr_duration_hours"], 0)


if __name__ == "__main__":
    unittest.main()
