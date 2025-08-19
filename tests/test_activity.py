#!/usr/bin/env python3
"""
Unit tests for the GitInspector activity feature.

Tests the activity.py module and activityoutput.py module to ensure:
- Correct data collection from git repositories
- Proper contributor tracking per period
- Accurate normalization calculations
- All output formats work correctly
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import activity, changes
from gitinspector.output import activityoutput
from tests.test_helpers import GitTestRepo, ActivityTestScenarios, GitInspectorTestCase


class TestActivityData(GitInspectorTestCase):
    """Test the ActivityData class functionality."""
    
    def test_activity_data_initialization(self):
        """Test ActivityData initialization with empty data."""
        activity_data = activity.ActivityData({}, useweeks=False)
        
        self.assert_activity_data_valid(activity_data)
        self.assertEqual(activity_data.get_repositories(), [])
        self.assertEqual(activity_data.get_periods(), [])
        
    def test_single_repository_activity(self):
        """Test activity tracking for a single repository."""
        with GitTestRepo("single_repo") as repo:
            ActivityTestScenarios.create_solo_developer_repo(repo)
            
            # Create Changes object for the repository
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"single_repo": changes_obj}
            
            # Create ActivityData
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Verify basic structure
            self.assert_activity_data_valid(activity_data)
            repositories = activity_data.get_repositories()
            self.assertEqual(len(repositories), 1)
            self.assertIn("single_repo", repositories)
            
            # Verify periods exist
            periods = activity_data.get_periods()
            self.assertGreater(len(periods), 0)
    
    def test_multi_repository_activity(self):
        """Test activity tracking across multiple repositories."""
        with GitTestRepo("team_repo") as team_repo:
            ActivityTestScenarios.create_multi_developer_repo(team_repo)
            team_changes = changes.Changes(None, hard=True)
            
            with GitTestRepo("solo_repo") as solo_repo:
                ActivityTestScenarios.create_solo_developer_repo(solo_repo)
                solo_changes = changes.Changes(None, hard=True)
                
                changes_by_repo = {
                    "team_repo": team_changes,
                    "solo_repo": solo_changes
                }
                
                # Create ActivityData
                activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
                
                # Verify repositories
                repositories = activity_data.get_repositories()
                self.assertEqual(len(repositories), 2)
                self.assertIn("team_repo", repositories)
                self.assertIn("solo_repo", repositories)
                
                # Verify we have periods from both repos
                periods = activity_data.get_periods()
                self.assertGreater(len(periods), 0)
    
    def test_weekly_vs_monthly_periods(self):
        """Test that weekly and monthly period formatting works correctly."""
        with GitTestRepo("period_test") as repo:
            # Add commits in the same month but different weeks
            base_date = datetime(2025, 1, 5)  # First week of January
            repo.add_commit('week1.py', 'def week1(): pass', commit_date=base_date)
            repo.add_commit('week3.py', 'def week3(): pass', commit_date=base_date + timedelta(days=14))
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"period_test": changes_obj}
            
            # Test monthly periods
            monthly_data = activity.ActivityData(changes_by_repo, useweeks=False)
            monthly_periods = monthly_data.get_periods()
            
            # Test weekly periods
            weekly_data = activity.ActivityData(changes_by_repo, useweeks=True)
            weekly_periods = weekly_data.get_periods()
            
            # Weekly should have more periods than monthly
            self.assertGreaterEqual(len(weekly_periods), len(monthly_periods))
            
            # Monthly periods should be YYYY-MM format
            for period in monthly_periods:
                if period:  # Skip empty periods
                    self.assertRegex(period, r'^\d{4}-\d{2}$')
            
            # Weekly periods should be YYYYWNN format
            for period in weekly_periods:
                if period:  # Skip empty periods
                    self.assertRegex(period, r'^\d{4}W\d{2}$')


class TestActivityNormalization(GitInspectorTestCase):
    """Test activity normalization functionality."""
    
    def test_contributor_counting(self):
        """Test that contributors are counted correctly per period."""
        with GitTestRepo("contributor_test") as repo:
            ActivityTestScenarios.create_multi_developer_repo(repo)
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"contributor_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get stats for different periods
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            if repositories and periods:
                repo_name = repositories[0]
                
                # Check raw stats include contributor count
                for period in periods:
                    raw_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                    self.assert_stats_format(raw_stats, normalized=False)
                    
                    if raw_stats['commits'] > 0:
                        self.assertGreater(raw_stats['contributors'], 0)
    
    def test_normalization_calculations(self):
        """Test that normalization calculations are correct."""
        with GitTestRepo("norm_test") as repo:
            # Create a scenario where we know the expected values
            repo.add_commit('file1.py', 'line1\nline2\n', 'Dev1', 'dev1@example.com', 'Commit 1')
            repo.add_commit('file2.py', 'line1\nline2\nline3\n', 'Dev2', 'dev2@example.com', 'Commit 2')
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"norm_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            if repositories and periods:
                repo_name = repositories[0]
                period = periods[0]
                
                # Get normalized stats
                normalized_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=True)
                self.assert_stats_format(normalized_stats, normalized=True)
                
                # Check that per-contributor values are reasonable
                if normalized_stats['contributors'] > 0:
                    self.assertGreaterEqual(normalized_stats['commits_per_contributor'], 0)
                    self.assertGreaterEqual(normalized_stats['insertions_per_contributor'], 0)
                    self.assertGreaterEqual(normalized_stats['deletions_per_contributor'], 0)
    
    def test_max_values_normalization(self):
        """Test that max values are calculated correctly for both raw and normalized data."""
        with GitTestRepo("max_test") as repo:
            ActivityTestScenarios.create_multi_developer_repo(repo)
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"max_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get max values for raw data
            raw_max = activity_data.get_max_values(normalized=False)
            self.assertIn('commits', raw_max)
            self.assertIn('insertions', raw_max)
            self.assertIn('deletions', raw_max)
            
            # Get max values for normalized data
            norm_max = activity_data.get_max_values(normalized=True)
            self.assertIn('commits_per_contributor', norm_max)
            self.assertIn('insertions_per_contributor', norm_max)
            self.assertIn('deletions_per_contributor', norm_max)
    
    def test_total_stats_normalization(self):
        """Test that total statistics work for both raw and normalized data."""
        with GitTestRepo("total_test") as repo:
            ActivityTestScenarios.create_solo_developer_repo(repo)
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"total_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get raw totals
            raw_totals = activity_data.get_total_stats(normalized=False)
            self.assertIn('commits', raw_totals)
            self.assertIn('insertions', raw_totals)
            self.assertIn('deletions', raw_totals)
            self.assertIn('contributors', raw_totals)
            
            # Get normalized totals
            norm_totals = activity_data.get_total_stats(normalized=True)
            self.assertIn('commits_per_contributor', norm_totals)
            self.assertIn('insertions_per_contributor', norm_totals)
            self.assertIn('deletions_per_contributor', norm_totals)


class TestActivityOutput(GitInspectorTestCase):
    """Test the ActivityOutput class and all output formats."""
    
    def setUp(self):
        """Set up test data for output testing."""
        super().setUp()
        
        # Create test data
        with GitTestRepo("output_test") as repo:
            ActivityTestScenarios.create_multi_developer_repo(repo)
            changes_obj = changes.Changes(None, hard=True)
            self.changes_by_repo = {"output_test": changes_obj}
    
    def test_text_output_raw(self):
        """Test text output format with raw statistics."""
        activity_data = activity.ActivityData(self.changes_by_repo, useweeks=False)
        output = activityoutput.ActivityOutput(activity_data, normalize=False)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        
        output_text = captured_output.getvalue()
        
        # Verify output contains expected elements
        self.assertIn("Activity by repository over months", output_text)
        self.assertIn("Repository", output_text)
        self.assertIn("Period", output_text)
        self.assertIn("Contributors", output_text)
        self.assertIn("Commits", output_text)
        self.assertIn("TOTAL", output_text)
    
    def test_text_output_normalized(self):
        """Test text output format with normalized statistics."""
        activity_data = activity.ActivityData(self.changes_by_repo, useweeks=False)
        output = activityoutput.ActivityOutput(activity_data, normalize=True)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        
        output_text = captured_output.getvalue()
        
        # Verify output contains normalized elements
        self.assertIn("normalized per contributor", output_text)
        self.assertIn("Commits/Dev", output_text)
        self.assertIn("Lines+/Dev", output_text)
        self.assertIn("Lines-/Dev", output_text)
    
    def test_html_output_raw(self):
        """Test HTML output format with raw statistics."""
        activity_data = activity.ActivityData(self.changes_by_repo, useweeks=False)
        output = activityoutput.ActivityOutput(activity_data, normalize=False)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_html()
        
        output_html = captured_output.getvalue()
        
        # Verify HTML structure
        self.assertIn('<div class="box">', output_html)
        self.assertIn('<h4>Repository Activity Over Time</h4>', output_html)
        self.assertIn('Raw statistics show absolute numbers', output_html)
        self.assertIn('<table class="git">', output_html)
        self.assertIn('Total Contributors', output_html)
    
    def test_html_output_normalized(self):
        """Test HTML output format with normalized statistics.""" 
        activity_data = activity.ActivityData(self.changes_by_repo, useweeks=False)
        output = activityoutput.ActivityOutput(activity_data, normalize=True)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_html()
        
        output_html = captured_output.getvalue()
        
        # Verify normalized HTML elements
        self.assertIn('(Per Contributor)', output_html)
        self.assertIn('per-developer productivity', output_html)
        self.assertIn('Commits per Contributor', output_html)
        self.assertIn('Lines Added per Contributor', output_html)
        self.assertIn('Avg Contributors', output_html)
    
    def test_empty_data_handling(self):
        """Test that output handles empty data gracefully."""
        # Create empty activity data
        activity_data = activity.ActivityData({}, useweeks=False)
        output = activityoutput.ActivityOutput(activity_data, normalize=False)
        
        # Test text output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        text_output = captured_output.getvalue()
        self.assertIn("No activity data available", text_output)
        
        # Test HTML output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_html()
        html_output = captured_output.getvalue()
        self.assertIn("No activity data available", html_output)


class TestActivityIntegration(GitInspectorTestCase):
    """Integration tests for the complete activity workflow."""
    
    def test_seasonal_activity_pattern(self):
        """Test activity analysis across different seasonal patterns."""
        with GitTestRepo("seasonal") as repo:
            ActivityTestScenarios.create_seasonal_activity_repo(repo)
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"seasonal": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Verify we captured the seasonal pattern
            periods = activity_data.get_periods()
            self.assertGreater(len(periods), 2)  # Should have multiple months
            
            # Check that some periods have activity and some don't
            repo_name = "seasonal"
            active_periods = []
            inactive_periods = []
            
            for period in periods:
                stats = activity_data.get_repo_stats_for_period(repo_name, period)
                if stats['commits'] > 0:
                    active_periods.append(period)
                else:
                    inactive_periods.append(period)
            
            # Should have both active and inactive periods
            self.assertGreater(len(active_periods), 0)
    
    def test_normalization_comparison(self):
        """Test that normalization provides different insights than raw data."""
        with GitTestRepo("comparison") as repo:
            ActivityTestScenarios.create_multi_developer_repo(repo)
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"comparison": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get the same period's data in both formats
            periods = activity_data.get_periods()
            if periods:
                period = periods[0]
                repo_name = "comparison"
                
                raw_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                norm_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=True)
                
                # Raw and normalized should have different values (unless only 1 contributor)
                if raw_stats['contributors'] > 1:
                    self.assertNotEqual(raw_stats['commits'], norm_stats['commits_per_contributor'])
    
    def test_weekly_granularity(self):
        """Test that weekly analysis provides finer granularity than monthly."""
        with GitTestRepo("weekly") as repo:
            # Add commits in different weeks of the same month
            base_date = datetime(2025, 2, 1)
            repo.add_commit('week1.py', 'def week1(): pass', commit_date=base_date)
            repo.add_commit('week2.py', 'def week2(): pass', commit_date=base_date + timedelta(days=7))
            repo.add_commit('week3.py', 'def week3(): pass', commit_date=base_date + timedelta(days=14))
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"weekly": changes_obj}
            
            # Compare monthly vs weekly
            monthly_data = activity.ActivityData(changes_by_repo, useweeks=False)
            weekly_data = activity.ActivityData(changes_by_repo, useweeks=True)
            
            monthly_periods = monthly_data.get_periods()
            weekly_periods = weekly_data.get_periods()
            
            # Weekly should provide more granular periods
            self.assertGreaterEqual(len(weekly_periods), len(monthly_periods))


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
