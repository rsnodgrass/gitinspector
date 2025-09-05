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
from .outputable import Outputable, get_no_collapsible


ACTIVITY_INFO_TEXT = N_("The following activity statistics show repository-level contributions over time")


class ActivityOutput(Outputable):
    def __init__(self, activity_data, normalize=False, show_both=False, chart_type="line"):
        self.activity_data = activity_data
        self.normalize = normalize
        self.show_both = show_both  # New parameter to show both raw and normalized
        self.chart_type = chart_type if chart_type in ("line", "bar") else "line"
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

        if self.show_both:
            # Show both raw and normalized data
            print(f"\nActivity by repository over {period_type} (raw totals and per-contributor averages):\n")

            # Header showing both raw and normalized columns
            terminal.printb(
                terminal.ljust("Repository", 18)
                + terminal.ljust("Period", 10)
                + terminal.rjust("Contribs", 9)
                + terminal.rjust("Commits", 8)
                + terminal.rjust("C/Dev", 6)
                + terminal.rjust("Lines+", 8)
                + terminal.rjust("L+/Dev", 7)
                + terminal.rjust("Lines-", 8)
                + terminal.rjust("L-/Dev", 7)
            )

            # Data rows showing both raw and normalized data
            for repo in repositories:
                for period in periods:
                    raw_stats = self.activity_data.get_repo_stats_for_period(repo, period, normalized=False)
                    norm_stats = self.activity_data.get_repo_stats_for_period(repo, period, normalized=True)

                    if raw_stats["commits"] > 0:  # Only show periods with activity
                        print(
                            terminal.ljust(repo, 18)
                            + terminal.ljust(period, 10)
                            + str(raw_stats["contributors"]).rjust(9)
                            + str(raw_stats["commits"]).rjust(8)
                            + f"{norm_stats['commits_per_contributor']:.1f}".rjust(6)
                            + str(raw_stats["insertions"]).rjust(8)
                            + f"{norm_stats['insertions_per_contributor']:.1f}".rjust(7)
                            + str(raw_stats["deletions"]).rjust(8)
                            + f"{norm_stats['deletions_per_contributor']:.1f}".rjust(7)
                        )
        else:
            # Show either raw or normalized data (existing behavior)
            norm_text = " (normalized per contributor)" if self.normalize else ""
            print(f"\nActivity by repository over {period_type}{norm_text}:\n")

            if self.normalize:
                # Header for normalized data
                terminal.printb(
                    terminal.ljust("Repository", 20)
                    + terminal.ljust("Period", 12)
                    + terminal.rjust("Contributors", 13)
                    + terminal.rjust("Commits/Dev", 12)
                    + terminal.rjust("Lines+/Dev", 12)
                    + terminal.rjust("Lines-/Dev", 12)
                )

                # Data rows for normalized data
                for repo in repositories:
                    for period in periods:
                        stats = self.activity_data.get_repo_stats_for_period(repo, period, self.normalize)
                        if stats["commits"] > 0:  # Only show periods with activity
                            print(
                                terminal.ljust(repo, 20)
                                + terminal.ljust(period, 12)
                                + str(stats["contributors"]).rjust(13)
                                + f"{stats['commits_per_contributor']:.1f}".rjust(12)
                                + f"{stats['insertions_per_contributor']:.1f}".rjust(12)
                                + f"{stats['deletions_per_contributor']:.1f}".rjust(12)
                            )
            else:
                # Header for raw data
                terminal.printb(
                    terminal.ljust("Repository", 20)
                    + terminal.ljust("Period", 12)
                    + terminal.rjust("Contributors", 13)
                    + terminal.rjust("Commits", 10)
                    + terminal.rjust("Insertions", 12)
                    + terminal.rjust("Deletions", 12)
                )

                # Data rows for raw data
                for repo in repositories:
                    for period in periods:
                        stats = self.activity_data.get_repo_stats_for_period(repo, period, self.normalize)
                        if stats["commits"] > 0:  # Only show periods with activity
                            print(
                                terminal.ljust(repo, 20)
                                + terminal.ljust(period, 12)
                                + str(stats["contributors"]).rjust(13)
                                + str(stats["commits"]).rjust(10)
                                + str(stats["insertions"]).rjust(12)
                                + str(stats["deletions"]).rjust(12)
                            )

        # Summary
        if self.show_both:
            # Summary showing both raw and normalized totals
            raw_totals = self.activity_data.get_total_stats(normalized=False)
            norm_totals = self.activity_data.get_total_stats(normalized=True)
            print("\n" + "=" * 75)
            print(
                terminal.ljust("TOTAL", 18)
                + terminal.ljust("", 10)
                + str(raw_totals.get("contributors", 0)).rjust(9)
                + str(raw_totals["commits"]).rjust(8)
                + f"{norm_totals.get('commits_per_contributor', 0):.1f}".rjust(6)
                + str(raw_totals["insertions"]).rjust(8)
                + f"{norm_totals.get('insertions_per_contributor', 0):.1f}".rjust(7)
                + str(raw_totals["deletions"]).rjust(8)
                + f"{norm_totals.get('deletions_per_contributor', 0):.1f}".rjust(7)
            )
        else:
            # Summary for single mode (existing behavior)
            totals = self.activity_data.get_total_stats(self.normalize)
            print("\n" + "=" * 81)
            if self.normalize:
                avg_contributors = totals.get("contributors", 1)
                print(
                    terminal.ljust("TOTAL", 20)
                    + terminal.ljust("", 12)
                    + str(avg_contributors).rjust(13)
                    + f"{totals.get('commits_per_contributor', 0):.1f}".rjust(12)
                    + f"{totals.get('insertions_per_contributor', 0):.1f}".rjust(12)
                    + f"{totals.get('deletions_per_contributor', 0):.1f}".rjust(12)
                )
            else:
                print(
                    terminal.ljust("TOTAL", 20)
                    + terminal.ljust("", 12)
                    + str(totals.get("contributors", 0)).rjust(13)
                    + str(totals["commits"]).rjust(10)
                    + str(totals["insertions"]).rjust(12)
                    + str(totals["deletions"]).rjust(12)
                )

    def output_html(self):
        if not self.activity_data.get_repositories():
            print('<div class="box"><h4>Repository Activity</h4><p>No activity data available.</p></div>')
            return

        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()
        max_values = self.activity_data.get_max_values(self.normalize)

        if not periods:
            print('<div class="box"><h4>Repository Activity</h4><p>No time periods found.</p></div>')
            return

        period_type = "weeks" if self.activity_data.useweeks else "months"

        print(f'<div class="box">')
        if self.show_both:
            print(f"<h4>Repository Activity Over Time</h4>")
            print(
                f"<p>{_(ACTIVITY_INFO_TEXT)} by {period_type}. Shows both raw totals and per-contributor averages for comprehensive analysis.</p>"
            )
        else:
            norm_text = " (Per Contributor)" if self.normalize else ""
            print(f"<h4>Repository Activity Over Time{norm_text}</h4>")
            print(f"<p>{_(ACTIVITY_INFO_TEXT)} by {period_type}. ", end="")
            if self.normalize:
                print(
                    "Statistics are normalized by the number of contributors per period to show per-developer productivity.</p>"
                )
            else:
                print("Raw statistics show absolute numbers.</p>")

        # Generate color palette for repositories
        colors = [
            "#3498db",
            "#e74c3c",
            "#2ecc71",
            "#f39c12",
            "#9b59b6",
            "#1abc9c",
            "#34495e",
            "#e67e22",
            "#95a5a6",
            "#27ae60",
        ]

        # Create charts for each metric
        if self.show_both:
            # Show both raw and normalized charts
            raw_max_values = self.activity_data.get_max_values(normalized=False)
            norm_max_values = self.activity_data.get_max_values(normalized=True)

            metrics = [
                ("commits", "Commits (Total)", raw_max_values["commits"], False),
                (
                    "commits_per_contributor",
                    "Commits per Contributor",
                    norm_max_values.get("commits_per_contributor", 0),
                    True,
                ),
                ("insertions", "Lines Added (Total)", raw_max_values["insertions"], False),
                (
                    "insertions_per_contributor",
                    "Lines Added per Contributor",
                    norm_max_values.get("insertions_per_contributor", 0),
                    True,
                ),
                ("deletions", "Lines Deleted (Total)", raw_max_values["deletions"], False),
                (
                    "deletions_per_contributor",
                    "Lines Deleted per Contributor",
                    norm_max_values.get("deletions_per_contributor", 0),
                    True,
                ),
            ]
        else:
            # Show either raw or normalized charts (existing behavior)
            max_values = self.activity_data.get_max_values(self.normalize)
            if self.normalize:
                metrics = [
                    (
                        "commits_per_contributor",
                        "Commits per Contributor",
                        max_values.get("commits_per_contributor", 0),
                        True,
                    ),
                    (
                        "insertions_per_contributor",
                        "Lines Added per Contributor",
                        max_values.get("insertions_per_contributor", 0),
                        True,
                    ),
                    (
                        "deletions_per_contributor",
                        "Lines Deleted per Contributor",
                        max_values.get("deletions_per_contributor", 0),
                        True,
                    ),
                ]
            else:
                metrics = [
                    ("commits", "Commits", max_values["commits"], False),
                    ("insertions", "Lines Added", max_values["insertions"], False),
                    ("deletions", "Lines Deleted", max_values["deletions"], False),
                ]

        for metric, title, max_val, is_normalized in metrics:
            if max_val == 0:
                continue

            chart_id = f"{metric.replace('_', '-')}-chart"

            # Make each chart individually collapsible unless disabled
            if get_no_collapsible():
                # Show chart title without collapsible wrapper
                print(f"<h4>{title} by Repository</h4>")
            else:
                print(f'<div class="chart-collapsible-header" data-target="{chart_id}">')
                print(f"    {title} by Repository")
                print(f'    <span class="chart-collapse-icon">▶</span>')
                print(f"</div>")
                print(f'<div id="{chart_id}" class="chart-collapsible-content" style="display: none;">')
            print(f'<div class="activity-chart">')
            print('<div class="chart-container">')

            # Chart data and styling
            print("<style>")
            print(".activity-chart { margin: 20px 0; }")
            print(".chart-container { margin: 10px 0; }")
            # Styles used for bar charts
            print(".chart-bar { display: inline-block; margin: 2px; vertical-align: bottom; }")
            print(".bar-group { margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }")
            print(".bar-label { font-size: 12px; text-align: center; margin-top: 5px; }")
            print(".period-label { font-weight: bold; margin: 15px 0 10px 0; color: #2c3e50; }")
            print(".repo-stats { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }")
            print(".repo-bar { flex: 1; min-width: 120px; text-align: center; }")
            print(".bar-fill { height: 20px; border-radius: 3px; margin: 5px 0; position: relative; }")
            print(".bar-text { font-size: 11px; color: white; line-height: 20px; font-weight: bold; }")
            # Styles used for line charts
            print(".line-chart { width: 100%; height: 320px; }")
            print(".legend { margin: 20px 0; }")
            print(".legend-item { display: inline-block; margin: 5px 10px 5px 0; }")
            print(
                ".legend-color { display: inline-block; width: 16px; height: 16px; margin-right: 5px; vertical-align: middle; }"
            )
            print("</style>")

            # Legend
            print('<div class="legend">')
            print("<strong>Repositories:</strong>")
            for i, repo in enumerate(repositories):
                color = colors[i % len(colors)]
                print(f'<span class="legend-item">')
                print(f'<span class="legend-color" style="background-color: {color};"></span>')
                print(f"{repo}")
                print("</span>")
            print("</div>")

            if self.chart_type == "bar":
                # Existing bar representation by period
                for period in periods:
                    # Show the section for the period regardless of activity so the x-axis is complete

                    print(f'<div class="period-label">{period}</div>')
                    print('<div class="repo-stats">')

                    for i, repo in enumerate(repositories):
                        stats = self.activity_data.get_repo_stats_for_period(repo, period, normalized=is_normalized)
                        value = stats.get(metric, 0)

                        percentage = (value / max_val) * 100 if max_val > 0 else 0
                        color = colors[i % len(colors)]

                        # Format value display based on whether it's normalized
                        if is_normalized and metric.endswith("_per_contributor"):
                            display_value = f"{value:.1f}"
                        else:
                            display_value = str(int(value))

                        print(f'<div class="repo-bar">')
                        print(f'<div class="bar-fill" style="background-color: {color}; width: {percentage:.1f}%;">')
                        print(f'<span class="bar-text">{display_value}</span>')
                        print("</div>")
                        print(f'<div class="bar-label">{repo}</div>')
                        print("</div>")

                    print("</div>")
            else:
                # Line chart using Flot: one series per repo, x-axis = periods
                container_id = f"{chart_id}-flot"
                print(f'<div id="{container_id}" class="line-chart"></div>')
                # Prepare JS arrays
                print('<script type="text/javascript">')
                print("(function(){")
                print("  var periods = [")
                for idx, period in enumerate(periods):
                    comma = "," if idx < len(periods) - 1 else ""
                    print(f'    [ {idx}, "{period}" ]{comma}')
                print("  ];")
                # Build series per repo
                print("  var series = [];")
                for i, repo in enumerate(repositories):
                    color = colors[i % len(colors)]
                    print("  (function(){")
                    print(f"    var data = [];")
                    for idx, period in enumerate(periods):
                        print(
                            f"    data.push([{idx}, {self.activity_data.get_repo_stats_for_period(repo, period, normalized=is_normalized).get(metric, 0)}]);"
                        )
                    print(f'    series.push({{ label: "{repo}", data: data, color: "{color}" }});')
                    print("  })();")
                print("  window.gitinspectorCharts = window.gitinspectorCharts || {};")
                print(f'  window.gitinspectorCharts["{container_id}"] = {{ series: series, ticks: periods }};')
                print("})();")
                print("</script>")

            print("</div>")  # chart-container
            print("</div>")  # activity-chart
            if not get_no_collapsible():
                print("</div>")  # chart-collapsible-content

        # Summary table
        print("<h5>Summary Statistics</h5>")
        if self.show_both:
            # Show both raw and normalized statistics
            print('<table class="git">')
            print(
                "<thead><tr><th>Repository</th><th>Contributors</th><th>Total Commits</th><th>Commits/Dev</th><th>Total Lines+</th><th>Lines+/Dev</th><th>Total Lines-</th><th>Lines-/Dev</th></tr></thead>"
            )
            print("<tbody>")

            for repo in repositories:
                # Get aggregated raw stats
                total_commits = 0
                total_insertions = 0
                total_deletions = 0
                unique_contributors = set()

                for period in periods:
                    raw_stats = self.activity_data.get_repo_stats_for_period(repo, period, normalized=False)
                    if raw_stats["commits"] > 0:
                        total_commits += raw_stats["commits"]
                        total_insertions += raw_stats["insertions"]
                        total_deletions += raw_stats["deletions"]

                # Get unique contributors for this repository using the dedicated method
                unique_contributors = self.activity_data.get_repo_unique_contributors(repo)
                total_contributors = len(unique_contributors)
                commits_per_dev = total_commits / max(1, total_contributors)
                insertions_per_dev = total_insertions / max(1, total_contributors)
                deletions_per_dev = total_deletions / max(1, total_contributors)

                print(f"<tr>")
                print(f"<td>{repo}</td>")
                print(f"<td>{total_contributors}</td>")
                print(f"<td>{total_commits}</td>")
                print(f"<td>{commits_per_dev:.1f}</td>")
                print(f"<td>{total_insertions}</td>")
                print(f"<td>{insertions_per_dev:.1f}</td>")
                print(f"<td>{total_deletions}</td>")
                print(f"<td>{deletions_per_dev:.1f}</td>")
                print(f"</tr>")
        else:
            # Show either raw or normalized (existing behavior)
            if self.normalize:
                print('<table class="git">')
                print(
                    "<thead><tr><th>Repository</th><th>Avg Contributors</th><th>Commits/Dev</th><th>Insertions/Dev</th><th>Deletions/Dev</th></tr></thead>"
                )
                print("<tbody>")

                for repo in repositories:
                    total_commits = 0
                    total_insertions = 0
                    total_deletions = 0
                    total_contributor_periods = 0

                    for period in periods:
                        stats = self.activity_data.get_repo_stats_for_period(repo, period, False)  # Get raw stats
                        if stats["commits"] > 0:
                            total_commits += stats["commits"]
                            total_insertions += stats["insertions"]
                            total_deletions += stats["deletions"]
                            total_contributor_periods += stats["contributors"]

                    # Calculate average contributors per active period
                    active_periods = sum(
                        1
                        for period in periods
                        if self.activity_data.get_repo_stats_for_period(repo, period, False)["commits"] > 0
                    )
                    avg_contributors = total_contributor_periods / active_periods if active_periods > 0 else 0

                    print(f"<tr>")
                    print(f"<td>{repo}</td>")
                    print(f"<td>{avg_contributors:.1f}</td>")
                    print(f"<td>{total_commits / max(1, total_contributor_periods):.1f}</td>")
                    print(f"<td>{total_insertions / max(1, total_contributor_periods):.1f}</td>")
                    print(f"<td>{total_deletions / max(1, total_contributor_periods):.1f}</td>")
                    print(f"</tr>")
            else:
                print('<table class="git">')
                print(
                    "<thead><tr><th>Repository</th><th>Total Contributors</th><th>Total Commits</th><th>Total Insertions</th><th>Total Deletions</th></tr></thead>"
                )
                print("<tbody>")

                for repo in repositories:
                    total_commits = 0
                    total_insertions = 0
                    total_deletions = 0
                    unique_contributors = set()

                    for period in periods:
                        stats = self.activity_data.get_repo_stats_for_period(repo, period, False)
                        total_commits += stats["commits"]
                        total_insertions += stats["insertions"]
                        total_deletions += stats["deletions"]

                    # Get unique contributors for this repository using the dedicated method
                    unique_contributors = self.activity_data.get_repo_unique_contributors(repo)

                    print(f"<tr>")
                    print(f"<td>{repo}</td>")
                    print(f"<td>{len(unique_contributors)}</td>")
                    print(f"<td>{total_commits}</td>")
                    print(f"<td>{total_insertions}</td>")
                    print(f"<td>{total_deletions}</td>")
                    print(f"</tr>")

        print("</tbody></table>")
        print("</div>")  # box

    def output_json(self):
        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()

        print(',\n\t\t"activity": {')
        print(f'\t\t\t"message": "{_(ACTIVITY_INFO_TEXT)}",')
        print(f'\t\t\t"period_type": "{"weeks" if self.activity_data.useweeks else "months"}",')
        print('\t\t\t"periods": [')

        period_json_items = []
        for period in periods:
            period_data = {"period": period, "repositories": []}

            for repo in repositories:
                stats = self.activity_data.get_repo_stats_for_period(repo, period)
                if stats["commits"] > 0:  # Only include periods with activity
                    period_data["repositories"].append(
                        {
                            "name": repo,
                            "commits": stats["commits"],
                            "insertions": stats["insertions"],
                            "deletions": stats["deletions"],
                        }
                    )

            if period_data["repositories"]:  # Only include periods with activity
                period_json = f"\t\t\t\t{{"
                period_json += f'\n\t\t\t\t\t"period": "{period}",'
                period_json += f'\n\t\t\t\t\t"repositories": ['

                repo_items = []
                for repo_data in period_data["repositories"]:
                    repo_json = f"\n\t\t\t\t\t\t{{"
                    repo_json += f'\n\t\t\t\t\t\t\t"name": "{repo_data["name"]}",'
                    repo_json += f'\n\t\t\t\t\t\t\t"commits": {repo_data["commits"]},'
                    repo_json += f'\n\t\t\t\t\t\t\t"insertions": {repo_data["insertions"]},'
                    repo_json += f'\n\t\t\t\t\t\t\t"deletions": {repo_data["deletions"]}'
                    repo_json += f"\n\t\t\t\t\t\t}}"
                    repo_items.append(repo_json)

                period_json += ",".join(repo_items)
                period_json += f"\n\t\t\t\t\t]"
                period_json += f"\n\t\t\t\t}}"
                period_json_items.append(period_json)

        print(",\n".join(period_json_items))
        print("\n\t\t\t]")
        print("\t\t}", end="")

    def output_xml(self):
        repositories = self.activity_data.get_repositories()
        periods = self.activity_data.get_periods()

        print("\t<activity>")
        print(f"\t\t<message>{_(ACTIVITY_INFO_TEXT)}</message>")
        print(f'\t\t<period_type>{"weeks" if self.activity_data.useweeks else "months"}</period_type>')

        for period in periods:
            has_activity = any(
                self.activity_data.get_repo_stats_for_period(repo, period)["commits"] > 0 for repo in repositories
            )

            if has_activity:
                print(f'\t\t<period name="{period}">')

                for repo in repositories:
                    stats = self.activity_data.get_repo_stats_for_period(repo, period)
                    if stats["commits"] > 0:
                        print(f'\t\t\t<repository name="{repo}">')
                        print(f'\t\t\t\t<commits>{stats["commits"]}</commits>')
                        print(f'\t\t\t\t<insertions>{stats["insertions"]}</insertions>')
                        print(f'\t\t\t\t<deletions>{stats["deletions"]}</deletions>')
                        print(f"\t\t\t</repository>")

                print(f"\t\t</period>")

        print("\t</activity>")
