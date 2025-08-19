# GitInspector Test Suite

This directory contains comprehensive tests for the GitInspector project, focusing on the test vs main code breakdown feature.

## Test Framework

The tests use [pytest](https://pytest.org/) for modern Python testing with fixtures and parametrized tests.

## Test Files

### `test_blame_categorization.py`
Tests the core functionality for identifying and categorizing test files:
- **File Detection**: Tests the `is_test_file()` function with various file patterns
- **BlameEntry**: Tests the data structure that tracks main vs test code rows
- **Percentage Calculations**: Tests the logic for calculating test coverage percentages

### `test_blame_integration.py`
Integration tests for the blame processing workflow:
- **Categorization Workflow**: End-to-end testing of file categorization
- **Aggregation Logic**: Tests summing blame data across multiple files per author
- **Multi-Author Support**: Tests aggregation with multiple developers

### `test_blame_output.py`
Tests all output formats with the new test/main breakdown:
- **Text Output**: Console output with Main, Test, and Test % columns
- **JSON Output**: JSON format with `main_rows`, `test_rows`, and `test_percentage` fields
- **XML Output**: XML format with corresponding elements
- **HTML Output**: HTML table with new column headers

## Running Tests

### Prerequisites
```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Install pytest if not already installed
pip install pytest
```

### Quick Test Setup
```bash
# Create test repositories (one-time setup)
cd tests
python create_simple_test_repos.py

# Run comprehensive test suite
python test_runner.py
```

### Run All Tests
```bash
cd tests
pytest -v
```

### Run Activity Feature Tests
```bash
# Run unit tests for activity feature only
python -m unittest tests.test_activity -v

# Run integration tests with real repositories
python test_runner.py
```

### Run Specific Test Files
```bash
# Test file categorization only
pytest test_blame_categorization.py -v

# Test integration logic only  
pytest test_blame_integration.py -v

# Test output formats only
pytest test_blame_output.py -v
```

### Run Specific Test Categories
```bash
# Test only file detection logic
pytest test_blame_categorization.py::TestFileCategorizationTest -v

# Test only percentage calculations
pytest test_blame_categorization.py::TestPercentageCalculation -v

# Test only output formatting
pytest test_blame_output.py::TestBlameOutput -v
```

## Test Infrastructure

### Test Repositories

The test suite includes **5 permanent test repositories** designed for comprehensive testing:

🏢 **`team_growth_repo`** - Simulates team growth over time
- Month 1: 1 developer (Founder Dev)
- Month 2: 2 developers (+ Developer 2) 
- Month 3: 4 developers (+ Backend Dev, Frontend Dev)
- Perfect for testing normalization features

👤 **`solo_productive_repo`** - High-productivity solo developer
- Consistent weekly commits over 3 months
- 5 commits with progressive feature development
- Tests individual productivity patterns

📊 **`seasonal_activity_repo`** - Seasonal development patterns
- Q1: High activity (4 commits)
- Q2: Low activity (sparse commits)
- Q4: Release push (2 commits)
- Tests time-based analysis

🎨 **`mixed_project_repo`** - Multiple file types and test files
- Python, JavaScript, HTML, CSS files
- Both main code and test files
- Tests file categorization and blame analysis

🏛️ **`legacy_maintenance_repo`** - Legacy system maintenance
- Initial commit from 2020
- Sparse maintenance commits over years
- Tests long-term repository analysis

### Test Helper Classes

**`GitTestRepo`** - Context manager for temporary repositories
**`ActivityTestScenarios`** - Pre-defined test scenarios
**`GitInspectorTestCase`** - Base test case with common utilities

## Test Coverage

The test suite includes **100+ test cases** covering:

✅ **Test File Detection** (51 tests)
- Directory-based detection (`test/`, `tests/`, `__tests__/`, etc.)
- Filename pattern detection (`.test.`, `.spec.`, `-test`, etc.)
- File extension combinations (`.test.js`, `.spec.ts`, etc.)
- Case-insensitive detection
- Edge cases and false positives

✅ **Data Structure Testing** (4 tests)
- BlameEntry initialization
- Main vs test row tracking
- Row count consistency

✅ **Calculation Logic** (6 tests)
- Test percentage calculations
- Zero division protection
- Edge case handling

✅ **Integration Testing** (6 tests)
- End-to-end blame categorization workflow
- Multi-file aggregation per author
- Multiple author scenarios

✅ **Output Format Testing** (6 tests)
- All output formats (text, JSON, XML, HTML)
- New column/field integration
- Zero division handling in output

✅ **Activity Feature Testing** (25+ tests)
- ActivityData initialization and data collection
- Contributor tracking per repository per period
- Normalization calculations (per-contributor metrics)
- Weekly vs monthly time period handling
- All output formats (text, HTML) with normalization
- Multi-repository activity analysis
- Seasonal activity pattern detection
- Integration testing with real git repositories

✅ **Test Infrastructure** (5 repositories)
- Permanent test repositories for consistent testing
- Repository creation and validation utilities
- Performance testing with multiple repositories
- Integration testing scenarios

## Bug Fixes Included

The test development also identified and fixed:

1. **Zero Division Errors**: Fixed division by zero when calculating age (skew/rows) and comment percentage in blame output
2. **Gravatar Mocking**: Proper mocking of external gravatar URL generation in tests

## Test File Detection Logic

The test detection uses multiple strategies:

1. **Directory Detection**: Files in directories named `test/`, `tests/`, `__tests__/`, `spec/`, `specs/`, `testing/`
2. **Pattern Detection**: Files with patterns like `.test.`, `.spec.`, `-test`, `-spec`, `_test`, `_spec`
3. **Extension Matching**: Combines test patterns with common code file extensions (`.js`, `.ts`, `.py`, etc.)
4. **Case Insensitive**: All detection is case-insensitive for robustness

This approach ensures comprehensive detection of test files across different project structures and naming conventions.

## Activity Feature Testing

### Unit Tests (`test_activity.py`)

**Core Functionality Tests:**
- `TestActivityData` - Data collection and initialization
- `TestActivityNormalization` - Contributor counting and normalization
- `TestActivityOutput` - All output formats (text, HTML)
- `TestActivityIntegration` - End-to-end workflows

### Integration Tests (`test_runner.py`)

**Real Repository Tests:**
- Single repository analysis
- Multi-repository analysis  
- Normalized vs raw statistics comparison
- Weekly vs monthly granularity
- HTML output generation
- Performance testing with all 5 repositories

### Activity Testing Examples

```bash
# Test basic activity functionality
cd tests
python -m unittest test_activity.TestActivityData.test_single_repository_activity -v

# Test normalization features
python -m unittest test_activity.TestActivityNormalization -v

# Test all output formats
python -m unittest test_activity.TestActivityOutput -v

# Run comprehensive activity test suite
python -m unittest test_activity -v

# Integration tests with real repositories
python test_runner.py
```

### Creating New Activity Tests

When adding new activity features:

1. **Add unit tests** in `test_activity.py`
2. **Use test repositories** from `test_repositories/`
3. **Test both raw and normalized** output
4. **Test all output formats** (text, HTML, JSON, XML)
5. **Add integration scenarios** to `test_runner.py`

Example test pattern:
```python
def test_new_feature(self):
    with GitTestRepo("test_repo") as repo:
        ActivityTestScenarios.create_multi_developer_repo(repo)
        changes_obj = changes.Changes(None, hard=True)
        changes_by_repo = {"test_repo": changes_obj}
        
        activity_data = activity.ActivityData(changes_by_repo, useweeks=False)
        
        # Test your new feature
        result = activity_data.new_feature()
        self.assertEqual(expected_value, result)
```