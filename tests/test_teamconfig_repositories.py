#!/usr/bin/env python3
"""
Unit tests for the enhanced teamconfig module with repository support.

Tests the new functionality for loading repositories from config files
alongside team members.
"""

import os
import sys
import unittest
import tempfile
import json

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import teamconfig


class TestTeamConfigRepositories(unittest.TestCase):
    """Test the repository functionality in teamconfig module."""

    def setUp(self):
        """Set up test environment."""
        teamconfig.clear_team_config()

    def tearDown(self):
        """Clean up after tests."""
        teamconfig.clear_team_config()

    def test_load_config_with_repositories(self):
        """Test loading a config file that includes repositories."""
        config_data = {
            "team": ["user1", "user2"],
            "repositories": ["/path/to/repo1", "/path/to/repo2", "/path/to/repo3"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            # Check team members
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            team_members = teamconfig.get_team_members()
            self.assertEqual(len(team_members), 2)
            self.assertIn("user1", team_members)
            self.assertIn("user2", team_members)
            
            # Check repositories
            self.assertTrue(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 3)
            self.assertIn("/path/to/repo1", repositories)
            self.assertIn("/path/to/repo2", repositories)
            self.assertIn("/path/to/repo3", repositories)
            
        finally:
            os.unlink(config_file)

    def test_load_config_without_repositories(self):
        """Test loading a config file that only has team members."""
        config_data = {
            "team": ["user1", "user2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            # Check team members
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            team_members = teamconfig.get_team_members()
            self.assertEqual(len(team_members), 2)
            
            # Check repositories
            self.assertFalse(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 0)
            
        finally:
            os.unlink(config_file)

    def test_load_config_with_empty_repositories(self):
        """Test loading a config file with empty repositories list."""
        config_data = {
            "team": ["user1"],
            "repositories": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            # Check team members
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            
            # Check repositories
            self.assertTrue(teamconfig.has_repositories())
            repositories = teamconfig.get_repositories()
            self.assertEqual(len(repositories), 0)
            
        finally:
            os.unlink(config_file)

    def test_load_config_with_invalid_repositories_type(self):
        """Test loading a config file with invalid repositories type."""
        config_data = {
            "team": ["user1"],
            "repositories": "not_a_list"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            with self.assertRaises(teamconfig.TeamConfigError) as context:
                teamconfig.load_team_config(config_file)
            
            self.assertIn("repositories' must be a list", str(context.exception))
            
        finally:
            os.unlink(config_file)

    def test_clear_team_config(self):
        """Test that clear_team_config resets both team and repository data."""
        config_data = {
            "team": ["user1"],
            "repositories": ["/path/to/repo1"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            # Verify data is loaded
            self.assertTrue(teamconfig.is_team_filtering_enabled())
            self.assertTrue(teamconfig.has_repositories())
            
            # Clear config
            teamconfig.clear_team_config()
            
            # Verify data is cleared
            self.assertFalse(teamconfig.is_team_filtering_enabled())
            self.assertFalse(teamconfig.has_repositories())
            self.assertEqual(len(teamconfig.get_team_members()), 0)
            self.assertEqual(len(teamconfig.get_repositories()), 0)
            
        finally:
            os.unlink(config_file)

    def test_get_repositories_returns_copy(self):
        """Test that get_repositories returns a copy, not the original list."""
        config_data = {
            "team": ["user1"],
            "repositories": ["/path/to/repo1", "/path/to/repo2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            repositories1 = teamconfig.get_repositories()
            repositories2 = teamconfig.get_repositories()
            
            # Verify they are different objects
            self.assertIsNot(repositories1, repositories2)
            
            # Verify they have the same content
            self.assertEqual(repositories1, repositories2)
            
            # Verify modifying one doesn't affect the other
            repositories1.append("/path/to/repo3")
            self.assertNotEqual(repositories1, repositories2)
            
        finally:
            os.unlink(config_file)

    def test_get_team_members_returns_copy(self):
        """Test that get_team_members returns a copy, not the original set."""
        config_data = {
            "team": ["user1", "user2"],
            "repositories": ["/path/to/repo1"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            team_members1 = teamconfig.get_team_members()
            team_members2 = teamconfig.get_team_members()
            
            # Verify they are different objects
            self.assertIsNot(team_members1, team_members2)
            
            # Verify they have the same content
            self.assertEqual(team_members1, team_members2)
            
            # Verify modifying one doesn't affect the other
            team_members1.add("user3")
            self.assertNotEqual(team_members1, team_members2)
            
        finally:
            os.unlink(config_file)

    def test_team_filtering_without_config(self):
        """Test team filtering behavior when no config is loaded."""
        # No config loaded, should include everyone
        self.assertFalse(teamconfig.is_team_filtering_enabled())
        self.assertTrue(teamconfig.is_team_member("anyone"))
        self.assertTrue(teamconfig.is_team_member("unknown_user"))

    def test_team_filtering_with_config(self):
        """Test team filtering behavior when config is loaded."""
        config_data = {
            "team": ["John Doe", "jane.smith@company.com"],
            "repositories": ["/path/to/repo1"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            teamconfig.load_team_config(config_file)
            
            # Should include team members
            self.assertTrue(teamconfig.is_team_member("John Doe"))
            self.assertTrue(teamconfig.is_team_member("jane.smith@company.com"))
            
            # Should exclude non-team members
            self.assertFalse(teamconfig.is_team_member("Unknown User"))
            self.assertFalse(teamconfig.is_team_member("alice@company.com"))
            
        finally:
            os.unlink(config_file)


if __name__ == "__main__":
    unittest.main()
