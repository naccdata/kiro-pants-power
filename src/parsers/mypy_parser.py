"""MyPy output parser for extracting type checking errors."""

import logging
import re

from src.models import TypeCheckError, TypeCheckResults

logger = logging.getLogger(__name__)


class MyPyOutputParser:
    """Parser for MyPy type checking console output.

    Extracts type checking errors from MyPy console output, including
    file paths, line numbers, error codes, and error messages.
    """

    # MyPy error line format: file.py:line:column: error: message [error-code]
    # Example: src/main.py:42:10: error: Argument 1 has incompatible type
    # Also handles Windows paths: C:\path\file.py:42:10: error: message
    ERROR_PATTERN = re.compile(
        r'^(?P<file_path>(?:[A-Za-z]:)?[^:]+):(?P<line>\d+):(?P<column>\d+):'
        r'\s+(?P<severity>\w+):\s+(?P<message>.+?)'
        r'(?:\s+\[(?P<error_code>[^\]]+)\])?$'
    )

    # Alternative pattern without column: file.py:line: error: message
    ERROR_PATTERN_NO_COLUMN = re.compile(
        r'^(?P<file_path>(?:[A-Za-z]:)?[^:]+):(?P<line>\d+):'
        r'\s+(?P<severity>\w+):\s+(?P<message>.+?)'
        r'(?:\s+\[(?P<error_code>[^\]]+)\])?$'
    )

    # Pattern to detect MyPy report file paths
    # Example: "Writing HTML report to mypy-html/"
    # Example: "Generating XML report in mypy-reports/coverage.xml"
    REPORT_PATH_PATTERN = re.compile(
        r'(?:Writing|Generating|Created)\s+(?:HTML\s+|XML\s+)?report\s+(?:to|in|at)\s+["\']?([^"\'\s]+)["\']?',
        re.IGNORECASE
    )

    def parse_output(self, output: str) -> TypeCheckResults:
        """Parse MyPy errors from console output.

        Extracts all type checking errors from MyPy console output,
        aggregates them by file, and extracts report file paths.

        Args:
            output: MyPy console output (stdout/stderr combined)

        Returns:
            TypeCheckResults object with parsed error information
        """
        errors_by_file: dict[str, list[TypeCheckError]] = {}
        report_paths: list[str] = []

        lines = output.split('\n')

        for line in lines:
            # Try to extract error line
            error = self.extract_error_line(line)
            if error:
                # Add error to the file's error list
                if error.file_path not in errors_by_file:
                    errors_by_file[error.file_path] = []
                errors_by_file[error.file_path].append(error)
                continue

            # Try to extract report path
            report_match = self.REPORT_PATH_PATTERN.search(line)
            if report_match:
                report_path = report_match.group(1)
                if report_path not in report_paths:
                    report_paths.append(report_path)

        # Calculate total error count
        error_count = sum(len(errors) for errors in errors_by_file.values())

        return TypeCheckResults(
            error_count=error_count,
            errors_by_file=errors_by_file,
            report_paths=report_paths
        )

    def extract_error_line(self, line: str) -> TypeCheckError | None:
        """Parse a single MyPy error line.

        Extracts file path, line number, column (if present), error code,
        and error message from a MyPy error line.

        Args:
            line: Single line from MyPy output

        Returns:
            TypeCheckError object if the line is an error, None otherwise
        """
        # Try pattern with column first
        match = self.ERROR_PATTERN.match(line)
        if match:
            file_path = match.group('file_path')
            line_number = int(match.group('line'))
            column = int(match.group('column'))
            severity = match.group('severity')
            message = match.group('message').strip()
            error_code = match.group('error_code') or 'unknown'

            # Only process error severity (not note, warning, etc.)
            if severity.lower() == 'error':
                return TypeCheckError(
                    file_path=file_path,
                    line_number=line_number,
                    column=column,
                    error_code=error_code,
                    error_message=message
                )

        # Try pattern without column
        match = self.ERROR_PATTERN_NO_COLUMN.match(line)
        if match:
            file_path = match.group('file_path')
            line_number = int(match.group('line'))
            severity = match.group('severity')
            message = match.group('message').strip()
            error_code = match.group('error_code') or 'unknown'

            # Only process error severity
            if severity.lower() == 'error':
                return TypeCheckError(
                    file_path=file_path,
                    line_number=line_number,
                    column=None,
                    error_code=error_code,
                    error_message=message
                )

        return None
