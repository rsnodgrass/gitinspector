#!/usr/bin/env python3
"""
Script to create permanent test repositories for gitinspector testing.

This script creates several test repositories with known patterns that can be
used for consistent testing of gitinspector features.
"""

import os
import shutil
import sys
from datetime import datetime, timedelta

# Add gitinspector to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_helpers import GitTestRepo, ActivityTestScenarios


def create_test_repositories():
    """Create all test repositories in the test_repositories directory."""
    
    test_dir = os.path.join(os.path.dirname(__file__), 'test_repositories')
    
    # Clean up existing test repositories
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        # Repository 1: Multi-developer team with growth over time
        print("Creating team_growth_repo...")
        create_team_growth_repo()
        
        # Repository 2: Solo developer with consistent activity
        print("Creating solo_productive_repo...")
        create_solo_productive_repo()
        
        # Repository 3: Seasonal activity patterns
        print("Creating seasonal_activity_repo...")
        create_seasonal_activity_repo()
        
        # Repository 4: Multiple file types and test files
        print("Creating mixed_project_repo...")
        create_mixed_project_repo()
        
        # Repository 5: Legacy repo with sparse activity
        print("Creating legacy_maintenance_repo...")
        create_legacy_maintenance_repo()
        
        print(f"\n✅ Created 5 test repositories in {test_dir}")
        print("These repositories can be used for:")
        print("- Activity feature testing")
        print("- Multi-repository analysis")
        print("- Normalization testing")
        print("- Integration testing")
        
    finally:
        os.chdir(original_cwd)


def create_team_growth_repo():
    """Create a repository showing team growth over time."""
    repo_helper = GitTestRepo("team_growth_repo")
    with repo_helper as repo:
        base_date = datetime(2024, 1, 1)
        
        # Month 1: Solo developer
        repo.add_commit(
            'core.py',
            'class Core:\n    def __init__(self):\n        self.version = "1.0"\n',
            'Founder Dev', 'founder@company.com',
            'Initial core implementation',
            base_date
        )
        
        # Month 2: Second developer joins
        repo.add_commit(
            'utils.py',
            'def helper_function():\n    return True\n\ndef format_data(data):\n    return str(data)\n',
            'Developer 2', 'dev2@company.com',
            'Add utility functions',
            base_date + timedelta(days=32)
        )
        
        repo.modify_file_commit(
            'core.py',
            'class Core:\n    def __init__(self):\n        self.version = "1.1"\n        self.debug = False\n',
            'Founder Dev', 'founder@company.com',
            'Update core version',
            base_date + timedelta(days=35)
        )
        
        # Month 3: Team of 4
        repo.add_commit(
            'api.py',
            'from flask import Flask\n\napp = Flask(__name__)\n\n@app.route("/")\ndef home():\n    return "Hello World"\n',
            'Backend Dev', 'backend@company.com',
            'Add API layer',
            base_date + timedelta(days=62)
        )
        
        repo.add_commit(
            'frontend.js',
            'function main() {\n    console.log("Frontend loaded");\n    setupUI();\n}\n\nfunction setupUI() {\n    // Setup code\n}\n',
            'Frontend Dev', 'frontend@company.com',
            'Add frontend code',
            base_date + timedelta(days=65)
        )
        
        # All developers active in month 3
        for i, (dev_name, dev_email) in enumerate([
            ('Founder Dev', 'founder@company.com'),
            ('Developer 2', 'dev2@company.com'),
            ('Backend Dev', 'backend@company.com'),
            ('Frontend Dev', 'frontend@company.com')
        ]):
            repo.add_commit(
                f'feature_{i+1}.py',
                f'def feature_{i+1}():\n    return "Feature {i+1} implementation"\n',
                dev_name, dev_email,
                f'Add feature {i+1}',
                base_date + timedelta(days=68 + i)
            )
    
    # Copy the repository to permanent location
    import shutil
    shutil.copytree(repo_helper.repo_path, "team_growth_repo")


