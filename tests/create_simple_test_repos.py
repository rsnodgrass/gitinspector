#!/usr/bin/env python3
"""
Simple script to create permanent test repositories for gitinspector testing.
"""

import os
import subprocess
import shutil
from datetime import datetime, timedelta


def create_git_repo(repo_path, author_name="Test User", author_email="test@example.com"):
    """Create a git repository at the given path."""
    os.makedirs(repo_path, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(repo_path)
    
    try:
        # Initialize git repository
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', author_email], check=True)
        subprocess.run(['git', 'config', 'user.name', author_name], check=True)
        
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        os.chdir(original_cwd)


def add_commit(repo_path, filename, content, author_name="Test User", author_email="test@example.com", 
               commit_message=None, commit_date=None):
    """Add a file and create a commit."""
    original_cwd = os.getcwd()
    os.chdir(repo_path)
    
    try:
        # Write file
        with open(filename, 'w') as f:
            f.write(content)
        
        # Stage file
        subprocess.run(['git', 'add', filename], check=True, capture_output=True)
        
        # Set environment for commit
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
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating commit: {e}")
        return False
    finally:
        os.chdir(original_cwd)


def create_test_repositories():
    """Create all test repositories."""
    test_dir = os.path.join(os.path.dirname(__file__), 'test_repositories')
    
    # Clean up existing test repositories
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    print("Creating test repositories...")
    
    # Repository 1: Team Growth Repository
    print("1. Creating team_growth_repo...")
    team_repo = os.path.join(test_dir, 'team_growth_repo')
    create_git_repo(team_repo)
    
    base_date = datetime(2024, 1, 1)
    
    # Month 1: Solo developer
    add_commit(team_repo, 'core.py', 
               'class Core:\n    def __init__(self):\n        self.version = "1.0"\n',
               'Founder Dev', 'founder@company.com', 'Initial core implementation', base_date)
    
    # Month 2: Second developer joins
    add_commit(team_repo, 'utils.py',
               'def helper_function():\n    return True\n\ndef format_data(data):\n    return str(data)\n',
               'Developer 2', 'dev2@company.com', 'Add utility functions', 
               base_date + timedelta(days=32))
    
    # Month 3: Team of 4
    add_commit(team_repo, 'api.py',
               'from flask import Flask\n\napp = Flask(__name__)\n\n@app.route("/")\ndef home():\n    return "Hello World"\n',
               'Backend Dev', 'backend@company.com', 'Add API layer',
               base_date + timedelta(days=62))
    
    add_commit(team_repo, 'frontend.js',
               'function main() {\n    console.log("Frontend loaded");\n}\n',
               'Frontend Dev', 'frontend@company.com', 'Add frontend code',
               base_date + timedelta(days=65))
    
    # Repository 2: Solo Productive Repository
    print("2. Creating solo_productive_repo...")
    solo_repo = os.path.join(test_dir, 'solo_productive_repo')
    create_git_repo(solo_repo)
    
    solo_base = datetime(2024, 6, 1)
    features = ['authentication.py', 'database.py', 'config.py', 'models.py', 'views.py']
    
    for i, feature in enumerate(features):
        content = f'# {feature.replace(".py", "").title()} Module\ndef {feature.replace(".py", "")}_function():\n    return "implemented"\n'
        add_commit(solo_repo, feature, content,
                  'Solo Expert', 'expert@company.com', f'Implement {feature}',
                  solo_base + timedelta(days=i*7))
    
    # Repository 3: Seasonal Activity Repository  
    print("3. Creating seasonal_activity_repo...")
    seasonal_repo = os.path.join(test_dir, 'seasonal_activity_repo')
    create_git_repo(seasonal_repo)
    
    # Q1: High activity
    q1_base = datetime(2024, 1, 1)
    for i, feature in enumerate(['planning.py', 'roadmap.py', 'goals.py']):
        content = f'# Q1 Planning\ndef {feature.replace(".py", "")}():\n    pass\n'
        add_commit(seasonal_repo, feature, content,
                  'Planning Team', 'planning@company.com', f'Q1 planning: {feature}',
                  q1_base + timedelta(days=i*7))
    
    # Q4: High activity  
    q4_base = datetime(2024, 10, 1)
    for i, feature in enumerate(['optimization.py', 'release.py']):
        content = f'# Q4 Release\ndef {feature.replace(".py", "")}():\n    return "optimized"\n'
        add_commit(seasonal_repo, feature, content,
                  'Release Team', 'release@company.com', f'Q4 release: {feature}',
                  q4_base + timedelta(days=i*10))
    
    # Repository 4: Mixed Project Repository
    print("4. Creating mixed_project_repo...")
    mixed_repo = os.path.join(test_dir, 'mixed_project_repo')
    create_git_repo(mixed_repo)
    
    mixed_base = datetime(2024, 3, 1)
    
    # Python files
    add_commit(mixed_repo, 'main.py',
               'def main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()\n',
               'Python Dev', 'python@company.com', 'Add Python main module', mixed_base)
    
    # Test files
    add_commit(mixed_repo, 'test_main.py',
               'import unittest\n\nclass TestMain(unittest.TestCase):\n    def test_main_runs(self):\n        pass\n',
               'QA Engineer', 'qa@company.com', 'Add Python tests',
               mixed_base + timedelta(days=10))
    
    # Repository 5: Legacy Maintenance Repository
    print("5. Creating legacy_maintenance_repo...")
    legacy_repo = os.path.join(test_dir, 'legacy_maintenance_repo')
    create_git_repo(legacy_repo)
    
    # Old initial commit
    add_commit(legacy_repo, 'legacy_system.py',
               '# Legacy System\nclass LegacyProcessor:\n    def __init__(self):\n        self.version = "1.0.0"\n',
               'Original Dev', 'original@oldcompany.com', 'Initial legacy system',
               datetime(2020, 1, 1))
    
    # Recent maintenance
    add_commit(legacy_repo, 'security_patch.py',
               '# Security patch\ndef patch_security_issue():\n    return "patched"\n',
               'Maintenance Team', 'maintenance@company.com', 'Critical security patch',
               datetime(2024, 2, 20))
    
    print(f"\n✅ Created 5 test repositories in {test_dir}")
    print("Repository summary:")
    
    for repo_name in ['team_growth_repo', 'solo_productive_repo', 'seasonal_activity_repo', 
                      'mixed_project_repo', 'legacy_maintenance_repo']:
        repo_path = os.path.join(test_dir, repo_name)
        try:
            result = subprocess.run(['git', 'log', '--oneline'], 
                                  capture_output=True, text=True, cwd=repo_path)
            if result.returncode == 0:
                commit_count = len(result.stdout.strip().split('\n'))
                print(f"  - {repo_name}: {commit_count} commits")
            else:
                print(f"  - {repo_name}: Error reading commits")
        except Exception as e:
            print(f"  - {repo_name}: Error - {e}")


if __name__ == '__main__':
    create_test_repositories()
