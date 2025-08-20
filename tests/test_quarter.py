#!/usr/bin/env python3
"""
Unit tests for the quarter functionality in GitInspector.

Tests that the --quarter option correctly sets since and until dates
for business quarters.
"""

import os
import sys
import unittest
from datetime import datetime

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.interval import set_quarter, get_since, get_until, set_since, set_until


class TestQuarterFunctionality(unittest.TestCase):
    """Test the quarter parsing and date setting functionality."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing interval settings
        set_since("")
        set_until("")

    def test_q1_2025(self):
        """Test Q1-2025 (Jan 1 - Mar 31)."""
        set_quarter("Q1-2025")
        self.assertEqual(get_since(), "--since=2025-01-01")
        self.assertEqual(get_until(), "--until=2025-03-31")

    def test_q2_2025(self):
        """Test Q2-2025 (Apr 1 - Jun 30)."""
        set_quarter("Q2-2025")
        self.assertEqual(get_since(), "--since=2025-04-01")
        self.assertEqual(get_until(), "--until=2025-06-30")

    def test_q3_2025(self):
        """Test Q3-2025 (Jul 1 - Sep 30)."""
        set_quarter("Q3-2025")
        self.assertEqual(get_since(), "--since=2025-07-01")
        self.assertEqual(get_until(), "--until=2025-09-30")

    def test_q4_2025(self):
        """Test Q4-2025 (Oct 1 - Dec 31)."""
        set_quarter("Q4-2025")
        self.assertEqual(get_since(), "--since=2025-10-01")
        self.assertEqual(get_until(), "--until=2025-12-31")

    def test_case_insensitive(self):
        """Test that quarter parsing is case insensitive."""
        set_quarter("q2-2025")
        self.assertEqual(get_since(), "--since=2025-04-01")
        self.assertEqual(get_until(), "--until=2025-06-30")

    def test_different_years(self):
        """Test quarters for different years."""
        set_quarter("Q1-2024")
        self.assertEqual(get_since(), "--since=2024-01-01")
        self.assertEqual(get_until(), "--until=2024-03-31")

        set_quarter("Q4-2026")
        self.assertEqual(get_since(), "--since=2026-10-01")
        self.assertEqual(get_until(), "--until=2026-12-31")

    def test_invalid_quarter_number(self):
        """Test that invalid quarter numbers raise ValueError."""
        with self.assertRaises(ValueError) as context:
            set_quarter("Q5-2025")
        self.assertIn("Invalid quarter format", str(context.exception))

    def test_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        invalid_formats = [
            "Q1-202",      # Short year
            "Q1-20255",    # Long year
            "Q1-2025-",    # Extra dash
            "Q1-2025-01",  # Extra date part
            "Q1",          # Missing year
            "2025-Q1",     # Wrong order
            "Q1_2025",     # Wrong separator
            "Q1 2025",     # Space separator
        ]
        
        for invalid_format in invalid_formats:
            with self.assertRaises(ValueError) as context:
                set_quarter(invalid_format)
            self.assertIn("Invalid quarter format", str(context.exception))

    def test_quarter_boundaries(self):
        """Test that quarter boundaries are correct."""
        # Q1: Jan 1 - Mar 31
        set_quarter("Q1-2025")
        self.assertEqual(get_since(), "--since=2025-01-01")
        self.assertEqual(get_until(), "--until=2025-03-31")
        
        # Q2: Apr 1 - Jun 30
        set_quarter("Q2-2025")
        self.assertEqual(get_since(), "--since=2025-04-01")
        self.assertEqual(get_until(), "--until=2025-06-30")
        
        # Q3: Jul 1 - Sep 30
        set_quarter("Q3-2025")
        self.assertEqual(get_since(), "--since=2025-07-01")
        self.assertEqual(get_until(), "--until=2025-09-30")
        
        # Q4: Oct 1 - Dec 31
        set_quarter("Q4-2025")
        self.assertEqual(get_since(), "--since=2025-10-01")
        self.assertEqual(get_until(), "--until=2025-12-31")

    def test_quarter_overwrites_previous(self):
        """Test that setting a new quarter overwrites previous settings."""
        # Set initial quarter
        set_quarter("Q1-2025")
        self.assertEqual(get_since(), "--since=2025-01-01")
        self.assertEqual(get_until(), "--until=2025-03-31")
        
        # Set new quarter
        set_quarter("Q3-2026")
        self.assertEqual(get_since(), "--since=2026-07-01")
        self.assertEqual(get_until(), "--until=2026-09-30")

    def test_quarter_with_manual_dates(self):
        """Test that quarter works with manually set dates."""
        # Set manual dates first
        set_since("2024-01-01")
        set_until("2024-12-31")
        
        # Set quarter (should overwrite manual dates)
        set_quarter("Q2-2025")
        self.assertEqual(get_since(), "--since=2025-04-01")
        self.assertEqual(get_until(), "--until=2025-06-30")


if __name__ == "__main__":
    unittest.main()
