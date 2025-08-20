#!/usr/bin/env python3
"""
Unit tests for collapsible HTML output functionality.

Tests that HTML output sections are properly wrapped in collapsible containers
with appropriate CSS classes and JavaScript functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch
from io import StringIO

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitinspector.output import outputable
from gitinspector.output.activityoutput import ActivityOutput
from gitinspector.output.changesoutput import ChangesOutput
from gitinspector.output.blameoutput import BlameOutput
from tests.test_helpers import GitInspectorTestCase


class MockOutputable(outputable.Outputable):
    """Mock outputable for testing collapsible functionality."""

    def __init__(self, content="<div>Test content</div>"):
        self.content = content
        super().__init__()

    def output_html(self):
        print(self.content)


class TestCollapsibleHTML(GitInspectorTestCase):
    """Test collapsible HTML output functionality."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()

    def test_section_title_mapping(self):
        """Test that section titles are correctly mapped."""
        # Test activity output title
        activity_mock = MockOutputable()
        activity_mock.__class__.__name__ = "ActivityOutput"
        title = outputable._get_section_title(activity_mock)
        self.assertEqual(title, "Repository Activity Over Time")

        # Test changes output title
        changes_mock = MockOutputable()
        changes_mock.__class__.__name__ = "ChangesOutput"
        title = outputable._get_section_title(changes_mock)
        self.assertEqual(title, "Commit History & Statistics")

        # Test blame output title
        blame_mock = MockOutputable()
        blame_mock.__class__.__name__ = "BlameOutput"
        title = outputable._get_section_title(blame_mock)
        self.assertEqual(title, "File Ownership & Code Authorship")

        # Test unknown output type (fallback)
        unknown_mock = MockOutputable()
        unknown_mock.__class__.__name__ = "CustomOutput"
        title = outputable._get_section_title(unknown_mock)
        self.assertEqual(title, "Custom Analysis")

    def test_section_id_mapping(self):
        """Test that section IDs are correctly mapped."""
        # Test activity output ID
        activity_mock = MockOutputable()
        activity_mock.__class__.__name__ = "ActivityOutput"
        section_id = outputable._get_section_id(activity_mock)
        self.assertEqual(section_id, "activity-section")

        # Test changes output ID
        changes_mock = MockOutputable()
        changes_mock.__class__.__name__ = "ChangesOutput"
        section_id = outputable._get_section_id(changes_mock)
        self.assertEqual(section_id, "changes-section")

        # Test unknown output type (fallback)
        unknown_mock = MockOutputable()
        unknown_mock.__class__.__name__ = "CustomOutput"
        section_id = outputable._get_section_id(unknown_mock)
        self.assertEqual(section_id, "custom-section")

    @patch("gitinspector.format.get_selected")
    def test_collapsible_html_wrapper(self, mock_format):
        """Test that HTML output is wrapped in collapsible sections."""
        mock_format.return_value = "html"

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Create mock outputable with test content
            test_content = '<div class="box"><h4>Test Section</h4><p>Test content</p></div>'
            mock_outputable = MockOutputable(test_content)
            mock_outputable.__class__.__name__ = "TestOutput"

            # Call the output function
            outputable.output(mock_outputable)

            # Get the generated HTML
            html_output = sys.stdout.getvalue()

        finally:
            sys.stdout = old_stdout

        # Verify collapsible structure
        self.assertIn("collapsible-header", html_output)
        self.assertIn("collapsible-content", html_output)
        self.assertIn("collapse-icon", html_output)
        self.assertIn("Test Analysis", html_output)  # Title
        self.assertIn('id="test-section"', html_output)  # Section ID
        self.assertIn(test_content, html_output)  # Original content

    @patch("gitinspector.format.get_selected")
    def test_empty_content_not_wrapped(self, mock_format):
        """Test that empty content is not wrapped in collapsible sections."""
        mock_format.return_value = "html"

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Create mock outputable with empty content
            mock_outputable = MockOutputable("")

            # Call the output function
            outputable.output(mock_outputable)

            # Get the generated HTML
            html_output = sys.stdout.getvalue()

        finally:
            sys.stdout = old_stdout

        # Verify no collapsible structure for empty content
        self.assertEqual(html_output.strip(), "")

    @patch("gitinspector.format.get_selected")
    def test_non_html_formats_unchanged(self, mock_format):
        """Test that non-HTML formats are not affected by collapsible wrapper."""
        mock_format.return_value = "text"

        # Create a mock that tracks if output_html was called
        class TrackingMock(MockOutputable):
            def __init__(self):
                super().__init__()
                self.html_called = False
                self.text_called = False

            def output_html(self):
                self.html_called = True
                print("HTML output")

            def output_text(self):
                self.text_called = True
                print("Text output")

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            mock_outputable = TrackingMock()
            outputable.output(mock_outputable)
            html_output = sys.stdout.getvalue()

        finally:
            sys.stdout = old_stdout

        # Verify text output was called, not HTML
        self.assertFalse(mock_outputable.html_called)
        self.assertTrue(mock_outputable.text_called)
        self.assertEqual(html_output.strip(), "Text output")

    def test_collapsible_css_classes(self):
        """Test that all necessary CSS classes are defined in the HTML header."""
        # Read the HTML header file
        header_path = os.path.join(os.path.dirname(__file__), "..", "gitinspector", "html", "html.header")
        with open(header_path, "r") as f:
            header_content = f.read()

        # Check for required CSS classes
        required_classes = [
            ".collapsible-header",
            ".collapsible-content",
            ".collapse-icon",
            ".collapsible-header:hover",
            ".collapsible-header.expanded",
        ]

        for css_class in required_classes:
            self.assertIn(css_class, header_content, f"CSS class {css_class} not found in header")

        # Check for JavaScript functionality
        required_js = ["collapsible-header').click", "slideUp(300)", "slideDown(300)", "collapse-icon"]

        for js_snippet in required_js:
            self.assertIn(js_snippet, header_content, f"JavaScript snippet {js_snippet} not found in header")


