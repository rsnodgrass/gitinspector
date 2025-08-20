#!/usr/bin/env python3
"""
Unit tests for the new --team and --config-repos flags.

Tests the simplified configuration system where:
- --config-repos: Reads repositories from team_config.json (no team filtering)
- --team: Reads team members from team_config.json and applies team filtering
"""

import os
import sys
import unittest
import tempfile
import json

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import teamconfig


class TestNewConfigFlags(unittest.TestCase):
    """Test the new --team and --config-repos functionality."""

    def setUp(self):
        """Set up test environment."""
        teamconfig.clear_team_config()

    def tearDown(self):
        """Clean up after tests."""
        teamconfig.clear_team_config()

    def test_load_config_repos_only(self):
        """Test loading repositories without team filtering."""
        config_data = {
            "team": ["user1", "user2"],
            "repositories": ["/path/to/repo1", "/path/to/repo2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config with team filtering disabled (--config-repos behavior)
            teamconfig.load_team_config(config_file, enable_team_filtering=False)
            
            # Check that repositories are loaded
            self.assertTrue(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 2)
            self.assertIn("/path/to/repo1", repositories)
            self.assertIn("/path/to/repo2", repositories)
            
            # Check that team filtering is disabled
            self.assertFalse(teamconfig.is_team_filtering_enabled())
            
            # Verify that all authors are considered team members (no filtering)
            self.assertTrue(teamconfig.is_team_member("anyone"))
            self.assertTrue(teamconfig.is_team_member("external_user"))
            
        finally:
            os.unlink(config_file)

    def test_load_team_filtering_only(self):
        """Test loading team members with filtering enabled."""
        config_data = {
            "team": ["alice", "bob"],
            "repositories": ["/path/to/repo1", "/path/to/repo2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config with team filtering enabled (--team behavior)
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
            
            # Check that repositories are still loaded
            self.assertTrue(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 2)
            
            # Check that team filtering is enabled
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            
            # Verify that team filtering works
            self.assertTrue(teamconfig.is_team_member("alice"))
            self.assertTrue(teamconfig.is_team_member("bob"))
            self.assertFalse(teamconfig.is_team_member("charlie"))
            self.assertFalse(teamconfig.is_team_member("external_user"))
            
        finally:
            os.unlink(config_file)

    def test_load_both_repos_and_team(self):
        """Test loading repositories and team filtering together."""
        config_data = {
            "team": ["developer1", "developer2", "developer3"],
            "repositories": ["../repo1", "../repo2", "../repo3"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config with team filtering enabled (--team --config-repos behavior)
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
            
            # Check repositories
            self.assertTrue(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 3)
            self.assertIn("../repo1", repositories)
            self.assertIn("../repo2", repositories)
            self.assertIn("../repo3", repositories)
            
            # Check team filtering
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            team_members = teamconfig.get_team_members()
            self.assertEqual(len(team_members), 3)
            self.assertIn("developer1", team_members)
            self.assertIn("developer2", team_members)
            self.assertIn("developer3", team_members)
            
            # Verify filtering works
            self.assertTrue(teamconfig.is_team_member("developer1"))
            self.assertFalse(teamconfig.is_team_member("outsider"))
            
        finally:
            os.unlink(config_file)

    def test_config_without_repositories_section(self):
        """Test loading config file that has no repositories section."""
        config_data = {
            "team": ["user1", "user2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config with team filtering disabled
            teamconfig.load_team_config(config_file, enable_team_filtering=False)
            
            # Check that no repositories are loaded
            self.assertFalse(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 0)
            
            # Check that team filtering is disabled
            self.assertFalse(teamconfig.is_team_filtering_enabled())
            
            # Load config with team filtering enabled
            teamconfig.clear_team_config()
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
            
            # Check that team filtering is enabled
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            team_members = teamconfig.get_team_members()
            self.assertEqual(len(team_members), 2)
            
        finally:
            os.unlink(config_file)

    def test_repositories_only_no_team_filtering(self):
        """Test that repositories can be loaded without any team filtering."""
        config_data = {
            "team": ["restricted_user"],
            "repositories": ["../public_repo"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config with team filtering disabled (simulates --config-repos without --team)
            teamconfig.load_team_config(config_file, enable_team_filtering=False)
            
            # Repositories should be available
            self.assertTrue(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(repositories, ["../public_repo"])
            
            # Team filtering should be disabled - everyone is included
            self.assertFalse(teamconfig.is_team_filtering_enabled())
            self.assertTrue(teamconfig.is_team_member("restricted_user"))
            self.assertTrue(teamconfig.is_team_member("external_contributor"))
            self.assertTrue(teamconfig.is_team_member("anyone_else"))
            
        finally:
            os.unlink(config_file)

    def test_team_filtering_without_repositories(self):
        """Test that team filtering can be applied without loading repositories."""
        config_data = {
            "team": ["alice", "bob"],
            "repositories": ["../some_repo"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config with team filtering enabled (simulates --team without --config-repos)
            teamconfig.load_team_config(config_file, enable_team_filtering=True)
            
            # Repositories should still be loaded (they're part of the same file)
            self.assertTrue(teamconfig.has_repositories())
            
            # Team filtering should be enabled
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            self.assertTrue(teamconfig.is_team_member("alice"))
            self.assertTrue(teamconfig.is_team_member("bob"))
            self.assertFalse(teamconfig.is_team_member("charlie"))
            
        finally:
            os.unlink(config_file)

    def test_enable_team_filtering_parameter_default(self):
        """Test that the default value for enable_team_filtering is True."""
        config_data = {
            "team": ["default_user"],
            "repositories": ["../default_repo"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load config without specifying enable_team_filtering (should default to True)
            teamconfig.load_team_config(config_file)
            
            # Team filtering should be enabled by default
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            self.assertTrue(teamconfig.is_team_member("default_user"))
            self.assertFalse(teamconfig.is_team_member("external_user"))
            
        finally:
            os.unlink(config_file)


if __name__ == "__main__":
    unittest.main()
