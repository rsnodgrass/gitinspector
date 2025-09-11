#!/usr/bin/env python3
"""
Integration tests for analyze_repository_prs function.
These tests verify the complete workflow with realistic data scenarios.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_integration import GitHubIntegration, GitHubIntegrationError
from tests.github_test_helpers import GitHubTestContext


class TestAnalyzeRepositoryPRsIntegration(unittest.TestCase):
    """Integration tests for analyze_repository_prs function."""

    def setUp(self):
        """Set up test environment."""
        self.test_context = GitHubTestContext(self)
        self.helper = self.test_context.__enter__()
        self.integration = self.helper.integration

    def tearDown(self):
        """Clean up test environment."""
        self.test_context.__exit__(None, None, None)

    def test_complete_workflow_with_realistic_data(self):
        """Test complete workflow with realistic repository data."""
        repository = "test/realistic-repo"

        # Create realistic test data
        prs = [
            # Merged PRs with different durations
            self.helper.create_test_pr(1, "closed", True, "alice", 5),  # 5 days ago
            self.helper.create_test_pr(2, "closed", True, "bob", 3),  # 3 days ago
            self.helper.create_test_pr(3, "closed", True, "alice", 1),  # 1 day ago
            # Open PRs
            self.helper.create_test_pr(4, "open", False, "charlie", 2),
            self.helper.create_test_pr(5, "open", False, "david", 1),
            # Closed but not merged PRs
            self.helper.create_test_pr(6, "closed", False, "eve", 4),
        ]

        # Create realistic reviews and comments
        reviews = {
            1: [
                self.helper.create_test_review("bob", "APPROVED"),
                self.helper.create_test_review("charlie", "COMMENTED"),
            ],
            2: [
                self.helper.create_test_review("alice", "APPROVED"),
            ],
            3: [
                self.helper.create_test_review("bob", "CHANGES_REQUESTED"),
                self.helper.create_test_review("david", "APPROVED"),
            ],
            4: [
                self.helper.create_test_review("alice", "COMMENTED"),
            ],
        }

        comments = {
            1: [
                self.helper.create_test_comment("bob", "Great implementation!"),
                self.helper.create_test_comment("charlie", "I have some concerns about performance"),
            ],
            2: [
                self.helper.create_test_comment("alice", "Looks good to me"),
            ],
            3: [
                self.helper.create_test_comment("bob", "Please fix the linting issues"),
                self.helper.create_test_comment("david", "The tests are failing"),
            ],
            4: [
                self.helper.create_test_comment("alice", "When will this be ready?"),
            ],
        }

        review_comments = {
            1: [
                self.helper.create_test_comment("bob", "Line 42: Consider using a more efficient algorithm"),
                self.helper.create_test_comment("charlie", "This function is too complex"),
            ],
            2: [
                self.helper.create_test_comment("alice", "Nice refactoring!"),
            ],
            3: [
                self.helper.create_test_comment("bob", "Line 15: Missing error handling"),
                self.helper.create_test_comment("david", "Line 23: This could be simplified"),
            ],
        }

        # Set up cached data
        self.helper.setup_cached_data(repository, prs, reviews, comments, review_comments)

        # Run analysis
        analysis = self.integration.analyze_repository_prs("test", "realistic-repo")

        # Verify basic structure
        self.helper.assert_analysis_structure(analysis, repository, 6)

        # Verify PR counts
        self.assertEqual(analysis["open_prs"], 2)
        self.assertEqual(analysis["closed_prs"], 1)  # Only non-merged closed PRs
        self.assertEqual(analysis["merged_prs"], 3)

        # Verify duration calculations
        self.assertEqual(len(analysis["pr_durations"]), 3)  # Only merged PRs have durations
        self.assertGreater(analysis["avg_pr_duration_hours"], 0)
        self.assertGreater(analysis["median_pr_duration_hours"], 0)

        # Verify user statistics
        self._verify_realistic_user_stats(analysis)

        # Verify review statistics
        self.helper.assert_review_stats(analysis, "bob", 2)  # 2 reviews given
        self.helper.assert_review_stats(analysis, "alice", 2)  # 2 reviews given
        self.helper.assert_review_stats(analysis, "charlie", 1)  # 1 review given
        self.helper.assert_review_stats(analysis, "david", 1)  # 1 review given

        # Verify comment statistics
        self.helper.assert_comment_stats(analysis, "bob", 4)  # 2 comments + 2 review comments given
        self.helper.assert_comment_stats(analysis, "alice", 3)  # 2 comments + 1 review comment given
        self.helper.assert_comment_stats(analysis, "charlie", 2)  # 1 comment + 1 review comment given
        self.helper.assert_comment_stats(analysis, "david", 2)  # 1 comment + 1 review comment given

    def test_workflow_with_date_filtering(self):
        """Test complete workflow with date filtering."""
        repository = "test/date-filtered-repo"

        # Create PRs with different creation dates
        now = datetime.now(timezone.utc)
        prs = [
            self.helper.create_test_pr(1, "closed", True, "alice", 10),  # 10 days ago
            self.helper.create_test_pr(2, "closed", True, "bob", 5),  # 5 days ago
            self.helper.create_test_pr(3, "closed", True, "charlie", 2),  # 2 days ago
            self.helper.create_test_pr(4, "open", False, "david", 1),  # 1 day ago
        ]

        self.helper.setup_cached_data(repository, prs)

        # Test with since filter (7 days ago)
        since_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        analysis = self.integration.analyze_repository_prs("test", "date-filtered-repo", since=since_date)

        # Should only include PRs from the last 7 days
        self.assertEqual(analysis["total_prs"], 3)  # PRs 2, 3, 4
        self.assertEqual(analysis["merged_prs"], 2)  # PRs 2, 3
        self.assertEqual(analysis["open_prs"], 1)  # PR 4

        # Test with until filter (3 days ago)
        until_date = (now - timedelta(days=3)).strftime("%Y-%m-%d")
        analysis = self.integration.analyze_repository_prs("test", "date-filtered-repo", until=until_date)

        # Should only include PRs older than 3 days
        self.assertEqual(analysis["total_prs"], 2)  # PRs 1, 2
        self.assertEqual(analysis["merged_prs"], 2)  # PRs 1, 2
        self.assertEqual(analysis["open_prs"], 0)

    def test_workflow_with_large_dataset(self):
        """Test workflow with a large dataset to verify performance and correctness."""
        repository = "test/large-repo"

        # Create a large number of PRs
        prs = []
        reviews = {}
        comments = {}
        review_comments = {}

        for i in range(1, 101):  # 100 PRs
            author = f"user{(i % 10) + 1}"  # 10 different users
            state = "closed" if i % 3 != 0 else "open"
            merged = state == "closed" and i % 2 == 0

            pr = self.helper.create_test_pr(i, state, merged, author, i % 10 + 1)
            prs.append(pr)

            # Add some reviews and comments for every 5th PR
            if i % 5 == 0:
                reviewer = f"reviewer{(i % 5) + 1}"
                commenter = f"commenter{(i % 5) + 1}"

                reviews[i] = [self.helper.create_test_review(reviewer, "APPROVED")]
                comments[i] = [self.helper.create_test_comment(commenter, f"Comment on PR {i}")]
                review_comments[i] = [self.helper.create_test_comment(reviewer, f"Review comment on PR {i}")]

        self.helper.setup_cached_data(repository, prs, reviews, comments, review_comments)

        # Run analysis
        analysis = self.integration.analyze_repository_prs("test", "large-repo")

        # Verify basic counts
        self.assertEqual(analysis["total_prs"], 100)
        self.assertEqual(analysis["open_prs"], 33)  # Every 3rd PR is open
        self.assertEqual(analysis["merged_prs"], 34)  # Closed PRs where i % 2 == 0
        self.assertEqual(analysis["closed_prs"], 33)  # Remaining closed PRs (not merged)

        # Verify user statistics (should have 10 PR authors + 5 commenters + 5 reviewers = 20 users)
        # But some users might be both authors and commenters/reviewers, so we expect at least 10
        self.assertGreaterEqual(len(analysis["user_stats"]), 10)

        # Verify that all users have reasonable stats
        for user, stats in analysis["user_stats"].items():
            self.assertGreaterEqual(stats["prs_created"], 0)
            self.assertGreaterEqual(stats["prs_merged"], 0)
            self.assertGreaterEqual(stats["total_comments_received"], 0)
            self.assertGreaterEqual(stats["total_reviews_received"], 0)

        # Verify review and comment stats
        self.assertEqual(len(analysis["review_stats"]), 1)  # Only reviewer1 is used
        self.assertGreaterEqual(len(analysis["comment_stats"]), 1)  # At least commenter1 is used

    def test_workflow_with_edge_cases(self):
        """Test workflow with edge cases and boundary conditions."""
        repository = "test/edge-cases-repo"

        # Edge case: PR with no reviews or comments
        pr1 = self.helper.create_test_pr(1, "closed", True, "lonely_author")

        # Edge case: PR with many reviews and comments
        pr2 = self.helper.create_test_pr(2, "closed", True, "popular_author")

        # Edge case: PR created and merged on the same day
        pr3 = self.helper.create_test_pr(3, "closed", True, "quick_author", 0)

        prs = [pr1, pr2, pr3]

        # Many reviews and comments for PR 2
        reviews = {
            2: [
                self.helper.create_test_review("reviewer1", "APPROVED"),
                self.helper.create_test_review("reviewer2", "COMMENTED"),
                self.helper.create_test_review("reviewer3", "CHANGES_REQUESTED"),
                self.helper.create_test_review("reviewer1", "APPROVED"),  # Second review
            ]
        }

        comments = {
            2: [
                self.helper.create_test_comment("commenter1", "Great work!"),
                self.helper.create_test_comment("commenter2", "I have some questions"),
                self.helper.create_test_comment("commenter3", "This looks good to me"),
                self.helper.create_test_comment("commenter1", "Actually, I found a bug"),
            ]
        }

        review_comments = {
            2: [
                self.helper.create_test_comment("reviewer1", "Line 10: Consider using a constant"),
                self.helper.create_test_comment("reviewer2", "Line 25: This could be optimized"),
                self.helper.create_test_comment("reviewer3", "Line 30: Missing documentation"),
            ]
        }

        self.helper.setup_cached_data(repository, prs, reviews, comments, review_comments)

        # Run analysis
        analysis = self.integration.analyze_repository_prs("test", "edge-cases-repo")

        # Verify basic counts
        self.assertEqual(analysis["total_prs"], 3)
        self.assertEqual(analysis["merged_prs"], 3)
        self.assertEqual(analysis["open_prs"], 0)
        self.assertEqual(analysis["closed_prs"], 0)

        # Verify durations
        self.assertEqual(len(analysis["pr_durations"]), 3)
        self.assertGreater(analysis["pr_durations"][0], 0)  # PR 1 duration
        self.assertGreater(analysis["pr_durations"][1], 0)  # PR 2 duration
        self.assertGreater(analysis["pr_durations"][2], 0)  # PR 3 duration (same day)

        # Verify user stats
        self.helper.assert_user_stats(
            analysis,
            "lonely_author",
            {
                "prs_created": 1,
                "prs_merged": 1,
                "total_comments_received": 0,
                "total_reviews_received": 0,
            },
        )

        self.helper.assert_user_stats(
            analysis,
            "popular_author",
            {
                "prs_created": 1,
                "prs_merged": 1,
                "total_comments_received": 7,  # 4 comments + 3 review comments
                "total_reviews_received": 4,  # 4 reviews
            },
        )

        # Verify review stats
        self.helper.assert_review_stats(analysis, "reviewer1", 2)  # 2 reviews
        self.helper.assert_review_stats(analysis, "reviewer2", 1)  # 1 review
        self.helper.assert_review_stats(analysis, "reviewer3", 1)  # 1 review

        # Verify comment stats
        self.helper.assert_comment_stats(analysis, "commenter1", 2)  # 2 comments
        self.helper.assert_comment_stats(analysis, "commenter2", 1)  # 1 comment
        self.helper.assert_comment_stats(analysis, "commenter3", 1)  # 1 comment

    def test_workflow_error_handling(self):
        """Test workflow error handling and recovery."""
        repository = "test/error-repo"

        # Test with empty repository
        self.helper.setup_cached_data(repository, [])
        analysis = self.integration.analyze_repository_prs("test", "error-repo")

        self.helper.assert_analysis_structure(analysis, repository, 0)
        self.assertEqual(analysis["avg_pr_duration_hours"], 0)
        self.assertEqual(analysis["median_pr_duration_hours"], 0)

        # Test with non-existent repository
        with self.assertRaises(GitHubIntegrationError):
            self.integration.analyze_repository_prs("nonexistent", "repo")

    @patch("gitinspector.github_integration.print")
    def test_workflow_logging(self, mock_print):
        """Test that the workflow logs appropriately."""
        repository = "test/logging-repo"
        prs = [self.helper.create_test_pr(1, "closed", True, "author")]

        self.helper.setup_cached_data(repository, prs)

        # Run analysis
        self.integration.analyze_repository_prs("test", "logging-repo")

        # Verify logging calls
        mock_print.assert_any_call("Analyzing PRs for test/logging-repo...", file=sys.stderr)
        mock_print.assert_any_call("  Processing PR 1/1 (100.0%)", file=sys.stderr)

    def test_workflow_with_mixed_data_types(self):
        """Test workflow with mixed data types and special characters."""
        repository = "test/mixed-data-repo"

        # Create PRs with special characters in titles and usernames
        prs = [
            self.helper.create_test_pr(1, "closed", True, "user-with-dashes"),
            self.helper.create_test_pr(2, "closed", True, "user_with_underscores"),
            self.helper.create_test_pr(3, "closed", True, "user.with.dots"),
        ]

        # Create reviews and comments with special characters
        reviews = {
            1: [self.helper.create_test_review("reviewer-with-dashes", "APPROVED")],
            2: [self.helper.create_test_review("reviewer_with_underscores", "COMMENTED")],
            3: [self.helper.create_test_review("reviewer.with.dots", "CHANGES_REQUESTED")],
        }

        comments = {
            1: [self.helper.create_test_comment("commenter-with-dashes", "Great work! 🎉")],
            2: [self.helper.create_test_comment("commenter_with_underscores", "Needs improvement 😞")],
            3: [self.helper.create_test_comment("commenter.with.dots", "LGTM! 👍")],
        }

        self.helper.setup_cached_data(repository, prs, reviews, comments)

        # Run analysis
        analysis = self.integration.analyze_repository_prs("test", "mixed-data-repo")

        # Verify that special characters are handled correctly
        self.assertEqual(analysis["total_prs"], 3)
        self.assertIn("user-with-dashes", analysis["user_stats"])
        self.assertIn("user_with_underscores", analysis["user_stats"])
        self.assertIn("user.with.dots", analysis["user_stats"])

        self.assertIn("reviewer-with-dashes", analysis["review_stats"])
        self.assertIn("reviewer_with_underscores", analysis["review_stats"])
        self.assertIn("reviewer.with.dots", analysis["review_stats"])

        self.assertIn("commenter-with-dashes", analysis["comment_stats"])
        self.assertIn("commenter_with_underscores", analysis["comment_stats"])
        self.assertIn("commenter.with.dots", analysis["comment_stats"])

    def _verify_realistic_user_stats(self, analysis):
        """Verify user statistics for the realistic data test."""
        self.helper.assert_user_stats(
            analysis,
            "alice",
            {
                "prs_created": 2,
                "prs_merged": 2,
                "total_comments_received": 8,  # 4 comments + 4 review comments on PRs 1 and 3
                "total_reviews_received": 4,  # 2 reviews on PR 1 + 2 reviews on PR 3
            },
        )

        self.helper.assert_user_stats(
            analysis,
            "bob",
            {
                "prs_created": 1,
                "prs_merged": 1,
                "total_comments_received": 2,  # 1 comment + 1 review comment on PR 2
                "total_reviews_received": 1,  # 1 review on PR 2
            },
        )


if __name__ == "__main__":
    unittest.main()
