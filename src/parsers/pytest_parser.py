"""Pytest output parser for extracting detailed failure information."""

import logging
import re
from typing import ClassVar

from src.models import AssertionFailure, PytestFailure, PytestResults

logger = logging.getLogger(__name__)


class PytestOutputParser:
    """Parser for pytest console output.

    Extracts detailed failure information from pytest console output,
    including test names, failure types, assertion details, and stack traces.
    """

    # Pattern for FAILED test lines in short test summary
    # Example: FAILED tests/test_example.py::test_function - AssertionError
    # Example: FAILED tests/test_example.py::TestClass::test_method - ValueError
    FAILED_TEST_PATTERN = re.compile(
        r'^FAILED\s+(?P<test_path>[^:]+)::(?P<test_name>\S+)'
        r'(?:\s+-\s+(?P<failure_info>.+))?$'
    )

    # Pattern for assertion comparison details
    # Example: assert 1 == 2
    # Example: assert result != expected
    ASSERTION_PATTERN = re.compile(
        r'assert\s+(?P<left>.+?)\s+'
        r'(?P<operator>==|!=|<|>|<=|>=|in|not in|is|is not)\s+(?P<right>.+?)$'
    )

    # Pattern for exception type in failure sections
    # Example: E   AssertionError: assert 1 == 2
    # Example: E   ValueError: invalid value
    EXCEPTION_PATTERN = re.compile(
        r'^E\s+(?P<exception_type>\w+(?:Error|Exception|Warning)?):?\s*'
        r'(?P<message>.*)?$'
    )

    # Pattern to identify framework internal stack frames to filter
    FRAMEWORK_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        # Pytest framework internals
        re.compile(r'/_pytest/'),
        re.compile(r'/pytest\.py'),
        re.compile(r'\.pytest_cache/'),
        # Plugin system
        re.compile(r'/pluggy/'),
        # Standard library testing frameworks
        re.compile(r'/unittest/'),
        re.compile(r'/unittest\.py'),
        # Python internals
        re.compile(r'<frozen '),
        re.compile(r'<string>'),
        re.compile(r'/importlib/'),
        re.compile(r'/site-packages/_pytest/'),
        re.compile(r'/site-packages/pluggy/'),
        # Common test runners
        re.compile(r'/py\.test'),
        re.compile(r'/_pydev_'),
        re.compile(r'/pydevd'),
    ]

    # Patterns to identify application code (should be kept)
    APPLICATION_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(r'/src/'),
        re.compile(r'/tests/'),
        re.compile(r'/test_'),
        re.compile(r'^src/'),
        re.compile(r'^tests/'),
        re.compile(r'\s+src/'),  # Match with leading whitespace
        re.compile(r'\s+tests/'),  # Match with leading whitespace
    ]

    # Maximum number of stack frames to include in excerpt
    MAX_STACK_FRAMES = 10

    # Maximum number of relevant frames to keep (most recent)
    MAX_RELEVANT_FRAMES = 5

    def parse_output(self, output: str) -> PytestResults:
        """Parse pytest console output for failures.

        Extracts all test failures from pytest output, including failure
        summaries, assertion details, and relevant stack traces.

        Args:
            output: Pytest console output (stdout/stderr combined)

        Returns:
            PytestResults object with parsed failure information
        """
        failed_tests = []

        # Extract the short test summary section
        summary_lines = self.extract_failure_summary(output)

        # Parse each failed test from the summary
        for line in summary_lines:
            match = self.FAILED_TEST_PATTERN.match(line)
            if match:
                test_path = match.group('test_path')
                test_name = match.group('test_name')
                failure_info = match.group('failure_info') or ''

                # Extract failure type from the failure info
                failure_type = 'Unknown'
                failure_message = failure_info

                # Try to extract exception type
                if ':' in failure_info:
                    parts = failure_info.split(':', 1)
                    potential_type = parts[0].strip()
                    # Check if it looks like an exception type
                    exception_names = [
                        'AssertionError', 'ValueError', 'TypeError', 'KeyError'
                    ]
                    if potential_type and (
                        potential_type.endswith('Error') or
                        potential_type.endswith('Exception') or
                        potential_type.endswith('Warning') or
                        potential_type in exception_names
                    ):
                        failure_type = potential_type
                        failure_message = parts[1].strip() if len(parts) > 1 else ''

                # Try to find detailed failure information in the full output
                assertion_details = self._extract_assertion_for_test(
                    output, test_path, test_name
                )
                stack_trace_excerpt = self._extract_stack_trace_for_test(
                    output, test_path, test_name
                )

                failed_tests.append(PytestFailure(
                    test_name=test_name,
                    test_file=test_path,
                    failure_type=failure_type,
                    failure_message=failure_message,
                    assertion_details=assertion_details,
                    stack_trace_excerpt=stack_trace_excerpt
                ))

        return PytestResults(failed_tests=failed_tests)

    def extract_failure_summary(self, output: str) -> list[str]:
        """Extract FAILED test lines from short test summary.

        Finds the "short test summary info" section in pytest output
        and extracts all FAILED test lines.

        Args:
            output: Pytest console output

        Returns:
            List of FAILED test lines
        """
        lines = output.split('\n')
        summary_lines = []
        in_summary = False

        for line in lines:
            # Look for the short test summary section
            if '= FAILURES =' in line or '= short test summary info =' in line:
                in_summary = True
                continue

            # Stop at the next section marker
            if in_summary and line.startswith('='):
                break

            # Collect FAILED lines
            if in_summary and line.strip().startswith('FAILED'):
                summary_lines.append(line.strip())

        return summary_lines

    def extract_assertion_details(self, output: str) -> list[AssertionFailure]:
        """Parse assertion failure details from output.

        Extracts assertion comparison details including expected values,
        actual values, and comparison operators.

        Args:
            output: Pytest console output

        Returns:
            List of AssertionFailure objects
        """
        assertion_failures = []
        lines = output.split('\n')

        for line in lines:
            # Look for assertion lines (usually prefixed with E)
            if line.strip().startswith('E       assert'):
                # Remove the E prefix and whitespace
                assertion_line = line.strip()[1:].strip()

                match = self.ASSERTION_PATTERN.search(assertion_line)
                if match:
                    left = match.group('left').strip()
                    operator = match.group('operator').strip()
                    right = match.group('right').strip()

                    assertion_failures.append(AssertionFailure(
                        expected_value=right,
                        actual_value=left,
                        comparison_operator=operator
                    ))

        return assertion_failures

    def _extract_assertion_for_test(
        self,
        output: str,
        test_file: str,
        test_name: str
    ) -> AssertionFailure | None:
        """Extract assertion details for a specific test.

        Args:
            output: Full pytest output
            test_file: Path to the test file
            test_name: Name of the test

        Returns:
            AssertionFailure object if found, None otherwise
        """
        lines = output.split('\n')
        in_test_section = False

        for line in lines:
            # Look for the test failure section header
            if f'{test_file}::{test_name}' in line or f'_ {test_name} _' in line:
                in_test_section = True
                continue

            # Stop at the next test section
            if in_test_section and line.startswith('_'):
                break

            # Look for assertion lines in this test's section
            if in_test_section and 'E       assert' in line:
                assertion_line = line.strip()[1:].strip()  # Remove E prefix

                match = self.ASSERTION_PATTERN.search(assertion_line)
                if match:
                    left = match.group('left').strip()
                    operator = match.group('operator').strip()
                    right = match.group('right').strip()

                    return AssertionFailure(
                        expected_value=right,
                        actual_value=left,
                        comparison_operator=operator
                    )

        return None

    def _extract_stack_trace_for_test(
        self,
        output: str,
        test_file: str,
        test_name: str
    ) -> str | None:
        """Extract relevant stack trace excerpt for a specific test.

        Filters out framework internals and returns only application code frames.
        Prioritizes application code and limits depth to most actionable frames.

        Args:
            output: Full pytest output
            test_file: Path to the test file
            test_name: Name of the test

        Returns:
            Stack trace excerpt as a string, or None if not found
        """
        lines = output.split('\n')
        in_test_section = False
        stack_frames: list[str] = []
        current_frame: list[str] = []

        for line in lines:
            # Look for the test failure section header
            test_header = (
                f'{test_file}::{test_name}' in line or
                f'_ {test_name} _' in line
            )
            if test_header:
                in_test_section = True
                continue

            # Stop at the next test section
            if in_test_section and line.startswith('_') and not line.startswith('_ '):
                break

            # Collect stack trace lines
            if in_test_section:
                self._process_stack_frame_line(
                    line, current_frame, stack_frames
                )

        # Add the last frame if any
        self._finalize_stack_frame(current_frame, stack_frames)

        # Filter and prioritize frames
        relevant_frames = self._filter_and_prioritize_frames(stack_frames)

        if relevant_frames:
            return '\n'.join(relevant_frames)

        return None

    def _process_stack_frame_line(
        self,
        line: str,
        current_frame: list[str],
        stack_frames: list[str]
    ) -> None:
        """Process a single line for stack frame extraction.

        Args:
            line: Current line being processed
            current_frame: Current frame being built
            stack_frames: List of completed frames
        """
        # Stack trace lines typically start with specific patterns
        is_trace_line = (
            line.startswith('    ') or
            line.startswith('E   ') or
            line.startswith('>   ')
        )

        if is_trace_line:
            current_frame.append(line)
        elif current_frame:
            # Check if this frame should be included (not framework internal)
            frame_text = '\n'.join(current_frame)
            if not self._is_framework_frame(frame_text):
                stack_frames.append(frame_text)
            current_frame.clear()

    def _finalize_stack_frame(
        self,
        current_frame: list[str],
        stack_frames: list[str]
    ) -> None:
        """Finalize the last stack frame if any.

        Args:
            current_frame: Current frame being built
            stack_frames: List of completed frames
        """
        if current_frame:
            frame_text = '\n'.join(current_frame)
            if not self._is_framework_frame(frame_text):
                stack_frames.append(frame_text)

    def _is_framework_frame(self, frame_text: str) -> bool:
        """Check if a stack frame is from framework internals.

        Args:
            frame_text: Stack frame text

        Returns:
            True if the frame is from framework code, False otherwise
        """
        return any(
            pattern.search(frame_text) for pattern in self.FRAMEWORK_PATTERNS
        )

    def _is_application_frame(self, frame_text: str) -> bool:
        """Check if a stack frame is from application code.

        Args:
            frame_text: Stack frame text

        Returns:
            True if the frame is from application code, False otherwise
        """
        return any(
            pattern.search(frame_text) for pattern in self.APPLICATION_PATTERNS
        )

    def _filter_and_prioritize_frames(
        self,
        stack_frames: list[str]
    ) -> list[str]:
        """Filter and prioritize stack frames for display.

        Strategy:
        1. Remove all framework internal frames
        2. Prioritize application code frames (src/, tests/)
        3. Limit to MAX_RELEVANT_FRAMES most recent frames
        4. If no application frames, keep last few frames anyway

        Args:
            stack_frames: List of all stack frames

        Returns:
            Filtered and prioritized list of frames
        """
        # First pass: categorize frames
        application_frames = []
        other_frames = []

        for frame in stack_frames:
            if self._is_framework_frame(frame):
                # Skip framework internals entirely
                continue
            elif self._is_application_frame(frame):
                application_frames.append(frame)
            else:
                other_frames.append(frame)

        # Prioritize application frames
        if application_frames:
            # Use application frames, limited to most recent
            relevant = application_frames[-self.MAX_RELEVANT_FRAMES:]
        elif other_frames:
            # Fallback to other frames if no application frames found
            relevant = other_frames[-self.MAX_RELEVANT_FRAMES:]
        else:
            # Last resort: use original frames (shouldn't happen often)
            relevant = stack_frames[-self.MAX_RELEVANT_FRAMES:]

        # Ensure we don't exceed maximum frame count
        if len(relevant) > self.MAX_STACK_FRAMES:
            relevant = relevant[-self.MAX_STACK_FRAMES:]

        return relevant
