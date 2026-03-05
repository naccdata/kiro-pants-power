"""Unit tests for EnhancedErrorFormatter."""

import pytest

from src.formatters.enhanced_error_formatter import EnhancedErrorFormatter
from src.models import (
    AssertionFailure,
    CommandResult,
    CoverageData,
    FileCoverage,
    ParsedOutput,
    PytestFailure,
    PytestResults,
    SandboxInfo,
    TestFailure,
    TestResults,
    TypeCheckError,
    TypeCheckResults,
)


@pytest.fixture
def formatter():
    """Create a formatter with default settings."""
    return EnhancedErrorFormatter(max_errors_per_category=10)


@pytest.fixture
def sample_test_results():
    """Create sample test results with failures."""
    return TestResults(
        total_count=10,
        pass_count=7,
        fail_count=2,
        skip_count=1,
        failures=[
            TestFailure(
                test_name="test_addition",
                test_file="tests/test_math.py",
                test_class="TestMath",
                failure_type="AssertionError",
                failure_message="Expected 5 but got 4",
                stack_trace="  File tests/test_math.py, line 10\n    assert result == 5",
            ),
            TestFailure(
                test_name="test_division",
                test_file="tests/test_math.py",
                test_class="TestMath",
                failure_type="ZeroDivisionError",
                failure_message="division by zero",
                stack_trace=None,
            ),
        ],
        execution_time=1.5,
    )


@pytest.fixture
def sample_type_results():
    """Create sample type checking results."""
    return TypeCheckResults(
        error_count=3,
        errors_by_file={
            "src/main.py": [
                TypeCheckError(
                    file_path="src/main.py",
                    line_number=10,
                    column=5,
                    error_code="arg-type",
                    error_message="Argument 1 has incompatible type 'str'; expected 'int'",
                ),
                TypeCheckError(
                    file_path="src/main.py",
                    line_number=20,
                    column=None,
                    error_code="return-value",
                    error_message="Expected return type 'str' but got 'None'",
                ),
            ],
            "src/utils.py": [
                TypeCheckError(
                    file_path="src/utils.py",
                    line_number=5,
                    column=10,
                    error_code="name-defined",
                    error_message="Name 'undefined_var' is not defined",
                ),
            ],
        },
        report_paths=["/tmp/mypy-report/index.html"],
    )


@pytest.fixture
def sample_coverage():
    """Create sample coverage data."""
    return CoverageData(
        total_coverage=75.5,
        file_coverage={
            "src/main.py": FileCoverage(
                file_path="src/main.py",
                coverage_percent=80.0,
                covered_lines=40,
                total_lines=50,
                uncovered_ranges=[(10, 15), (30, 30)],
            ),
            "src/utils.py": FileCoverage(
                file_path="src/utils.py",
                coverage_percent=60.0,
                covered_lines=30,
                total_lines=50,
                uncovered_ranges=[(5, 10), (20, 25), (40, 45)],
            ),
        },
        report_path="/tmp/coverage.json",
    )


@pytest.fixture
def sample_pytest_results():
    """Create sample pytest results."""
    return PytestResults(
        failed_tests=[
            PytestFailure(
                test_name="test_example",
                test_file="tests/test_example.py",
                failure_type="AssertionError",
                failure_message="assert 1 == 2",
                assertion_details=AssertionFailure(
                    expected_value="2",
                    actual_value="1",
                    comparison_operator="==",
                ),
                stack_trace_excerpt="tests/test_example.py:10: AssertionError",
            ),
        ],
    )


@pytest.fixture
def sample_sandboxes():
    """Create sample sandbox information."""
    return [
        SandboxInfo(
            sandbox_path="/tmp/pants-sandbox-abc123",
            process_description="pytest tests/test_math.py",
            timestamp="2024-01-01T12:00:00",
        ),
    ]


@pytest.fixture
def sample_command_result():
    """Create sample command result."""
    return CommandResult(
        exit_code=1,
        stdout="Running tests...\nFailed: 2 tests",
        stderr="Error: Tests failed",
        command="pants test ::",
        success=False,
    )


