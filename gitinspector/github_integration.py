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
import sys
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
from .github_cache import GitHubCache, GitHubCacheError


class GitHubIntegrationError(Exception):
    """Custom exception for GitHub integration errors."""

    pass


class GitHubIntegration:
    """GitHub integration for fetching PR data and statistics."""

    def __init__(
        self,
        app_id: str = None,
        private_key_path: str = None,
        private_key_content: str = None,
        use_cache: bool = True,
        cache_dir: str = ".github_cache",
    ):
        """
        Initialize GitHub integration.

        Args:
            app_id: GitHub App ID (required only if not using cache)
            private_key_path: Path to private key file (required only if not using cache)
            private_key_content: Private key content as string (required only if not using cache)
            use_cache: Whether to use cached data instead of API calls
            cache_dir: Directory for cache files
        """
        self.use_cache = use_cache
        self.cache = GitHubCache(cache_dir) if use_cache else None

        if not use_cache:
            if not app_id:
                raise GitHubIntegrationError("app_id is required when not using cache")

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
                {"Accept": "application/vnd.github.v3+json", "User-Agent": "GitInspector-GitHub-Integration"}
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
            return jwt.encode(payload, private_key, algorithm="RS256")

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

    def _filter_cached_prs(self, prs: List[Dict], state: str, since: str = None, until: str = None) -> List[Dict]:
        """Filter cached PRs by state, since date, and until date."""
        filtered_prs = []

        for pr in prs:
            # Filter by state
            if state != "all" and pr.get("state") != state:
                continue

            # Filter by date range - convert to datetime for proper comparison
            if since or until:
                try:
                    from datetime import datetime, timezone

                    pr_created_str = pr.get("created_at", "")
                    pr_created = datetime.fromisoformat(pr_created_str.replace("Z", "+00:00"))

                    # Parse since date and make it timezone-aware (assume UTC if no timezone)
                    if since:
                        if "T" in since or "Z" in since:
                            since_date = datetime.fromisoformat(since.replace("Z", "+00:00"))
                        else:
                            # If it's just a date like "2025-08-01", assume UTC midnight
                            since_date = datetime.fromisoformat(since + "T00:00:00+00:00")

                        if pr_created < since_date:
                            continue

                    # Parse until date and make it timezone-aware (assume UTC if no timezone)
                    if until:
                        if "T" in until or "Z" in until:
                            until_date = datetime.fromisoformat(until.replace("Z", "+00:00"))
                        else:
                            # If it's just a date like "2025-08-01", assume UTC end of day
                            until_date = datetime.fromisoformat(until + "T23:59:59+00:00")

                        if pr_created > until_date:
                            continue

                except (ValueError, TypeError):
                    # If date parsing fails, skip this PR
                    continue

            filtered_prs.append(pr)

        return filtered_prs

    def _fetch_prs_from_api(self, owner: str, repo: str, state: str, since: str = None) -> List[Dict]:
        """Fetch PRs from GitHub API."""
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

    def get_pull_requests(
        self, owner: str, repo: str, state: str = "all", since: str = None, until: str = None
    ) -> List[Dict]:
        """
        Get pull requests for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            since: ISO 8601 timestamp to filter PRs created after this time
            until: ISO 8601 timestamp to filter PRs created before this time

        Returns:
            List of pull request data
        """
        repository = f"{owner}/{repo}"

        # If using cache, try to get from cache first
        if self.use_cache and self.cache.is_repository_cached(repository):
            cached_prs = self.cache.get_cached_pull_requests(repository)
            if cached_prs is not None:
                return self._filter_cached_prs(cached_prs, state, since, until)

        # If not using cache, fetch from API
        if not self.use_cache:
            return self._fetch_prs_from_api(owner, repo, state, since)

        raise GitHubIntegrationError(f"No cached data available for {repository}. Run the sync script first.")

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get reviews for a specific pull request."""
        repository = f"{owner}/{repo}"

        # If using cache, try to get from cache first
        if self.use_cache and self.cache.is_repository_cached(repository):
            return self.cache.get_cached_reviews(repository, pr_number)

        # If not using cache, fetch from API
        if not self.use_cache:
            try:
                return self._make_authenticated_request(owner, repo, f"pulls/{pr_number}/reviews")
            except GitHubIntegrationError as e:
                if "404" in str(e):
                    # No reviews exist for this PR - this is normal
                    return []
                # Re-raise other errors
                raise

        raise GitHubIntegrationError(f"No cached data available for {repository}. Run the sync script first.")

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get comments for a specific pull request."""
        repository = f"{owner}/{repo}"

        # If using cache, try to get from cache first
        if self.use_cache and self.cache.is_repository_cached(repository):
            return self.cache.get_cached_comments(repository, pr_number)

        # If not using cache, fetch from API
        if not self.use_cache:
            try:
                return self._make_authenticated_request(owner, repo, f"pulls/{pr_number}/comments")
            except GitHubIntegrationError as e:
                if "404" in str(e):
                    # No comments exist for this PR - this is normal
                    return []
                # Re-raise other errors
                raise

        raise GitHubIntegrationError(f"No cached data available for {repository}. Run the sync script first.")

    def get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get review comments for a specific pull request."""
        repository = f"{owner}/{repo}"

        # If using cache, try to get from cache first
        if self.use_cache and self.cache.is_repository_cached(repository):
            return self.cache.get_cached_review_comments(repository, pr_number)

        # If not using cache, fetch from API
        if not self.use_cache:
            try:
                return self._make_authenticated_request(owner, repo, f"pulls/{pr_number}/reviews/comments")
            except GitHubIntegrationError as e:
                if "404" in str(e):
                    # No review comments exist for this PR - this is normal
                    return []
                # Re-raise other errors
                raise

        raise GitHubIntegrationError(f"No cached data available for {repository}. Run the sync script first.")

    def get_pr_general_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get general PR comments (issue comments) for a specific pull request."""
        repository = f"{owner}/{repo}"

        # If using cache, try to get from cache first
        if self.use_cache and self.cache.is_repository_cached(repository):
            return self.cache.get_cached_general_comments(repository, pr_number)

        # If not using cache, fetch from API
        if not self.use_cache:
            try:
                return self._make_authenticated_request(owner, repo, f"issues/{pr_number}/comments")
            except GitHubIntegrationError as e:
                if "404" in str(e):
                    # No general comments exist for this PR - this is normal
                    return []
                # Re-raise other errors
                raise

        raise GitHubIntegrationError(f"No cached data available for {repository}. Run the sync script first.")

    def analyze_repository_prs(self, owner: str, repo: str, since: str = None, until: str = None) -> Dict:
        """
        Analyze PR data for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            since: ISO 8601 timestamp to filter PRs created after this time
            until: ISO 8601 timestamp to filter PRs created before this time

        Returns:
            Dictionary containing PR analysis data
        """
        self._log_analysis_start(owner, repo)

        # Get all PRs
        prs = self.get_pull_requests(owner, repo, since=since, until=until)

        # Initialize analysis structure
        analysis = self._initialize_analysis_structure(f"{owner}/{repo}")

        # Process each PR
        self._process_prs(owner, repo, prs, analysis)

        # Calculate final statistics
        self._calculate_final_statistics(analysis)

        return analysis

    def _log_analysis_start(self, owner: str, repo: str) -> None:
        """Log the start of analysis for a repository."""
        print(f"Analyzing PRs for {owner}/{repo}...", file=os.sys.stderr)

    def _initialize_analysis_structure(self, repository: str) -> Dict:
        """Initialize the analysis data structure."""
        return {
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

    def _process_prs(self, owner: str, repo: str, prs: List[Dict], analysis: Dict) -> None:
        """Process all PRs and update analysis data."""
        total_prs = len(prs)
        analysis["total_prs"] = total_prs

        for i, pr in enumerate(prs, 1):
            self._show_progress(i, total_prs)
            self._process_single_pr(owner, repo, pr, analysis)
            self._apply_rate_limiting()

    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting between PR processing."""
        time.sleep(0.1)  # Rate limiting

    def _show_progress(self, current: int, total: int) -> None:
        """Show progress for PR processing."""
        if current % 10 == 0 or current == total:
            print(f"  Processing PR {current}/{total} ({(current/total)*100:.1f}%)", file=os.sys.stderr)

    def _process_single_pr(self, owner: str, repo: str, pr: Dict, analysis: Dict) -> None:
        """Process a single PR and update analysis data."""
        # Process basic PR information
        self._process_pr_basic_info(pr, analysis)

        # Process user statistics
        self._process_pr_user_stats(pr, analysis)

        # Get and process reviews and comments
        pr_data = self._fetch_pr_related_data(owner, repo, pr["number"])
        self._process_pr_related_data(pr, pr_data, analysis)

    def _fetch_pr_related_data(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Fetch all data related to a PR (reviews, comments, review comments)."""
        return {
            "reviews": self.get_pr_reviews(owner, repo, pr_number),
            "comments": self.get_pr_comments(owner, repo, pr_number),
            "review_comments": self.get_pr_review_comments(owner, repo, pr_number),
            "general_comments": self.get_pr_general_comments(owner, repo, pr_number),
        }

    def _process_pr_related_data(self, pr: Dict, pr_data: Dict, analysis: Dict) -> None:
        """Process all data related to a PR (reviews, comments, etc.)."""
        reviews = pr_data["reviews"]
        comments = pr_data["comments"]
        review_comments = pr_data["review_comments"]
        general_comments = pr_data["general_comments"]

        # Process comment statistics first
        self._process_comment_stats(pr, comments, review_comments, general_comments, analysis)

        # Process review statistics (after comment stats so comments_given is available)
        self._process_review_stats(reviews, analysis)

        # Update reviews received for PR author
        author = pr["user"]["login"]
        analysis["user_stats"][author]["total_reviews_received"] += len(reviews)

    def _process_pr_basic_info(self, pr: Dict, analysis: Dict) -> None:
        """Process basic PR information (state, duration)."""
        if pr["state"] == "open":
            analysis["open_prs"] += 1
        elif pr["merged_at"]:
            analysis["merged_prs"] += 1
            duration_hours = self._calculate_pr_duration(pr)
            analysis["pr_durations"].append(duration_hours)
        else:
            analysis["closed_prs"] += 1

    def _calculate_pr_duration(self, pr: Dict) -> float:
        """Calculate PR duration in hours."""
        created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        return (merged_at - created_at).total_seconds() / 3600

    def _process_pr_user_stats(self, pr: Dict, analysis: Dict) -> None:
        """Process user statistics for a PR."""
        author = pr["user"]["login"]
        self._ensure_user_in_stats(author, analysis["user_stats"])

        analysis["user_stats"][author]["prs_created"] += 1
        if pr["merged_at"]:
            analysis["user_stats"][author]["prs_merged"] += 1

    def _ensure_user_in_stats(self, user: str, user_stats: Dict) -> None:
        """Ensure user exists in user_stats with default values."""
        if user not in user_stats:
            user_stats[user] = {
                "prs_created": 0,
                "prs_merged": 0,
                "total_comments_received": 0,
                "total_reviews_received": 0,
            }

    def _process_review_stats(self, reviews: List[Dict], analysis: Dict) -> None:
        """Process review statistics."""
        for review in reviews:
            reviewer = review["user"]["login"]
            if reviewer not in analysis["review_stats"]:
                analysis["review_stats"][reviewer] = {"reviews_given": 0, "comments_given": 0}
            analysis["review_stats"][reviewer]["reviews_given"] += 1

            # Count comments given by this reviewer
            if reviewer in analysis["comment_stats"]:
                analysis["review_stats"][reviewer]["comments_given"] = analysis["comment_stats"][reviewer][
                    "comments_given"
                ]

    def _process_comment_stats(
        self, pr: Dict, comments: List[Dict], review_comments: List[Dict], general_comments: List[Dict], analysis: Dict
    ) -> None:
        """Process comment statistics."""
        author = pr["user"]["login"]
        all_comments = comments + review_comments + general_comments

        # Process individual comments
        for comment in all_comments:
            commenter = comment["user"]["login"]
            self._ensure_commenter_in_stats(commenter, analysis)
            analysis["comment_stats"][commenter]["comments_given"] += 1

        # Update comments received for PR author
        self._update_author_comment_stats(author, all_comments, analysis)

    def _ensure_commenter_in_stats(self, commenter: str, analysis: Dict) -> None:
        """Ensure commenter exists in both comment_stats and user_stats."""
        if commenter not in analysis["comment_stats"]:
            analysis["comment_stats"][commenter] = {"comments_given": 0, "comments_received": 0}

        self._ensure_user_in_stats(commenter, analysis["user_stats"])

    def _update_author_comment_stats(self, author: str, all_comments: List[Dict], analysis: Dict) -> None:
        """Update comment statistics for PR author."""
        # Ensure author exists in user_stats
        self._ensure_user_in_stats(author, analysis["user_stats"])

        analysis["user_stats"][author]["total_comments_received"] += len(all_comments)

        if author not in analysis["comment_stats"]:
            analysis["comment_stats"][author] = {"comments_given": 0, "comments_received": 0}
        analysis["comment_stats"][author]["comments_received"] += len(all_comments)

    def _calculate_final_statistics(self, analysis: Dict) -> None:
        """Calculate final statistics (averages, medians)."""
        if analysis["pr_durations"]:
            analysis["avg_pr_duration_hours"] = sum(analysis["pr_durations"]) / len(analysis["pr_durations"])
            analysis["median_pr_duration_hours"] = sorted(analysis["pr_durations"])[len(analysis["pr_durations"]) // 2]
        else:
            analysis["avg_pr_duration_hours"] = 0
            analysis["median_pr_duration_hours"] = 0

    def analyze_multiple_repositories(self, repositories: List[str], since: str = None, until: str = None) -> Dict:
        """
        Analyze PR data for multiple repositories.

        Args:
            repositories: List of repositories in format "owner/repo"
            since: ISO 8601 timestamp to filter PRs created after this time
            until: ISO 8601 timestamp to filter PRs created before this time

        Returns:
            Dictionary containing combined analysis data
        """
        # Try to get cached results first
        if cached_results := self._try_get_cached_results(repositories, since, until):
            return cached_results

        # Initialize combined analysis structure
        combined_analysis = self._initialize_combined_analysis_structure(len(repositories))

        # Process each repository
        self._process_repositories(repositories, since, until, combined_analysis)

        # Calculate final combined statistics
        self._calculate_combined_statistics(combined_analysis)

        # Cache the results for future use
        self._cache_analysis_results(repositories, since, until, combined_analysis)

        return combined_analysis

    def _try_get_cached_results(self, repositories: List[str], since: str, until: str = None) -> Dict:
        """Try to get cached results for the repositories."""
        if not (self.use_cache and self.cache):
            return None

        from .github_results_cache import GitHubResultsCache

        results_cache = GitHubResultsCache(self.cache.cache_dir)

        # Get cache timestamps for validation
        cache_timestamps = self._get_cache_timestamps(repositories)

        # Try to get cached results
        if cached_results := results_cache.get_cached_results(repositories, since, until, cache_timestamps):
            print(f"Using cached analysis results for {len(repositories)} repositories", file=sys.stderr)
            return cached_results

        return None

    def _get_cache_timestamps(self, repositories: List[str]) -> Dict[str, str]:
        """Get cache timestamps for the given repositories."""
        cache_timestamps = {}
        for repo in repositories:
            if self.cache.is_repository_cached(repo):
                all_metadata = self.cache.get_cache_metadata()
                repo_metadata = all_metadata.get("repositories", {}).get(repo, {})
                if repo_metadata and "last_sync" in repo_metadata:
                    cache_timestamps[repo] = repo_metadata["last_sync"]
        return cache_timestamps

    def _initialize_combined_analysis_structure(self, total_repositories: int) -> Dict:
        """Initialize the combined analysis data structure."""
        return {
            "total_repositories": total_repositories,
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

    def _process_repositories(self, repositories: List[str], since: str, until: str, combined_analysis: Dict) -> None:
        """Process all repositories and aggregate their analysis data."""
        for repo in repositories:
            try:
                owner, repo_name = repo.split("/", 1)
                analysis = self.analyze_repository_prs(owner, repo_name, since, until)

                combined_analysis["repositories"][repo] = analysis
                self._aggregate_repository_analysis(analysis, combined_analysis)

            except Exception as e:
                print(f"Error analyzing repository {repo}: {str(e)}", file=os.sys.stderr)
                continue

    def _aggregate_repository_analysis(self, analysis: Dict, combined_analysis: Dict) -> None:
        """Aggregate a single repository's analysis into the combined analysis."""
        # Aggregate overall stats
        self._aggregate_overall_stats(analysis, combined_analysis)

        # Aggregate user stats
        self._aggregate_user_stats(analysis, combined_analysis)

        # Aggregate review stats
        self._aggregate_review_stats(analysis, combined_analysis)

        # Aggregate comment stats
        self._aggregate_comment_stats(analysis, combined_analysis)

    def _aggregate_overall_stats(self, analysis: Dict, combined_analysis: Dict) -> None:
        """Aggregate overall statistics."""
        combined_analysis["overall_stats"]["total_prs"] += analysis["total_prs"]
        combined_analysis["overall_stats"]["total_open_prs"] += analysis["open_prs"]
        combined_analysis["overall_stats"]["total_merged_prs"] += analysis["merged_prs"]

    def _aggregate_user_stats(self, analysis: Dict, combined_analysis: Dict) -> None:
        """Aggregate user statistics."""
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
            combined_analysis["user_stats"][user]["total_comments_received"] += stats["total_comments_received"]
            combined_analysis["user_stats"][user]["total_reviews_received"] += stats["total_reviews_received"]

    def _aggregate_review_stats(self, analysis: Dict, combined_analysis: Dict) -> None:
        """Aggregate review statistics."""
        for user, stats in analysis["review_stats"].items():
            if user not in combined_analysis["review_stats"]:
                combined_analysis["review_stats"][user] = {"reviews_given": 0, "comments_given": 0}

            combined_analysis["review_stats"][user]["reviews_given"] += stats["reviews_given"]
            combined_analysis["review_stats"][user]["comments_given"] += stats["comments_given"]

    def _aggregate_comment_stats(self, analysis: Dict, combined_analysis: Dict) -> None:
        """Aggregate comment statistics."""
        for user, stats in analysis["comment_stats"].items():
            if user not in combined_analysis["comment_stats"]:
                combined_analysis["comment_stats"][user] = {"comments_given": 0, "comments_received": 0}

            combined_analysis["comment_stats"][user]["comments_given"] += stats["comments_given"]
            combined_analysis["comment_stats"][user]["comments_received"] += stats["comments_received"]

    def _calculate_combined_statistics(self, combined_analysis: Dict) -> None:
        """Calculate final combined statistics."""
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

    def _cache_analysis_results(
        self, repositories: List[str], since: str, until: str, combined_analysis: Dict
    ) -> None:
        """Cache the analysis results for future use."""
        if not (self.use_cache and self.cache):
            return

        from .github_results_cache import GitHubResultsCache

        results_cache = GitHubResultsCache(self.cache.cache_dir)

        # Get cache timestamps for validation
        cache_timestamps = self._get_cache_timestamps(repositories)

        # Cache the results
        results_cache.cache_results(repositories, combined_analysis, since, until, cache_timestamps)
        print(f"Cached analysis results for {len(repositories)} repositories", file=sys.stderr)


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
    if private_key_path := os.getenv("GITHUB_PRIVATE_KEY_PATH"):
        if not os.path.exists(private_key_path):
            raise GitHubIntegrationError(f"Private key file not found: {private_key_path}")
        return app_id, private_key_path

    # Try private key content
    if private_key_content := os.getenv("GITHUB_PRIVATE_KEY"):
        return app_id, private_key_content

    raise GitHubIntegrationError("Either GITHUB_PRIVATE_KEY_PATH or GITHUB_PRIVATE_KEY must be set")
