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


import textwrap
from ..localization import N_
from .. import terminal, format
from .outputable import Outputable


ACTIVITY_INFO_TEXT = N_(
    "The following activity statistics show repository-level contributions over time"
)


class ActivityOutput(Outputable):
    def __init__(self, activity_data):
        self.activity_data = activity_data
        Outputable.__init__(self)

    def output_text(self):
        if not self.activity_data.get_repositories():
            print("No activity data available.")
            return
            
        print("\n" + textwrap.fill(_(ACTIVITY_INFO_TEXT) + ":", width=terminal.get_size()[0]))
        
        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()
        max_values = self.activity_data.get_max_values()
        
        if not periods:
            print("No time periods found.")
            return
        
        period_type = "weeks" if self.activity_data.useweeks else "months"
        print(f"\nActivity by repository over {period_type}:\n")
        
        # Header
        terminal.printb(
            terminal.ljust("Repository", 20) +
            terminal.ljust("Period", 12) +
            terminal.rjust("Commits", 10) +
            terminal.rjust("Insertions", 12) +
            terminal.rjust("Deletions", 12)
        )
        
        # Data rows
        for repo in repositories:
            for period in periods:
                stats = self.activity_data.get_repo_stats_for_period(repo, period)
                if stats['commits'] > 0:  # Only show periods with activity
                    print(
                        terminal.ljust(repo, 20) +
                        terminal.ljust(period, 12) +
                        str(stats['commits']).rjust(10) +
                        str(stats['insertions']).rjust(12) +
                        str(stats['deletions']).rjust(12)
                    )
        
        # Summary
        totals = self.activity_data.get_total_stats()
        print("\n" + "="*66)
        print(
            terminal.ljust("TOTAL", 20) +
            terminal.ljust("", 12) +
            str(totals['commits']).rjust(10) +
            str(totals['insertions']).rjust(12) +
            str(totals['deletions']).rjust(12)
        )

    def output_html(self):
        if not self.activity_data.get_repositories():
            print('<div class="box"><h4>Repository Activity</h4><p>No activity data available.</p></div>')
            return
            
        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()
        max_values = self.activity_data.get_max_values()
        
        if not periods:
            print('<div class="box"><h4>Repository Activity</h4><p>No time periods found.</p></div>')
            return
        
        period_type = "weeks" if self.activity_data.useweeks else "months"
        
        print(f'<div class="box">')
        print(f'<h4>Repository Activity Over Time</h4>')
        print(f'<p>{_(ACTIVITY_INFO_TEXT)} by {period_type}.</p>')
        
        # Generate color palette for repositories
        colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#27ae60'
        ]
        
        # Create charts for each metric
        metrics = [
            ('commits', 'Commits', max_values['commits']),
            ('insertions', 'Lines Added', max_values['insertions']),
            ('deletions', 'Lines Deleted', max_values['deletions'])
        ]
        
        for metric, title, max_val in metrics:
            if max_val == 0:
                continue
                
            print(f'<div class="activity-chart">')
            print(f'<h5>{title} by Repository</h5>')
            print('<div class="chart-container">')
            
            # Chart data and styling
            print('<style>')
            print('.activity-chart { margin: 20px 0; }')
            print('.chart-container { margin: 10px 0; }')
            print('.chart-bar { display: inline-block; margin: 2px; vertical-align: bottom; }')
            print('.bar-group { margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }')
            print('.bar-label { font-size: 12px; text-align: center; margin-top: 5px; }')
            print('.period-label { font-weight: bold; margin: 15px 0 10px 0; color: #2c3e50; }')
            print('.repo-stats { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }')
            print('.repo-bar { flex: 1; min-width: 120px; text-align: center; }')
            print('.bar-fill { height: 20px; border-radius: 3px; margin: 5px 0; position: relative; }')
            print('.bar-text { font-size: 11px; color: white; line-height: 20px; font-weight: bold; }')
            print('.legend { margin: 20px 0; }')
            print('.legend-item { display: inline-block; margin: 5px 10px 5px 0; }')
            print('.legend-color { display: inline-block; width: 16px; height: 16px; margin-right: 5px; vertical-align: middle; }')
            print('</style>')
            
            # Legend
            print('<div class="legend">')
            print('<strong>Repositories:</strong>')
            for i, repo in enumerate(repositories):
                color = colors[i % len(colors)]
                print(f'<span class="legend-item">')
                print(f'<span class="legend-color" style="background-color: {color};"></span>')
                print(f'{repo}')
                print('</span>')
            print('</div>')
            
            # Chart by period
            for period in periods:
                has_activity = any(
                    self.activity_data.get_repo_stats_for_period(repo, period)[metric] > 0 
                    for repo in repositories
                )
                
                if not has_activity:
                    continue
                    
                print(f'<div class="period-label">{period}</div>')
                print('<div class="repo-stats">')
                
                for i, repo in enumerate(repositories):
                    stats = self.activity_data.get_repo_stats_for_period(repo, period)
                    value = stats[metric]
                    
                    if value > 0:
                        percentage = (value / max_val) * 100 if max_val > 0 else 0
                        color = colors[i % len(colors)]
                        
                        print(f'<div class="repo-bar">')
                        print(f'<div class="bar-fill" style="background-color: {color}; width: {percentage:.1f}%;">')
                        print(f'<span class="bar-text">{value}</span>')
                        print('</div>')
                        print(f'<div class="bar-label">{repo}</div>')
                        print('</div>')
                
                print('</div>')
            
            print('</div>')  # chart-container
            print('</div>')  # activity-chart
        
        # Summary table
        print('<h5>Summary Statistics</h5>')
        print('<table class="git">')
        print('<thead><tr><th>Repository</th><th>Total Commits</th><th>Total Insertions</th><th>Total Deletions</th></tr></thead>')
        print('<tbody>')
        
        for repo in repositories:
            total_commits = 0
            total_insertions = 0
            total_deletions = 0
            
            for period in periods:
                stats = self.activity_data.get_repo_stats_for_period(repo, period)
                total_commits += stats['commits']
                total_insertions += stats['insertions']
                total_deletions += stats['deletions']
            
            print(f'<tr>')
            print(f'<td>{repo}</td>')
            print(f'<td>{total_commits}</td>')
            print(f'<td>{total_insertions}</td>')
            print(f'<td>{total_deletions}</td>')
            print(f'</tr>')
        
        print('</tbody></table>')
        print('</div>')  # box

    def output_json(self):
        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()
        
        print(',\n\t\t"activity": {')
        print(f'\t\t\t"message": "{_(ACTIVITY_INFO_TEXT)}",')
        print(f'\t\t\t"period_type": "{"weeks" if self.activity_data.useweeks else "months"}",')
        print('\t\t\t"periods": [')
        
        period_json_items = []
        for period in periods:
            period_data = {
                'period': period,
                'repositories': []
            }
            
            for repo in repositories:
                stats = self.activity_data.get_repo_stats_for_period(repo, period)
                if stats['commits'] > 0:  # Only include periods with activity
                    period_data['repositories'].append({
                        'name': repo,
                        'commits': stats['commits'],
                        'insertions': stats['insertions'],
                        'deletions': stats['deletions']
                    })
            
            if period_data['repositories']:  # Only include periods with activity
                period_json = f'\t\t\t\t{{'
                period_json += f'\n\t\t\t\t\t"period": "{period}",'
                period_json += f'\n\t\t\t\t\t"repositories": ['
                
                repo_items = []
                for repo_data in period_data['repositories']:
                    repo_json = f'\n\t\t\t\t\t\t{{'
                    repo_json += f'\n\t\t\t\t\t\t\t"name": "{repo_data["name"]}",'
                    repo_json += f'\n\t\t\t\t\t\t\t"commits": {repo_data["commits"]},'
                    repo_json += f'\n\t\t\t\t\t\t\t"insertions": {repo_data["insertions"]},'
                    repo_json += f'\n\t\t\t\t\t\t\t"deletions": {repo_data["deletions"]}'
                    repo_json += f'\n\t\t\t\t\t\t}}'
                    repo_items.append(repo_json)
                
                period_json += ','.join(repo_items)
                period_json += f'\n\t\t\t\t\t]'
                period_json += f'\n\t\t\t\t}}'
                period_json_items.append(period_json)
        
        print(',\n'.join(period_json_items))
        print('\n\t\t\t]')
        print('\t\t}', end='')

    def output_xml(self):
        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()
        
        print('\t<activity>')
        print(f'\t\t<message>{_(ACTIVITY_INFO_TEXT)}</message>')
        print(f'\t\t<period_type>{"weeks" if self.activity_data.useweeks else "months"}</period_type>')
        
        for period in periods:
            has_activity = any(
                self.activity_data.get_repo_stats_for_period(repo, period)['commits'] > 0 
                for repo in repositories
            )
            
            if has_activity:
                print(f'\t\t<period name="{period}">')
                
                for repo in repositories:
                    stats = self.activity_data.get_repo_stats_for_period(repo, period)
                    if stats['commits'] > 0:
                        print(f'\t\t\t<repository name="{repo}">')
                        print(f'\t\t\t\t<commits>{stats["commits"]}</commits>')
                        print(f'\t\t\t\t<insertions>{stats["insertions"]}</insertions>')
                        print(f'\t\t\t\t<deletions>{stats["deletions"]}</deletions>')
                        print(f'\t\t\t</repository>')
                
                print(f'\t\t</period>')
        
        print('\t</activity>')
