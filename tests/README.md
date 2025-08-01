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

### Run All Tests
```bash
cd tests
pytest -v
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

## Test Coverage

The test suite includes **73 test cases** covering:

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