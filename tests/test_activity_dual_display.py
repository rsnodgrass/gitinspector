#!/usr/bin/env python3
"""
Unit tests for dual display functionality in the GitInspector activity feature.

Tests the new --activity-dual option that shows both raw totals and 
normalized per-contributor statistics side-by-side.
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import activity, changes
from gitinspector.output import activityoutput
from tests.test_helpers import GitTestRepo, ActivityTestScenarios, GitInspectorTestCase


class TestActivityDualDisplay(GitInspectorTestCase):
    """Test the dual display functionality for activity output."""
    
    def setUp(self):
        """Set up test data for dual display testing."""
        super().setUp()
        
        # Create test data with known values
        with GitTestRepo("dual_test") as repo:
            ActivityTestScenarios.create_multi_developer_repo(repo)
            changes_obj = changes.Changes(None, hard=True)
            self.changes_by_repo = {"dual_test": changes_obj}
            self.activity_data = activity.ActivityData(self.changes_by_repo, useweeks=False)
    
    def test_activity_output_constructor_with_dual_option(self):
        """Test that ActivityOutput constructor accepts the show_both parameter."""
        # Test default behavior (single mode)
        output_single = activityoutput.ActivityOutput(self.activity_data, normalize=False)
        self.assertFalse(output_single.show_both)
        self.assertFalse(output_single.normalize)
        
        # Test normalized single mode
        output_norm = activityoutput.ActivityOutput(self.activity_data, normalize=True)
        self.assertFalse(output_norm.show_both)
        self.assertTrue(output_norm.normalize)
        
        # Test dual mode
        output_dual = activityoutput.ActivityOutput(self.activity_data, normalize=False, show_both=True)
        self.assertTrue(output_dual.show_both)
        self.assertFalse(output_dual.normalize)
        
        # Test dual mode with normalize (should still show both)
        output_dual_norm = activityoutput.ActivityOutput(self.activity_data, normalize=True, show_both=True)
        self.assertTrue(output_dual_norm.show_both)
        self.assertTrue(output_dual_norm.normalize)
    
    def test_text_output_dual_display(self):
        """Test that dual display shows both raw and normalized columns in text output."""
        output = activityoutput.ActivityOutput(self.activity_data, normalize=False, show_both=True)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        
        output_text = captured_output.getvalue()
        
        # Verify dual display elements are present
        self.assertIn("raw totals and per-contributor averages", output_text)
        self.assertIn("Contribs", output_text)  # Contributors column
        self.assertIn("Commits", output_text)   # Raw commits column
        self.assertIn("C/Dev", output_text)     # Commits per dev column
        self.assertIn("Lines+", output_text)    # Raw lines added column
        self.assertIn("L+/Dev", output_text)    # Lines added per dev column
        self.assertIn("Lines-", output_text)    # Raw lines deleted column
        self.assertIn("L-/Dev", output_text)    # Lines deleted per dev column
        self.assertIn("TOTAL", output_text)     # Summary row
    
    def test_text_output_single_mode_raw(self):
        """Test that single mode shows only raw data when normalize=False."""
        output = activityoutput.ActivityOutput(self.activity_data, normalize=False, show_both=False)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        
        output_text = captured_output.getvalue()
        
        # Verify single mode raw elements
        self.assertNotIn("raw totals and per-contributor averages", output_text)
        self.assertIn("Contributors", output_text)
        self.assertIn("Commits", output_text)
        self.assertIn("Insertions", output_text)
        self.assertIn("Deletions", output_text)
        self.assertNotIn("C/Dev", output_text)      # No normalized columns
        self.assertNotIn("L+/Dev", output_text)
        self.assertNotIn("L-/Dev", output_text)
    
    def test_text_output_single_mode_normalized(self):
        """Test that single mode shows only normalized data when normalize=True."""
        output = activityoutput.ActivityOutput(self.activity_data, normalize=True, show_both=False)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        
        output_text = captured_output.getvalue()
        
        # Verify single mode normalized elements
        self.assertIn("normalized per contributor", output_text)
        self.assertIn("Contributors", output_text)
        self.assertIn("Commits/Dev", output_text)
        self.assertIn("Lines+/Dev", output_text)
        self.assertIn("Lines-/Dev", output_text)
        self.assertNotIn("raw totals", output_text)
    
    def test_html_output_dual_display(self):
        """Test that dual display works correctly in HTML output."""
        output = activityoutput.ActivityOutput(self.activity_data, normalize=False, show_both=True)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_html()
        
        output_html = captured_output.getvalue()
        
        # Verify HTML dual display elements
        self.assertIn('<h4>Repository Activity Over Time</h4>', output_html)
        self.assertIn('both raw totals and per-contributor averages', output_html)
        
        # Should have both raw and normalized charts
        self.assertIn('Commits (Total)', output_html)
        self.assertIn('Commits per Contributor', output_html)
        self.assertIn('Lines Added (Total)', output_html)
        self.assertIn('Lines Added per Contributor', output_html)
        self.assertIn('Lines Deleted (Total)', output_html)
        self.assertIn('Lines Deleted per Contributor', output_html)
        
        # Summary table should have both columns
        self.assertIn('<th>Total Commits</th>', output_html)
        self.assertIn('<th>Commits/Dev</th>', output_html)
        self.assertIn('<th>Total Lines+</th>', output_html)
        self.assertIn('<th>Lines+/Dev</th>', output_html)
    
    def test_html_output_single_mode_raw(self):
        """Test that single mode HTML shows only raw charts."""
        output = activityoutput.ActivityOutput(self.activity_data, normalize=False, show_both=False)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_html()
        
        output_html = captured_output.getvalue()
        
        # Verify single mode raw HTML
        self.assertNotIn('(Per Contributor)', output_html)
        self.assertIn('Raw statistics show absolute numbers', output_html)
        
        # Should have only raw charts
        self.assertIn('Commits by Repository', output_html)
        self.assertIn('Lines Added by Repository', output_html)
        self.assertIn('Lines Deleted by Repository', output_html)
        self.assertNotIn('per Contributor', output_html)
    
    def test_html_output_single_mode_normalized(self):
        """Test that single mode HTML shows only normalized charts."""
        output = activityoutput.ActivityOutput(self.activity_data, normalize=True, show_both=False)
        
        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_html()
        
        output_html = captured_output.getvalue()
        
        # Verify single mode normalized HTML
        self.assertIn('(Per Contributor)', output_html)
        self.assertIn('per-developer productivity', output_html)
        
        # Should have only normalized charts
        self.assertIn('Commits per Contributor', output_html)
        self.assertIn('Lines Added per Contributor', output_html)
        self.assertIn('Lines Deleted per Contributor', output_html)
        self.assertNotIn('(Total)', output_html)


class TestActivityDualDisplayDataAccuracy(GitInspectorTestCase):
    """Test that dual display shows accurate data for both raw and normalized values."""
    
    def test_dual_display_data_consistency(self):
        """Test that dual display shows consistent data between raw and normalized."""
        with GitTestRepo("consistency_test") as repo:
            # Create specific scenario with known values
            repo.add_commit('file1.py', 'line1\nline2\n', 'Dev1', 'dev1@example.com', 'Commit 1')
            repo.add_commit('file2.py', 'line1\nline2\nline3\n', 'Dev2', 'dev2@example.com', 'Commit 2')
            
            changes_obj = changes.Changes(None, hard=True)
            changes_by_repo = {"consistency_test": changes_obj}
            activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
            
            # Get both raw and normalized stats for the same period
            repositories = activity_data.get_repositories()
            periods = activity_data.get_periods()
            
            if repositories and periods:
                repo_name = repositories[0]
                period = periods[0]
                
                raw_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=False)
                norm_stats = activity_data.get_repo_stats_for_period(repo_name, period, normalized=True)
                
                # Verify normalization calculations are correct
                if raw_stats['contributors'] > 0:
                    expected_commits_per_dev = raw_stats['commits'] / raw_stats['contributors']
                    expected_insertions_per_dev = raw_stats['insertions'] / raw_stats['contributors']
                    expected_deletions_per_dev = raw_stats['deletions'] / raw_stats['contributors']
                    
                    self.assertAlmostEqual(norm_stats['commits_per_contributor'], expected_commits_per_dev, places=2)
                    self.assertAlmostEqual(norm_stats['insertions_per_contributor'], expected_insertions_per_dev, places=2)
                    self.assertAlmostEqual(norm_stats['deletions_per_contributor'], expected_deletions_per_dev, places=2)
    
    def test_dual_display_with_zero_contributors(self):
        """Test that dual display handles edge cases with zero contributors gracefully."""
        # Create empty activity data
        activity_data = activity.ActivityData({}, useweeks=False)
        output = activityoutput.ActivityOutput(activity_data, normalize=False, show_both=True)
        
        # Should not crash with empty data
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            output.output_text()
        
        output_text = captured_output.getvalue()
        self.assertIn("No activity data available", output_text)


class TestActivityParameterIntegration(GitInspectorTestCase):
    """Test integration of the dual display parameter with the main GitInspector CLI."""
    
    def test_activity_dual_parameter_parsing(self):
        """Test that the --activity-dual parameter is correctly parsed."""
        # This would typically require integration testing with the main CLI
        # For now, we test the parameter structure
        
        # Test that the parameter exists in the CLI options
        from gitinspector import gitinspector
        
        # Create a runner instance
        runner = gitinspector.Runner()
        
        # Verify the activity_dual attribute exists and defaults to False
        self.assertFalse(runner.activity_dual)
        
        # Verify it can be set to True
        runner.activity_dual = True
        self.assertTrue(runner.activity_dual)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
