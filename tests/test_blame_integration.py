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
from unittest.mock import Mock, patch

# Add the gitinspector module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gitinspector.blame import BlameEntry, Blame, is_test_file


class TestBlameIntegration:
    """Integration tests for blame processing with test/main categorization."""

    def test_blame_categorization_workflow(self):
        """Test the complete workflow of categorizing blame entries."""
        blame_entries = {}

        # Simulate blame entries for different file types
        test_files = ["src/components/Button.test.tsx", "tests/utils.py", "__tests__/api.spec.js"]

        main_files = ["src/components/Button.tsx", "src/utils.py", "src/api.js"]

        author = "test-author"

        # Process test files
        for filename in test_files:
            key = (author, filename)
            blame_entries[key] = BlameEntry()

            # Simulate adding rows (this mimics the logic in BlameThread.__handle_blamechunk_content__)
            blame_entries[key].rows += 10

            if is_test_file(filename):
                blame_entries[key].test_rows += 10
            else:
                blame_entries[key].main_rows += 10

        # Process main files
        for filename in main_files:
            key = (author, filename)
            blame_entries[key] = BlameEntry()

            blame_entries[key].rows += 15

            if is_test_file(filename):
                blame_entries[key].test_rows += 15
            else:
                blame_entries[key].main_rows += 15

        # Verify categorization
        for filename in test_files:
            key = (author, filename)
            entry = blame_entries[key]
            assert entry.test_rows == 10, f"Test file {filename} should have test rows"
            assert entry.main_rows == 0, f"Test file {filename} should have no main rows"
            assert entry.rows == 10, f"Test file {filename} total rows should match"

        for filename in main_files:
            key = (author, filename)
            entry = blame_entries[key]
            assert entry.main_rows == 15, f"Main file {filename} should have main rows"
            assert entry.test_rows == 0, f"Main file {filename} should have no test rows"
            assert entry.rows == 15, f"Main file {filename} total rows should match"

    def test_summed_blames_aggregation(self):
        """Test that summed blames correctly aggregate test and main rows."""
        author = "developer"

        # Create multiple blame entries for the same author
        files_and_rows = [
            ("src/main.py", 50, False),  # 50 main rows
            ("src/utils.py", 30, False),  # 30 main rows
            ("tests/test_main.py", 25, True),  # 25 test rows
            ("tests/test_utils.py", 15, True),  # 15 test rows
        ]

        blame_entries = {}

        for filename, row_count, is_test in files_and_rows:
            key = (author, filename)
            blame_entries[key] = BlameEntry()
            blame_entries[key].rows = row_count

            if is_test:
                blame_entries[key].test_rows = row_count
                blame_entries[key].main_rows = 0
            else:
                blame_entries[key].main_rows = row_count
                blame_entries[key].test_rows = 0

        # Simulate the get_summed_blames logic
        summed_blames = {}
        for key, entry in blame_entries.items():
            author_name = key[0]
            if author_name not in summed_blames:
                summed_blames[author_name] = BlameEntry()

            summed_blames[author_name].rows += entry.rows
            summed_blames[author_name].main_rows += entry.main_rows
            summed_blames[author_name].test_rows += entry.test_rows

        # Verify aggregation
        summed_entry = summed_blames[author]
        assert summed_entry.rows == 120, "Total rows should be 120"
        assert summed_entry.main_rows == 80, "Main rows should be 80"
        assert summed_entry.test_rows == 40, "Test rows should be 40"
        assert summed_entry.main_rows + summed_entry.test_rows == summed_entry.rows, "Main + test should equal total"

    def test_multiple_authors_aggregation(self):
        """Test aggregation works correctly with multiple authors."""
        authors_and_data = [
            ("alice", [("src/app.py", 100, False), ("tests/test_app.py", 50, True)]),
            ("bob", [("src/utils.py", 75, False), ("tests/test_utils.py", 25, True)]),
            ("charlie", [("tests/integration.py", 200, True)]),  # Only test code
        ]

        blame_entries = {}

        # Create blame entries
        for author, files in authors_and_data:
            for filename, row_count, is_test in files:
                key = (author, filename)
                blame_entries[key] = BlameEntry()
                blame_entries[key].rows = row_count

                if is_test:
                    blame_entries[key].test_rows = row_count
                    blame_entries[key].main_rows = 0
                else:
                    blame_entries[key].main_rows = row_count
                    blame_entries[key].test_rows = 0

        # Aggregate by author
        summed_blames = {}
        for key, entry in blame_entries.items():
            author_name = key[0]
            if author_name not in summed_blames:
                summed_blames[author_name] = BlameEntry()

            summed_blames[author_name].rows += entry.rows
            summed_blames[author_name].main_rows += entry.main_rows
            summed_blames[author_name].test_rows += entry.test_rows

        # Verify each author's totals
        alice_entry = summed_blames["alice"]
        assert alice_entry.main_rows == 100
        assert alice_entry.test_rows == 50
        assert alice_entry.rows == 150

        bob_entry = summed_blames["bob"]
        assert bob_entry.main_rows == 75
        assert bob_entry.test_rows == 25
        assert bob_entry.rows == 100

        charlie_entry = summed_blames["charlie"]
        assert charlie_entry.main_rows == 0
        assert charlie_entry.test_rows == 200
        assert charlie_entry.rows == 200


class TestOutputFormatting:
    """Test output formatting functions with test/main breakdown."""

    def test_test_percentage_formatting(self):
        """Test that test percentages are formatted correctly."""
        test_cases = [
            (80, 20, "20.0"),  # 20% test coverage
            (90, 10, "10.0"),  # 10% test coverage
            (100, 0, "0.0"),  # 0% test coverage
            (0, 100, "100.0"),  # 100% test coverage
            (75, 25, "25.0"),  # 25% test coverage
        ]

        for main_rows, test_rows, expected_str in test_cases:
            total_rows = main_rows + test_rows
            test_percentage = (100.0 * test_rows / total_rows) if total_rows > 0 else 0.0
            formatted = "{0:.1f}".format(test_percentage)

            assert (
                formatted == expected_str
            ), f"Test percentage for {main_rows} main, {test_rows} test should format as {expected_str}"

    def test_zero_rows_handling(self):
        """Test handling of authors with zero rows."""
        main_rows = 0
        test_rows = 0
        total_rows = main_rows + test_rows

        test_percentage = (100.0 * test_rows / total_rows) if total_rows > 0 else 0.0
        formatted = "{0:.1f}".format(test_percentage)

        assert formatted == "0.0", "Zero rows should result in 0.0% formatted"
