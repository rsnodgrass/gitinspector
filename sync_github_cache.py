#!/usr/bin/env python3
"""
GitHub Cache Sync Script for GitInspector

This script fetches GitHub data and stores it in a local cache for fast access.
Run this script to populate the cache before using gitinspector with --github.
"""

import os
import sys
import argparse
import time
from datetime import datetime, timezone
from typing import List, Dict

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gitinspector.github_integration import GitHubIntegration, load_github_config, GitHubIntegrationError
from gitinspector.github_cache import GitHubCache, GitHubCacheError
from gitinspector import teamconfig


def sync_repository_data(
    github_integration: GitHubIntegration,
    cache: GitHubCache,
    owner: str,
    repo: str,
    since: str = None,
    full_sync: bool = False,
    test_mode: bool = False,
) -> None:
    """
    Sync data for a single repository.

    Args:
        github_integration: GitHub integration instance (not using cache)
        cache: Cache instance
        owner: Repository owner
        repo: Repository name
        since: ISO 8601 timestamp to filter PRs (if None, will use incremental sync)
        full_sync: If True, force full sync instead of incremental
        test_mode: If True, limit to small amount of data for testing
    """
    repository = f"{owner}/{repo}"
    print("Syncing data for {repository}...".format(repository=repository))

    try:
        # Determine sync strategy
        if full_sync:
            print("  Force full sync requested")
            since = None
        elif since is None and cache.is_repository_cached(repository):
            # Incremental sync - find latest activity time
            latest_activity = cache.get_latest_activity_time(repository)
            if latest_activity:
                since = latest_activity
                print(f"  Using incremental sync from {since}")
            else:
                print("  No previous activity found, doing full sync")
        elif since:
            print(f"  Using provided since parameter: {since}")
        else:
            print("  First time sync - fetching all data")

        # Get PRs (incremental or full based on since parameter)
        print(f"  Fetching pull requests...")
        prs = github_integration.get_pull_requests(owner, repo, since=since)
        print(f"  Found {len(prs)} pull requests")

        if prs:
            # In test mode, limit to first 5 PRs for quick testing
            if test_mode and len(prs) > 5:
                prs = prs[:5]
                print(f"  Test mode: Limited to first 5 PRs for quick testing")

            # Merge PRs with existing data (or cache if first time)
            if cache.is_repository_cached(repository):
                cache.merge_pull_requests(repository, prs)
                print(f"  Merged {len(prs)} PRs with existing data")
            else:
                cache.cache_pull_requests(repository, prs)
                print(f"  Cached {len(prs)} PRs")
        else:
            print("  No new PRs found")
            return

        # Process each PR to get reviews and comments
        total_prs = len(prs)
        for i, pr in enumerate(prs, 1):
            pr_number = pr["number"]

            # Show progress every 10 PRs or for the last one
            if i % 10 == 0 or i == total_prs:
                print(f"  Processing PR {i}/{total_prs} ({(i/total_prs)*100:.1f}%)")

            # Get and merge reviews
            try:
                reviews = github_integration.get_pr_reviews(owner, repo, pr_number)
                if cache.is_repository_cached(repository):
                    cache.merge_reviews(repository, pr_number, reviews)
                else:
                    cache.cache_reviews(repository, pr_number, reviews)
            except Exception as e:
                print(f"    Warning: Failed to fetch reviews for PR #{pr_number}: {e}")
                if not cache.is_repository_cached(repository):
                    cache.cache_reviews(repository, pr_number, [])

            # Get and merge comments
            try:
                comments = github_integration.get_pr_comments(owner, repo, pr_number)
                if cache.is_repository_cached(repository):
                    cache.merge_comments(repository, pr_number, comments)
                else:
                    cache.cache_comments(repository, pr_number, comments)
            except Exception as e:
                print(f"    Warning: Failed to fetch comments for PR #{pr_number}: {e}")
                if not cache.is_repository_cached(repository):
                    cache.cache_comments(repository, pr_number, [])

            # Get and merge review comments
            try:
                review_comments = github_integration.get_pr_review_comments(owner, repo, pr_number)
                if cache.is_repository_cached(repository):
                    cache.merge_review_comments(repository, pr_number, review_comments)
                else:
                    cache.cache_review_comments(repository, pr_number, review_comments)
            except Exception as e:
                print(f"    Warning: Failed to fetch review comments for PR #{pr_number}: {e}")
                if not cache.is_repository_cached(repository):
                    cache.cache_review_comments(repository, pr_number, [])

            # Rate limiting - be respectful to GitHub API
            time.sleep(0.1)

        # Update cache metadata
        cache.update_cache_metadata(repository)
        print(f"  Successfully synced {repository}")

    except Exception as e:
        print(f"  Error syncing {repository}: {e}")
        raise


def _create_github_integration(app_id: str, private_key: str) -> GitHubIntegration:
    """Create GitHub integration instance."""
    return GitHubIntegration(
        app_id,
        private_key_path=private_key if os.path.exists(private_key) else None,
        private_key_content=private_key if not os.path.exists(private_key) else None,
        use_cache=False,  # This instance will fetch from API
    )


def sync_all_repositories(
    github_integration: GitHubIntegration,
    cache: GitHubCache,
    repositories: List[str],
    since: str = None,
    full_sync: bool = False,
    test_mode: bool = False,
) -> None:
    """
    Sync data for all repositories.

    Args:
        github_integration: GitHub integration instance (not using cache)
        cache: Cache instance
        repositories: List of repositories in format "owner/repo"
        since: ISO 8601 timestamp to filter PRs
        full_sync: If True, force full sync instead of incremental
        test_mode: If True, limit to small amount of data for testing
    """
    print(f"Syncing data for {len(repositories)} repositories...")

    successful_syncs = 0
    failed_syncs = 0

    for repository in repositories:
        try:
            owner, repo = repository.split("/", 1)
            sync_repository_data(github_integration, cache, owner, repo, since, full_sync, test_mode)
            successful_syncs += 1
        except Exception as e:
            print(f"Failed to sync {repository}: {e}")
            failed_syncs += 1
            continue

    print(f"\nSync completed:")
    print(f"  Successful: {successful_syncs}")
    print(f"  Failed: {failed_syncs}")


