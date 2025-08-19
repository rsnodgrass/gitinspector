#!/usr/bin/env python3
"""
Unit tests for team filtering integration with the GitInspector activity feature.

Tests that the activity feature correctly respects --team-config filtering
and that team filtering works properly with all activity display modes.
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import activity, changes, teamconfig, filtering
from gitinspector.output import activityoutput
from tests.test_helpers import GitTestRepo, GitInspectorTestCase


class TestActivityTeamFiltering(GitInspectorTestCase):
    """Test team filtering functionality with activity analysis."""
    
    def setUp(self):
        """Set up test environment for team filtering tests."""
        super().setUp()
        
        # Clear any existing team config
        teamconfig.clear_team_config()
        
        # Set up mock team members
        self.team_members = ["Alice", "Bob", "Charlie"]
        self.external_contributors = ["External Dev", "Contractor"]
    
    def tearDown(self):
        """Clean up after tests."""
        # Clear team config after each test
        teamconfig.clear_team_config()
        super().tearDown()
    
    def _setup_mock_team_config(self):
        """Set up mock team configuration."""
        # Directly set the team members (simulating loaded config)
        teamconfig.__team_members__ = set(self.team_members)
        teamconfig.__team_config_loaded__ = True
    
    def test_activity_respects_team_filtering_basic(self):
        """Test that activity analysis respects basic team filtering."""
        with GitTestRepo("team_filter_test") as repo:
            # Add commits from team members
            repo.add_commit('team1.py', 'team code 1', 'Alice', 'alice@company.com', 'Team commit 1')
            repo.add_commit('team2.py', 'team code 2', 'Bob', 'bob@company.com', 'Team commit 2')
            
            # Add commits from external contributors
            repo.add_commit('external1.py', 'external code 1', 'External Dev', 'external@contractor.com', 'External commit 1')
            repo.add_commit('external2.py', 'external code 2', 'Contractor', 'contractor@company.com', 'External commit 2')
            
            # Set up team configuration
            self._setup_mock_team_config()
            
            # Create activity data
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"team_filter_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get activity stats
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            if repositories and periods:
                repo_name = repositories[0]
                period = periods[0]
                
                stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                
                # Should only include team members (2 commits, not 4)
                self.assertEqual(stats['commits'], 2, "Should only count team member commits")
                self.assertEqual(stats['contributors'], 2, "Should only count team member contributors")
    
    def test_activity_without_team_filtering(self):
        """Test that activity analysis includes all contributors when no team config is loaded."""
        with GitTestRepo("no_filter_test") as repo:
            # Add commits from various contributors
            repo.add_commit('file1.py', 'code 1', 'Alice', 'alice@company.com', 'Commit 1')
            repo.add_commit('file2.py', 'code 2', 'External Dev', 'external@contractor.com', 'Commit 2')
            repo.add_commit('file3.py', 'code 3', 'Contractor', 'contractor@company.com', 'Commit 3')
            
            # No team configuration set up
            
            # Create activity data
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"no_filter_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get activity stats
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            if repositories and periods:
                repo_name = repositories[0]
                period = periods[0]
                
                stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                
                # Should include all contributors
                self.assertEqual(stats['commits'], 3, "Should count all commits without team filtering")
                self.assertEqual(stats['contributors'], 3, "Should count all contributors without team filtering")
    
    def test_team_filtering_with_normalization(self):
        """Test that team filtering works correctly with normalization."""
        with GitTestRepo("filter_norm_test") as repo:
            # Add commits: 2 team members, 2 external
            repo.add_commit('team1.py', 'team\ncode\n1\n', 'Alice', 'alice@company.com', 'Team commit 1')  # 3 lines
            repo.add_commit('team2.py', 'team\ncode\n2\n', 'Bob', 'bob@company.com', 'Team commit 2')      # 3 lines
            repo.add_commit('ext1.py', 'external\ncode\n', 'External Dev', 'external@contractor.com', 'External 1')  # 2 lines
            repo.add_commit('ext2.py', 'contractor\ncode\n', 'Contractor', 'contractor@company.com', 'External 2')  # 2 lines
            
            # Set up team configuration
            self._setup_mock_team_config()
            
            # Create activity data
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"filter_norm_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get normalized stats
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            if repositories and periods:
                repo_name = repositories[0]
                period = periods[0]
                
                raw_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                norm_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=True)
                
                # Raw stats should only include team members
                self.assertEqual(raw_stats['commits'], 2)
                self.assertEqual(raw_stats['contributors'], 2)
                
                # Normalized stats should be correct (1 commit per contributor)
                self.assertEqual(norm_stats['commits_per_contributor'], 1.0)
    
    def test_team_filtering_output_text(self):
        """Test that team filtering is reflected in text output."""
        with GitTestRepo("filter_output_test") as repo:
            # Add team and external commits
            repo.add_commit('team.py', 'team code', 'Alice', 'alice@company.com', 'Team commit')
            repo.add_commit('external.py', 'external code', 'External Dev', 'external@contractor.com', 'External commit')
            
            # Set up team configuration
            self._setup_mock_team_config()
            
            # Create activity data and output
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"filter_output_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Test single mode output
            output = activityoutput.ActivityOutput(activity_data, normalize=False, show_both=False)
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                output.output_text()
            
            output_text = captured_output.getvalue()
            
            # Should only show data for team members (1 commit, 1 contributor)
            self.assertIn("1", output_text)  # Should show 1 commit
            # Should not show 2 commits
            lines = output_text.split('\n')
            data_lines = [line for line in lines if 'filter_output_test' in line]
            if data_lines:
                # Parse the data line to check commit count
                data_parts = data_lines[0].split()
                commit_count = int(data_parts[2])  # Assuming commits is 3rd column
                self.assertEqual(commit_count, 1, "Should only show commits from team members")
    
    def test_team_filtering_output_dual_display(self):
        """Test that team filtering works with dual display mode."""
        with GitTestRepo("filter_dual_test") as repo:
            # Add team commits
            repo.add_commit('team1.py', 'team\ncode\n1\n', 'Alice', 'alice@company.com', 'Team commit 1')
            repo.add_commit('team2.py', 'team\ncode\n2\n', 'Bob', 'bob@company.com', 'Team commit 2')
            # Add external commits (should be filtered out)
            repo.add_commit('ext.py', 'external\ncode\n', 'External Dev', 'external@contractor.com', 'External')
            
            # Set up team configuration
            self._setup_mock_team_config()
            
            # Create activity data and dual display output
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"filter_dual_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            output = activityoutput.ActivityOutput(activity_data, normalize=False, show_both=True)
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                output.output_text()
            
            output_text = captured_output.getvalue()
            
            # Should show dual display format
            self.assertIn("raw totals and per-contributor averages", output_text)
            
            # Should only show team member data (2 commits, 2 contributors)
            lines = output_text.split('\n')
            data_lines = [line for line in lines if 'filter_dual_test' in line]
            if data_lines:
                # In dual display, commits should be 2, contributors should be 2
                # The per-contributor metrics should be 1.0 (2 commits / 2 contributors)
                self.assertIn("2", data_lines[0])  # Should contain 2 for commits and contributors
                self.assertIn("1.0", data_lines[0])  # Should contain 1.0 for commits per dev
    
    def test_team_filtering_is_author_team_filtered_function(self):
        """Test the filtering.is_author_team_filtered function directly."""
        # Test without team config
        self.assertFalse(filtering.is_author_team_filtered("Anyone"))
        
        # Set up team configuration
        self._setup_mock_team_config()
        
        # Test team members (should not be filtered)
        for member in self.team_members:
            self.assertFalse(filtering.is_author_team_filtered(member), 
                           f"Team member {member} should not be filtered")
        
        # Test external contributors (should be filtered)
        for external in self.external_contributors:
            self.assertTrue(filtering.is_author_team_filtered(external), 
                          f"External contributor {external} should be filtered")
        
        # Test case insensitive matching
        self.assertFalse(filtering.is_author_team_filtered("alice"))  # Should match "Alice"
        self.assertFalse(filtering.is_author_team_filtered("ALICE"))  # Should match "Alice"
    
    def test_team_filtering_partial_name_matching(self):
        """Test that team filtering works with partial name matching."""
        # Set up team with partial names
        teamconfig.__team_members__ = {"Alice", "Bob"}
        teamconfig.__team_config_loaded__ = True
        
        # Test partial matches (should work)
        self.assertFalse(filtering.is_author_team_filtered("Alice Johnson"))  # Contains "Alice"
        self.assertFalse(filtering.is_author_team_filtered("Bob Smith"))      # Contains "Bob"
        
        # Test non-matches (should be filtered)
        self.assertTrue(filtering.is_author_team_filtered("Charlie Brown"))   # No match
        self.assertTrue(filtering.is_author_team_filtered("External Dev"))    # No match


class TestActivityTeamFilteringEdgeCases(GitInspectorTestCase):
    """Test edge cases for team filtering with activity analysis."""
    
    def test_empty_team_config(self):
        """Test behavior with empty team configuration."""
        # Set up empty team config
        teamconfig.__team_members__ = set()
        teamconfig.__team_config_loaded__ = True
        
        with GitTestRepo("empty_team_test") as repo:
            repo.add_commit('file.py', 'code', 'Developer', 'dev@company.com', 'Commit')
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"empty_team_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Should filter out all contributors
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            # Should have no activity data due to filtering
            self.assertEqual(len(repositories), 1)  # Repository exists
            if repositories and periods:
                repo_name = repositories[0]
                period = periods[0] if periods else None
                if period:
                    stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                    self.assertEqual(stats['commits'], 0, "Empty team config should filter out all commits")
    
    def test_team_filtering_with_multiple_repositories(self):
        """Test team filtering across multiple repositories."""
        with GitTestRepo("multi_repo1") as repo1:
            repo1.add_commit('file1.py', 'code1', 'Alice', 'alice@company.com', 'Commit 1')
            repo1.add_commit('file2.py', 'code2', 'External', 'external@contractor.com', 'External 1')
            changes1 = changes.Changes(None, hard=True)
            
            with GitTestRepo("multi_repo2") as repo2:
                repo2.add_commit('file3.py', 'code3', 'Bob', 'bob@company.com', 'Commit 2')
                repo2.add_commit('file4.py', 'code4', 'Contractor', 'contractor@company.com', 'External 2')
                changes2 = changes.Changes(None, hard=True)
                
                # Set up team configuration
                teamconfig.__team_members__ = {"Alice", "Bob"}
                teamconfig.__team_config_loaded__ = True
                
                changes_by_repo = {
                    "multi_repo1": changes1,
                    "multi_repo2": changes2
                }
                
                activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
                
                # Each repository should only show team member commits
                repositories = activity_data.get_repositories()
                periods = activity_data.get_periods()
                
                for repo_name in repositories:
                    for period in periods:
                        stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                        if stats['commits'] > 0:
                            # Each repo should have 1 commit (from team member) not 2
                            self.assertEqual(stats['commits'], 1, 
                                           f"Repository {repo_name} should only show team member commits")
                            self.assertEqual(stats['contributors'], 1, 
                                           f"Repository {repo_name} should only show team member contributors")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