def create_solo_productive_repo():
    """Create a repository with a highly productive solo developer."""
    repo_helper = GitTestRepo("solo_productive_repo")
    with repo_helper as repo:
        base_date = datetime(2024, 6, 1)
        
        # Consistent weekly commits over 3 months
        features = [
            ('authentication.py', 'class AuthManager:\n    def login(self, user, password):\n        return True\n'),
            ('database.py', 'import sqlite3\n\nclass Database:\n    def __init__(self):\n        self.conn = sqlite3.connect("app.db")\n'),
            ('config.py', 'CONFIG = {\n    "debug": True,\n    "port": 8000,\n    "host": "localhost"\n}\n'),
            ('models.py', 'class User:\n    def __init__(self, name, email):\n        self.name = name\n        self.email = email\n'),
            ('views.py', 'from models import User\n\ndef get_user_profile(user_id):\n    return User.get(user_id)\n'),
            ('tests.py', 'import unittest\n\nclass TestAuth(unittest.TestCase):\n    def test_login(self):\n        self.assertTrue(True)\n'),
            ('migrations.py', 'def migrate_v1_to_v2():\n    # Migration logic\n    pass\n'),
            ('logging.py', 'import logging\n\nlogger = logging.getLogger(__name__)\n'),
            ('cache.py', 'class Cache:\n    def __init__(self):\n        self.data = {}\n    \n    def get(self, key):\n        return self.data.get(key)\n'),
            ('validators.py', 'def validate_email(email):\n    return "@" in email\n\ndef validate_password(password):\n    return len(password) >= 8\n'),
            ('middleware.py', 'def cors_middleware(request):\n    # CORS handling\n    return request\n'),
            ('serializers.py', 'import json\n\nclass JSONSerializer:\n    def serialize(self, obj):\n        return json.dumps(obj)\n')
        ]
        
        for i, (filename, content) in enumerate(features):
            commit_date = base_date + timedelta(days=i*7)  # Weekly commits
            repo.add_commit(
                filename, content,
                'Solo Expert', 'expert@company.com',
                f'Implement {filename.replace(".py", "")} module',
                commit_date
            )
    
    # Copy the repository to permanent location
    import shutil
    shutil.copytree(repo_helper.repo_path, "solo_productive_repo")


def create_seasonal_activity_repo():
    """Create a repository with seasonal development patterns."""
    repo_helper = GitTestRepo("seasonal_activity_repo")
    with repo_helper as repo:
        # Q1: High activity (new year planning)
        q1_base = datetime(2024, 1, 1)
        q1_features = ['planning.py', 'roadmap.py', 'goals.py', 'metrics.py']
        for i, feature in enumerate(q1_features):
            repo.add_commit(
                feature,
                f'# Q1 Planning Module\ndef {feature.replace(".py", "")}_function():\n    pass\n',
                'Planning Team', 'planning@company.com',
                f'Q1 planning: {feature}',
                q1_base + timedelta(days=i*7)
            )
        
        # Q2: Medium activity (implementation)
        q2_base = datetime(2024, 4, 1)
        q2_features = ['implementation.py', 'integration.py']
        for i, feature in enumerate(q2_features):
            repo.add_commit(
                feature,
                f'# Q2 Implementation\ndef {feature.replace(".py", "")}_logic():\n    return "implemented"\n',
                'Dev Team', 'dev@company.com',
                f'Q2 work: {feature}',
                q2_base + timedelta(days=i*14)
            )
        
        # Q3: Low activity (summer vacation)
        q3_base = datetime(2024, 7, 1)
        repo.add_commit(
            'bugfix.py',
            '# Critical bugfix\ndef fix_urgent_issue():\n    return "fixed"\n',
            'On-call Dev', 'oncall@company.com',
            'Q3 critical bugfix',
            q3_base + timedelta(days=30)
        )
        
        # Q4: High activity (year-end push)
        q4_base = datetime(2024, 10, 1)
        q4_features = ['optimization.py', 'performance.py', 'cleanup.py', 'release.py']
        for i, feature in enumerate(q4_features):
            repo.add_commit(
                feature,
                f'# Q4 Final Push\ndef {feature.replace(".py", "")}_task():\n    return "optimized"\n',
                'Release Team', 'release@company.com',
                f'Q4 release: {feature}',
                q4_base + timedelta(days=i*10)
            )
    
    # Copy the repository to permanent location
    import shutil
    shutil.copytree(repo_helper.repo_path, "seasonal_activity_repo")


