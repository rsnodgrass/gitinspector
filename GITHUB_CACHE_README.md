# GitHub Cache System for GitInspector

This document describes the new GitHub caching system that significantly improves performance by avoiding repeated API calls to GitHub.

## Overview

The GitHub integration now uses a local cache to store GitHub data, eliminating the need to query GitHub's API every time you run gitinspector. This makes the tool much faster and reduces API rate limiting issues.

## Components

### 1. GitHub Cache (`gitinspector/github_cache.py`)
- **Purpose**: Manages local storage of GitHub data using JSON files
- **Features**:
  - Stores pull requests, reviews, comments, and review comments
  - Tracks metadata like last sync times
  - Provides methods to clear cache for specific repositories or all data
  - Handles JSON file operations with error handling

### 2. Modified GitHub Integration (`gitinspector/github_integration.py`)
- **Purpose**: Updated to use cache by default instead of API calls
- **Features**:
  - `use_cache=True` by default (can be disabled for API-only mode)
  - Falls back to cache-only mode if GitHub credentials aren't available
  - Maintains backward compatibility with existing API functionality

### 3. Sync Script (`sync_github_cache.py`)
- **Purpose**: Standalone script to populate the cache with GitHub data
- **Features**:
  - Fetches all PR data from GitHub API
  - Stores data in local cache files
  - Supports filtering by date (`--since`)
  - Can sync specific repositories or all from team config
  - Provides cache management commands (status, clear)

## Usage

### 1. Initial Setup

First, set up your GitHub credentials (same as before):
```bash
export GITHUB_APP_ID="your_app_id"
export GITHUB_PRIVATE_KEY_PATH="/path/to/private_key.pem"
# OR
export GITHUB_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
```

### 2. Sync GitHub Data

Run the sync script to populate the cache:
```bash
# Incremental sync (default) - only sync new/updated data since last sync
python sync_github_cache.py

# Force full sync - resync everything from scratch
python sync_github_cache.py --full-sync

# Sync specific repositories
python sync_github_cache.py --repos company/repo1 company/repo2

# Sync with date filter (only PRs created after this date)
python sync_github_cache.py --since 2024-01-01

# Check cache status
python sync_github_cache.py --status

# Clear all cached data
python sync_github_cache.py --clear
```

### 3. Run GitInspector

Now gitinspector will use the cached data instead of making API calls:
```bash
# This will now be much faster!
python gitinspector.py --github --format=text
```

## Cache Structure

The cache is stored in `.github_cache/` directory with the following files:
- `metadata.json` - Repository metadata and sync times
- `pull_requests.json` - All pull request data
- `reviews.json` - PR reviews organized by repository and PR number
- `comments.json` - PR comments organized by repository and PR number
- `review_comments.json` - PR review comments organized by repository and PR number

## Benefits

1. **Performance**: No more waiting for GitHub API calls during analysis
2. **Rate Limiting**: Avoids GitHub API rate limits
3. **Offline Analysis**: Can analyze data without internet connection
4. **Consistency**: Same data used across multiple runs
5. **Flexibility**: Can still use API mode when needed
6. **Incremental Sync**: Only downloads new/updated data, making subsequent syncs much faster
7. **Smart Merging**: Updates existing data and adds new data without losing information

## Incremental Sync Behavior

The sync script now uses **incremental syncing** by default:

### How It Works
1. **First Run**: Downloads all data from GitHub (full sync)
2. **Subsequent Runs**: Only downloads data updated since the last sync
3. **Smart Merging**: New data is merged with existing data, updating changed items and adding new ones
4. **Timestamp Detection**: Uses the latest `updated_at` timestamp from all cached data (PRs, reviews, comments)

### Sync Strategies
- **Incremental (Default)**: `python sync_github_cache.py` - Only sync new/updated data
- **Test Mode**: `python sync_github_cache.py --test-mode` - Sync only recent data (last 7 days, max 5 PRs per repo)
- **Full Sync**: `python sync_github_cache.py --full-sync` - Resync everything
- **Date Filter**: `python sync_github_cache.py --since 2024-01-01` - Sync from specific date

### Benefits of Incremental Sync
- **Faster**: Subsequent syncs are much faster (only new data)
- **Efficient**: Reduces API calls and bandwidth usage
- **Up-to-date**: Always gets the latest changes without re-downloading everything
- **Safe**: Merges data intelligently, preserving existing information

### Test Mode for Development
The `--test-mode` flag is perfect for development and testing:
- **Limited Data**: Only syncs data from the last 7 days
- **PR Limit**: Maximum 5 PRs per repository for quick testing
- **Fast Verification**: Quickly test end-to-end functionality
- **Safe Testing**: Won't overwhelm with large amounts of data

Perfect for:
- Verifying the sync process works
- Testing gitinspector with real GitHub data
- Development and debugging
- CI/CD pipelines

## Migration from Old System

The new system is backward compatible:
- Existing gitinspector commands work the same way
- GitHub credentials are still required for the sync script
- The `--github` flag behavior is unchanged
- All output formats remain the same

## Troubleshooting

### No Cached Data Error
If you see "No cached data available" error:
1. Run the sync script first: `python sync_github_cache.py`
2. Make sure your team config has GitHub repositories configured

### Cache Out of Date
To refresh cached data:
1. Run sync script again: `python sync_github_cache.py`
2. Or clear and re-sync: `python sync_github_cache.py --clear && python sync_github_cache.py`

### API Mode
To use API mode instead of cache (for testing or one-off analysis):
```python
# In your code
github_integration = GitHubIntegration(
    app_id="your_app_id",
    private_key_content="your_key",
    use_cache=False
)
```

## Testing

Run the test suite to verify everything works:
```bash
# Test cache functionality
python -m unittest tests.test_github_cache -v

# Test integration with cache
python -m unittest tests.test_github_integration_cache -v
```
