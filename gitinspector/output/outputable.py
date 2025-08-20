# coding: utf-8
#
# Copyright © 2012-2013 Ejwa Software. All rights reserved.
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


from .. import format


class Outputable(object):
    def output_html(self):
        raise NotImplementedError(_("HTML output not yet supported in") + ' "' + self.__class__.__name__ + '".')

    def output_json(self):
        raise NotImplementedError(_("JSON output not yet supported in") + ' "' + self.__class__.__name__ + '".')

    def output_text(self):
        raise NotImplementedError(_("Text output not yet supported in") + ' "' + self.__class__.__name__ + '".')

    def output_xml(self):
        raise NotImplementedError(_("XML output not yet supported in") + ' "' + self.__class__.__name__ + '".')


def output(outputable):
    if format.get_selected() == "html" or format.get_selected() == "htmlembedded":
        # For HTML output, wrap in collapsible sections for most outputs.
        # ActivityOutput already renders its own internal structure and chart-level collapsibles,
        # so do NOT add a top-level collapsible around it.
        if outputable.__class__.__name__ == "ActivityOutput":
            outputable.output_html()
        else:
            _output_html_with_collapsible(outputable)
    elif format.get_selected() == "json":
        outputable.output_json()
    elif format.get_selected() == "text":
        outputable.output_text()
    else:
        outputable.output_xml()


def _output_html_with_collapsible(outputable):
    """
    Wrapper that captures HTML output and makes it collapsible.
    """
    import sys
    from io import StringIO

    # Get the section title based on the output type
    section_title = _get_section_title(outputable)
    section_id = _get_section_id(outputable)

    # Capture the HTML output
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        outputable.output_html()
        html_content = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    # Only create collapsible if there's actual content and it's not activity output
    if html_content.strip():
        if outputable.__class__.__name__ == "ActivityOutput":
            # Directly print activity HTML without top-level collapsible wrapper
            print(html_content, end="")
            return

        print(f'<div class="collapsible-header" data-target="{section_id}">')
        print(f"    {section_title}")
        print(f'    <span class="collapse-icon">▶</span>')
        print(f"</div>")
        print(f'<div id="{section_id}" class="collapsible-content">')
        print(html_content, end="")  # HTML content already has proper formatting
        print(f"</div>")


def _get_section_title(outputable):
    """Get a human-readable title for the output section."""
    class_name = outputable.__class__.__name__

    title_map = {
        "ChangesOutput": "Commit History & Statistics",
        "BlameOutput": "File Ownership & Code Authorship",
        "TimelineOutput": "Timeline Analysis",
        "MetricsOutput": "Code Quality Metrics",
        "ResponsibilitiesOutput": "Author Responsibilities",
        "FilteringOutput": "Applied Filters",
        "ExtensionsOutput": "File Types Analysis",
        "ActivityOutput": "Repository Activity Over Time",
    }

    return title_map.get(class_name, class_name.replace("Output", " Analysis"))


def _get_section_id(outputable):
    """Get a CSS-friendly ID for the output section."""
    class_name = outputable.__class__.__name__

    id_map = {
        "ChangesOutput": "changes-section",
        "BlameOutput": "blame-section",
        "TimelineOutput": "timeline-section",
        "MetricsOutput": "metrics-section",
        "ResponsibilitiesOutput": "responsibilities-section",
        "FilteringOutput": "filtering-section",
        "ExtensionsOutput": "extensions-section",
        "ActivityOutput": "activity-section",
    }

    return id_map.get(class_name, class_name.lower().replace("output", "-section"))
