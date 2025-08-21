#!/usr/bin/env python3
"""
GitHub Integration Module for GitInspector

Fetches Pull Request data from GitHub repositories including:
- PR open duration (creation to merge)
- Review counts per user
- Comment counts on PRs
- Comments made by users on others' PRs
"""

import os
import base64
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import jwt


class GitHubIntegrationError(Exception):
    """Custom exception for GitHub integration errors."""

    pass


class GitHubIntegration:
    """GitHub integration for fetching PR data and statistics."""

    def __init__(self, app_id: str, private_key_path: str = None, private_key_content: str = None):
        """
        Initialize GitHub integration.

        Args:
            app_id: GitHub App ID
            private_key_path: Path to private key file
            private_key_content: Private key content as string
        """
        self.app_id = app_id
        self.api_base_url = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
        self.api_version = os.getenv("GITHUB_API_VERSION", "2022-11-28")

        # Load private key
        if private_key_path:
            with open(private_key_path, "r") as f:
                self.private_key = f.read()
        elif private_key_content:
            self.private_key = private_key_content
        else:
            raise GitHubIntegrationError("Either private_key_path or private_key_content must be provided")

        # Initialize session
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": f"application/vnd.github.v3+json", "User-Agent": "GitInspector-GitHub-Integration"}
        )

        # Cache for installation tokens
        self._installation_tokens = {}

    def _create_jwt(self) -> str:
        """Create a JWT token for GitHub App authentication."""
        try:
            # Parse the private key
            private_key = serialization.load_pem_private_key(self.private_key.encode("utf-8"), password=None)

            # Create JWT payload
            now = int(time.time())
            payload = {"iat": now, "exp": now + 600, "iss": self.app_id}  # 10 minutes

            # Sign the JWT
            token = jwt.encode(payload, private_key, algorithm="RS256")
            return token

        except Exception as e:
            raise GitHubIntegrationError(f"Failed to create JWT: {str(e)}")

    def _get_installation_token(self, owner: str, repo: str) -> str:
        """Get installation token for a specific repository."""
        cache_key = f"{owner}/{repo}"

        # Check if we have a cached token that's still valid
        if cache_key in self._installation_tokens:
            token_data = self._installation_tokens[cache_key]
            if token_data["expires_at"] > datetime.now(timezone.utc):
                return token_data["token"]

        # Create JWT for app authentication
        jwt_token = self._create_jwt()

        # Get installation ID
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = self.session.get(f"{self.api_base_url}/repos/{owner}/{repo}/installation", headers=headers)

        if response.status_code != 200:
            raise GitHubIntegrationError(f"Failed to get installation: {response.status_code} - {response.text}")

        installation_id = response.json()["id"]

        # Get installation token
        response = self.session.post(
            f"{self.api_base_url}/app/installations/{installation_id}/access_tokens", headers=headers
        )

        if response.status_code != 201:
            raise GitHubIntegrationError(f"Failed to get installation token: {response.status_code} - {response.text}")

        token_data = response.json()
        expires_at = datetime.fromisoformat(token_data["expires_at"].replace("Z", "+00:00"))

        # Cache the token
        self._installation_tokens[cache_key] = {"token": token_data["token"], "expires_at": expires_at}

        return token_data["token"]

    def _make_authenticated_request(self, owner: str, repo: str, endpoint: str, params: Dict = None) -> Dict:
        """Make an authenticated request to GitHub API."""
        token = self._get_installation_token(owner, repo)
        headers = {"Authorization": f"token {token}"}

        url = f"{self.api_base_url}/repos/{owner}/{repo}/{endpoint}"
        response = self.session.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise GitHubIntegrationError(f"GitHub API request failed: {response.status_code} - {response.text}")

        return response.json()

    def get_pull_requests(self, owner: str, repo: str, state: str = "all", since: str = None) -> List[Dict]:
        """
        Get pull requests for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            since: ISO 8601 timestamp to filter PRs created after this time

        Returns:
            List of pull request data
        """
        params = {"state": state, "per_page": 100}
        if since:
            params["since"] = since

        prs = []
        page = 1

        while True:
            params["page"] = page
            data = self._make_authenticated_request(owner, repo, "pulls", params)

            if not data:  # No more PRs
                break

            prs.extend(data)
            page += 1

            # Rate limiting - be respectful
            if "X-RateLimit-Remaining" in self.session.headers:
                remaining = int(self.session.headers["X-RateLimit-Remaining"])
                if remaining < 10:
                    time.sleep(60)  # Wait a minute if rate limit is low

        return prs

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get reviews for a specific pull request."""
        return self._make_authenticated_request(owner, repo, f"pulls/{pr_number}/reviews")

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get comments for a specific pull request."""
        return self._make_authenticated_request(owner, repo, f"pulls/{pr_number}/comments")

    def get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get review comments for a specific pull request."""
        return self._make_authenticated_request(owner, repo, f"pulls/{pr_number}/reviews/comments")

    def analyze_repository_prs(self, owner: str, repo: str, since: str = None) -> Dict:
        """
        Analyze PR data for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            since: ISO 8601 timestamp to filter PRs

        Returns:
            Dictionary containing PR analysis data
        """
        print(f"Analyzing PRs for {owner}/{repo}...", file=os.sys.stderr)

        # Get all PRs
        prs = self.get_pull_requests(owner, repo, since=since)

        analysis = {
            "repository": f"{owner}/{repo}",
            "total_prs": len(prs),
            "open_prs": 0,
            "closed_prs": 0,
            "merged_prs": 0,
            "pr_durations": [],
            "user_stats": {},
            "review_stats": {},
            "comment_stats": {},
        }

        for pr in prs:
            # Basic PR info
            if pr["state"] == "open":
                analysis["open_prs"] += 1
            elif pr["merged_at"]:
                analysis["merged_prs"] += 1
                # Calculate duration for merged PRs
                created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                duration_hours = (merged_at - created_at).total_seconds() / 3600
                analysis["pr_durations"].append(duration_hours)
            else:
                analysis["closed_prs"] += 1

            # User statistics
            author = pr["user"]["login"]
            if author not in analysis["user_stats"]:
                analysis["user_stats"][author] = {
                    "prs_created": 0,
                    "prs_merged": 0,
                    "total_comments_received": 0,
                    "total_reviews_received": 0,
                }

            analysis["user_stats"][author]["prs_created"] += 1
            if pr["merged_at"]:
                analysis["user_stats"][author]["prs_merged"] += 1

            # Get reviews and comments
            try:
                reviews = self.get_pr_reviews(owner, repo, pr["number"])
                comments = self.get_pr_comments(owner, repo, pr["number"])
                review_comments = self.get_pr_review_comments(owner, repo, pr["number"])

                # Review statistics
                for review in reviews:
                    reviewer = review["user"]["login"]
                    if reviewer not in analysis["review_stats"]:
                        analysis["review_stats"][reviewer] = {"reviews_given": 0, "comments_given": 0}

                    analysis["review_stats"][reviewer]["reviews_given"] += 1

                # Comment statistics
                all_comments = comments + review_comments
                for comment in all_comments:
                    commenter = comment["user"]["login"]
                    if commenter not in analysis["comment_stats"]:
                        analysis["comment_stats"][commenter] = {"comments_given": 0, "comments_received": 0}

                    analysis["comment_stats"][commenter]["comments_given"] += 1
                    analysis["user_stats"][author]["total_comments_received"] += 1

                # Count reviews received
                analysis["user_stats"][author]["total_reviews_received"] += len(reviews)

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"Warning: Could not fetch details for PR #{pr['number']}: {str(e)}", file=os.sys.stderr)
                continue

        # Calculate averages
        if analysis["pr_durations"]:
            analysis["avg_pr_duration_hours"] = sum(analysis["pr_durations"]) / len(analysis["pr_durations"])
            analysis["median_pr_duration_hours"] = sorted(analysis["pr_durations"])[len(analysis["pr_durations"]) // 2]
        else:
            analysis["avg_pr_duration_hours"] = 0
            analysis["median_pr_duration_hours"] = 0

        return analysis

    def analyze_multiple_repositories(self, repositories: List[str], since: str = None) -> Dict:
        """
        Analyze PR data for multiple repositories.

        Args:
            repositories: List of repositories in format "owner/repo"
            since: ISO 8601 timestamp to filter PRs

        Returns:
            Dictionary containing combined analysis data
        """
        combined_analysis = {
            "total_repositories": len(repositories),
            "repositories": {},
            "overall_stats": {
                "total_prs": 0,
                "total_open_prs": 0,
                "total_merged_prs": 0,
                "avg_pr_duration_hours": 0,
                "total_reviews": 0,
                "total_comments": 0,
            },
            "user_stats": {},
            "review_stats": {},
            "comment_stats": {},
        }

        for repo in repositories:
            try:
                owner, repo_name = repo.split("/", 1)
                analysis = self.analyze_repository_prs(owner, repo_name, since)

                combined_analysis["repositories"][repo] = analysis

                # Aggregate overall stats
                combined_analysis["overall_stats"]["total_prs"] += analysis["total_prs"]
                combined_analysis["overall_stats"]["total_open_prs"] += analysis["open_prs"]
                combined_analysis["overall_stats"]["total_merged_prs"] += analysis["merged_prs"]

                # Aggregate user stats
                for user, stats in analysis["user_stats"].items():
                    if user not in combined_analysis["user_stats"]:
                        combined_analysis["user_stats"][user] = {
                            "prs_created": 0,
                            "prs_merged": 0,
                            "total_comments_received": 0,
                            "total_reviews_received": 0,
                        }

                    combined_analysis["user_stats"][user]["prs_created"] += stats["prs_created"]
                    combined_analysis["user_stats"][user]["prs_merged"] += stats["prs_merged"]
                    combined_analysis["user_stats"][user]["total_comments_received"] += stats[
                        "total_comments_received"
                    ]
                    combined_analysis["user_stats"][user]["total_reviews_received"] += stats["total_reviews_received"]

                # Aggregate review stats
                for user, stats in analysis["review_stats"].items():
                    if user not in combined_analysis["review_stats"]:
                        combined_analysis["review_stats"][user] = {"reviews_given": 0, "comments_given": 0}

                    combined_analysis["review_stats"][user]["reviews_given"] += stats["reviews_given"]
                    combined_analysis["review_stats"][user]["comments_given"] += stats["comments_given"]

                # Aggregate comment stats
                for user, stats in analysis["comment_stats"].items():
                    if user not in combined_analysis["comment_stats"]:
                        combined_analysis["comment_stats"][user] = {"comments_given": 0, "comments_received": 0}

                    combined_analysis["comment_stats"][user]["comments_given"] += stats["comments_given"]
                    combined_analysis["comment_stats"][user]["comments_received"] += stats["comments_received"]

            except Exception as e:
                print(f"Error analyzing repository {repo}: {str(e)}", file=os.sys.stderr)
                continue

        # Calculate overall averages
        total_durations = []
        for repo_analysis in combined_analysis["repositories"].values():
            total_durations.extend(repo_analysis["pr_durations"])

        if total_durations:
            combined_analysis["overall_stats"]["avg_pr_duration_hours"] = sum(total_durations) / len(total_durations)

        # Count total reviews and comments
        combined_analysis["overall_stats"]["total_reviews"] = sum(
            stats["reviews_given"] for stats in combined_analysis["review_stats"].values()
        )
        combined_analysis["overall_stats"]["total_comments"] = sum(
            stats["comments_given"] for stats in combined_analysis["comment_stats"].values()
        )

        return combined_analysis


def load_github_config() -> Tuple[str, str]:
    """
    Load GitHub configuration from environment variables.

    Returns:
        Tuple of (app_id, private_key)

    Raises:
        GitHubIntegrationError: If configuration is missing or invalid
    """
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        raise GitHubIntegrationError("GITHUB_APP_ID environment variable not set")

    # Try private key path first
    private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    if private_key_path:
        if not os.path.exists(private_key_path):
            raise GitHubIntegrationError(f"Private key file not found: {private_key_path}")
        return app_id, private_key_path

    # Try private key content
    private_key_content = os.getenv("GITHUB_PRIVATE_KEY")
    if private_key_content:
        return app_id, private_key_content

    raise GitHubIntegrationError("Either GITHUB_PRIVATE_KEY_PATH or GITHUB_PRIVATE_KEY must be set")