class TestFormatTestFailures:
    """Tests for format_test_failures method."""

    def test_format_with_failures(self, formatter, sample_test_results):
        """Test formatting test results with failures."""
        result = formatter.format_test_failures(sample_test_results)

        assert "Test Results: 2 failed, 7 passed, 1 skipped out of 10 total" in result
        assert "test_addition" in result
        assert "test_division" in result
        assert "tests/test_math.py" in result
        assert "AssertionError" in result
        assert "Expected 5 but got 4" in result

    def test_format_all_passed(self, formatter):
        """Test formatting when all tests pass."""
        results = TestResults(
            total_count=5,
            pass_count=5,
            fail_count=0,
            skip_count=0,
            failures=[],
            execution_time=1.0,
        )
        result = formatter.format_test_failures(results)

        assert "All 5 tests passed" in result

    def test_format_limits_failures(self):
        """Test that formatter limits number of failures shown."""
        formatter = EnhancedErrorFormatter(max_errors_per_category=2)
        failures = [
            TestFailure(
                test_name=f"test_{i}",
                test_file="test.py",
                test_class=None,
                failure_type="AssertionError",
                failure_message=f"Failure {i}",
                stack_trace=None,
            )
            for i in range(5)
        ]
        results = TestResults(
            total_count=5,
            pass_count=0,
            fail_count=5,
            skip_count=0,
            failures=failures,
            execution_time=1.0,
        )

        result = formatter.format_test_failures(results)

        assert "test_0" in result
        assert "test_1" in result
        assert "test_2" not in result
        assert "and 3 more failures" in result


class TestFormatTypeErrors:
    """Tests for format_type_errors method."""

    def test_format_with_errors(self, formatter, sample_type_results):
        """Test formatting type checking results with errors."""
        result = formatter.format_type_errors(sample_type_results)

        assert "Type Checking: 3 errors found" in result
        assert "src/main.py: 2 errors" in result
        assert "src/utils.py: 1 errors" in result
        assert "arg-type" in result
        assert "Argument 1 has incompatible type" in result

    def test_format_no_errors(self, formatter):
        """Test formatting when no type errors exist."""
        results = TypeCheckResults(
            error_count=0,
            errors_by_file={},
            report_paths=[],
        )
        result = formatter.format_type_errors(results)

        assert "Type checking passed with no errors" in result

    def test_format_includes_report_paths(self, formatter, sample_type_results):
        """Test that report paths are included in output."""
        result = formatter.format_type_errors(sample_type_results)

        assert "MyPy report files:" in result
        assert "/tmp/mypy-report/index.html" in result


class TestFormatCoverageSummary:
    """Tests for format_coverage_summary method."""

    def test_format_coverage(self, formatter, sample_coverage):
        """Test formatting coverage data."""
        result = formatter.format_coverage_summary(sample_coverage)

        assert "Coverage: 75.5%" in result
        assert "/tmp/coverage.json" in result
        assert "src/main.py: 80.0%" in result
        assert "src/utils.py: 60.0%" in result

    def test_format_shows_uncovered_ranges(self, formatter, sample_coverage):
        """Test that uncovered line ranges are shown."""
        result = formatter.format_coverage_summary(sample_coverage)

        assert "Uncovered lines:" in result
        assert "10-15" in result or "5-10" in result


class TestFormatPytestFailures:
    """Tests for format_pytest_failures method."""

    def test_format_with_failures(self, formatter, sample_pytest_results):
        """Test formatting pytest failures."""
        result = formatter.format_pytest_failures(sample_pytest_results)

        assert "Pytest Failures: 1 tests failed" in result
        assert "test_example" in result
        assert "tests/test_example.py" in result
        assert "Expected: 2" in result
        assert "Actual: 1" in result
        assert "Operator: ==" in result

    def test_format_no_failures(self, formatter):
        """Test formatting when no pytest failures exist."""
        results = PytestResults(failed_tests=[])
        result = formatter.format_pytest_failures(results)

        assert "All pytest tests passed" in result


class TestFormatSandboxes:
    """Tests for format_sandboxes method."""

    def test_format_sandboxes(self, formatter, sample_sandboxes):
        """Test formatting sandbox information."""
        result = formatter.format_sandboxes(sample_sandboxes)

        assert "Preserved Sandboxes:" in result
        assert "/tmp/pants-sandbox-abc123" in result
        assert "pytest tests/test_math.py" in result
        assert "2024-01-01T12:00:00" in result

    def test_format_empty_sandboxes(self, formatter):
        """Test formatting when no sandboxes exist."""
        result = formatter.format_sandboxes([])

        assert result == ""


