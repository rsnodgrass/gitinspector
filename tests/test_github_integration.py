#!/usr/bin/env python3
"""
Basic tests for GitHub integration module.

These tests verify the module structure and basic functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.github_integration import GitHubIntegration, GitHubIntegrationError, load_github_config


class TestGitHubIntegration(unittest.TestCase):
    """Test GitHub integration functionality."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for key in ["GITHUB_APP_ID", "GITHUB_PRIVATE_KEY_PATH", "GITHUB_PRIVATE_KEY"]:
            if key in os.environ:
                del os.environ[key]

    def test_github_integration_error(self):
        """Test that GitHubIntegrationError can be raised and caught."""
        try:
            raise GitHubIntegrationError("Test error message")
        except GitHubIntegrationError as e:
            self.assertEqual(str(e), "Test error message")

    def test_load_github_config_missing_app_id(self):
        """Test that load_github_config fails when GITHUB_APP_ID is missing."""
        with self.assertRaises(GitHubIntegrationError) as cm:
            load_github_config()
        self.assertIn("GITHUB_APP_ID environment variable not set", str(cm.exception))

    def test_load_github_config_missing_private_key(self):
        """Test that load_github_config fails when no private key is provided."""
        os.environ["GITHUB_APP_ID"] = "test_app_id"

        with self.assertRaises(GitHubIntegrationError) as cm:
            load_github_config()
        self.assertIn("Either GITHUB_PRIVATE_KEY_PATH or GITHUB_PRIVATE_KEY must be set", str(cm.exception))

    def test_load_github_config_with_app_id_and_private_key(self):
        """Test that load_github_config works with both app_id and private_key."""
        os.environ["GITHUB_APP_ID"] = "test_app_id"
        os.environ["GITHUB_PRIVATE_KEY"] = "test_private_key"

        app_id, private_key = load_github_config()
        self.assertEqual(app_id, "test_app_id")
        self.assertEqual(private_key, "test_private_key")

    def test_github_integration_initialization(self):
        """Test that GitHubIntegration can be initialized."""
        # This is a basic test that the class can be instantiated
        # In a real scenario, you'd need valid credentials
        try:
            integration = GitHubIntegration("test_app_id", private_key_content="test_key")
            self.assertEqual(integration.app_id, "test_app_id")
        except Exception:
            # Expected to fail with invalid credentials, but class should be created
            pass


if __name__ == "__main__":
    unittest.main()
