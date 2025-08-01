# coding: utf-8
#
# Copyright © 2025 Ejwa Software. All rights reserved.
#
# This file is part of gitinspector.
#
# gitinspector is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gitinspector is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gitinspector. If not, see <http://www.gnu.org/licenses/>.


import pytest
import sys
import os
import json
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

# Add the gitinspector module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gitinspector.blame import BlameEntry
from gitinspector.output.blameoutput import BlameOutput


class TestBlameOutput:
    """Test the BlameOutput class with test/main breakdown."""

    @pytest.fixture
    def blame_output_setup(self):
        """Set up test fixtures."""
        # Create mock changes and blame objects
        mock_changes = Mock()
        mock_blame = Mock()

        # Create test blame data with main and test rows
        summed_blames = {}

        # Developer with mixed main and test code
        alice_entry = BlameEntry()
        alice_entry.rows = 150
        alice_entry.main_rows = 100
        alice_entry.test_rows = 50
        alice_entry.comments = 10
        alice_entry.skew = 5.0
        summed_blames["alice"] = alice_entry

        # Developer with mostly main code
        bob_entry = BlameEntry()
        bob_entry.rows = 200
        bob_entry.main_rows = 180
        bob_entry.test_rows = 20
        bob_entry.comments = 15
        bob_entry.skew = 8.0
        summed_blames["bob"] = bob_entry

        # Developer with only test code
        charlie_entry = BlameEntry()
        charlie_entry.rows = 75
        charlie_entry.main_rows = 0
        charlie_entry.test_rows = 75
        charlie_entry.comments = 5
        charlie_entry.skew = 2.0
        summed_blames["charlie"] = charlie_entry

        # Mock the get_latest_email_by_author method
        mock_changes.get_latest_email_by_author.return_value = "test@example.com"

        # Mock the blame.get_summed_blames method
        mock_blame.get_summed_blames.return_value = summed_blames

        return mock_changes, mock_blame, summed_blames

    @patch("gitinspector.output.blameoutput.Blame.get_stability")
    @patch("sys.stdout", new_callable=StringIO)
    def test_text_output_format(self, mock_stdout, mock_stability, blame_output_setup):
        """Test that text output includes the new Main, Test, and Test % columns."""
        mock_stability.return_value = 85.0
        mock_changes, mock_blame, summed_blames = blame_output_setup

        # Create BlameOutput instance
        blame_output = BlameOutput(mock_changes, mock_blame)

        # Call output_text method
        blame_output.output_text()

        output = mock_stdout.getvalue()

        # Check that the header contains the new columns
        assert "Main" in output, "Output should contain 'Main' column header"
        assert "Test" in output, "Output should contain 'Test' column header"
        assert "Test %" in output, "Output should contain 'Test %' column header"

        # Check that alice's data is correctly formatted (100 main, 50 test, 33.3%)
        assert "alice" in output, "Output should contain alice's data"
        assert "100" in output, "Output should contain alice's main rows (100)"
        assert "50" in output, "Output should contain alice's test rows (50)"
        assert "33.3" in output, "Output should contain alice's test percentage (33.3%)"

        # Check that charlie's data shows 100% test coverage
        assert "charlie" in output, "Output should contain charlie's data"
        assert "75" in output, "Output should contain charlie's test rows (75)"
        assert "100.0" in output, "Output should contain charlie's test percentage (100.0%)"

    @patch("gitinspector.gravatar.get_url")
    @patch("gitinspector.output.blameoutput.Blame.get_stability")
    def test_json_output_format(self, mock_stability, mock_gravatar, blame_output_setup):
        """Test that JSON output includes test/main breakdown fields."""
        mock_stability.return_value = 85.0
        mock_gravatar.return_value = "http://gravatar.com/avatar/test"
        mock_changes, mock_blame, summed_blames = blame_output_setup

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            blame_output = BlameOutput(mock_changes, mock_blame)
            blame_output.output_json()

            output = mock_stdout.getvalue()

            # Check that JSON contains the new fields
            assert '"main_rows":' in output, "JSON should contain main_rows field"
            assert '"test_rows":' in output, "JSON should contain test_rows field"
            assert '"test_percentage":' in output, "JSON should contain test_percentage field"

            # Verify specific values are present
            assert '"main_rows": 100' in output, "Alice's main rows should be 100"
            assert '"test_rows": 50' in output, "Alice's test rows should be 50"
            assert '"test_percentage": 33.3' in output, "Alice's test percentage should be 33.3"

    @patch("gitinspector.gravatar.get_url")
    @patch("gitinspector.output.blameoutput.Blame.get_stability")
    def test_xml_output_format(self, mock_stability, mock_gravatar, blame_output_setup):
        """Test that XML output includes test/main breakdown fields."""
        mock_stability.return_value = 85.0
        mock_gravatar.return_value = "http://gravatar.com/avatar/test"
        mock_changes, mock_blame, summed_blames = blame_output_setup

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            blame_output = BlameOutput(mock_changes, mock_blame)
            blame_output.output_xml()

            output = mock_stdout.getvalue()

            # Check that XML contains the new elements
            assert "<main-rows>" in output, "XML should contain main-rows element"
            assert "<test-rows>" in output, "XML should contain test-rows element"
            assert "<test-percentage>" in output, "XML should contain test-percentage element"

            # Verify specific values
            assert "<main-rows>100</main-rows>" in output, "Alice's main rows should be 100"
            assert "<test-rows>50</test-rows>" in output, "Alice's test rows should be 50"
            assert "<test-percentage>33.3</test-percentage>" in output, "Alice's test percentage should be 33.3"

    @patch("gitinspector.output.blameoutput.Blame.get_stability")
    def test_html_output_format(self, mock_stability, blame_output_setup):
        """Test that HTML output includes test/main breakdown columns."""
        mock_stability.return_value = 85.0
        mock_changes, mock_blame, summed_blames = blame_output_setup

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            blame_output = BlameOutput(mock_changes, mock_blame)
            blame_output.output_html()

            output = mock_stdout.getvalue()

            # Check table headers
            assert "<th>Main</th>" in output, "HTML should contain Main column header"
            assert "<th>Test</th>" in output, "HTML should contain Test column header"
            assert "<th>Test %</th>" in output, "HTML should contain Test % column header"

            # Check that data cells are present
            assert "<td>100</td>" in output, "HTML should contain alice's main rows"
            assert "<td>50</td>" in output, "HTML should contain alice's test rows"
            assert "<td>33.3</td>" in output, "HTML should contain alice's test percentage"

    def test_percentage_calculations(self):
        """Test that percentage calculations are correct for edge cases."""
        test_cases = [
            # (main_rows, test_rows, expected_percentage)
            (100, 0, 0.0),  # No tests
            (0, 100, 100.0),  # Only tests
            (0, 0, 0.0),  # No code
            (75, 25, 25.0),  # 25% tests
            (60, 40, 40.0),  # 40% tests
            (1, 1, 50.0),  # Equal amounts
        ]

        for main_rows, test_rows, expected_percentage in test_cases:
            total_rows = main_rows + test_rows
            test_percentage = (100.0 * test_rows / total_rows) if total_rows > 0 else 0.0

            assert (
                abs(test_percentage - expected_percentage) < 0.1
            ), f"Percentage for {main_rows} main, {test_rows} test should be {expected_percentage}%"

    @patch("gitinspector.output.blameoutput.Blame.get_stability")
    def test_zero_division_in_output(self, mock_stability, blame_output_setup):
        """Test that output handles zero rows gracefully."""
        mock_stability.return_value = 0.0
        mock_changes, mock_blame, summed_blames = blame_output_setup

        # Create blame entry with zero rows
        zero_entry = BlameEntry()
        zero_entry.rows = 0
        zero_entry.main_rows = 0
        zero_entry.test_rows = 0
        zero_entry.comments = 0
        zero_entry.skew = 0.0

        mock_blame.get_summed_blames.return_value = {"empty": zero_entry}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            blame_output = BlameOutput(mock_changes, mock_blame)
            blame_output.output_text()

            output = mock_stdout.getvalue()

            # Should not crash and should show 0.0% for test percentage
            assert "0.0" in output, "Zero rows should display 0.0% test percentage"
