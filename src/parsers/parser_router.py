"""Parser router for coordinating output parsing across multiple parsers."""

import logging
from pathlib import Path

from src.models import CommandResult, CoverageData, ParsedOutput
from src.parsers.coverage_parser import CoverageReportParser
from src.parsers.junit_parser import JUnitXMLParser
from src.parsers.mypy_parser import MyPyOutputParser
from src.parsers.pytest_parser import PytestOutputParser
from src.parsers.sandbox_extractor import SandboxPathExtractor

logger = logging.getLogger(__name__)


class ParserRouter:
    """Routes command output to appropriate parsers based on command type.

    Coordinates parsing across multiple specialized parsers (JUnit XML,
    coverage reports, MyPy errors, pytest output, sandbox paths) and
    aggregates results into a unified ParsedOutput object.
    """

    def __init__(
        self,
        junit_parser: JUnitXMLParser | None = None,
        coverage_parser: CoverageReportParser | None = None,
        mypy_parser: MyPyOutputParser | None = None,
        pytest_parser: PytestOutputParser | None = None,
        sandbox_extractor: SandboxPathExtractor | None = None
    ):
        """Initialize parser router with optional parser instances.

        Args:
            junit_parser: Parser for JUnit XML test reports
            coverage_parser: Parser for coverage reports
            mypy_parser: Parser for MyPy type checking output
            pytest_parser: Parser for pytest console output
            sandbox_extractor: Extractor for sandbox paths
        """
        self.junit_parser = junit_parser or JUnitXMLParser()
        self.coverage_parser = coverage_parser or CoverageReportParser()
        self.mypy_parser = mypy_parser or MyPyOutputParser()
        self.pytest_parser = pytest_parser or PytestOutputParser()
        self.sandbox_extractor = sandbox_extractor or SandboxPathExtractor()

    def parse_command_output(
        self,
        command: str,
        result: CommandResult,
        report_dir: str | None = None
    ) -> ParsedOutput:
        """Route output to appropriate parsers based on command type.

        Determines which parsers to invoke based on the command, locates
        report files, coordinates parsing, and handles errors gracefully.

        Args:
            command: The Pants command that was executed
            result: The command execution result
            report_dir: Optional directory containing report files

        Returns:
            ParsedOutput object with aggregated parsing results
        """
        parsed_output = ParsedOutput()

        # Always extract sandbox paths from output
        try:
            sandboxes = self.sandbox_extractor.extract_sandboxes(result.output)
            parsed_output.sandboxes = sandboxes
        except Exception as e:
            error_msg = f"Failed to extract sandbox paths: {e}"
            logger.error(error_msg)
            parsed_output.parsing_errors.append(error_msg)

        # Determine which parsers to use based on command
        parsers_to_use = self.get_parsers_for_command(command)

        # Parse JUnit XML test reports
        if 'junit' in parsers_to_use and report_dir:
            try:
                test_results = self.junit_parser.parse_reports(report_dir)
                if test_results.total_count > 0:
                    parsed_output.test_results = test_results
                    logger.info(
                        f"Parsed {test_results.total_count} tests "
                        f"({test_results.fail_count} failures)"
                    )
            except Exception as e:
                error_msg = f"Failed to parse JUnit XML reports: {e}"
                logger.error(error_msg)
                parsed_output.parsing_errors.append(error_msg)

        # Parse coverage reports
        if 'coverage' in parsers_to_use and report_dir:
            try:
                coverage_data = self._find_and_parse_coverage(report_dir)
                if coverage_data:
                    parsed_output.coverage_data = coverage_data
                    logger.info(
                        f"Parsed coverage data: {coverage_data.total_coverage:.1f}%"
                    )
            except Exception as e:
                error_msg = f"Failed to parse coverage reports: {e}"
                logger.error(error_msg)
                parsed_output.parsing_errors.append(error_msg)

        # Parse MyPy type checking errors
        if 'mypy' in parsers_to_use:
            try:
                type_results = self.mypy_parser.parse_output(result.output)
                if type_results.error_count > 0:
                    parsed_output.type_check_results = type_results
                    logger.info(
                        f"Parsed {type_results.error_count} type checking errors"
                    )
            except Exception as e:
                error_msg = f"Failed to parse MyPy output: {e}"
                logger.error(error_msg)
                parsed_output.parsing_errors.append(error_msg)

        # Parse pytest console output
        if 'pytest' in parsers_to_use:
            try:
                pytest_results = self.pytest_parser.parse_output(result.output)
                if pytest_results.failed_tests:
                    parsed_output.pytest_results = pytest_results
                    logger.info(
                        f"Parsed {len(pytest_results.failed_tests)} pytest failures"
                    )
            except Exception as e:
                error_msg = f"Failed to parse pytest output: {e}"
                logger.error(error_msg)
                parsed_output.parsing_errors.append(error_msg)

        return parsed_output

    def get_parsers_for_command(self, command: str) -> list[str]:
        """Determine which parsers to use based on command type.

        Args:
            command: The Pants command string

        Returns:
            List of parser identifiers to use
        """
        parsers = []

        # Normalize command for matching
        cmd_lower = command.lower()

        # Test commands need JUnit, coverage, and pytest parsers
        if 'test' in cmd_lower:
            parsers.extend(['junit', 'coverage', 'pytest'])

        # Check commands need MyPy parser
        if 'check' in cmd_lower or 'mypy' in cmd_lower:
            parsers.append('mypy')

        # Lint commands might have pytest output if tests are run
        if 'lint' in cmd_lower:
            parsers.append('pytest')

        return parsers

    def _find_and_parse_coverage(self, report_dir: str) -> CoverageData | None:
        """Find and parse coverage report in the report directory.

        Looks for coverage reports in common formats (JSON, XML) and
        parses the first one found.

        Args:
            report_dir: Directory to search for coverage reports

        Returns:
            CoverageData object if a report is found and parsed, None otherwise
        """
        report_path = Path(report_dir)

        if not report_path.exists():
            logger.debug(f"Report directory does not exist: {report_dir}")
            return None

        # Look for common coverage report file names
        coverage_files = [
            'coverage.json',
            'coverage.xml',
            'cobertura.xml',
            '.coverage.json'
        ]

        for filename in coverage_files:
            coverage_file = report_path / filename
            if coverage_file.exists():
                try:
                    return self.coverage_parser.parse_coverage(str(coverage_file))
                except Exception as e:
                    logger.warning(
                        f"Failed to parse coverage file {coverage_file}: {e}"
                    )
                    continue

        # If no standard files found, look for any JSON or XML files
        json_files = list(report_path.glob('*.json'))
        xml_files = list(report_path.glob('*.xml'))

        for coverage_file in json_files + xml_files:
            try:
                return self.coverage_parser.parse_coverage(str(coverage_file))
            except Exception as e:
                logger.debug(
                    f"File {coverage_file} is not a valid coverage report: {e}"
                )
                continue

        logger.debug(f"No coverage reports found in {report_dir}")
        return None
