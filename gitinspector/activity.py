# coding: utf-8
#
# Copyright © 2012-2015 Ejwa Software. All rights reserved.
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


import datetime


class ActivityData(object):
    def __init__(self, changes_by_repo, useweeks):
        """
        Initialize activity data for repository-level statistics over time periods.
        
        Args:
            changes_by_repo: Dictionary mapping repository names to Changes objects
            useweeks: Boolean indicating whether to use weeks (True) or months (False)
        """
        self.changes_by_repo = changes_by_repo
        self.useweeks = useweeks
        self.repo_activity = {}  # {repo_name: {period: {commits, insertions, deletions}}}
        self.all_periods = set()
        
        # Process each repository's data
        for repo_name, changes in changes_by_repo.items():
            self.repo_activity[repo_name] = {}
            authordateinfo_list = sorted(changes.get_authordateinfo_list().items())
            
            # Aggregate data by time period
            for date_author_info, author_stats in authordateinfo_list:
                date_str, author = date_author_info
                period = self._get_period_from_date(date_str)
                self.all_periods.add(period)
                
                if period not in self.repo_activity[repo_name]:
                    self.repo_activity[repo_name][period] = {
                        'commits': 0,
                        'insertions': 0,
                        'deletions': 0
                    }
                
                # Add to repository totals for this period
                self.repo_activity[repo_name][period]['commits'] += 1
                self.repo_activity[repo_name][period]['insertions'] += author_stats.insertions
                self.repo_activity[repo_name][period]['deletions'] += author_stats.deletions
        
        self.all_periods = sorted(list(self.all_periods))
    
    def _get_period_from_date(self, date_str):
        """Convert date string (YYYY-MM-DD) to period string (YYYY-MM or YYYY-WNN)"""
        try:
            date_obj = datetime.date(int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10]))
            
            if self.useweeks:
                yearweek = date_obj.isocalendar()
                return str(yearweek[0]) + "W" + "{0:02d}".format(yearweek[1])
            else:
                return date_str[0:7]  # YYYY-MM
        except (ValueError, IndexError):
            # Fallback for malformed dates
            return date_str[0:7] if len(date_str) >= 7 else date_str
    
    def get_repositories(self):
        """Get list of repository names"""
        return list(self.repo_activity.keys())
    
    def get_periods(self):
        """Get sorted list of all time periods"""
        return self.all_periods
    
    def get_repo_stats_for_period(self, repo_name, period):
        """Get statistics for a specific repository and period"""
        return self.repo_activity.get(repo_name, {}).get(period, {
            'commits': 0,
            'insertions': 0,
            'deletions': 0
        })
    
    def get_max_values(self):
        """Get maximum values across all repositories and periods for scaling charts"""
        max_commits = 0
        max_insertions = 0
        max_deletions = 0
        
        for repo_name in self.repo_activity:
            for period in self.repo_activity[repo_name]:
                stats = self.repo_activity[repo_name][period]
                max_commits = max(max_commits, stats['commits'])
                max_insertions = max(max_insertions, stats['insertions'])
                max_deletions = max(max_deletions, stats['deletions'])
        
        return {
            'commits': max_commits,
            'insertions': max_insertions,
            'deletions': max_deletions
        }
    
    def get_total_stats(self):
        """Get total statistics across all repositories and periods"""
        total_commits = 0
        total_insertions = 0
        total_deletions = 0
        
        for repo_name in self.repo_activity:
            for period in self.repo_activity[repo_name]:
                stats = self.repo_activity[repo_name][period]
                total_commits += stats['commits']
                total_insertions += stats['insertions']
                total_deletions += stats['deletions']
        
        return {
            'commits': total_commits,
            'insertions': total_insertions,
            'deletions': total_deletions
        }
