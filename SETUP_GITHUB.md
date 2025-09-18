# GitHub Setup Guide

This guide helps you set up GitHub credentials for testing the sync functionality.

## 🔧 Quick Setup

### 1. Edit the `.env` file
```bash
# Edit the .env file with your actual GitHub App credentials
nano .env
```

Replace the placeholder values:
```bash
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
```

### 2. Test the setup
```bash
# Test environment loading
python load_env.py

# Test GitHub sync (test mode)
python test_sync.py

# Or run sync directly
python sync_github_cache.py --test-mode
```

## 🔑 Getting GitHub App Credentials

### Option 1: Create a New GitHub App
1. Go to [GitHub Settings → Developer settings → GitHub Apps](https://github.com/settings/apps)
2. Click "New GitHub App"
3. Fill in the required fields:
   - **App name**: `gitinspector-cache` (or any name)
   - **Homepage URL**: `https://github.com/yourusername/gitinspector`
   - **Webhook URL**: Leave empty
   - **Repository permissions**:
     - Pull requests: Read
     - Issues: Read
     - Contents: Read
4. Click "Create GitHub App"
5. Copy the **App ID** (numeric)
6. Generate a **private key** and download it

### Option 2: Use Existing GitHub App
If you already have a GitHub App, use its credentials.

## 📁 File Structure

```
gitinspector/
├── .env                    # Your credentials (ignored by git)
├── .github_cache/          # Cache directory (ignored by git)
├── load_env.py            # Environment loader
├── test_sync.py           # Test script
└── sync_github_cache.py   # Main sync script
```

## 🧪 Testing Commands

```bash
# Test environment loading
python load_env.py

# Test sync with environment
python test_sync.py

# Manual sync commands
python sync_github_cache.py --test-mode
python sync_github_cache.py --status
python sync_github_cache.py --clear

# Run gitinspector with cached data
python run_gitinspector.py --github --format=text

# Or run as a module (alternative)
python -m gitinspector.gitinspector --github --format=text
```

## 🔒 Security Notes

- The `.env` file is ignored by Git and won't be committed
- Never share your private key
- Keep your GitHub App credentials secure
- The cache directory is also ignored by Git

## 🐛 Troubleshooting

### "GITHUB_APP_ID environment variable not set"
- Make sure your `.env` file exists and has the correct format
- Run `python load_env.py` to test environment loading

### "Invalid private key"
- Check that your private key file path is correct
- Ensure the private key is in PEM format
- Make sure the file is readable

### "Repository not found"
- Verify the repository name in `team_config.json`
- Check that your GitHub App has access to the repository
- Ensure the repository exists and is accessible

## 📚 Next Steps

Once setup is complete:
1. Run `python test_sync.py` to test the sync
2. Check `python sync_github_cache.py --status` to see cached data
3. Run `python gitinspector/gitinspector.py --github` to use cached data
4. Set up automated syncing with cron or GitHub Actions
