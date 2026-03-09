"""JUnit XML parser for extracting structured test results."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from src.models import TestFailure, TestResults

logger = logging.getLogger(__name__)


class JUnitXMLParser:
    """Parser for JUnit XML test report files.

    Extracts structured test results including test counts, execution times,
    and detailed failure information from JUnit XML format reports.
    """

    def parse_reports(self, report_dir: str) -> TestResults:
        """Parse all JUnit XML files in a directory.

        Aggregates results from all XML files found in the directory,
        combining test counts and failure details.

        Args:
            report_dir: Path to directory containing JUnit XML report files

        Returns:
            TestResults object with aggregated results from all reports
        """
        report_path = Path(report_dir)

        if not report_path.exists():
            logger.warning(f"Report directory does not exist: {report_dir}")
            return TestResults(
                total_count=0,
                pass_count=0,
                fail_count=0,
                skip_count=0,
                failures=[],
                execution_time=0.0
            )

        # Find all XML files in the directory
        xml_files = list(report_path.glob("*.xml"))

        if not xml_files:
            logger.warning(f"No XML files found in directory: {report_dir}")
            return TestResults(
                total_count=0,
                pass_count=0,
                fail_count=0,
                skip_count=0,
                failures=[],
                execution_time=0.0
            )

        # Aggregate results from all files
        total_count = 0
        pass_count = 0
        fail_count = 0
        skip_count = 0
        all_failures = []
        total_time = 0.0

        for xml_file in xml_files:
            try:
                result = self.parse_single_report(str(xml_file))
                total_count += result.total_count
                pass_count += result.pass_count
                fail_count += result.fail_count
                skip_count += result.skip_count
                all_failures.extend(result.failures)
                total_time += result.execution_time
            except Exception as e:
                logger.error(f"Failed to parse {xml_file}: {e}")
                continue

        return TestResults(
            total_count=total_count,
            pass_count=pass_count,
            fail_count=fail_count,
            skip_count=skip_count,
            failures=all_failures,
            execution_time=total_time
        )

    def parse_single_report(self, xml_path: str) -> TestResults:  # noqa: C901
        """Parse a single JUnit XML file.

        Extracts test case information including names, status, execution times,
        and failure details from a single JUnit XML report file.

        Args:
            xml_path: Path to the JUnit XML file

        Returns:
            TestResults object with parsed test information

        Raises:
            FileNotFoundError: If the XML file does not exist
            ET.ParseError: If the XML is malformed
        """
        path = Path(xml_path)

        if not path.exists():
            logger.error(f"XML file does not exist: {xml_path}")
            raise FileNotFoundError(f"XML file not found: {xml_path}")

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Malformed XML in {xml_path}: {e}")
            raise

        # Initialize counters
        total_count = 0
        pass_count = 0
        fail_count = 0
        skip_count = 0
        failures = []
        execution_time = 0.0

        # Parse test suites (can be nested or flat)
        test_suites: list[ET.Element] = []
        if root.tag == "testsuites":
            test_suites = root.findall("testsuite")
        elif root.tag == "testsuite":
            test_suites = [root]
        else:
            logger.warning(f"Unexpected root element in {xml_path}: {root.tag}")
            return TestResults(
                total_count=0,
                pass_count=0,
                fail_count=0,
                skip_count=0,
                failures=[],
                execution_time=0.0
            )

        # Process each test suite
        for suite in test_suites:
            # Get suite-level timing if available
            suite_time = suite.get("time")
            if suite_time:
                try:
                    execution_time += float(suite_time)
                except ValueError:
                    logger.debug(f"Invalid time value in suite: {suite_time}")

            # Process test cases in the suite
            for testcase in suite.findall("testcase"):
                total_count += 1

                # Extract test case information
                test_name = testcase.get("name", "unknown")
                test_class = testcase.get("classname")
                test_file = testcase.get("file", test_class or "unknown")

                # Check for failure
                failure_elem = testcase.find("failure")
                error_elem = testcase.find("error")
                skipped_elem = testcase.find("skipped")

                if skipped_elem is not None:
                    skip_count += 1
                elif failure_elem is not None or error_elem is not None:
                    fail_count += 1

                    # Extract failure details
                    failure_node = failure_elem if failure_elem is not None else error_elem
                    assert failure_node is not None  # Type narrowing
                    failure_type = failure_node.get("type", "Unknown")
                    failure_message = failure_node.get("message", "")
                    stack_trace = failure_node.text

                    failures.append(TestFailure(
                        test_name=test_name,
                        test_file=test_file,
                        test_class=test_class,
                        failure_type=failure_type,
                        failure_message=failure_message,
                        stack_trace=stack_trace
                    ))
                else:
                    pass_count += 1

        return TestResults(
            total_count=total_count,
            pass_count=pass_count,
            fail_count=fail_count,
            skip_count=skip_count,
            failures=failures,
            execution_time=execution_time
        )
