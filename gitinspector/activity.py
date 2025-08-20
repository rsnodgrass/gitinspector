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
from . import filtering


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
        self.repo_activity = {}  # {repo_name: {period: {commits, insertions, deletions, contributors, authors}}}
        self.all_periods = set()

        # Process each repository's data
        for repo_name, changes in changes_by_repo.items():
            self.repo_activity[repo_name] = {}
            authordateinfo_list = sorted(changes.get_authordateinfo_list().items())

            # Aggregate data by time period
            for date_author_info, author_stats in authordateinfo_list:
                date_str, author = date_author_info

                # Apply team filtering - skip authors not in team config
                if filtering.is_author_team_filtered(author):
                    continue

                period = self._get_period_from_date(date_str)
                self.all_periods.add(period)

                if period not in self.repo_activity[repo_name]:
                    self.repo_activity[repo_name][period] = {
                        "commits": 0,
                        "insertions": 0,
                        "deletions": 0,
                        "contributors": set(),  # Track unique contributors per period
                        "authors": set(),  # For debugging/validation
                    }

                # Add to repository totals for this period
                self.repo_activity[repo_name][period]["commits"] += 1
                self.repo_activity[repo_name][period]["insertions"] += author_stats.insertions
                self.repo_activity[repo_name][period]["deletions"] += author_stats.deletions
                self.repo_activity[repo_name][period]["contributors"].add(author)
                self.repo_activity[repo_name][period]["authors"].add(author)

        # If team filtering removed all periods, fall back to timeline skeleton
        # derived from all commit dates (unfiltered) so charts have an x-axis.
        if len(self.all_periods) == 0:
            fallback_periods = set()
            for _repo_name, _changes in changes_by_repo.items():
                for (date_str, _author), _stats in _changes.get_authordateinfo_list().items():
                    fallback_periods.add(self._get_period_from_date(date_str))
            self.all_periods = fallback_periods

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

    def get_repo_stats_for_period(self, repo_name, period, normalized=False):
        """Get statistics for a specific repository and period"""
        raw_stats = self.repo_activity.get(repo_name, {}).get(
            period, {"commits": 0, "insertions": 0, "deletions": 0, "contributors": set(), "authors": set()}
        )

        # Convert sets to counts and prepare return data
        stats = {
            "commits": raw_stats["commits"],
            "insertions": raw_stats["insertions"],
            "deletions": raw_stats["deletions"],
            "contributors": len(raw_stats["contributors"]),
            "authors": len(raw_stats["authors"]),
        }

        # Apply normalization if requested
        if normalized and stats["contributors"] > 0:
            stats["commits_per_contributor"] = round(stats["commits"] / stats["contributors"], 2)
            stats["insertions_per_contributor"] = round(stats["insertions"] / stats["contributors"], 2)
            stats["deletions_per_contributor"] = round(stats["deletions"] / stats["contributors"], 2)
        else:
            stats["commits_per_contributor"] = 0
            stats["insertions_per_contributor"] = 0
            stats["deletions_per_contributor"] = 0

        return stats

    def get_max_values(self, normalized=False):
        """Get maximum values across all repositories and periods for scaling charts"""
        max_commits = 0
        max_insertions = 0
        max_deletions = 0
        max_commits_per_contributor = 0
        max_insertions_per_contributor = 0
        max_deletions_per_contributor = 0

        for repo_name in self.repo_activity:
            for period in self.repo_activity[repo_name]:
                stats = self.get_repo_stats_for_period(repo_name, period, normalized)
                max_commits = max(max_commits, stats["commits"])
                max_insertions = max(max_insertions, stats["insertions"])
                max_deletions = max(max_deletions, stats["deletions"])

                if normalized:
                    max_commits_per_contributor = max(max_commits_per_contributor, stats["commits_per_contributor"])
                    max_insertions_per_contributor = max(
                        max_insertions_per_contributor, stats["insertions_per_contributor"]
                    )
                    max_deletions_per_contributor = max(
                        max_deletions_per_contributor, stats["deletions_per_contributor"]
                    )

        result = {"commits": max_commits, "insertions": max_insertions, "deletions": max_deletions}

        if normalized:
            result.update(
                {
                    "commits_per_contributor": max_commits_per_contributor,
                    "insertions_per_contributor": max_insertions_per_contributor,
                    "deletions_per_contributor": max_deletions_per_contributor,
                }
            )

        return result

    def get_total_stats(self, normalized=False):
        """Get total statistics across all repositories and periods"""
        total_commits = 0
        total_insertions = 0
        total_deletions = 0
        total_contributors = set()  # Track unique contributors across all repos

        for repo_name in self.repo_activity:
            for period in self.repo_activity[repo_name]:
                period_data = self.repo_activity[repo_name][period]
                total_commits += period_data["commits"]
                total_insertions += period_data["insertions"]
                total_deletions += period_data["deletions"]
                total_contributors.update(period_data["contributors"])

        result = {
            "commits": total_commits,
            "insertions": total_insertions,
            "deletions": total_deletions,
            "contributors": len(total_contributors),
        }

        if normalized and len(total_contributors) > 0:
            result.update(
                {
                    "commits_per_contributor": round(total_commits / len(total_contributors), 2),
                    "insertions_per_contributor": round(total_insertions / len(total_contributors), 2),
                    "deletions_per_contributor": round(total_deletions / len(total_contributors), 2),
                }
            )

        return result

    def get_repo_unique_contributors(self, repo_name):
        """Get unique contributors for a specific repository across all periods"""
        unique_contributors = set()
        if repo_name in self.repo_activity:
            for period_data in self.repo_activity[repo_name].values():
                if "contributors" in period_data and isinstance(period_data["contributors"], set):
                    unique_contributors.update(period_data["contributors"])
        return unique_contributors
