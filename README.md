[![Latest release](https://img.shields.io/github/release/ejwa/gitinspector.svg?style=flat-square)](https://github.com/ejwa/gitinspector/releases/latest)
[![License](https://img.shields.io/github/license/ejwa/gitinspector.svg?style=flat-square)](https://github.com/ejwa/gitinspector/blob/master/LICENSE.txt)
<h2>
 <img align="left" height="65px"
      src="https://raw.githubusercontent.com/ejwa/gitinspector/master/gitinspector/html/gitinspector_piclet.png"/>
      &nbsp;About Gitinspector
</h2>
<img align="right" width="30%" src="https://raw.github.com/wiki/ejwa/gitinspector/images/html_example.jpg" /> 
Gitinspector is a statistical analysis tool for git repositories. The default analysis shows general statistics per author, which can be complemented with a timeline analysis that shows the workload and activity of each author. Under normal operation, it filters the results to only show statistics about a number of given extensions and by default only includes source files in the statistical analysis.

This tool was originally written to help fetch repository statistics from student projects in the course Object-oriented Programming Project (TDA367/DIT211) at Chalmers University of Technology and Gothenburg University.

Today, gitinspector is used as a grading aid by universities worldwide.

A full [Documentation](https://github.com/ejwa/gitinspector/wiki/Documentation) of the usage and available options of gitinspector is available on the wiki. For help on the most common questions, please refer to the [FAQ](https://github.com/ejwa/gitinspector/wiki/FAQ) document.

## Installation

### Requirements
- **Python 3.8+** (no additional dependencies required!)

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/ejwa/gitinspector.git
   cd gitinspector
   ```

2. **Run directly:**
   ```bash
   python gitinspector.py [options] <repository-path>
   ```

That's it! No virtual environment or package installation needed.

## Usage

### Basic Usage
```bash
# Analyze current directory
python gitinspector.py .

# Analyze a specific repository
python gitinspector.py /path/to/your/repo

# 🌟 Analyze multiple repositories (aggregated statistics)
python gitinspector.py /path/to/repo1 /path/to/repo2 /path/to/repo3

# Get help with all available options
python gitinspector.py --help
```

### Multi-Repository Analysis
gitinspector supports analyzing multiple repositories simultaneously, providing aggregated statistics across all repositories. This is perfect for teams working across multiple codebases:

```bash
# Analyze multiple local repositories
python gitinspector.py ~/projects/frontend ~/projects/backend ~/projects/mobile

# Mix local and remote repositories
python gitinspector.py \
  /local/repo \
  https://github.com/team/repo1.git \
  https://github.com/team/repo2.git

# Full team analysis across multiple repositories
python gitinspector.py \
  -F html \
  --since 2024-01-01 \
  --team-config team_config.json \
  -r -m -T -w \
  /path/to/frontend-repo \
  /path/to/backend-repo > team_report.html
```

**Dynamic Progress Tracking**: When analyzing multiple repositories, gitinspector shows beautiful real-time progress indicators:
```
Repository 1/3: frontend-repo [████████▓░░░░░░░░░░░░░░░░]  45% - Analyzing commits...
Repository 1/3: frontend-repo [████████████████▓░░░░░░░]  78% - Analyzing file ownership...
Repository 1/3: frontend-repo [█████████████████████████] 100% ✓ Completed

Repository 2/3: backend-repo [██████▓░░░░░░░░░░░░░░░░░░]  32% - Analyzing commits...
Repository 2/3: backend-repo [█████████████████████████] 100% ✓ Completed
...
```

The progress bars work with all output formats and show:
- Real-time percentage completion per repository
- Current analysis phase (commits, file ownership, metrics)
- Visual progress bar with modern Unicode characters
- Proper handling of long repository names
- Progress indicators work even when output is redirected to files

### Repository Activity Statistics

The `--activity` / `-A` parameter provides powerful insights into repository development patterns over time:

```bash
# Show monthly activity statistics across repositories
# Now defaults to showing BOTH raw totals and normalized per-contributor stats
python gitinspector.py -A repo1 repo2 repo3

# Show weekly activity with HTML charts
python gitinspector.py -A -w -F html repo1 repo2 repo3 > activity_report.html

# 🎯 Normalized per-contributor analysis only
python gitinspector.py -A --activity-normalize repo1 repo2 repo3

# 🌟 Dual display: Show both raw and normalized statistics (same as default -A)
python gitinspector.py -A --activity-dual repo1 repo2 repo3

# 📊 Choose chart type: line graphs (default) or bar charts
python gitinspector.py -A --activity-chart=bar -F html repo1 repo2 repo3

# Combine with other analysis options
python gitinspector.py -A --activity-normalize -F html --since 2024-01-01 \
  --team-config team_config.json \
  frontend-repo backend-repo mobile-repo > team_activity.html
```

**Features:**
- **Time-based Analysis**: Monthly or weekly breakdowns (`-w` for weeks)
- **Repository Comparison**: Side-by-side activity comparison
- **Multiple Metrics**: Commits, line insertions, and deletions per repository
- **🔥 Normalization**: `--activity-normalize` shows per-contributor productivity only
- **🌟 Dual Display**: `--activity-dual` shows both raw totals and normalized averages (now the default for `-A`)
- **📊 Chart Types**: Choose between line graphs (default) or bar charts with `--activity-chart`
- **Beautiful Charts**: HTML output includes interactive, collapsible charts
- **All Formats**: Text, HTML, JSON, and XML output supported
- **Performance Optimized**: Automatically skips expensive analysis when only activity data is needed

**Why Use Normalization?**

Raw activity statistics can be misleading when team sizes grow over time. The `--activity-normalize` feature solves this by showing **per-contributor averages**:

```bash
# Default -A: Shows BOTH raw totals and normalized per-contributor stats
python gitinspector.py -A repo1 repo2

# Normalized stats only: Shows per-developer averages (true productivity)
python gitinspector.py -A --activity-normalize repo1 repo2
```

**Example Output Comparison:**
- **Raw**: "50 commits in Q3" (but team grew from 2 to 5 people)
- **Normalized**: "12.5 commits/developer in Q3" (actual productivity per person)

**HTML Output Includes:**
- Color-coded bar charts for each metric (commits, insertions, deletions)
- Period-by-period visualization (e.g., 2024-01, 2024-02, etc.)
- Summary statistics table with repository totals
- Responsive design with modern styling

### Business Quarter Analysis

The new `--quarter` option makes it easy to analyze specific business quarters without manual date calculations:

```bash
# Analyze Q2 2025 (April 1 - June 30, 2025)
python gitinspector.py --quarter Q2-2025 -T -F html -f "**" repo1 repo2

# Analyze Q1 2024 (January 1 - March 31, 2024)
python gitinspector.py --quarter Q1-2024 -A --activity-normalize repo1 repo2

# Combine with team configuration
python gitinspector.py --quarter Q3-2025 --team-config team.json -A repo1 repo2
```

**Supported Quarter Formats:**
- **Q1-YYYY**: January 1 - March 31
- **Q2-YYYY**: April 1 - June 30
- **Q3-YYYY**: July 1 - September 30
- **Q4-YYYY**: October 1 - December 31

**Examples:**
- `Q1-2025` → Jan 1, 2025 - Mar 31, 2025
- `Q2-2025` → Apr 1, 2025 - Jun 30, 2025
- `Q3-2025` → Jul 1, 2025 - Sep 30, 2025
- `Q4-2025` → Oct 1, 2025 - Dec 31, 2025

This replaces the need to manually calculate and specify `--since` and `--until` dates for quarterly analysis.

### Configuration System
GitInspector uses a standardized `team_config.json` file for configuration. This file can contain both team member definitions and repository paths:

**team_config.json:**
```json
{
  "team": [
    "john.doe@company.com",
    "jane.smith@company.com",
    "alice.johnson",
    "bob.wilson"
  ],
  "_comment_repos": "optional: list of repository paths to analyze when using --config-repos",
  "repositories": [
    "../recall-api",
    "../otter-web",
    "/path/to/other/repo"
  ]
}
```

**Configuration Flags:**

- **`--team`**: Apply team filtering (include only team members from `team_config.json`)
- **`--config-repos`**: Use repository paths from `team_config.json`
- **Combine both flags**: Use both repositories and team filtering together

```bash
# Analyze repositories from config, but include ALL contributors (no team filtering)
# -A now defaults to showing both raw and normalized stats
python gitinspector.py --config-repos -A --quarter Q2-2025 -F html -f "**" > analysis.html

# Analyze current directory, but filter to TEAM MEMBERS ONLY
# -A now defaults to showing both raw and normalized stats
python gitinspector.py --team -A --quarter Q2-2025 -F html -f "**" > analysis.html

# Use BOTH repositories and team filtering from config file
# -A now defaults to showing both raw and normalized stats
python gitinspector.py --team --config-repos -A --quarter Q2-2025 -F html -f "**" > analysis.html

# Override config repositories with command line (still apply team filtering)
python gitinspector.py --team --config-repos -A --quarter Q2-2025 -F html -f "**" ../different-repo > analysis.html
```

**Benefits:**
- **🎯 Precise Control**: Choose exactly what you want - repositories, team filtering, or both
- **🚀 Convenience**: No need to type repository paths or team members repeatedly
- **⚡ Flexible**: Mix and match config options with command line overrides
- **👥 Team Consistency**: Share the same configuration across team members
- **🔧 Maintenance**: Update team and repository lists in one place

### Comprehensive Examples

#### Example 1: Full Team Analysis Report
```bash
python gitinspector.py \
  -F html \
  --since 2025-07-01 \
  --team-config team_config.json \
  -r -m -T -w \
  -f "**" \
  ../my-repository-parent-directory/my-repository/ > analysis_report.html
```

**What this command does:**
- `--since 2025-07-01` - Only analyze commits from July 1st, 2025 onwards
- `--team-config team_config.json` - Filter results to team members listed in JSON file
- `-r` - Show responsibility analysis (who owns which files)
- `-m` - Include code metrics and violation reports
- `-T` - Generate timeline analysis
- `-w` - Show results in weeks instead of months
- `-F html` - Output in HTML format
- `-f "**"` - Include all file types in analysis
- `../my-repository/` - Path to the repository to analyze
- `> analysis_report.html` - Save output to HTML file

#### Example 2: Quarterly Activity Analysis
```bash
# Analyze Q2 2025 activity across repositories from config file
python gitinspector.py \
  --quarter Q2-2025 \
  -A \
  --activity-chart=line \
  --team --config-repos \
  -F html \
  -f "**" > q2_activity.html
```

**What this command does:**
- `--quarter Q2-2025` - Analyze April 1 - June 30, 2025 (automatically sets dates)
- `-A` - Enable activity statistics (now defaults to showing both raw and normalized stats)
- `--activity-chart=line` - Use line graphs instead of bar charts
- `--team` - Filter to team members from `team_config.json`
- `--config-repos` - Use repository paths from `team_config.json`
- `-F html` - HTML output format
- `-f "**"` - Include all file types

#### Example 3: Performance-Optimized Activity Analysis
```bash
# Fast activity analysis (skips expensive operations)
python gitinspector.py \
  -A --activity-normalize \
  --since 2024-01-01 \
  -F html \
  repo1 repo2 repo3 > activity_report.html
```

**What this command does:**
- `-A` - Activity mode only (automatically skips blame analysis for speed)
- `--activity-normalize` - Show per-contributor productivity metrics
- `--since 2024-01-01` - Analyze from January 1st, 2024 onwards
- `-F html` - HTML output with interactive charts
- Multiple repositories for comparison

#### Example 4: Repositories Only (No Team Filtering)
```bash
# Use repositories from config file but analyze ALL contributors
python gitinspector.py \
  --config-repos \
  --quarter Q2-2025 \
  -A \
  -F html \
  -f "**" > q2_all_contributors_analysis.html
```

**What this command does:**
- `--config-repos` - Read repository paths from `team_config.json`
- `--quarter Q2-2025` - Analyze Q2 2025 (April 1 - June 30)
- `-A` - Show both raw and normalized activity statistics (now the default)
- `-F html` - HTML output format
- `-f "**"` - Include all file types
- **No `--team` flag** - Include ALL contributors, not just team members

#### Example 5: Team Filtering Only
```bash
# Filter to team members but analyze current directory
python gitinspector.py \
  --team \
  --quarter Q2-2025 \
  -A --activity-normalize \
  -F html \
  -f "**" > q2_team_only_analysis.html
```

**What this command does:**
- `--team` - Apply team filtering from `team_config.json`
- `--quarter Q2-2025` - Analyze Q2 2025 (April 1 - June 30)
- `-A --activity-normalize` - Show normalized activity statistics
- `-F html` - HTML output format
- `-f "**"` - Include all file types
- **No `--config-repos` flag** - Analyze current directory, not config repositories

### Enhanced HTML Output

The HTML output format has been significantly enhanced with modern features:

**Interactive Charts:**
- **Activity Charts**: Line graphs (default) or bar charts for repository activity
- **Chart Type Selection**: Choose between line and bar charts with `--activity-chart`
- **Collapsible Sections**: All report sections can be collapsed/expanded for better navigation
- **Responsive Design**: Modern, mobile-friendly interface

**Chart Features:**
- **Line Charts**: Default option showing trends over time with one line per repository
- **Bar Charts**: Alternative visualization showing period-by-period comparisons
- **Interactive Legends**: Click to show/hide specific repositories
- **Hover Information**: Detailed tooltips on chart elements

**Navigation:**
- **Collapsible Headers**: Click any section header to expand/collapse content
- **Chart Collapsibles**: Individual charts can be collapsed independently
- **Default State**: All sections start collapsed for cleaner initial view

### Output Formats
- **HTML**: Rich, interactive reports with charts and collapsible sections
- **Plain Text**: Simple console output with `-f text`
- **JSON**: Machine-readable format with `-f json`
- **XML**: Structured data format with `-f xml`

### Key Features

**Core Analysis:**
- **Multi-Repository Support**: Analyze multiple repositories simultaneously with aggregated statistics
- **Author Statistics**: Shows cumulative work by each author in the history
- **File Type Filtering**: Filters results by extension (default: java,c,cc,cpp,h,hh,hpp,py,glsl,rb,js,sql,tsx,ts,jsx,css,html)
  **Note**: The default extensions now include modern web technologies like TypeScript (ts, tsx), React (jsx), and CSS/HTML
- **Timeline Analysis**: Can display a statistical timeline analysis with `-T`
- **File Type Discovery**: Scans for all filetypes (by extension) found in the repository
- **Metrics Analysis**: Can report violations of different code metrics with `-m`

**Performance & Optimization:**
- **Multi-threaded**: Uses multiple instances of git to speed up analysis when possible
- **Smart Analysis**: Automatically skips expensive operations when only activity data is needed
- **Progress Tracking**: Real-time progress indicators for long-running analyses
- **Memory Efficient**: Optimized for large repositories and multiple repository analysis

**Advanced Features:**
- **Team Filtering**: Filter results to specific team members with `--team`
- **Repository Management**: Store repository paths in config files with `--config-repos`
- **Flexible Configuration**: Use standardized `team_config.json` for team and repository definitions
- **Date Ranges**: Analyze specific time periods with `--since`/`--until` or `--quarter`
- **Exclusion Patterns**: Exclude specific files, authors, or commits with `-x`
- **Localization**: Support for multiple languages with `-L`

### Example outputs
Below are some example outputs for a number of famous open source projects. All the statistics were generated using the *"-HTlrm"* flags.

| Project name | | | | |
|---|---|---|---|---|
| Django | [HTML](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/django_output.html) | [HTML Embedded](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/django_output.emb.html) | [Plain Text](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/django_output.txt) | [XML](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/django_output.xml) |
| JQuery | [HTML](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/jquery_output.html) | [HTML Embedded](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/jquery_output.emb.html) | [Plain Text](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/jquery_output.txt) | [XML](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/jquery_output.xml) |
| Pango | [HTML](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/pango_output.html) | [HTML Embedded](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/pango_output.emb.html) | [Plain Text](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/pango_output.txt) | [XML](http://githubproxy.ejwa.se/wiki/ejwa/gitinspector/examples/pango_output.xml) |

### The Team
  * Adam Waldenberg, Lead maintainer and Swedish translation
  * Agustín Cañas, Spanish translation
  * Bart van Andel, npm package maintainer
  * Bill Wang, Chinese translation
  * Christian Kastner, Debian package maintainer
  * Jiwon Kim, Korean translation
  * Kamila Chyla, Polish translation
  * Luca Motta, Italian translation
  * Philipp Nowak, German translation
  * Sergei Lomakov, Russian translation
  * Yannick Moy, French translation

*We need translations for gitinspector!* If you are a gitinspector user, feel willing to help and have good language skills in any unsupported language we urge you to contact us. We also happily accept code patches. Please refer to [Contributing](https://github.com/ejwa/gitinspector/wiki/Contributing) for more information on how to contribute to the project.

### Installation Methods

#### Option 1: Direct Usage (Recommended)
Since gitinspector now has **zero external dependencies**, you can simply clone and run:
```bash
git clone https://github.com/ejwa/gitinspector.git
cd gitinspector
python gitinspector.py --help
```

#### Option 2: Package Managers
The Debian packages offered with releases of gitinspector are unofficial and very simple packages generated with [stdeb](https://github.com/astraw/stdeb). Christian Kastner is maintaining the official Debian packages. You can check the current status on the [Debian Package Tracker](https://tracker.debian.org/pkg/gitinspector).  Consequently, there are official packages for many Debian based distributions installable via *apt-get*.

An [npm](https://npmjs.com) package is provided for convenience as well. To install it globally, execute `npm i -g gitinspector`.

> **Note:** As of the latest version, gitinspector requires **no external Python dependencies** (PyYAML dependency has been removed), making direct usage the simplest installation method.

### License
gitinspector is licensed under the *GNU GPL v3*. The gitinspector logo is partly based on the git logo; based on the work of Jason Long. The logo is licensed under the *Creative Commons Attribution 3.0 Unported License*.
