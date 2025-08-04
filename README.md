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

# Get help with all available options
python gitinspector.py --help
```

### Team Configuration (Optional)
To filter analysis to specific team members, create a JSON configuration file:

**team_config.json:**
```json
{
  "team": [
    "john.doe@company.com",
    "jane.smith@company.com",
    "alice.johnson",
    "bob.wilson"
  ]
}
```

### Comprehensive Example
Here's a complete example that generates a full analysis report:

```bash
python gitinspector.py \
  --since 2025-07-01 \
  --team-config team_config.json \
  -r -m -T -w \
  -f "**" \
  ../my-repository/ > analysis_report.html
```

**What this command does:**
- `--since 2025-07-01` - Only analyze commits from July 1st, 2025 onwards
- `--team-config team_config.json` - Filter results to team members listed in JSON file
- `-r` - Show responsibility analysis (who owns which files)
- `-m` - Include code metrics and violation reports
- `-T` - Generate timeline analysis
- `-w` - Show results in weeks instead of months
- `-f "**"` - Include all file types in analysis
- `../my-repository/` - Path to the repository to analyze
- `> analysis_report.html` - Save output to HTML file

### Output Formats
- **HTML** (default): Rich, interactive reports with charts
- **Plain Text**: Simple console output with `-f text`
- **JSON**: Machine-readable format with `-f json`
- **XML**: Structured data format with `-f xml`

### Some of the features
  * Shows cumulative work by each author in the history.
  * Filters results by extension (default: java,c,cc,cpp,h,hh,hpp,py,glsl,rb,js,sql).
  * Can display a statistical timeline analysis.
  * Scans for all filetypes (by extension) found in the repository.
  * Multi-threaded; uses multiple instances of git to speed up analysis when possible.
  * Supports HTML, JSON, XML and plain text output (console).
  * Can report violations of different code metrics.

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
