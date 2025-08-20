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


import atexit
import getopt
import os
import sys
from .blame import Blame
from .changes import Changes
from .config import GitConfig
from .metrics import MetricsLogic
from . import (
    basedir,
    clone,
    extensions,
    filtering,
    format,
    help,
    interval,
    localization,
    optval,
    teamconfig,
    terminal,
    version,
)
from .output import outputable
from .output.blameoutput import BlameOutput
from .output.changesoutput import ChangesOutput
from .output.extensionsoutput import ExtensionsOutput
from .output.filteringoutput import FilteringOutput
from .output.metricsoutput import MetricsOutput
from .output.responsibilitiesoutput import ResponsibilitiesOutput
from .output.timelineoutput import TimelineOutput
from .output.activityoutput import ActivityOutput
from . import activity

localization.init()


class Runner(object):
    def __init__(self):
        self.hard = False
        self.include_metrics = False
        self.list_file_types = False
        self.localize_output = False
        self.responsibilities = False
        self.grading = False
        self.timeline = False
        self.useweeks = False
        self.activity = False
        self.activity_normalize = False
        self.activity_dual = False
        self.activity_chart_type = "line"  # 'line' (default) or 'bar'

    def _show_repo_progress(self, current_repo, total_repos, repo_name, progress_percent, status=""):
        """Show dynamic progress bar for repository processing"""
        # Create progress bar with better visual appeal
        bar_width = 25
        filled_width = int(bar_width * progress_percent / 100)

        # Use different characters for a more modern look
        if progress_percent == 100:
            bar = "█" * bar_width  # Solid bar when complete
        else:
            bar = (
                "█" * filled_width
                + "▓" * min(1, bar_width - filled_width)
                + "░" * max(0, bar_width - filled_width - 1)
            )

        # Format the progress message with better spacing
        repo_info = "Repository {}/{}: {}".format(current_repo, total_repos, repo_name)
        progress_info = "[{}] {:3d}%".format(bar, progress_percent)

        if status:
            if progress_percent == 100:
                message = "{} {} {}".format(repo_info, progress_info, status)
            else:
                message = "{} {} - {}".format(repo_info, progress_info, status)
        else:
            message = "{} {}".format(repo_info, progress_info)

        # Clear line and show progress (ensure it fits terminal width)
        terminal_width = terminal.get_size()[0]
        if len(message) > terminal_width - 1:
            # Truncate repo name if message is too long
            max_repo_name_len = max(10, terminal_width - 50)  # Reserve space for progress bar
            if len(repo_name) > max_repo_name_len:
                truncated_repo_name = repo_name[: max_repo_name_len - 3] + "..."
                repo_info = "Repository {}/{}: {}".format(current_repo, total_repos, truncated_repo_name)
                if status:
                    if progress_percent == 100:
                        message = "{} {} {}".format(repo_info, progress_info, status)
                    else:
                        message = "{} {} - {}".format(repo_info, progress_info, status)
                else:
                    message = "{} {}".format(repo_info, progress_info)

        print("\r{}\r{}".format(" " * terminal_width, message), end="", file=sys.stderr)
        sys.stderr.flush()

    def _needs_blame_analysis(self):
        """Determine if blame analysis is required based on enabled features."""
        return (
            not self.activity  # If not activity-only mode, we need blame for default output
            or self.responsibilities  # ResponsibilitiesOutput requires blame
            # Note: Default blame output is always shown unless in activity-only mode
        )

    def _is_activity_only_mode(self):
        """Check if only activity analysis is requested (optimization opportunity)."""
        return (
            self.activity
            and not self.responsibilities
            and not self.timeline
            and not self.include_metrics
            and not self.list_file_types
            # In this mode, we only need Changes analysis, not Blame
        )

    def process(self, repos):
        localization.check_compatibility(version.__version__)

        if not self.localize_output:
            localization.disable()

        terminal.skip_escapes(not sys.stdout.isatty())
        terminal.set_stdout_encoding()
        previous_directory = os.getcwd()

        # Conditional initialization based on what analysis is needed
        needs_blame = self._needs_blame_analysis()
        summed_blames = Blame.__new__(Blame) if needs_blame else None
        summed_changes = Changes.__new__(Changes)
        summed_metrics = MetricsLogic.__new__(MetricsLogic) if self.include_metrics else None
        changes_by_repo = {}  # Store changes by repository for activity analysis

        for repo_index, repo in enumerate(repos, 1):
            repo_name = repo.name or os.path.basename(repo.location)

            # Show repository progress for multiple repositories
            if len(repos) > 1 and sys.stderr.isatty():
                self._show_repo_progress(repo_index, len(repos), repo_name, 0)

            os.chdir(repo.location)
            repo = repo if len(repos) > 1 else None

            # Step 1: Changes analysis (always needed)
            if len(repos) > 1 and sys.stderr.isatty():
                self._show_repo_progress(repo_index, len(repos), repo_name, 10, "Analyzing commits...")
            changes = Changes(repo, self.hard)

            # Step 2: Blame analysis (conditional - skip if only activity is needed)
            if needs_blame:
                if len(repos) > 1 and sys.stderr.isatty():
                    self._show_repo_progress(repo_index, len(repos), repo_name, 50, "Analyzing file ownership...")
                summed_blames += Blame(repo, self.hard, self.useweeks, changes)

            summed_changes += changes

            # Store changes by repository for activity analysis
            if self.activity:
                changes_by_repo[repo_name] = changes

            # Step 3: Metrics analysis (conditional)
            if self.include_metrics:
                progress_step = 90 if needs_blame else 50  # Adjust progress based on what steps we're doing
                if len(repos) > 1 and sys.stderr.isatty():
                    self._show_repo_progress(
                        repo_index, len(repos), repo_name, progress_step, "Calculating metrics..."
                    )
                summed_metrics += MetricsLogic()

            # Show completion
            if len(repos) > 1 and sys.stderr.isatty():
                self._show_repo_progress(repo_index, len(repos), repo_name, 100, "✓ Completed")
                print(file=sys.stderr)  # Add newline after completion

            if sys.stdout.isatty() and format.is_interactive_format():
                terminal.clear_row()
        else:
            os.chdir(previous_directory)

        format.output_header(repos)

        # Conditional output based on requested analysis
        if self._is_activity_only_mode():
            # Activity-only mode: skip default outputs and only show activity
            if self.activity and changes_by_repo:
                activity_data = activity.ActivityData(changes_by_repo, self.useweeks)
                outputable.output(
                    ActivityOutput(
                        activity_data, self.activity_normalize, self.activity_dual, self.activity_chart_type
                    )
                )
        else:
            # Standard mode: show requested outputs
            outputable.output(ChangesOutput(summed_changes))

            if summed_changes.get_commits():
                # Only output blame if we computed it
                if summed_blames is not None:
                    outputable.output(BlameOutput(summed_changes, summed_blames))

                if self.timeline:
                    outputable.output(TimelineOutput(summed_changes, self.useweeks))

                if self.include_metrics and summed_metrics is not None:
                    outputable.output(MetricsOutput(summed_metrics))

                if self.responsibilities and summed_blames is not None:
                    outputable.output(ResponsibilitiesOutput(summed_changes, summed_blames))

                outputable.output(FilteringOutput())

                if self.list_file_types:
                    outputable.output(ExtensionsOutput())

                if self.activity and changes_by_repo:
                    activity_data = activity.ActivityData(changes_by_repo, self.useweeks)
                    outputable.output(
                        ActivityOutput(
                            activity_data, self.activity_normalize, self.activity_dual, self.activity_chart_type
                        )
                    )

        format.output_footer()
        os.chdir(previous_directory)


