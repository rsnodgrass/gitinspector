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


from shlex import quote

__since__ = ""

__until__ = ""

__ref__ = "HEAD"


def has_interval():
    return __since__ + __until__ != ""


def get_since():
    return __since__


def set_since(since):
    global __since__
    __since__ = "--since=" + quote(since)


def get_until():
    return __until__


def set_until(until):
    global __until__
    __until__ = "--until=" + quote(until)


def get_ref():
    return __ref__


def set_ref(ref):
    global __ref__
    __ref__ = ref


def set_quarter(quarter_str):
    """Set since and until dates based on a quarter string (e.g., 'Q1-2025', 'Q2-2025').

    Quarter format: Q{1-4}-{year}
    Q1: Jan 1 - Mar 31
    Q2: Apr 1 - Jun 30
    Q3: Jul 1 - Sep 30
    Q4: Oct 1 - Dec 31
    """
    import re
    from datetime import datetime, timedelta

    # Parse quarter string (e.g., "Q1-2025", "Q2-2025")
    # Must be exactly Q{1-4}-{4-digit-year} with no extra characters
    match = re.match(r"^Q([1-4])-(\d{4})$", quarter_str.upper())
    if not match:
        raise ValueError(f"Invalid quarter format: {quarter_str}. Expected format: Q1-2025, Q2-2025, etc.")

    quarter = int(match.group(1))
    year = int(match.group(2))

    # Define quarter start dates
    quarter_starts = {
        1: (1, 1),  # January 1
        2: (4, 1),  # April 1
        3: (7, 1),  # July 1
        4: (10, 1),  # October 1
    }

    # Define quarter end dates
    quarter_ends = {
        1: (3, 31),  # March 31
        2: (6, 30),  # June 30
        3: (9, 30),  # September 30
        4: (12, 31),  # December 31
    }

    # Set since date (start of quarter)
    start_month, start_day = quarter_starts[quarter]
    since_date = datetime(year, start_month, start_day)
    set_since(since_date.strftime("%Y-%m-%d"))

    # Set until date (end of quarter)
    end_month, end_day = quarter_ends[quarter]
    until_date = datetime(year, end_month, end_day)
    set_until(until_date.strftime("%Y-%m-%d"))
