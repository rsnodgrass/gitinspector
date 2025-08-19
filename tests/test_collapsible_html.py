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
        activity_mock.__class__.__name__ = 'ActivityOutput'
        title = outputable._get_section_title(activity_mock)
        self.assertEqual(title, 'Repository Activity Over Time')
        
        # Test changes output title
        changes_mock = MockOutputable()
        changes_mock.__class__.__name__ = 'ChangesOutput'
        title = outputable._get_section_title(changes_mock)
        self.assertEqual(title, 'Commit History & Statistics')
        
        # Test blame output title
        blame_mock = MockOutputable()
        blame_mock.__class__.__name__ = 'BlameOutput'
        title = outputable._get_section_title(blame_mock)
        self.assertEqual(title, 'File Ownership & Code Authorship')
        
        # Test unknown output type (fallback)
        unknown_mock = MockOutputable()
        unknown_mock.__class__.__name__ = 'CustomOutput'
        title = outputable._get_section_title(unknown_mock)
        self.assertEqual(title, 'Custom Analysis')
    
    def test_section_id_mapping(self):
        """Test that section IDs are correctly mapped."""
        # Test activity output ID
        activity_mock = MockOutputable()
        activity_mock.__class__.__name__ = 'ActivityOutput'
        section_id = outputable._get_section_id(activity_mock)
        self.assertEqual(section_id, 'activity-section')
        
        # Test changes output ID
        changes_mock = MockOutputable()
        changes_mock.__class__.__name__ = 'ChangesOutput'
        section_id = outputable._get_section_id(changes_mock)
        self.assertEqual(section_id, 'changes-section')
        
        # Test unknown output type (fallback)
        unknown_mock = MockOutputable()
        unknown_mock.__class__.__name__ = 'CustomOutput'
        section_id = outputable._get_section_id(unknown_mock)
        self.assertEqual(section_id, 'custom-section')
    
    @patch('gitinspector.format.get_selected')
    def test_collapsible_html_wrapper(self, mock_format):
        """Test that HTML output is wrapped in collapsible sections."""
        mock_format.return_value = 'html'
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Create mock outputable with test content
            test_content = '<div class="box"><h4>Test Section</h4><p>Test content</p></div>'
            mock_outputable = MockOutputable(test_content)
            mock_outputable.__class__.__name__ = 'TestOutput'
            
            # Call the output function
            outputable.output(mock_outputable)
            
            # Get the generated HTML
            html_output = sys.stdout.getvalue()
            
        finally:
            sys.stdout = old_stdout
        
        # Verify collapsible structure
        self.assertIn('collapsible-header', html_output)
        self.assertIn('collapsible-content', html_output)
        self.assertIn('collapse-icon', html_output)
        self.assertIn('Test Analysis', html_output)  # Title
        self.assertIn('id="test-section"', html_output)  # Section ID
        self.assertIn(test_content, html_output)  # Original content
    
    @patch('gitinspector.format.get_selected')
    def test_empty_content_not_wrapped(self, mock_format):
        """Test that empty content is not wrapped in collapsible sections."""
        mock_format.return_value = 'html'
        
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
    
    @patch('gitinspector.format.get_selected')
    def test_non_html_formats_unchanged(self, mock_format):
        """Test that non-HTML formats are not affected by collapsible wrapper."""
        mock_format.return_value = 'text'
        
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
        # This is more of an integration test to ensure the CSS is properly included
        from gitinspector.html import html
        
        # Read the HTML header file
        header_path = os.path.join(os.path.dirname(__file__), '..', 'gitinspector', 'html', 'html.header')
        with open(header_path, 'r') as f:
            header_content = f.read()
        
        # Check for required CSS classes
        required_classes = [
            '.collapsible-header',
            '.collapsible-content',
            '.collapse-icon',
            '.collapsible-header:hover',
            '.collapsible-header.expanded'
        ]
        
        for css_class in required_classes:
            self.assertIn(css_class, header_content, f"CSS class {css_class} not found in header")
        
        # Check for JavaScript functionality
        required_js = [
            "collapsible-header').click",
            "slideUp(300)",
            "slideDown(300)",
            "collapse-icon"
        ]
        
        for js_snippet in required_js:
            self.assertIn(js_snippet, header_content, f"JavaScript snippet {js_snippet} not found in header")


class TestCollapsibleIntegration(GitInspectorTestCase):
    """Integration tests for collapsible functionality with real output modules."""
    
    @patch('gitinspector.format.get_selected')
    def test_multiple_sections_integration(self, mock_format):
        """Test that multiple sections are properly handled."""
        mock_format.return_value = 'html'
        
        # Capture stdout for multiple outputs
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Simulate multiple output calls
            outputs = [
                ('ActivityOutput', '<div>Activity content</div>'),
                ('ChangesOutput', '<div>Changes content</div>'),
                ('BlameOutput', '<div>Blame content</div>')
            ]
            
            for class_name, content in outputs:
                mock_outputable = MockOutputable(content)
                mock_outputable.__class__.__name__ = class_name
                outputable.output(mock_outputable)
            
            html_output = sys.stdout.getvalue()
            
        finally:
            sys.stdout = old_stdout
        
        # Verify all sections are present and collapsible
        expected_sections = [
            ('activity-section', 'Repository Activity Over Time'),
            ('changes-section', 'Commit History & Statistics'),
            ('blame-section', 'File Ownership & Code Authorship')
        ]
        
        for section_id, section_title in expected_sections:
            self.assertIn(f'id="{section_id}"', html_output)
            self.assertIn(section_title, html_output)
            
        # Count collapsible headers (should be 3)
        header_count = html_output.count('collapsible-header')
        self.assertEqual(header_count, 3)
        
        # Count collapsible content divs (should be 3)
        content_count = html_output.count('collapsible-content')
        self.assertEqual(content_count, 3)
    
    def test_collapsible_preserves_functionality(self):
        """Test that collapsible wrapper doesn't break existing functionality."""
        # The collapsible wrapper should not interfere with:
        # - Table sorting functionality
        # - Chart generation
        # - Filtering buttons
        # - Pie chart hover effects
        
        # This is verified by ensuring the original content is preserved exactly
        original_content = '''
        <div class="box">
            <table id="changes" class="git">
                <thead><tr><th>Test</th></tr></thead>
                <tbody><tr><td>Data</td></tr></tbody>
            </table>
            <div class="chart" id="test_chart"></div>
            <script>console.log("test");</script>
        </div>
        '''
        
        with patch('gitinspector.format.get_selected', return_value='html'):
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
