#!/usr/bin/env python3
"""
Test helper utilities for gitinspector tests.

This module provides utilities for creating temporary git repositories,
managing test data, and common test setup/teardown operations.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta


class GitTestRepo:
    """Helper class for creating and managing temporary git repositories for testing."""
    
    def __init__(self, name="test_repo"):
        self.name = name
        self.temp_dir = None
        self.repo_path = None
        self.original_cwd = os.getcwd()
        
    def __enter__(self):
        """Context manager entry - create temporary repository."""
        self.temp_dir = tempfile.mkdtemp(prefix=f"gitinspector_test_{self.name}_")
        self.repo_path = os.path.join(self.temp_dir, self.name)
        os.makedirs(self.repo_path)
        os.chdir(self.repo_path)
        
        # Initialize git repository
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temporary repository."""
        os.chdir(self.original_cwd)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def add_commit(self, filename, content, author_name="Test User", author_email="test@example.com", 
                   commit_message=None, commit_date=None):
        """Add a file and create a commit with specified author and date."""
        # Write file
        with open(filename, 'w') as f:
            f.write(content)
        
        # Stage file
        subprocess.run(['git', 'add', filename], check=True, capture_output=True)
        
        # Set author for this commit
        env = os.environ.copy()
        env['GIT_AUTHOR_NAME'] = author_name
        env['GIT_AUTHOR_EMAIL'] = author_email
        env['GIT_COMMITTER_NAME'] = author_name
        env['GIT_COMMITTER_EMAIL'] = author_email
        
        # Set commit date if provided
        if commit_date:
            if isinstance(commit_date, datetime):
                date_str = commit_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_str = commit_date
            env['GIT_AUTHOR_DATE'] = date_str
            env['GIT_COMMITTER_DATE'] = date_str
        
        # Create commit
        message = commit_message or f"Add {filename}"
        subprocess.run(['git', 'commit', '-m', message], 
                      check=True, capture_output=True, env=env)
    
    def add_multi_line_commit(self, filename, lines, author_name="Test User", 
                             author_email="test@example.com", commit_message=None, commit_date=None):
        """Add a file with multiple lines and create a commit."""
        content = '\n'.join(lines) + '\n'
        self.add_commit(filename, content, author_name, author_email, commit_message, commit_date)
    
    def modify_file_commit(self, filename, new_content, author_name="Test User", 
                          author_email="test@example.com", commit_message=None, commit_date=None):
        """Modify an existing file and create a commit."""
        self.add_commit(filename, new_content, author_name, author_email, commit_message, commit_date)


