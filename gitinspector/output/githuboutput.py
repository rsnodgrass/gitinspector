#!/usr/bin/env python3
"""
GitHub Output Module for GitInspector

Formats and outputs GitHub PR analysis data in various formats.
"""

import sys
from typing import Dict, Any
from . import outputable


class GitHubOutput(outputable.Outputable):
    """Output module for GitHub PR analysis data."""

    def __init__(self, github_data: Dict[str, Any]):
        """
        Initialize GitHub output module.

        Args:
            github_data: GitHub analysis data from GitHubIntegration
        """
        self.github_data = github_data

    def output_text(self):
        """Output GitHub data in text format."""
        if not self.github_data:
            print("No GitHub data available")
            return

        print("=" * 80)
        print("GITHUB PULL REQUEST ANALYSIS")
        print("=" * 80)

        # Overall statistics
        overall = self.github_data.get("overall_stats", {})
        print(f"\nOverall Statistics:")
        print(f"  Total Repositories: {self.github_data.get('total_repositories', 0)}")
        print(f"  Total Pull Requests: {overall.get('total_prs', 0)}")
        print(f"  Open PRs: {overall.get('total_open_prs', 0)}")
        print(f"  Merged PRs: {overall.get('total_merged_prs', 0)}")
        print(f"  Total Reviews: {overall.get('total_reviews', 0)}")
        print(f"  Total Comments: {overall.get('total_comments', 0)}")

        if overall.get("avg_pr_duration_hours", 0) > 0:
            avg_hours = overall["avg_pr_duration_hours"]
            avg_days = avg_hours / 24
            print(f"  Average PR Duration: {avg_hours:.1f} hours ({avg_days:.1f} days)")

        # Repository breakdown
        print(f"\nRepository Breakdown:")
        for repo_name, repo_data in self.github_data.get("repositories", {}).items():
            print(f"\n  {repo_name}:")
            print(f"    Total PRs: {repo_data.get('total_prs', 0)}")
            print(f"    Open PRs: {repo_data.get('open_prs', 0)}")
            print(f"    Merged PRs: {repo_data.get('merged_prs', 0)}")

            if repo_data.get("avg_pr_duration_hours", 0) > 0:
                avg_hours = repo_data["avg_pr_duration_hours"]
                avg_days = avg_hours / 24
                print(f"    Average PR Duration: {avg_hours:.1f} hours ({avg_days:.1f} days)")

        # User statistics
        print(f"\nUser Statistics:")
        user_stats = self.github_data.get("user_stats", {})
        if user_stats:
            # Sort by PRs created
            sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["prs_created"], reverse=True)

            for username, stats in sorted_users:
                print(f"\n  {username}:")
                print(f"    PRs Created: {stats['prs_created']}")
                print(f"    PRs Merged: {stats['prs_merged']}")
                print(f"    Comments Received: {stats['total_comments_received']}")
                print(f"    Reviews Received: {stats['total_reviews_received']}")

                if stats["prs_created"] > 0:
                    merge_rate = (stats["prs_merged"] / stats["prs_created"]) * 100
                    print(f"    Merge Rate: {merge_rate:.1f}%")

        # Review statistics
        print(f"\nReview Statistics:")
        review_stats = self.github_data.get("review_stats", {})
        if review_stats:
            # Sort by reviews given
            sorted_reviewers = sorted(review_stats.items(), key=lambda x: x[1]["reviews_given"], reverse=True)

            for username, stats in sorted_reviewers:
                print(f"\n  {username}:")
                print(f"    Reviews Given: {stats['reviews_given']}")
                print(f"    Comments Given: {stats['comments_given']}")

        # Comment statistics
        print(f"\nComment Statistics:")
        comment_stats = self.github_data.get("comment_stats", {})
        if comment_stats:
            # Sort by comments given
            sorted_commenters = sorted(comment_stats.items(), key=lambda x: x[1]["comments_given"], reverse=True)

            for username, stats in sorted_commenters:
                print(f"\n  {username}:")
                print(f"    Comments Given: {stats['comments_given']}")
                print(f"    Comments Received: {stats['comments_received']}")

    def output_html(self):
        """Output GitHub data in HTML format."""
        if not self.github_data:
            print("<p>No GitHub data available</p>")
            return

        overall = self.github_data.get("overall_stats", {})

        html = f"""
        <div class="github-analysis">
            <h2>GitHub Pull Request Analysis</h2>
            
            <div class="overall-stats">
                <h3>Overall Statistics</h3>
                <table class="stats-table">
                    <tr><td>Total Repositories:</td><td>{self.github_data.get('total_repositories', 0)}</td></tr>
                    <tr><td>Total Pull Requests:</td><td>{overall.get('total_prs', 0)}</td></tr>
                    <tr><td>Open PRs:</td><td>{overall.get('total_open_prs', 0)}</td></tr>
                    <tr><td>Merged PRs:</td><td>{overall.get('total_merged_prs', 0)}</td></tr>
                    <tr><td>Total Reviews:</td><td>{overall.get('total_reviews', 0)}</td></tr>
                    <tr><td>Total Comments:</td><td>{overall.get('total_comments', 0)}</td></tr>
        """

        if overall.get("avg_pr_duration_hours", 0) > 0:
            avg_hours = overall["avg_pr_duration_hours"]
            avg_days = avg_hours / 24
            html += f"""
                    <tr><td>Average PR Duration:</td><td>{avg_hours:.1f} hours ({avg_days:.1f} days)</td></tr>
            """

        html += """
                </table>
            </div>
        """

        # Repository breakdown
        html += """
            <div class="repository-breakdown">
                <h3>Repository Breakdown</h3>
                <table class="repo-table">
                    <thead>
                        <tr>
                            <th>Repository</th>
                            <th>Total PRs</th>
                            <th>Open PRs</th>
                            <th>Merged PRs</th>
                            <th>Avg Duration</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for repo_name, repo_data in self.github_data.get("repositories", {}).items():
            avg_duration = "N/A"
            if repo_data.get("avg_pr_duration_hours", 0) > 0:
                avg_hours = repo_data["avg_pr_duration_hours"]
                avg_days = avg_hours / 24
                avg_duration = f"{avg_hours:.1f}h ({avg_days:.1f}d)"

            html += f"""
                        <tr>
                            <td>{repo_name}</td>
                            <td>{repo_data.get('total_prs', 0)}</td>
                            <td>{repo_data.get('open_prs', 0)}</td>
                            <td>{repo_data.get('merged_prs', 0)}</td>
                            <td>{avg_duration}</td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>
            </div>
        """

        # User statistics
        html += """
            <div class="user-stats">
                <h3>User Statistics</h3>
                <table class="user-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>PRs Created</th>
                            <th>PRs Merged</th>
                            <th>Merge Rate</th>
                            <th>Comments Received</th>
                            <th>Reviews Received</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        user_stats = self.github_data.get("user_stats", {})
        if user_stats:
            # Sort by PRs created
            sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["prs_created"], reverse=True)

            for username, stats in sorted_users:
                merge_rate = "N/A"
                if stats["prs_created"] > 0:
                    rate = (stats["prs_merged"] / stats["prs_created"]) * 100
                    merge_rate = f"{rate:.1f}%"

                html += f"""
                        <tr>
                            <td>{username}</td>
                            <td>{stats['prs_created']}</td>
                            <td>{stats['prs_merged']}</td>
                            <td>{merge_rate}</td>
                            <td>{stats['total_comments_received']}</td>
                            <td>{stats['total_reviews_received']}</td>
                        </tr>
                """

        html += """
                    </tbody>
                </table>
            </div>
        """

        # Review statistics
        html += """
            <div class="review-stats">
                <h3>Review Statistics</h3>
                <table class="review-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Reviews Given</th>
                            <th>Comments Given</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        review_stats = self.github_data.get("review_stats", {})
        if review_stats:
            # Sort by reviews given
            sorted_reviewers = sorted(review_stats.items(), key=lambda x: x[1]["reviews_given"], reverse=True)

            for username, stats in sorted_reviewers:
                html += f"""
                        <tr>
                            <td>{username}</td>
                            <td>{stats['reviews_given']}</td>
                            <td>{stats['comments_given']}</td>
                        </tr>
                """

        html += """
                    </tbody>
                </table>
            </div>
        """

        # Comment statistics
        html += """
            <div class="comment-stats">
                <h3>Comment Statistics</h3>
                <table class="comment-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Comments Given</th>
                            <th>Comments Received</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        comment_stats = self.github_data.get("comment_stats", {})
        if comment_stats:
            # Sort by comments given
            sorted_commenters = sorted(comment_stats.items(), key=lambda x: x[1]["comments_given"], reverse=True)

            for username, stats in sorted_commenters:
                html += f"""
                        <tr>
                            <td>{username}</td>
                            <td>{stats['comments_given']}</td>
                            <td>{stats['comments_received']}</td>
                        </tr>
                """

        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """

        print(html)

    def output_json(self):
        """Output GitHub data in JSON format."""
        if not self.github_data:
            print("{}")
            return

        import json

        print(json.dumps(self.github_data, indent=2))

    def output_xml(self):
        """Output GitHub data in XML format."""
        if not self.github_data:
            print("<github_data></github_data>")
            return

        overall = self.github_data.get("overall_stats", {})

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<github_data>
    <overall_stats>
        <total_repositories>{self.github_data.get('total_repositories', 0)}</total_repositories>
        <total_prs>{overall.get('total_prs', 0)}</total_prs>
        <open_prs>{overall.get('total_open_prs', 0)}</open_prs>
        <merged_prs>{overall.get('total_merged_prs', 0)}</merged_prs>
        <total_reviews>{overall.get('total_reviews', 0)}</total_reviews>
        <total_comments>{overall.get('total_comments', 0)}</total_comments>
        <avg_pr_duration_hours>{overall.get('avg_pr_duration_hours', 0):.2f}</avg_pr_duration_hours>
    </overall_stats>
    
    <repositories>
        """

        for repo_name, repo_data in self.github_data.get("repositories", {}).items():
            xml += f"""
        <repository name="{repo_name}">
            <total_prs>{repo_data.get('total_prs', 0)}</total_prs>
            <open_prs>{repo_data.get('open_prs', 0)}</open_prs>
            <merged_prs>{repo_data.get('merged_prs', 0)}</merged_prs>
            <avg_pr_duration_hours>{repo_data.get('avg_pr_duration_hours', 0):.2f}</avg_pr_duration_hours>
        </repository>
            """

        xml += """
    </repositories>
    
    <user_stats>
        """

        for username, stats in self.github_data.get("user_stats", {}).items():
            xml += f"""
        <user name="{username}">
            <prs_created>{stats['prs_created']}</prs_created>
            <prs_merged>{stats['prs_merged']}</prs_merged>
            <total_comments_received>{stats['total_comments_received']}</total_comments_received>
            <total_reviews_received>{stats['total_reviews_received']}</total_reviews_received>
        </user>
            """

        xml += """
    </user_stats>
    
    <review_stats>
        """

        for username, stats in self.github_data.get("review_stats", {}).items():
            xml += f"""
        <user name="{username}">
            <reviews_given>{stats['reviews_given']}</reviews_given>
            <comments_given>{stats['comments_given']}</comments_given>
        </user>
            """

        xml += """
    </review_stats>
    
    <comment_stats>
        """

        for username, stats in self.github_data.get("comment_stats", {}).items():
            xml += f"""
        <user name="{username}">
            <comments_given>{stats['comments_given']}</comments_given>
            <comments_received>{stats['comments_received']}</comments_received>
        </user>
            """

        xml += """
    </comment_stats>
</github_data>
        """

        print(xml)
