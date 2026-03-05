# Test Fixtures for Enhanced Pants Output Capture

This directory contains realistic test fixtures used by integration tests for the enhanced pants output capture system.

## Directory Structure

### sample_junit_reports/
JUnit XML test report files representing various test execution scenarios:

- `single_test_pass.xml` - Single passing test
- `single_test_fail.xml` - Single failing test with assertion error
- `multiple_suites.xml` - Multiple test suites with mixed results
- `multiple_tests_mixed.xml` - Multiple tests with passes, failures, and skips
- `empty_suite.xml` - Empty test suite (no tests executed)
- `malformed.xml` - Malformed XML for error handling tests

### sample_coverage_reports/
Coverage reports in both JSON and XML (Cobertura) formats:

- `coverage.json` - Standard coverage report with multiple files (60% overall)
- `coverage_100_percent.json` - Perfect coverage (100%)
- `coverage_empty.json` - Empty coverage report (no files)
- `coverage_cobertura.xml` - XML format coverage report (Cobertura)
- `coverage_malformed.json` - Malformed JSON for error handling tests

### sample_mypy_output/
MyPy type checking output with various error scenarios:

- `no_errors.txt` - Successful type check with no errors
- `single_error.txt` - Single type error
- `multiple_errors.txt` - Multiple errors across multiple files
- `with_columns.txt` - Errors with column numbers
- `with_notes.txt` - Errors with additional notes
- `with_report_path.txt` - Output including report file paths

### sample_pants_logs/
Pants log output with sandbox preservation messages:

- `no_sandbox.txt` - Log without sandbox preservation
- `sandbox_on_failure.txt` - Sandbox preserved only for failed tests
- `sandbox_always.txt` - Sandbox preserved for all tests
- `multiple_sandboxes.txt` - Multiple preserved sandboxes
- `sandbox_with_timestamp.txt` - Sandbox messages with ISO timestamps

### sample_configs/
Pants configuration files (pants.toml) with various scenarios:

- `empty.toml` - Empty configuration file
- `minimal.toml` - Minimal valid configuration
- `valid_basic.toml` - Basic valid configuration with common settings
- `valid_complex.toml` - Complex configuration with many options
- `valid_with_comments.toml` - Configuration with comments
- `invalid_syntax.toml` - Invalid TOML syntax for error handling
- `invalid_type.toml` - Valid TOML but incorrect types for Pants options

### sample_pytest_output/
Pytest console output with various failure types:

- `all_passed.txt` - All tests passed
- `simple_assertion_failure.txt` - Simple assertion failure
- `string_comparison.txt` - String comparison assertion failure
- `list_comparison.txt` - List comparison assertion failure
- `complex_assertion.txt` - Complex dictionary comparison failure
- `exception_failure.txt` - Test failure due to exception
- `multiple_failures.txt` - Multiple test failures
- `mixed_results.txt` - Mixed results (passes, failures, skips)

## Usage in Tests

These fixtures are used by integration tests to verify parsing and formatting functionality:

```python
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

def test_junit_parser():
    report_path = FIXTURES_DIR / "sample_junit_reports" / "single_test_fail.xml"
    parser = JUnitXMLParser()
    results = parser.parse_single_report(str(report_path))
    assert results.fail_count == 1
```

## Maintenance

When adding new fixtures:

1. Use realistic examples based on actual tool output
2. Cover common cases, edge cases, and error scenarios
3. Include both valid and invalid examples for error handling tests
4. Document the fixture purpose in this README
5. Keep fixtures minimal but representative

## Coverage

These fixtures support testing of:

- JUnit XML parsing (Requirements 1.1-1.6)
- Coverage report parsing (Requirements 2.1-2.6)
- MyPy error extraction (Requirements 3.1-3.6)
- Sandbox path extraction (Requirements 4.1-4.5)
- Pytest output parsing (Requirements 10.1-10.6)
- Configuration parsing and formatting (Requirements 11.1-11.6)
- Error handling and graceful degradation (Requirements 7.1-7.6)