def create_mixed_project_repo():
    """Create a repository with multiple file types and test files."""
    repo_helper = GitTestRepo("mixed_project_repo")
    with repo_helper as repo:
        base_date = datetime(2024, 3, 1)
        
        # Python files
        repo.add_commit(
            'main.py',
            'def main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()\n',
            'Python Dev', 'python@company.com',
            'Add Python main module',
            base_date
        )
        
        # JavaScript files
        repo.add_commit(
            'app.js',
            'function startApp() {\n    console.log("App started");\n    loadModules();\n}\n\nfunction loadModules() {\n    // Module loading\n}\n',
            'JS Dev', 'js@company.com',
            'Add JavaScript app',
            base_date + timedelta(days=5)
        )
        
        # Test files
        repo.add_commit(
            'test_main.py',
            'import unittest\nfrom main import main\n\nclass TestMain(unittest.TestCase):\n    def test_main_runs(self):\n        self.assertIsNone(main())\n',
            'QA Engineer', 'qa@company.com',
            'Add Python tests',
            base_date + timedelta(days=10)
        )
        
        repo.add_commit(
            'app.test.js',
            'describe("App", () => {\n    it("should start", () => {\n        expect(startApp).toBeDefined();\n    });\n});\n',
            'QA Engineer', 'qa@company.com',
            'Add JavaScript tests',
            base_date + timedelta(days=12)
        )
        
        # CSS and HTML
        repo.add_commit(
            'styles.css',
            'body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n}\n\n.container {\n    max-width: 1200px;\n    margin: 0 auto;\n}\n',
            'Frontend Dev', 'frontend@company.com',
            'Add CSS styles',
            base_date + timedelta(days=15)
        )
        
        repo.add_commit(
            'index.html',
            '<!DOCTYPE html>\n<html>\n<head>\n    <title>Mixed Project</title>\n    <link rel="stylesheet" href="styles.css">\n</head>\n<body>\n    <div class="container">\n        <h1>Welcome</h1>\n    </div>\n    <script src="app.js"></script>\n</body>\n</html>\n',
            'Frontend Dev', 'frontend@company.com',
            'Add HTML template',
            base_date + timedelta(days=18)
        )
    
    # Copy the repository to permanent location
    import shutil
    shutil.copytree(repo_helper.repo_path, "mixed_project_repo")


def create_legacy_maintenance_repo():
    """Create a repository simulating legacy maintenance work."""
    repo_helper = GitTestRepo("legacy_maintenance_repo")
    with repo_helper as repo:
        # Old initial commit
        old_date = datetime(2020, 1, 1)
        repo.add_commit(
            'legacy_system.py',
            '# Legacy System - DO NOT MODIFY\nclass LegacyProcessor:\n    def __init__(self):\n        self.version = "1.0.0"\n        self.deprecated_feature = True\n\n    def process_data(self, data):\n        # Old processing logic\n        return data.upper()\n',
            'Original Dev', 'original@oldcompany.com',
            'Initial legacy system',
            old_date
        )
        
        # Sparse maintenance over years
        maintenance_dates = [
            (datetime(2021, 6, 15), 'security_patch.py', 'Critical security patch'),
            (datetime(2022, 3, 10), 'compatibility.py', 'Python 3.9 compatibility'),
            (datetime(2023, 8, 5), 'dependency_update.py', 'Update deprecated dependencies'),
            (datetime(2024, 2, 20), 'modern_interface.py', 'Add modern API interface'),
        ]
        
        for commit_date, filename, message in maintenance_dates:
            content = f'# {message}\n# Added on {commit_date.strftime("%Y-%m-%d")}\n\ndef {filename.replace(".py", "")}_function():\n    return "maintenance_update"\n'
            repo.add_commit(
                filename, content,
                'Maintenance Team', 'maintenance@company.com',
                message,
                commit_date
            )
    
    # Copy the repository to permanent location
    import shutil
    shutil.copytree(repo_helper.repo_path, "legacy_maintenance_repo")


if __name__ == '__main__':
    create_test_repositories()