class TestCollapsibleIntegration(GitInspectorTestCase):
    """Integration tests for collapsible functionality with real output modules."""

    @patch("gitinspector.format.get_selected")
    def test_multiple_sections_integration(self, mock_format):
        """Test that multiple sections are properly handled."""
        mock_format.return_value = "html"

        # Capture stdout for multiple outputs
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Simulate multiple output calls
            outputs = [
                ("ActivityOutput", "<div>Activity content</div>"),
                ("ChangesOutput", "<div>Changes content</div>"),
                ("BlameOutput", "<div>Blame content</div>"),
            ]

            for class_name, content in outputs:
                mock_outputable = MockOutputable(content)
                mock_outputable.__class__.__name__ = class_name
                outputable.output(mock_outputable)

            html_output = sys.stdout.getvalue()

        finally:
            sys.stdout = old_stdout

        # Verify non-activity sections are wrapped; activity is printed directly
        expected_wrapped = [
            ("changes-section", "Commit History & Statistics"),
            ("blame-section", "File Ownership & Code Authorship"),
        ]

        for section_id, section_title in expected_wrapped:
            self.assertIn(f'id="{section_id}"', html_output)
            self.assertIn(section_title, html_output)

        # Activity content should be present without top-level collapsible wrapper
        self.assertIn("Activity content", html_output)
        self.assertNotIn('id="activity-section"', html_output)

        # Count collapsible headers (should be 2 for changes and blame)
        header_count = html_output.count("collapsible-header")
        self.assertEqual(header_count, 2)

        # Count collapsible content divs (should be 2)
        content_count = html_output.count("collapsible-content")
        self.assertEqual(content_count, 2)