class TestFormatErrorSummary:
    """Tests for format_error_summary method."""

    def test_format_with_test_failures(
        self, formatter, sample_command_result, sample_test_results
    ):
        """Test formatting error summary with test failures."""
        result = formatter.format_error_summary(
            sample_command_result,
            test_results=sample_test_results,
        )

        assert "Error Type: Test Failure" in result
        assert "Command: pants test ::" in result
        assert "Exit Code: 1" in result
        assert "test_addition" in result

    def test_format_with_type_errors(
        self, formatter, sample_command_result, sample_type_results
    ):
        """Test formatting error summary with type errors."""
        result = formatter.format_error_summary(
            sample_command_result,
            type_results=sample_type_results,
        )

        assert "Error Type: Type Error" in result
        assert "Type Checking: 3 errors found" in result

    def test_format_with_sandboxes(
        self, formatter, sample_command_result, sample_sandboxes
    ):
        """Test that sandbox paths are included in error summary."""
        result = formatter.format_error_summary(
            sample_command_result,
            sandboxes=sample_sandboxes,
        )

        assert "Preserved Sandboxes:" in result
        assert "/tmp/pants-sandbox-abc123" in result

    def test_format_execution_error(self, formatter, sample_command_result):
        """Test formatting execution error without structured data."""
        result = formatter.format_error_summary(sample_command_result)

        assert "Error Type: Execution Error" in result
        assert "Raw Output (last 20 lines):" in result

    def test_format_success(self, formatter):
        """Test formatting successful command result."""
        success_result = CommandResult(
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            command="pants test ::",
            success=True,
        )
        result = formatter.format_error_summary(success_result)

        assert "Error Type: Success" in result


class TestFormatParsedOutput:
    """Tests for format_parsed_output method."""

    def test_format_complete_parsed_output(
        self,
        formatter,
        sample_test_results,
        sample_type_results,
        sample_coverage,
        sample_sandboxes,
    ):
        """Test formatting complete parsed output with all data types."""
        parsed_output = ParsedOutput(
            test_results=sample_test_results,
            type_check_results=sample_type_results,
            coverage_data=sample_coverage,
            sandboxes=sample_sandboxes,
            parsing_errors=[],
        )

        result = formatter.format_parsed_output(parsed_output)

        assert "Test Results:" in result
        assert "Type Checking:" in result
        assert "Coverage:" in result
        assert "Preserved Sandboxes:" in result

    def test_format_with_parsing_errors(self, formatter):
        """Test formatting parsed output with parsing errors."""
        parsed_output = ParsedOutput(
            parsing_errors=["Failed to parse JUnit XML", "Coverage report not found"],
        )

        result = formatter.format_parsed_output(parsed_output)

        assert "Parsing Errors:" in result
        assert "Failed to parse JUnit XML" in result
        assert "Coverage report not found" in result


class TestDetermineErrorType:
    """Tests for _determine_error_type method."""

    def test_determine_test_failure(self, formatter, sample_command_result, sample_test_results):
        """Test determining test failure error type."""
        error_type = formatter._determine_error_type(
            sample_command_result,
            sample_test_results,
            None,
            None,
        )

        assert error_type == "Test Failure"

    def test_determine_type_error(self, formatter, sample_command_result, sample_type_results):
        """Test determining type error error type."""
        error_type = formatter._determine_error_type(
            sample_command_result,
            None,
            sample_type_results,
            None,
        )

        assert error_type == "Type Error"

    def test_determine_execution_error(self, formatter, sample_command_result):
        """Test determining execution error type."""
        error_type = formatter._determine_error_type(
            sample_command_result,
            None,
            None,
            None,
        )

        assert error_type == "Execution Error"

    def test_determine_success(self, formatter):
        """Test determining success type."""
        success_result = CommandResult(
            exit_code=0,
            stdout="Success",
            stderr="",
            command="pants test ::",
            success=True,
        )
        error_type = formatter._determine_error_type(
            success_result,
            None,
            None,
            None,
        )

        assert error_type == "Success"