def show_cache_status(cache: GitHubCache) -> None:
    """Show current cache status."""
    print("Current cache status:")

    cached_repos = cache.get_cached_repositories()
    if not cached_repos:
        print("  No repositories cached")
        return

    metadata = cache.get_cache_metadata()
    cache_sizes = cache.get_cache_size()

    print(f"  Cached repositories: {len(cached_repos)}")
    for repo in cached_repos:
        repo_data = metadata.get("repositories", {}).get(repo, {})
        last_sync = repo_data.get("last_sync", "Unknown")
        print(f"    {repo}: last synced {last_sync}")

    print(f"  Cache size: {sum(cache_sizes.values())} bytes")
    for name, size in cache_sizes.items():
        if size > 0:
            print(f"    {name}: {size} bytes")
    
    # Show results cache info
    try:
        from gitinspector.github_results_cache import GitHubResultsCache
        results_cache = GitHubResultsCache(cache.cache_dir)
        results_info = results_cache.get_cache_info()
        
        print(f"\n  Processed Results Cache:")
        print(f"    Total Entries: {results_info['total_entries']}")
        print(f"    Total Size: {results_info['total_size_bytes'] / 1024:.2f} KB")
    except ImportError:
        print(f"\n  Processed Results Cache: Not available")


def main():
    """Main function."""
    # Try to load environment variables from .env file
    try:
        from load_env import load_env_file

        load_env_file()
    except ImportError:
        # load_env.py not available, continue without it
        pass

    parser = argparse.ArgumentParser(
        description="Sync GitHub data to local cache for GitInspector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Incremental sync (default) - only sync new/updated data
  python sync_github_cache.py

  # Test mode - sync only recent data (last 7 days) for testing
  python sync_github_cache.py --test-mode

  # Force full sync - resync everything
  python sync_github_cache.py --full-sync

  # Sync specific repositories
  python sync_github_cache.py --repos company/repo1 company/repo2

  # Sync with date filter
  python sync_github_cache.py --since 2024-01-01

  # Show cache status
  python sync_github_cache.py --status

  # Clear cache
  python sync_github_cache.py --clear
        """,
    )

    parser.add_argument("--repos", nargs="+", help="Specific repositories to sync (format: owner/repo)")
    parser.add_argument("--since", help="Only sync PRs created after this date (ISO 8601 format)")
    parser.add_argument("--cache-dir", default=".github_cache", help="Cache directory (default: .github_cache)")
    parser.add_argument("--status", action="store_true", help="Show current cache status")
    parser.add_argument("--clear", action="store_true", help="Clear all cached data")
    parser.add_argument("--clear-results", action="store_true", help="Clear processed results cache")
    parser.add_argument("--full-sync", action="store_true", help="Force full sync instead of incremental")
    parser.add_argument("--test-mode", action="store_true", help="Test mode - sync only recent data (last 7 days)")
    parser.add_argument(
        "--config-file",
        default="team_config.json",
        help="Team config file to load repositories from (default: team_config.json)",
    )

    args = parser.parse_args()

    # Initialize cache
    cache = GitHubCache(args.cache_dir)

    # Handle special operations
    if args.clear:
        cache.clear_all_cache()
        print("Cache cleared successfully")
        return

    if args.clear_results:
        print("Clearing processed results cache...")
        from gitinspector.github_results_cache import GitHubResultsCache
        results_cache = GitHubResultsCache(args.cache_dir)
        results_cache.clear_cache()
        print("Results cache cleared successfully!")
        return

    if args.status:
        show_cache_status(cache)
        return

    # Load GitHub configuration
    try:
        app_id, private_key = load_github_config()
        github_integration = _create_github_integration(app_id, private_key)
    except GitHubIntegrationError as e:
        print(f"Error loading GitHub configuration: {e}")
        print("Please set GITHUB_APP_ID and either GITHUB_PRIVATE_KEY_PATH or GITHUB_PRIVATE_KEY")
        sys.exit(1)

    # Handle test mode
    if args.test_mode:
        from datetime import datetime, timedelta

        test_since = (datetime.now() - timedelta(days=7)).isoformat()
        if args.since:
            print("Warning: --since specified with --test-mode, using test mode date instead")
        args.since = test_since
        print(f"Test mode enabled - syncing data from last 7 days (since {test_since})")

    # Determine repositories to sync
    repositories = []

    if args.repos:
        repositories = args.repos
    else:
        # Load from team config
        try:
            teamconfig.load_team_config(args.config_file, enable_team_filtering=False)
            if teamconfig.has_github_repositories():
                repositories = teamconfig.get_github_repositories()
            else:
                print("No GitHub repositories found in team config")
                print("Use --repos to specify repositories manually")
                sys.exit(1)
        except Exception as e:
            print(f"Error loading team config: {e}")
            print("Use --repos to specify repositories manually")
            sys.exit(1)

    if not repositories:
        print("No repositories to sync")
        sys.exit(1)

    # Sync repositories
    try:
        sync_all_repositories(github_integration, cache, repositories, args.since, args.full_sync, args.test_mode)
    except KeyboardInterrupt:
        print("\nSync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