def __check_python_version__():
    if sys.version_info < (3, 8):
        python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])
        sys.exit(_("gitinspector requires at least Python 3.8 to run (version {0} was found).").format(python_version))


def __get_validated_git_repos__(repos_relative):
    if not repos_relative:
        repos_relative = "."

    repos = []

    # Try to clone the repos or return the same directory and bail out.
    for repo in repos_relative:
        cloned_repo = clone.create(repo)

        if cloned_repo.name == None:
            cloned_repo.location = basedir.get_basedir_git(cloned_repo.location)
            cloned_repo.name = os.path.basename(cloned_repo.location)

        repos.append(cloned_repo)

    return repos


def main():
    terminal.check_terminal_encoding()
    terminal.set_stdin_encoding()
    argv = terminal.convert_command_line_to_utf8()
    run = Runner()
    repos = []

    try:
        opts, args = optval.gnu_getopt(
            argv[1:],
            "f:F:hHlLmrTwx:A",
            [
                "exclude=",
                "file-types=",
                "format=",
                "hard:true",
                "help",
                "list-file-types:true",
                "localize-output:true",
                "metrics:true",
                "responsibilities:true",
                "quarter=",
                "since=",
                "grading:true",
                "team:true",
                "config-repos:true",
                "timeline:true",
                "until=",
                "version",
                "weeks:true",
                "activity:true",
                "activity-normalize:true",
                "activity-dual:true",
                "activity-chart=",
            ],
        )

        # Process configuration options
        use_config_repos = False
        use_team_filtering = False

        for o, a in opts:
            if o == "--team":
                # Load team members and apply team filtering
                use_team_filtering = optval.get_boolean_argument(a)
            elif o == "--config-repos":
                # Load repositories without team filtering
                use_config_repos = optval.get_boolean_argument(a)

        # Load team config if any of the options are specified
        if use_config_repos or use_team_filtering:
            try:
                teamconfig.load_team_config("team_config.json", enable_team_filtering=use_team_filtering)
            except teamconfig.TeamConfigError as e:
                print(sys.argv[0], "\b:", e.msg, file=sys.stderr)
                sys.exit(1)

        # Determine which repositories to use
        if args:
            # Command line repositories always override config repositories
            repos = __get_validated_git_repos__(set(args))
            if use_config_repos and teamconfig.has_repositories():
                print("Command line repositories override config file repositories", file=sys.stderr)
        elif use_config_repos:
            # Use repositories from config file only when no command line repos
            if teamconfig.has_repositories():
                config_repos = teamconfig.get_repositories()
                if not config_repos:
                    print(sys.argv[0], "\b:", "No repositories found in config file", file=sys.stderr)
                    sys.exit(1)
                repos = __get_validated_git_repos__(config_repos)
                print("Using {0} repositories from config file".format(len(config_repos)), file=sys.stderr)
            else:
                print(
                    sys.argv[0],
                    "\b:",
                    "--config-repos specified but no repositories found in config file",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            # Fall back to current directory (existing behavior)
            repos = __get_validated_git_repos__(["."])

        # We need the repos above to be set before we read the git config.
        GitConfig(run, repos[-1].location).read()
        clear_x_on_next_pass = True

        for o, a in opts:
            if o in ("-h", "--help"):
                help.output()
                sys.exit(0)
            elif o in ("-f", "--file-types"):
                extensions.define(a)
            elif o in ("-F", "--format"):
                if not format.select(a):
                    raise format.InvalidFormatError(_("specified output format not supported."))
            elif o == "-H":
                run.hard = True
            elif o == "--hard":
                run.hard = optval.get_boolean_argument(a)
            elif o == "-l":
                run.list_file_types = True
            elif o == "--list-file-types":
                run.list_file_types = optval.get_boolean_argument(a)
            elif o == "-L":
                run.localize_output = True
            elif o == "--localize-output":
                run.localize_output = optval.get_boolean_argument(a)
            elif o == "-m":
                run.include_metrics = True
            elif o == "--metrics":
                run.include_metrics = optval.get_boolean_argument(a)
            elif o == "-r":
                run.responsibilities = True
            elif o == "--responsibilities":
                run.responsibilities = optval.get_boolean_argument(a)
            elif o == "--quarter":
                try:
                    interval.set_quarter(a)
                except ValueError as e:
                    print(sys.argv[0], "\b:", str(e), file=sys.stderr)
                    sys.exit(1)
            elif o == "--since":
                interval.set_since(a)
            elif o == "--version":
                version.output()
                sys.exit(0)
            elif o == "--grading":
                grading = optval.get_boolean_argument(a)
                run.include_metrics = grading
                run.list_file_types = grading
                run.responsibilities = grading
                run.grading = grading
                run.hard = grading
                run.timeline = grading
                run.useweeks = grading
            elif o == "--team-config":
                # Already processed above, skip here
                pass
            elif o == "-T":
                run.timeline = True
            elif o == "--timeline":
                run.timeline = optval.get_boolean_argument(a)
            elif o == "--until":
                interval.set_until(a)
            elif o == "-w":
                run.useweeks = True
            elif o == "--weeks":
                run.useweeks = optval.get_boolean_argument(a)
            elif o == "-A":
                run.activity = True
                run.activity_dual = True  # Default to showing both raw and normalized stats
            elif o == "--activity":
                run.activity = optval.get_boolean_argument(a)
            elif o == "--activity-normalize":
                run.activity_normalize = optval.get_boolean_argument(a)
            elif o == "--activity-dual":
                run.activity_dual = optval.get_boolean_argument(a)
            elif o == "--activity-chart":
                chart = a.strip().lower()
                if chart not in ("line", "bar"):
                    raise optval.InvalidOptionArgument("--activity-chart must be 'line' or 'bar'")
                run.activity_chart_type = chart
            elif o in ("-x", "--exclude"):
                if clear_x_on_next_pass:
                    clear_x_on_next_pass = False
                    filtering.clear()
                filtering.add(a)

        __check_python_version__()
        run.process(repos)

    except (
        filtering.InvalidRegExpError,
        format.InvalidFormatError,
        optval.InvalidOptionArgument,
        teamconfig.TeamConfigError,
        getopt.error,
    ) as exception:
        print(sys.argv[0], "\b:", exception.msg, file=sys.stderr)
        print(_("Try `{0} --help' for more information.").format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)


@atexit.register
def cleanup():
    clone.delete()


if __name__ == "__main__":
    main()