class ActivityTestScenarios:
    """Pre-defined test scenarios for activity testing."""
    
    @staticmethod
    def create_multi_developer_repo(repo: GitTestRepo):
        """Create a repository with multiple developers over time."""
        base_date = datetime(2025, 1, 1)
        
        # Developer 1: Early adopter - January
        repo.add_commit(
            'feature1.py', 
            'def feature1():\n    return "Hello World"\n',
            'Developer 1', 'dev1@example.com',
            'Initial feature implementation',
            base_date
        )
        
        # Developer 2: Joins in February  
        repo.add_commit(
            'feature2.py',
            'def feature2():\n    return "Feature 2"\n\ndef helper():\n    pass\n',
            'Developer 2', 'dev2@example.com', 
            'Add feature 2 with helper',
            base_date + timedelta(days=32)
        )
        
        # Developer 1: More work in February
        repo.modify_file_commit(
            'feature1.py',
            'def feature1():\n    return "Hello World Updated"\n\ndef feature1_helper():\n    pass\n',
            'Developer 1', 'dev1@example.com',
            'Enhance feature 1',
            base_date + timedelta(days=35)
        )
        
        # Developer 3: Joins in March
        repo.add_commit(
            'feature3.py',
            'class Feature3:\n    def __init__(self):\n        self.value = 42\n\n    def process(self):\n        return self.value * 2\n',
            'Developer 3', 'dev3@example.com',
            'Add Feature 3 class',
            base_date + timedelta(days=62)
        )
        
        # All developers active in March
        repo.add_commit(
            'shared.py',
            'SHARED_CONFIG = {\n    "version": "1.0",\n    "debug": True\n}\n',
            'Developer 1', 'dev1@example.com',
            'Add shared config',
            base_date + timedelta(days=65)
        )
        
        repo.modify_file_commit(
            'feature2.py',
            'def feature2():\n    return "Feature 2 Enhanced"\n\ndef helper():\n    return "Helper updated"\n\ndef new_function():\n    pass\n',
            'Developer 2', 'dev2@example.com',
            'Enhance feature 2',
            base_date + timedelta(days=67)
        )
        
        repo.add_commit(
            'tests.py',
            'import unittest\n\nclass TestFeatures(unittest.TestCase):\n    def test_feature1(self):\n        pass\n\n    def test_feature2(self):\n        pass\n',
            'Developer 3', 'dev3@example.com',
            'Add unit tests',
            base_date + timedelta(days=70)
        )
    
    @staticmethod
    def create_solo_developer_repo(repo: GitTestRepo):
        """Create a repository with a single productive developer."""
        base_date = datetime(2025, 1, 15)
        
        # Solo developer with consistent activity
        commits = [
            ('main.py', 'def main():\n    print("Hello")\n', 'Initial commit'),
            ('utils.py', 'def util1():\n    pass\n\ndef util2():\n    pass\n', 'Add utilities'),
            ('config.py', 'CONFIG = {"env": "dev"}\n', 'Add config'),
            ('main.py', 'def main():\n    print("Hello World!")\n\ndef run():\n    main()\n', 'Enhance main'),
            ('utils.py', 'def util1():\n    return True\n\ndef util2():\n    return False\n\ndef util3():\n    return None\n', 'Expand utils'),
        ]
        
        for i, (filename, content, message) in enumerate(commits):
            commit_date = base_date + timedelta(days=i*7)  # Weekly commits
            repo.add_commit(filename, content, 'Solo Developer', 'solo@example.com', message, commit_date)
    
    @staticmethod
    def create_seasonal_activity_repo(repo: GitTestRepo):
        """Create a repository with seasonal activity patterns."""
        # High activity in Q1, low in Q2, high in Q3
        dates_and_activity = [
            # Q1 - High activity (January)
            (datetime(2025, 1, 5), 'q1_feature1.py', 'Q1 Feature 1'),
            (datetime(2025, 1, 12), 'q1_feature2.py', 'Q1 Feature 2'), 
            (datetime(2025, 1, 19), 'q1_feature3.py', 'Q1 Feature 3'),
            (datetime(2025, 1, 26), 'q1_feature4.py', 'Q1 Feature 4'),
            
            # Q2 - Low activity (April)
            (datetime(2025, 4, 15), 'q2_bugfix.py', 'Q2 Bug fix'),
            
            # Q3 - High activity (July)
            (datetime(2025, 7, 1), 'q3_feature1.py', 'Q3 Feature 1'),
            (datetime(2025, 7, 8), 'q3_feature2.py', 'Q3 Feature 2'),
            (datetime(2025, 7, 15), 'q3_feature3.py', 'Q3 Feature 3'),
        ]
        
        for commit_date, filename, message in dates_and_activity:
            content = f'# {message}\ndef {filename.replace(".py", "")}():\n    pass\n'
            repo.add_commit(filename, content, 'Seasonal Dev', 'seasonal@example.com', message, commit_date)


class GitInspectorTestCase(unittest.TestCase):
    """Base test case with common gitinspector testing utilities."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_cwd = os.getcwd()
        # Ensure we're in the gitinspector directory for imports
        gitinspector_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(gitinspector_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
    
    def assert_activity_data_valid(self, activity_data):
        """Assert that activity data has the expected structure."""
        self.assertIsNotNone(activity_data)
        self.assertTrue(hasattr(activity_data, 'get_repositories'))
        self.assertTrue(hasattr(activity_data, 'get_periods'))
        self.assertTrue(hasattr(activity_data, 'get_repo_stats_for_period'))
        self.assertTrue(hasattr(activity_data, 'get_max_values'))
        self.assertTrue(hasattr(activity_data, 'get_total_stats'))
    
    def assert_stats_format(self, stats, normalized=False):
        """Assert that stats have the expected format."""
        required_keys = ['commits', 'insertions', 'deletions', 'contributors']
        for key in required_keys:
            self.assertIn(key, stats)
            self.assertIsInstance(stats[key], (int, float))
        
        if normalized:
            normalized_keys = ['commits_per_contributor', 'insertions_per_contributor', 'deletions_per_contributor']
            for key in normalized_keys:
                self.assertIn(key, stats)
                self.assertIsInstance(stats[key], (int, float))
