"""Enhanced error formatter for Pants command output.

This formatter creates actionable error summaries from parsed command output,
including test failures, type checking errors, coverage metrics, and sandbox paths.
"""

from src.models import (
    CommandResult,
    CoverageData,
    ParsedOutput,
    PytestResults,
    SandboxInfo,
    TestResults,
    TypeCheckResults,
)


class EnhancedErrorFormatter:
    """Formatter for creating enhanced error diagnostics.

    This formatter takes structured parsing results and creates concise,
    actionable error summaries optimized for agent consumption.
    """

    def __init__(self, max_errors_per_category: int = 10):
        """Initialize the formatter.

        Args:
            max_errors_per_category: Maximum number of errors to show per category
        """
        self.max_errors_per_category = max_errors_per_category

    def format_test_failures(self, results: TestResults) -> str:
        """Format test failure summary.

        Args:
            results: Structured test results from JUnit XML

        Returns:
            Formatted test failure summary
        """
        if not results.failures:
            return f"All {results.total_count} tests passed"

        lines = [
            (
                f"Test Results: {results.fail_count} failed, "
                f"{results.pass_count} passed, "
                f"{results.skip_count} skipped out of {results.total_count} total"
            ),
            "",
            "Failed Tests:",
        ]

        # Limit to max_errors_per_category
        failures_to_show = results.failures[: self.max_errors_per_category]
        for failure in failures_to_show:
            lines.append(f"  - {failure.test_name}")
            lines.append(f"    File: {failure.test_file}")
            if failure.test_class:
                lines.append(f"    Class: {failure.test_class}")
            lines.append(f"    Type: {failure.failure_type}")
            lines.append(f"    Message: {failure.failure_message}")
            if failure.stack_trace:
                # Show first few lines of stack trace
                trace_lines = failure.stack_trace.split("\n")[:3]
                lines.append(f"    Stack trace: {trace_lines[0]}")
                for trace_line in trace_lines[1:]:
                    lines.append(f"                 {trace_line}")
            lines.append("")

        if len(results.failures) > self.max_errors_per_category:
            remaining = len(results.failures) - self.max_errors_per_category
            lines.append(
                f"... and {remaining} more failures "
                f"(showing first {self.max_errors_per_category})"
            )

        return "\n".join(lines)

    def format_type_errors(self, results: TypeCheckResults) -> str:
        """Format type checking error summary.

        Args:
            results: Type checking results from MyPy

        Returns:
            Formatted type error summary
        """
        if results.error_count == 0:
            return "Type checking passed with no errors"

        lines = [
            f"Type Checking: {results.error_count} errors found",
            "",
            "Errors by file:",
        ]

        # Sort files by error count (descending)
        sorted_files = sorted(
            results.errors_by_file.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )

        errors_shown = 0
        for file_path, errors in sorted_files:
            if errors_shown >= self.max_errors_per_category:
                break

            lines.append(f"  {file_path}: {len(errors)} errors")

            # Show first few errors from this file
            errors_to_show = errors[
                : min(3, self.max_errors_per_category - errors_shown)
            ]
            for error in errors_to_show:
                location = f"Line {error.line_number}"
                if error.column:
                    location += f", Column {error.column}"
                lines.append(
                    f"    - {location}: [{error.error_code}] "
                    f"{error.error_message}"
                )
                errors_shown += 1

            if len(errors) > len(errors_to_show):
                remaining_in_file = len(errors) - len(errors_to_show)
                lines.append(
                    f"    ... and {remaining_in_file} more errors in this file"
                )

            lines.append("")

        if errors_shown < results.error_count:
            remaining = results.error_count - errors_shown
            lines.append(f"... and {remaining} more errors in other files")

        if results.report_paths:
            lines.append("")
            lines.append("MyPy report files:")
            for report_path in results.report_paths:
                lines.append(f"  - {report_path}")

        return "\n".join(lines)

    def format_coverage_summary(self, coverage: CoverageData) -> str:
        """Format coverage metrics summary.

        Args:
            coverage: Coverage data from coverage reports

        Returns:
            Formatted coverage summary
        """
        lines = [
            f"Coverage: {coverage.total_coverage:.1f}%",
            f"Report: {coverage.report_path}",
        ]

        if coverage.file_coverage:
            lines.append("")
            lines.append("Per-file coverage:")

            # Sort files by coverage percentage (ascending) to show worst coverage first
            sorted_files = sorted(
                coverage.file_coverage.items(),
                key=lambda x: x[1].coverage_percent,
            )

            # Show files with lowest coverage (up to max_errors_per_category)
            files_to_show = sorted_files[: self.max_errors_per_category]
            for file_path, file_cov in files_to_show:
                lines.append(
                    f"  {file_path}: {file_cov.coverage_percent:.1f}% "
                    f"({file_cov.covered_lines}/{file_cov.total_lines} lines)"
                )

                # Show uncovered ranges if available
                if file_cov.uncovered_ranges:
                    ranges_str = ", ".join(
                        f"{start}-{end}" if start != end else str(start)
                        for start, end in file_cov.uncovered_ranges[:5]
                    )
                    lines.append(f"    Uncovered lines: {ranges_str}")
                    if len(file_cov.uncovered_ranges) > 5:
                        remaining_ranges = len(file_cov.uncovered_ranges) - 5
                        lines.append(f"    ... and {remaining_ranges} more ranges")

            if len(coverage.file_coverage) > self.max_errors_per_category:
                remaining = len(coverage.file_coverage) - self.max_errors_per_category
                lines.append(f"  ... and {remaining} more files")

        return "\n".join(lines)

    def format_pytest_failures(self, results: PytestResults) -> str:
        """Format pytest failure summary.

        Args:
            results: Pytest-specific failure details

        Returns:
            Formatted pytest failure summary
        """
        if not results.failed_tests:
            return "All pytest tests passed"

        lines = [
            f"Pytest Failures: {len(results.failed_tests)} tests failed",
            "",
        ]

        # Limit to max_errors_per_category
        failures_to_show = results.failed_tests[: self.max_errors_per_category]
        for failure in failures_to_show:
            lines.append(f"  - {failure.test_name}")
            lines.append(f"    File: {failure.test_file}")
            lines.append(f"    Type: {failure.failure_type}")
            lines.append(f"    Message: {failure.failure_message}")

            if failure.assertion_details:
                lines.append(f"    Expected: {failure.assertion_details.expected_value}")
                lines.append(f"    Actual: {failure.assertion_details.actual_value}")
                lines.append(f"    Operator: {failure.assertion_details.comparison_operator}")

            if failure.stack_trace_excerpt:
                lines.append("    Stack trace excerpt:")
                for trace_line in failure.stack_trace_excerpt.split("\n")[:3]:
                    lines.append(f"      {trace_line}")

            lines.append("")

        if len(results.failed_tests) > self.max_errors_per_category:
            remaining = len(results.failed_tests) - self.max_errors_per_category
            lines.append(f"... and {remaining} more failures")

        return "\n".join(lines)

    def format_sandboxes(self, sandboxes: list[SandboxInfo]) -> str:
        """Format sandbox information.

        Args:
            sandboxes: List of preserved sandbox information

        Returns:
            Formatted sandbox paths
        """
        if not sandboxes:
            return ""

        lines = [
            "Preserved Sandboxes:",
        ]

        for sandbox in sandboxes:
            lines.append(f"  - {sandbox.sandbox_path}")
            lines.append(f"    Process: {sandbox.process_description}")
            if sandbox.timestamp:
                lines.append(f"    Timestamp: {sandbox.timestamp}")
            lines.append("")

        return "\n".join(lines)

    def format_error_summary(
        self,
        command_result: CommandResult,
        test_results: TestResults | None = None,
        type_results: TypeCheckResults | None = None,
        coverage: CoverageData | None = None,
        pytest_results: PytestResults | None = None,
        sandboxes: list[SandboxInfo] | None = None,
    ) -> str:
        """Format complete error diagnostic.

        Args:
            command_result: Base command execution result
            test_results: Optional test results from JUnit XML
            type_results: Optional type checking results
            coverage: Optional coverage data
            pytest_results: Optional pytest-specific results
            sandboxes: Optional list of preserved sandboxes

        Returns:
            Complete formatted error summary
        """
        lines = []

        # Determine error type
        error_type = self._determine_error_type(
            command_result, test_results, type_results, pytest_results
        )
        lines.append(f"Error Type: {error_type}")
        lines.append(f"Command: {command_result.command}")
        lines.append(f"Exit Code: {command_result.exit_code}")
        lines.append("")

        # Add test failures if present
        if test_results and test_results.failures:
            lines.append(self.format_test_failures(test_results))
            lines.append("")

        # Add pytest failures if present
        if pytest_results and pytest_results.failed_tests:
            lines.append(self.format_pytest_failures(pytest_results))
            lines.append("")

        # Add type errors if present
        if type_results and type_results.error_count > 0:
            lines.append(self.format_type_errors(type_results))
            lines.append("")

        # Add coverage summary if present
        if coverage:
            lines.append(self.format_coverage_summary(coverage))
            lines.append("")

        # Add sandbox paths if present
        if sandboxes:
            sandbox_info = self.format_sandboxes(sandboxes)
            if sandbox_info:
                lines.append(sandbox_info)
                lines.append("")

        # If no structured errors, show raw output excerpt
        if not any([test_results, type_results, pytest_results]):
            lines.append("Raw Output (last 20 lines):")
            output_lines = command_result.output.split("\n")
            for line in output_lines[-20:]:
                lines.append(f"  {line}")

        return "\n".join(lines).strip()

    def format_parsed_output(self, parsed_output: ParsedOutput) -> str:
        """Format complete parsed output summary.

        Args:
            parsed_output: Aggregated parsing results

        Returns:
            Formatted summary of all parsed data
        """
        lines = []

        # Add test results
        if parsed_output.test_results:
            lines.append(self.format_test_failures(parsed_output.test_results))
            lines.append("")

        # Add pytest results
        if parsed_output.pytest_results:
            lines.append(self.format_pytest_failures(parsed_output.pytest_results))
            lines.append("")

        # Add type check results
        if parsed_output.type_check_results:
            lines.append(self.format_type_errors(parsed_output.type_check_results))
            lines.append("")

        # Add coverage data
        if parsed_output.coverage_data:
            lines.append(self.format_coverage_summary(parsed_output.coverage_data))
            lines.append("")

        # Add sandbox info
        if parsed_output.sandboxes:
            sandbox_info = self.format_sandboxes(parsed_output.sandboxes)
            if sandbox_info:
                lines.append(sandbox_info)
                lines.append("")

        # Add parsing errors if any
        if parsed_output.parsing_errors:
            lines.append("Parsing Errors:")
            for error in parsed_output.parsing_errors:
                lines.append(f"  - {error}")
            lines.append("")

        return "\n".join(lines).strip()

    def _determine_error_type(
        self,
        command_result: CommandResult,
        test_results: TestResults | None,
        type_results: TypeCheckResults | None,
        pytest_results: PytestResults | None,
    ) -> str:
        """Determine the primary error type.

        Args:
            command_result: Command execution result
            test_results: Optional test results
            type_results: Optional type checking results
            pytest_results: Optional pytest results

        Returns:
            Error type string
        """
        if command_result.success:
            return "Success"

        # Check for test failures
        if test_results and test_results.failures:
            return "Test Failure"

        if pytest_results and pytest_results.failed_tests:
            return "Test Failure"

        # Check for type errors
        if type_results and type_results.error_count > 0:
            return "Type Error"

        # Default to execution error
        return "Execution Error"
