# coding: utf-8
#
# Copyright © 2025 gitinspector contributors. All rights reserved.
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

import os
from . import localization

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not found. Team filtering requires PyYAML to be installed.")
    print("Install with: pip install PyYAML")
    yaml = None

# Global variable to store team members
__team_members__ = set()
__team_config_loaded__ = False


class TeamConfigError(Exception):
    def __init__(self, msg):
        super(TeamConfigError, self).__init__(msg)
        self.msg = msg


def load_team_config(config_file_path):
    """Load team configuration from YAML file"""
    global __team_members__, __team_config_loaded__

    if yaml is None:
        raise TeamConfigError(_("PyYAML is required for team filtering. Install with: pip install PyYAML"))

    if not os.path.exists(config_file_path):
        raise TeamConfigError(_("Team config file not found: {0}").format(config_file_path))

    try:
        with open(config_file_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        if not config or "team" not in config:
            raise TeamConfigError(_("Invalid team config: 'team' key not found in {0}").format(config_file_path))

        if not isinstance(config["team"], list):
            raise TeamConfigError(_("Invalid team config: 'team' must be a list in {0}").format(config_file_path))

        # Store team members in global set for fast lookup
        __team_members__ = set(config["team"])
        __team_config_loaded__ = True

        print(_("Loaded team config with {0} members from {1}").format(len(__team_members__), config_file_path))

    except yaml.YAMLError as e:
        raise TeamConfigError(_("Error parsing YAML file {0}: {1}").format(config_file_path, str(e)))
    except Exception as e:
        raise TeamConfigError(_("Error loading team config {0}: {1}").format(config_file_path, str(e)))


def is_team_member(author_name):
    """Check if an author is a team member"""
    if not __team_config_loaded__:
        return True  # If no team config loaded, include everyone

    # Normalize author name (strip whitespace)
    author_name = author_name.strip()

    # Check exact match first
    if author_name in __team_members__:
        return True

    # Check if any team member name is a substring of the author name (case-insensitive)
    author_lower = author_name.lower()
    for member in __team_members__:
        if member.lower() in author_lower or author_lower in member.lower():
            return True

    return False


def get_team_members():
    """Get the set of team members"""
    return __team_members__.copy()


def is_team_filtering_enabled():
    """Check if team filtering is enabled"""
    return __team_config_loaded__


def clear_team_config():
    """Clear loaded team configuration"""
    global __team_members__, __team_config_loaded__
    __team_members__ = set()
    __team_config_loaded__ = False
