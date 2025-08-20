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


import sys
from .extensions import DEFAULT_EXTENSIONS
from .format import __available_formats__


__doc__ = _(
    """Usage: {0} [OPTION]... [REPOSITORY]...
List information about the repository in REPOSITORY. If no repository is
specified, the current directory is used. If multiple repositories are
given, information will be merged into a unified statistical report.

Mandatory arguments to long options are mandatory for short options too.
Boolean arguments can only be given to long options.
  -f, --file-types=EXTENSIONS    a comma separated list of file extensions to
                                   include when computing statistics. The
                                   default extensions used are:
                                   {1}
                                   Specifying * includes files with no
                                   extension, while ** includes all files
  -F, --format=FORMAT            define in which format output should be
                                   generated; the default format is 'text' and
                                   the available formats are:
                                   {2}
      --grading[=BOOL]           show statistics and information in a way that
                                   is formatted for grading of student
                                   projects; this is the same as supplying the
                                   options -HlmrTw
  -H, --hard[=BOOL]              track rows and look for duplicates harder;
                                   this can be quite slow with big repositories
  -l, --list-file-types[=BOOL]   list all the file extensions available in the
                                   current branch of the repository
  -L, --localize-output[=BOOL]   localize the generated output to the selected
                                   system language if a translation is
                                   available
  -m  --metrics[=BOOL]           include checks for certain metrics during the
                                   analysis of commits
  -r  --responsibilities[=BOOL]  show which files the different authors seem
                                   most responsible for
      --quarter=QUARTER          set since and until dates for a business quarter
                                   (e.g., Q1-2025, Q2-2025, Q3-2025, Q4-2025)
                                   Q1: Jan 1 - Mar 31, Q2: Apr 1 - Jun 30
                                   Q3: Jul 1 - Sep 30, Q4: Oct 1 - Dec 31
      --since=DATE               only show statistics for commits more recent
                                   than a specific date
      --team-config=FILE         path to JSON file containing team member names;
                                   only statistics for these team members will
                                   be included in the output
      --config-repos[=BOOL]      when enabled, read repository paths from the
                                   team config file instead of command line;
                                   command line repositories override config
                                   file repositories when both are specified
  -T, --timeline[=BOOL]          show commit timeline, including author names
      --until=DATE               only show statistics for commits older than a
                                   specific date
  -w, --weeks[=BOOL]             show all statistical information in weeks
                                   instead of in months
  -A, --activity[=BOOL]          show repository activity statistics over time
                                   periods with charts for each repository
      --activity-normalize[=BOOL] normalize activity statistics by number of
                                   contributors per period (shows per-contributor
                                   productivity instead of absolute numbers)
      --activity-dual[=BOOL]     show both raw totals and normalized per-contributor
                                   statistics side-by-side for comprehensive analysis
      --activity-chart=TYPE      select activity chart type in HTML output
                                   TYPE can be 'line' (default) or 'bar'
  -x, --exclude=PATTERN          an exclusion pattern describing the file
                                   paths, revisions, revisions with certain
                                   commit messages, author names or author
                                   emails that should be excluded from the
                                   statistics; can be specified multiple times
  -h, --help                     display this help and exit
      --version                  output version information and exit

gitinspector will filter statistics to only include commits that modify,
add or remove one of the specified extensions, see -f or --file-types for
more information.

gitinspector requires that the git executable is available in your PATH.
Report gitinspector bugs to gitinspector@ejwa.se."""
)


def output():
    print(__doc__.format(sys.argv[0], ",".join(DEFAULT_EXTENSIONS), ",".join(__available_formats__)))
