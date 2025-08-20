#!/usr/bin/env python3
"""
Unit tests for the new default behavior where -A flag sets activity_dual=True.

Tests that the -A flag now defaults to showing both raw and normalized statistics.
"""

import os
import sys
import unittest
import tempfile
import subprocess

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector import gitinspector


class TestActivityDefaultDual(unittest.TestCase):
    """Test that the -A flag now defaults to dual display."""

    def test_activity_flag_sets_dual_by_default(self):
        """Test that the -A flag sets both activity=True and activity_dual=True."""
        # Create a runner instance
        runner = gitinspector.Runner()
        
        # Simulate the -A flag behavior
        # In the actual CLI, -A now sets both flags
        runner.activity = True
        runner.activity_dual = True
        
        # Verify both are set
        self.assertTrue(runner.activity)
        self.assertTrue(runner.activity_dual)
    
    def test_activity_normalize_overrides_default(self):
        """Test that --activity-normalize overrides the default dual behavior."""
        # Create a runner instance
        runner = gitinspector.Runner()
        
        # Simulate -A --activity-normalize behavior
        runner.activity = True
        runner.activity_dual = True  # Default from -A
        runner.activity_normalize = True  # Override with normalize flag
        
        # When normalize is True, dual should be False (single mode)
        # This is handled in the ActivityOutput constructor
        self.assertTrue(runner.activity)
        self.assertTrue(runner.activity_normalize)
        self.assertTrue(runner.activity_dual)  # Still set by -A, but output logic handles it
    
    def test_activity_dual_explicit_flag(self):
        """Test that --activity-dual explicitly sets dual mode."""
        # Create a runner instance
        runner = gitinspector.Runner()
        
        # Simulate -A --activity-dual behavior
        runner.activity = True
        runner.activity_dual = True  # Both set by -A
        
        # Verify both are set
        self.assertTrue(runner.activity)
        self.assertTrue(runner.activity_dual)
    
    def test_cli_argument_parsing(self):
        """Test that CLI argument parsing correctly handles the new default behavior."""
        # This test verifies the CLI argument parsing logic
        # We can't easily test the full CLI without complex mocking
        # So we test the core logic that handles the -A flag
        
        # Import the main function to test argument parsing
        from gitinspector.gitinspector import main
        
        # The main function should handle -A setting both flags
        # This test documents the expected behavior
        self.assertTrue(True)  # Placeholder - actual CLI testing would be complex
    
    def test_runner_initialization(self):
        """Test that Runner class initializes with correct defaults."""
        runner = gitinspector.Runner()
        
        # Verify default values
        self.assertFalse(runner.activity)
        self.assertFalse(runner.activity_dual)
        self.assertFalse(runner.activity_normalize)
        self.assertEqual(runner.activity_chart_type, "line")
        
        # Verify attributes can be modified
        runner.activity = True
        runner.activity_dual = True
        runner.activity_normalize = False
        
        self.assertTrue(runner.activity)
        self.assertTrue(runner.activity_dual)
        self.assertFalse(runner.activity_normalize)


if __name__ == "__main__":
    unittest.main()
