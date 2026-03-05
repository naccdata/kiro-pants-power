"""Core data models for the Pants DevContainer Power."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandResult:
    """Result of executing a shell command.

    Attributes:
        exit_code: The exit code returned by the command
        stdout: Standard output from the command
        stderr: Standard error from the command
        command: The command that was executed
        success: Whether the command succeeded (exit_code == 0)
    """
    exit_code: int
    stdout: str
    stderr: str
    command: str
    success: bool

    @property
    def output(self) -> str:
        """Combined stdout and stderr output.

        Returns:
            Concatenated stdout and stderr, stripped of leading/trailing whitespace
        """
        return f"{self.stdout}\n{self.stderr}".strip()


@dataclass
class WorkflowResult:
    """Result of executing a multi-step workflow.

    Attributes:
        steps_completed: List of step names that were completed
        failed_step: Name of the step that failed, or None if all succeeded
        results: List of CommandResult objects for each step executed
        overall_success: Whether the entire workflow succeeded
    """
    steps_completed: list[str]
    failed_step: str | None
    results: list[CommandResult]
    overall_success: bool

    @property
    def summary(self) -> str:
        """Human-readable summary of workflow execution.

        Returns:
            A formatted string describing the workflow outcome
        """
        if self.overall_success:
            steps_str = ", ".join(self.steps_completed)
            return f"Workflow completed successfully. Steps executed: {steps_str}"
        else:
            completed_str = ", ".join(self.steps_completed)
            return (
                f"Workflow failed at step: {self.failed_step}\n"
                f"Steps completed before failure: {completed_str}"
            )


# Error exception classes

class PowerError(Exception):
    """Base exception for all power-related errors."""
    pass


class ContainerError(PowerError):
    """Exception raised when container operations fail.

    This includes failures in starting, stopping, rebuilding, or
    executing commands in the devcontainer.
    """
    pass


class CommandExecutionError(PowerError):
    """Exception raised when command execution fails.

    This includes failures in executing Pants commands or other
    shell commands within the container.
    """
    pass


class ValidationError(PowerError):
    """Exception raised when parameter validation fails.

    This includes invalid target specifications, workflow names,
    or other input parameters.
    """
    pass


# Enhanced output capture data models


@dataclass
class TestFailure:
    """Details of a single test failure.

    Attributes:
        test_name: Name of the failed test
        test_file: File path where the test is located
        test_class: Optional class name containing the test
        failure_type: Type of failure (e.g., AssertionError, Exception)
        failure_message: Detailed failure message
        stack_trace: Optional stack trace of the failure
    """
    test_name: str
    test_file: str
    test_class: str | None
    failure_type: str
    failure_message: str
    stack_trace: str | None


@dataclass
class TestResults:
    """Structured test execution results from JUnit XML.

    Attributes:
        total_count: Total number of tests executed
        pass_count: Number of tests that passed
        fail_count: Number of tests that failed
        skip_count: Number of tests that were skipped
        failures: List of detailed failure information
        execution_time: Total execution time in seconds
    """
    total_count: int
    pass_count: int
    fail_count: int
    skip_count: int
    failures: list[TestFailure]
    execution_time: float


@dataclass
class AssertionFailure:
    """Assertion failure details.

    Attributes:
        expected_value: The expected value in the assertion
        actual_value: The actual value that was compared
        comparison_operator: The comparison operator used (e.g., ==, !=, <)
    """
    expected_value: str
    actual_value: str
    comparison_operator: str


@dataclass
class PytestFailure:
    """Detailed pytest failure information.

    Attributes:
        test_name: Name of the failed test
        test_file: File path where the test is located
        failure_type: Type of failure (e.g., AssertionError, Exception)
        failure_message: Detailed failure message
        assertion_details: Optional assertion failure details
        stack_trace_excerpt: Optional relevant stack trace excerpt
    """
    test_name: str
    test_file: str
    failure_type: str
    failure_message: str
    assertion_details: AssertionFailure | None
    stack_trace_excerpt: str | None


@dataclass
class PytestResults:
    """Pytest-specific failure details.

    Attributes:
        failed_tests: List of detailed pytest failure information
    """
    failed_tests: list[PytestFailure]


@dataclass
class FileCoverage:
    """Per-file coverage information.

    Attributes:
        file_path: Path to the source file
        coverage_percent: Coverage percentage for this file
        covered_lines: Number of lines covered by tests
        total_lines: Total number of executable lines
        uncovered_ranges: List of line ranges not covered (start, end)
    """
    file_path: str
    coverage_percent: float
    covered_lines: int
    total_lines: int
    uncovered_ranges: list[tuple[int, int]]


@dataclass
class CoverageData:
    """Code coverage metrics.

    Attributes:
        total_coverage: Overall coverage percentage
        file_coverage: Per-file coverage information keyed by file path
        report_path: Path to the coverage report file
    """
    total_coverage: float
    file_coverage: dict[str, FileCoverage]
    report_path: str


@dataclass
class TypeCheckError:
    """Single type checking error.

    Attributes:
        file_path: Path to the file with the type error
        line_number: Line number where the error occurs
        column: Optional column number where the error occurs
        error_code: MyPy error code (e.g., 'arg-type', 'return-value')
        error_message: Detailed error message
    """
    file_path: str
    line_number: int
    column: int | None
    error_code: str
    error_message: str


@dataclass
class TypeCheckResults:
    """MyPy type checking results.

    Attributes:
        error_count: Total number of type errors
        errors_by_file: Type errors grouped by file path
        report_paths: Paths to generated MyPy report files
    """
    error_count: int
    errors_by_file: dict[str, list[TypeCheckError]]
    report_paths: list[str]


@dataclass
class SandboxInfo:
    """Preserved sandbox information.

    Attributes:
        sandbox_path: Full path to the preserved sandbox directory
        process_description: Description of the process that ran in the sandbox
        timestamp: Optional timestamp when the sandbox was preserved
    """
    sandbox_path: str
    process_description: str
    timestamp: str | None


@dataclass
class Configuration:
    """Pants configuration file structure.

    Attributes:
        sections: Configuration sections with their options and values
        comments: Comments associated with sections/options
        source_file: Path to the source configuration file
    """
    sections: dict[str, dict[str, Any]]
    comments: dict[str, str]
    source_file: str


# Note: ValidationError class already exists above as an exception class
# For configuration validation errors, we'll create a new class name
@dataclass
class ConfigValidationError:
    """Configuration validation error.

    Attributes:
        section: Configuration section where the error occurred
        option: Configuration option that has an error
        message: Detailed error message
        line_number: Optional line number in the config file
    """
    section: str
    option: str
    message: str
    line_number: int | None


@dataclass
class ParsedOutput:
    """Aggregated parsing results from all parsers.

    Attributes:
        test_results: Structured test results from JUnit XML
        coverage_data: Coverage metrics from coverage reports
        type_check_results: Type checking errors from MyPy
        pytest_results: Pytest-specific failure details
        sandboxes: List of preserved sandbox information
        parsing_errors: List of errors encountered during parsing
    """
    test_results: TestResults | None = None
    coverage_data: CoverageData | None = None
    type_check_results: TypeCheckResults | None = None
    pytest_results: PytestResults | None = None
    sandboxes: list[SandboxInfo] = field(default_factory=list)
    parsing_errors: list[str] = field(default_factory=list)


@dataclass
class EnhancedCommandResult(CommandResult):
    """Command result with parsed structured data.

    Attributes:
        parsed_output: Aggregated parsing results from all parsers
        formatted_summary: Human-readable summary of the results
        execution_time: Command execution time in seconds
    """
    parsed_output: ParsedOutput
    formatted_summary: str
    execution_time: float


@dataclass
class WorkflowProgress:
    """Real-time workflow progress information.

    Attributes:
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps in the workflow
        step_name: Name of the current step
        status: Current status (starting, running, completed, failed)
        elapsed_time: Optional elapsed time for the current step
    """
    current_step: int
    total_steps: int
    step_name: str
    status: str  # "starting", "running", "completed", "failed"
    elapsed_time: float | None


@dataclass
class EnhancedWorkflowResult(WorkflowResult):
    """Workflow result with enhanced diagnostics.

    Attributes:
        step_timings: Execution time for each step keyed by step name
        enhanced_results: List of enhanced command results for each step
        workflow_summary: Human-readable workflow summary with diagnostics
    """
    step_timings: dict[str, float]
    enhanced_results: list[EnhancedCommandResult]
    workflow_summary: str
