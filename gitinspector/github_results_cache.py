#!/usr/bin/env python3
"""
GitHub Results Cache Module for GitInspector

Caches processed GitHub analysis results to avoid expensive re-computation.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List


class GitHubResultsCache:
    """Cache for processed GitHub analysis results."""

    def __init__(self, cache_dir: str = ".github_cache"):
        """
        Initialize the results cache.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.results_file = self.cache_dir / "processed_results.json"
        self.metadata_file = self.cache_dir / "results_metadata.json"

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)

    def _generate_cache_key(
        self, repositories: List[str], since: str = None, until: str = None, cache_timestamps: Dict[str, str] = None
    ) -> str:
        """
        Generate a cache key based on repositories, since/until parameters, and cache timestamps.

        Args:
            repositories: List of repository names
            since: Since parameter for filtering
            until: Until parameter for filtering
            cache_timestamps: Timestamps of when each repository was last cached

        Returns:
            MD5 hash string as cache key
        """
        # Sort repositories for consistent key generation
        sorted_repos = sorted(repositories)

        # Create key components - only include timestamps if they exist
        key_data = {"repositories": sorted_repos, "since": since, "until": until}

        # Only include cache_timestamps if they are provided and not empty
        if cache_timestamps:
            key_data["cache_timestamps"] = cache_timestamps

        # Convert to JSON string and hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save cache metadata."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        except IOError:
            pass  # Fail silently if we can't save metadata

    def _load_results(self) -> Dict[str, Any]:
        """Load cached results."""
        if not self.results_file.exists():
            return {}

        try:
            with open(self.results_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_results(self, results: Dict[str, Any]):
        """Save cached results."""
        try:
            with open(self.results_file, "w") as f:
                json.dump(results, f, indent=2)
        except IOError:
            pass  # Fail silently if we can't save results

    def get_cached_results(
        self, repositories: List[str], since: str = None, until: str = None, cache_timestamps: Dict[str, str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached results if available and still valid.

        Args:
            repositories: List of repository names
            since: Since parameter for filtering
            until: Until parameter for filtering
            cache_timestamps: Timestamps of when each repository was last cached

        Returns:
            Cached results if valid, None otherwise
        """
        cache_key = self._generate_cache_key(repositories, since, until, cache_timestamps)
        metadata = self._load_metadata()
        results = self._load_results()

        # Check if we have cached results for this key
        if cache_key not in metadata:
            return None

        cache_info = metadata[cache_key]

        # Check if cache is still valid
        if not self._is_cache_valid(cache_info, cache_timestamps):
            return None

        # Return cached results
        return results.get(cache_key)

    def _is_cache_valid(self, cache_info: Dict[str, Any], cache_timestamps: Dict[str, str] = None) -> bool:
        """
        Check if cached results are still valid.

        Args:
            cache_info: Cache metadata for the key
            cache_timestamps: Current cache timestamps for repositories

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_timestamps:
            return True  # If no timestamps provided, assume valid

        # Check if any repository's cache has been updated since results were cached
        cached_timestamps = cache_info.get("cache_timestamps", {})

        # If no cached timestamps, assume valid (old cache format)
        if not cached_timestamps:
            return True

        for repo, current_timestamp in cache_timestamps.items():
            cached_timestamp = cached_timestamps.get(repo)
            if not cached_timestamp or current_timestamp > cached_timestamp:
                return False  # Cache is invalid if any repo has newer data

        return True

    def cache_results(
        self,
        repositories: List[str],
        results: Dict[str, Any] = None,
        since: str = None,
        until: str = None,
        cache_timestamps: Dict[str, str] = None,
    ):
        """
        Cache processed results.

        Args:
            repositories: List of repository names
            results: Processed analysis results
            since: Since parameter for filtering
            until: Until parameter for filtering
            cache_timestamps: Timestamps of when each repository was last cached
        """
        cache_key = self._generate_cache_key(repositories, since, until, cache_timestamps)

        # Load existing data
        metadata = self._load_metadata()
        cached_results = self._load_results()

        # Update metadata
        metadata[cache_key] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "repositories": repositories,
            "since": since,
            "cache_timestamps": cache_timestamps or {},
        }

        # Update results
        cached_results[cache_key] = results

        # Save data
        self._save_metadata(metadata)
        self._save_results(cached_results)

    def clear_cache(self):
        """Clear all cached results."""
        try:
            if self.results_file.exists():
                self.results_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
        except IOError:
            pass

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached results.

        Returns:
            Dictionary with cache statistics
        """
        metadata = self._load_metadata()

        total_entries = len(metadata)
        total_size = 0

        if self.results_file.exists():
            total_size = self.results_file.stat().st_size

        return {
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "cache_file": str(self.results_file),
            "metadata_file": str(self.metadata_file),
        }

    def cleanup_old_entries(self, max_age_days: int = 30):
        """
        Remove cache entries older than specified days.

        Args:
            max_age_days: Maximum age in days for cache entries
        """
        metadata = self._load_metadata()
        results = self._load_results()

        cutoff_date = datetime.now(timezone.utc).timestamp() - (max_age_days * 24 * 60 * 60)
        entries_to_remove = []

        for cache_key, cache_info in metadata.items():
            try:
                created_at = datetime.fromisoformat(cache_info["created_at"].replace("Z", "+00:00"))
                if created_at.timestamp() < cutoff_date:
                    entries_to_remove.append(cache_key)
            except (ValueError, KeyError):
                # If we can't parse the date, remove the entry
                entries_to_remove.append(cache_key)

        # Remove old entries
        for cache_key in entries_to_remove:
            metadata.pop(cache_key, None)
            results.pop(cache_key, None)

        # Save updated data
        if entries_to_remove:
            self._save_metadata(metadata)
            self._save_results(results)

        return len(entries_to_remove)
