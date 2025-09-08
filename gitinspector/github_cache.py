#!/usr/bin/env python3
"""
GitHub Cache Module for GitInspector

Provides caching functionality for GitHub data to avoid repeated API calls.
Uses JSON files to store cached data locally.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path


class GitHubCacheError(Exception):
    """Custom exception for GitHub cache errors."""

    pass


class GitHubCache:
    """GitHub data cache using JSON files."""

    def __init__(self, cache_dir: str = ".github_cache"):
        """
        Initialize GitHub cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache file paths
        self.metadata_file = self.cache_dir / "metadata.json"
        self.prs_file = self.cache_dir / "pull_requests.json"
        self.reviews_file = self.cache_dir / "reviews.json"
        self.comments_file = self.cache_dir / "comments.json"
        self.review_comments_file = self.cache_dir / "review_comments.json"

    def _load_json_file(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise GitHubCacheError(f"Failed to load cache file {file_path}: {str(e)}")

    def _save_json_file(self, file_path: Path, data: Dict) -> None:
        """Save JSON data to file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise GitHubCacheError(f"Failed to save cache file {file_path}: {str(e)}")

    def get_cache_metadata(self) -> Dict:
        """Get cache metadata including last sync times."""
        return self._load_json_file(self.metadata_file)

    def update_cache_metadata(self, repository: str, last_sync: str = None) -> None:
        """Update cache metadata for a repository."""
        metadata = self.get_cache_metadata()

        if last_sync is None:
            last_sync = datetime.now(timezone.utc).isoformat()

        if "repositories" not in metadata:
            metadata["repositories"] = {}

        metadata["repositories"][repository] = {
            "last_sync": last_sync,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        self._save_json_file(self.metadata_file, metadata)

    def is_repository_cached(self, repository: str) -> bool:
        """Check if repository data is cached."""
        metadata = self.get_cache_metadata()
        return repository in metadata.get("repositories", {})

    def get_last_sync_time(self, repository: str) -> Optional[str]:
        """Get last sync time for a repository."""
        metadata = self.get_cache_metadata()
        repo_data = metadata.get("repositories", {}).get(repository)
        return repo_data.get("last_sync") if repo_data else None

    def cache_pull_requests(self, repository: str, prs: List[Dict]) -> None:
        """Cache pull requests for a repository."""
        prs_data = self._load_json_file(self.prs_file)
        prs_data[repository] = prs
        self._save_json_file(self.prs_file, prs_data)

    def get_cached_pull_requests(self, repository: str) -> List[Dict]:
        """Get cached pull requests for a repository."""
        prs_data = self._load_json_file(self.prs_file)
        return prs_data.get(repository, [])

    def cache_reviews(self, repository: str, pr_number: int, reviews: List[Dict]) -> None:
        """Cache reviews for a specific PR."""
        reviews_data = self._load_json_file(self.reviews_file)

        if repository not in reviews_data:
            reviews_data[repository] = {}

        reviews_data[repository][str(pr_number)] = reviews
        self._save_json_file(self.reviews_file, reviews_data)

    def get_cached_reviews(self, repository: str, pr_number: int) -> List[Dict]:
        """Get cached reviews for a specific PR."""
        reviews_data = self._load_json_file(self.reviews_file)
        return reviews_data.get(repository, {}).get(str(pr_number), [])

    def cache_comments(self, repository: str, pr_number: int, comments: List[Dict]) -> None:
        """Cache comments for a specific PR."""
        comments_data = self._load_json_file(self.comments_file)

        if repository not in comments_data:
            comments_data[repository] = {}

        comments_data[repository][str(pr_number)] = comments
        self._save_json_file(self.comments_file, comments_data)

    def get_cached_comments(self, repository: str, pr_number: int) -> List[Dict]:
        """Get cached comments for a specific PR."""
        comments_data = self._load_json_file(self.comments_file)
        return comments_data.get(repository, {}).get(str(pr_number), [])

    def cache_review_comments(self, repository: str, pr_number: int, review_comments: List[Dict]) -> None:
        """Cache review comments for a specific PR."""
        review_comments_data = self._load_json_file(self.review_comments_file)

        if repository not in review_comments_data:
            review_comments_data[repository] = {}

        review_comments_data[repository][str(pr_number)] = review_comments
        self._save_json_file(self.review_comments_file, review_comments_data)

    def get_cached_review_comments(self, repository: str, pr_number: int) -> List[Dict]:
        """Get cached review comments for a specific PR."""
        review_comments_data = self._load_json_file(self.review_comments_file)
        return review_comments_data.get(repository, {}).get(str(pr_number), [])

    def clear_repository_cache(self, repository: str) -> None:
        """Clear all cached data for a repository."""
        # Clear PRs
        prs_data = self._load_json_file(self.prs_file)
        if repository in prs_data:
            del prs_data[repository]
            self._save_json_file(self.prs_file, prs_data)

        # Clear reviews
        reviews_data = self._load_json_file(self.reviews_file)
        if repository in reviews_data:
            del reviews_data[repository]
            self._save_json_file(self.reviews_file, reviews_data)

        # Clear comments
        comments_data = self._load_json_file(self.comments_file)
        if repository in comments_data:
            del comments_data[repository]
            self._save_json_file(self.comments_file, comments_data)

        # Clear review comments
        review_comments_data = self._load_json_file(self.review_comments_file)
        if repository in review_comments_data:
            del review_comments_data[repository]
            self._save_json_file(self.review_comments_file, review_comments_data)

        # Clear metadata
        metadata = self.get_cache_metadata()
        if "repositories" in metadata and repository in metadata["repositories"]:
            del metadata["repositories"][repository]
            self._save_json_file(self.metadata_file, metadata)

    def clear_all_cache(self) -> None:
        """Clear all cached data."""
        for file_path in [
            self.metadata_file,
            self.prs_file,
            self.reviews_file,
            self.comments_file,
            self.review_comments_file,
        ]:
            if file_path.exists():
                file_path.unlink()

    def get_cache_size(self) -> Dict[str, int]:
        """Get cache size information."""
        return {
            name: file_path.stat().st_size if file_path.exists() else 0
            for name, file_path in [
                ("metadata", self.metadata_file),
                ("pull_requests", self.prs_file),
                ("reviews", self.reviews_file),
                ("comments", self.comments_file),
                ("review_comments", self.review_comments_file),
            ]
        }

    def get_cached_repositories(self) -> List[str]:
        """Get list of cached repositories."""
        metadata = self.get_cache_metadata()
        return list(metadata.get("repositories", {}).keys())

    def get_latest_pr_update_time(self, repository: str) -> Optional[str]:
        """Get the latest updated_at timestamp from cached PRs for a repository."""
        prs = self.get_cached_pull_requests(repository)
        if not prs:
            return None

        # Find the latest updated_at timestamp
        latest_time = None
        for pr in prs:
            updated_at = pr.get("updated_at")
            if updated_at:
                if latest_time is None or updated_at > latest_time:
                    latest_time = updated_at

        return latest_time

    def get_latest_activity_time(self, repository: str) -> Optional[str]:
        """Get the latest activity timestamp from all cached data for a repository."""
        latest_time = None

        # Check PRs
        pr_time = self.get_latest_pr_update_time(repository)
        if pr_time and (latest_time is None or pr_time > latest_time):
            latest_time = pr_time

        # Check reviews
        reviews_data = self._load_json_file(self.reviews_file)
        repo_reviews = reviews_data.get(repository, {})
        for pr_number, reviews in repo_reviews.items():
            for review in reviews:
                updated_at = review.get("submitted_at") or review.get("created_at")
                if updated_at and (latest_time is None or updated_at > latest_time):
                    latest_time = updated_at

        # Check comments
        comments_data = self._load_json_file(self.comments_file)
        repo_comments = comments_data.get(repository, {})
        for pr_number, comments in repo_comments.items():
            for comment in comments:
                updated_at = comment.get("updated_at") or comment.get("created_at")
                if updated_at and (latest_time is None or updated_at > latest_time):
                    latest_time = updated_at

        # Check review comments
        review_comments_data = self._load_json_file(self.review_comments_file)
        repo_review_comments = review_comments_data.get(repository, {})
        for pr_number, review_comments in repo_review_comments.items():
            for review_comment in review_comments:
                updated_at = review_comment.get("updated_at") or review_comment.get("created_at")
                if updated_at and (latest_time is None or updated_at > latest_time):
                    latest_time = updated_at

        return latest_time

    def merge_pull_requests(self, repository: str, new_prs: List[Dict]) -> None:
        """Merge new PRs with existing cached PRs, updating existing ones and adding new ones."""
        existing_prs = self.get_cached_pull_requests(repository)

        # Create a dictionary for quick lookup by PR number
        existing_prs_dict = {pr["number"]: pr for pr in existing_prs}

        # Update existing PRs and add new ones
        for new_pr in new_prs:
            pr_number = new_pr["number"]
            existing_prs_dict[pr_number] = new_pr

        # Convert back to list and sort by PR number
        merged_prs = sorted(existing_prs_dict.values(), key=lambda pr: pr["number"], reverse=True)

        # Save merged data
        self.cache_pull_requests(repository, merged_prs)

    def merge_reviews(self, repository: str, pr_number: int, new_reviews: List[Dict]) -> None:
        """Merge new reviews with existing cached reviews for a specific PR."""
        existing_reviews = self.get_cached_reviews(repository, pr_number)

        # Create a dictionary for quick lookup by review ID
        existing_reviews_dict = {review["id"]: review for review in existing_reviews}

        # Update existing reviews and add new ones
        for new_review in new_reviews:
            review_id = new_review["id"]
            existing_reviews_dict[review_id] = new_review

        # Convert back to list and sort by ID
        merged_reviews = sorted(existing_reviews_dict.values(), key=lambda review: review["id"])

        # Save merged data
        self.cache_reviews(repository, pr_number, merged_reviews)

    def merge_comments(self, repository: str, pr_number: int, new_comments: List[Dict]) -> None:
        """Merge new comments with existing cached comments for a specific PR."""
        existing_comments = self.get_cached_comments(repository, pr_number)

        # Create a dictionary for quick lookup by comment ID
        existing_comments_dict = {comment["id"]: comment for comment in existing_comments}

        # Update existing comments and add new ones
        for new_comment in new_comments:
            comment_id = new_comment["id"]
            existing_comments_dict[comment_id] = new_comment

        # Convert back to list and sort by ID
        merged_comments = sorted(existing_comments_dict.values(), key=lambda comment: comment["id"])

        # Save merged data
        self.cache_comments(repository, pr_number, merged_comments)

    def merge_review_comments(self, repository: str, pr_number: int, new_review_comments: List[Dict]) -> None:
        """Merge new review comments with existing cached review comments for a specific PR."""
        existing_review_comments = self.get_cached_review_comments(repository, pr_number)

        # Create a dictionary for quick lookup by comment ID
        existing_review_comments_dict = {comment["id"]: comment for comment in existing_review_comments}

        # Update existing review comments and add new ones
        for new_review_comment in new_review_comments:
            comment_id = new_review_comment["id"]
            existing_review_comments_dict[comment_id] = new_review_comment

        # Convert back to list and sort by ID
        merged_review_comments = sorted(existing_review_comments_dict.values(), key=lambda comment: comment["id"])

        # Save merged data
        self.cache_review_comments(repository, pr_number, merged_review_comments)
