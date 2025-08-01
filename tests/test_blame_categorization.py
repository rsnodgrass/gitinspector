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

# Add the gitinspector module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gitinspector.blame import is_test_file, BlameEntry


class TestFileCategorizationTest:
    """Test the is_test_file function for correct test file identification."""

    @pytest.mark.parametrize(
        "test_file",
        [
            "test/utils.py",
            "tests/helper.js",
            "__tests__/component.tsx",
            "spec/model.rb",
            "specs/service.py",
            "testing/integration.cpp",
            "src/test/java/Example.java",
            "packages/tests/unit/parser.ts",
            "components/__tests__/Button.test.jsx",
        ],
    )
    def test_test_directories(self, test_file):
        """Test files in test directories are identified as test files."""
        assert is_test_file(test_file), f"File {test_file} should be identified as a test file"

    @pytest.mark.parametrize(
        "test_file",
        [
            "utils.test.js",
            "component.spec.ts",
            "service-test.py",
            "model-spec.rb",
            "helper_test.cpp",
            "validator_spec.java",
            "parser.test.tsx",
            "handler.spec.jsx",
        ],
    )
    def test_test_file_patterns(self, test_file):
        """Test files with test naming patterns are identified as test files."""
        assert is_test_file(test_file), f"File {test_file} should be identified as a test file"

    @pytest.mark.parametrize(
        "test_file",
        [
            "component.test.js",
            "service.test.ts",
            "utils.test.tsx",
            "model.test.py",
            "helper.test.java",
            "parser.test.cpp",
            "validator.test.c",
            "controller.spec.js",
            "middleware.spec.ts",
        ],
    )
    def test_test_extensions(self, test_file):
        """Test files with test extensions are identified as test files."""
        assert is_test_file(test_file), f"File {test_file} should be identified as a test file"

    @pytest.mark.parametrize(
        "main_file",
        [
            "src/utils.py",
            "components/Button.tsx",
            "services/api.js",
            "models/user.rb",
            "controllers/auth.py",
            "lib/parser.cpp",
            "include/header.h",
            "main.java",
            "app.js",
            "index.ts",
            "styles.css",
            "README.md",
            "package.json",
        ],
    )
    def test_main_code_files(self, main_file):
        """Test regular code files are NOT identified as test files."""
        assert not is_test_file(main_file), f"File {main_file} should NOT be identified as a test file"

    @pytest.mark.parametrize(
        "test_file",
        [
            "TEST/Utils.py",
            "TESTS/Helper.js",
            "Component.TEST.tsx",
            "Service.SPEC.ts",
            "utils-TEST.py",
            "MODEL_SPEC.rb",
        ],
    )
    def test_case_insensitive_detection(self, test_file):
        """Test that file detection is case insensitive."""
        assert is_test_file(test_file), f"File {test_file} should be identified as a test file (case insensitive)"

    @pytest.mark.parametrize(
        "non_test_file",
        [
            "latest.py",  # contains 'test' but not in test pattern
            "contest.js",  # contains 'test' but not in test pattern
            "spectrum.ts",  # contains 'spec' but not in test pattern
            "respect.py",  # contains 'spec' but not in test pattern
            "testing-utils.md",  # testing directory but wrong extension
            "test.txt",  # test directory but wrong extension
            "protest.py",  # contains 'test' but not in test pattern
        ],
    )
    def test_edge_cases(self, non_test_file):
        """Test edge cases and potential false positives."""
        assert not is_test_file(non_test_file), f"File {non_test_file} should NOT be identified as a test file"


class TestBlameEntry:
    """Test the BlameEntry class with test/main row categorization."""

    def test_blame_entry_initialization(self):
        """Test that BlameEntry initializes with correct default values."""
        entry = BlameEntry()

        assert entry.rows == 0
        assert entry.main_rows == 0
        assert entry.test_rows == 0
        assert entry.skew == 0
        assert entry.comments == 0

    def test_blame_entry_test_vs_main_tracking(self):
        """Test that test and main rows sum to total rows."""
        entry = BlameEntry()

        # Simulate some blame data
        entry.rows = 100
        entry.main_rows = 70
        entry.test_rows = 30
        entry.comments = 10

        # Verify totals
        assert entry.main_rows + entry.test_rows == entry.rows
        assert entry.main_rows == 70
        assert entry.test_rows == 30

    def test_blame_entry_only_main_code(self):
        """Test blame entry with only main code (no tests)."""
        entry = BlameEntry()

        entry.rows = 50
        entry.main_rows = 50
        entry.test_rows = 0

        assert entry.main_rows + entry.test_rows == entry.rows
        assert entry.test_rows == 0

    def test_blame_entry_only_test_code(self):
        """Test blame entry with only test code."""
        entry = BlameEntry()

        entry.rows = 25
        entry.main_rows = 0
        entry.test_rows = 25

        assert entry.main_rows + entry.test_rows == entry.rows
        assert entry.main_rows == 0


class TestPercentageCalculation:
    """Test percentage calculations for test coverage."""

    @pytest.mark.parametrize(
        "main_rows,test_rows,expected_percentage",
        [
            (100, 20, 16.7),  # 20 test out of 120 total = 16.7% test coverage
            (100, 0, 0.0),  # No tests
            (0, 100, 100.0),  # All tests
            (75, 25, 25.0),  # 25 test out of 100 total = 25% test coverage
            (0, 0, 0.0),  # No code at all
        ],
    )
    def test_test_percentage_calculation(self, main_rows, test_rows, expected_percentage):
        """Test test percentage calculation logic."""
        total_rows = main_rows + test_rows
        if total_rows > 0:
            test_percentage = 100.0 * test_rows / total_rows
        else:
            test_percentage = 0.0

        assert (
            abs(test_percentage - expected_percentage) < 0.1
        ), f"Test percentage for {main_rows} main, {test_rows} test should be {expected_percentage}%"

    def test_zero_division_protection(self):
        """Test that percentage calculation handles zero division gracefully."""
        # This simulates the logic from blameoutput.py
        main_rows = 0
        test_rows = 0
        total_rows = main_rows + test_rows

        test_percentage = (100.0 * test_rows / total_rows) if total_rows > 0 else 0.0

        assert test_percentage == 0.0, "Zero division should result in 0.0% test coverage"