class TestChartCollapsibleHTML(GitInspectorTestCase):
    """Test chart-specific collapsible functionality within activity output."""

    @patch("gitinspector.format.get_selected")
    def test_activity_chart_collapsibility(self, mock_format):
        """Test that individual activity charts are collapsible."""
        mock_format.return_value = "html"

        # Mock activity data for testing
        class MockActivityData:
            def __init__(self):
                self.useweeks = False
                # Minimal structure expected by ActivityOutput
                self.repo_activity = {
                    "repo1": {
                        "2024-01": {"commits": 5, "insertions": 50, "deletions": 25, "contributors": set(["a"])},
                        "2024-02": {"commits": 5, "insertions": 50, "deletions": 25, "contributors": set(["b"])},
                    },
                    "repo2": {
                        "2024-01": {"commits": 5, "insertions": 50, "deletions": 25, "contributors": set(["c"])},
                        "2024-02": {"commits": 5, "insertions": 50, "deletions": 25, "contributors": set(["d"])},
                    },
                }

            def get_repositories(self):
                return ["repo1", "repo2"]

            def get_periods(self):
                return ["2024-01", "2024-02"]

            def get_max_values(self, normalized=False):
                return {"commits": 10, "insertions": 100, "deletions": 50}

            def get_repo_stats_for_period(self, repo, period, normalized=False):
                return self.repo_activity.get(repo, {}).get(period, {"commits": 0, "insertions": 0, "deletions": 0})

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Create ActivityOutput with mock data
            from gitinspector.output.activityoutput import ActivityOutput

            activity_output = ActivityOutput(MockActivityData(), normalize=False, show_both=False)
            activity_output.output_html()

            html_output = sys.stdout.getvalue()

        finally:
            sys.stdout = old_stdout

        # Verify chart-specific collapsible structure
        self.assertIn("chart-collapsible-header", html_output)
        self.assertIn("chart-collapsible-content", html_output)
        self.assertIn("chart-collapse-icon", html_output)
        self.assertIn('data-target="commits-chart"', html_output)
        self.assertIn('data-target="insertions-chart"', html_output)

        # Verify individual chart titles
        self.assertIn("Commits by Repository", html_output)
        self.assertIn("Lines Added by Repository", html_output)
        self.assertIn("Lines Deleted by Repository", html_output)

    def test_chart_collapsible_css_classes(self):
        """Test that chart-specific CSS classes are defined."""
        # Read the HTML header file
        header_path = os.path.join(os.path.dirname(__file__), "..", "gitinspector", "html", "html.header")
        with open(header_path, "r") as f:
            header_content = f.read()

        # Check for chart-specific CSS classes
        required_chart_classes = [
            ".chart-collapsible-header",
            ".chart-collapsible-content",
            ".chart-collapse-icon",
            ".chart-collapsible-header:hover",
            ".chart-collapsible-header.expanded",
        ]

        for css_class in required_chart_classes:
            self.assertIn(css_class, header_content, f"Chart CSS class {css_class} not found in header")

        # Check for chart-specific JavaScript functionality
        required_chart_js = ["chart-collapsible-header').click", "data('target')", "chart-collapse-icon"]

        for js_snippet in required_chart_js:
            self.assertIn(js_snippet, header_content, f"Chart JavaScript snippet {js_snippet} not found in header")

    def test_header_content_pairing_structure(self):
        """Test that headers and content containers are properly paired."""
        # Test the data-target approach for precise ID matching
        mock_format = "html"

        with patch("gitinspector.format.get_selected", return_value=mock_format):
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                # Create a simple mock that generates the expected structure
                class TestCollapsibleOutput(outputable.Outputable):
                    def output_html(self):
                        print("<div>Test content</div>")

                test_output = TestCollapsibleOutput()
                test_output.__class__.__name__ = "TestOutput"

                outputable.output(test_output)
                html_output = sys.stdout.getvalue()

            finally:
                sys.stdout = old_stdout

        # Verify proper data-target and ID pairing
        self.assertIn('data-target="test-section"', html_output)
        self.assertIn('id="test-section"', html_output)

        # Verify structure: header immediately followed by content
        lines = html_output.strip().split("\n")
        header_line = None
        content_line = None

        for i, line in enumerate(lines):
            if "collapsible-header" in line and "data-target" in line:
                header_line = i
            elif 'id="test-section"' in line and "collapsible-content" in line:
                content_line = i
                break

        self.assertIsNotNone(header_line, "Header not found")
        self.assertIsNotNone(content_line, "Content container not found")

        # Content should come after header (allowing for closing tags)
        self.assertGreater(content_line, header_line, "Content container should come after header")

    def test_collapsible_preserves_functionality(self):
        """Test that collapsible wrapper doesn't break existing functionality."""
        # The collapsible wrapper should not interfere with:
        # - Table sorting functionality
        # - Chart generation
        # - Filtering buttons
        # - Pie chart hover effects

        # This is verified by ensuring the original content is preserved exactly
        original_content = """
        <div class="box">
            <table id="changes" class="git">
                <thead><tr><th>Test</th></tr></thead>
                <tbody><tr><td>Data</td></tr></tbody>
            </table>
            <div class="chart" id="test_chart"></div>
            <script>console.log("test");</script>
        </div>
        """

        with patch("gitinspector.format.get_selected", return_value="html"):
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                mock_outputable = MockOutputable(original_content.strip())
                outputable.output(mock_outputable)
                html_output = sys.stdout.getvalue()

            finally:
                sys.stdout = old_stdout

        # Verify original content is preserved within collapsible wrapper
        self.assertIn(original_content.strip(), html_output)
        self.assertIn('id="changes"', html_output)
        self.assertIn('id="test_chart"', html_output)
        self.assertIn('console.log("test")', html_output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
