"""Unit tests for JUnit XML parser."""

import tempfile
from pathlib import Path

import pytest

from src.models import TestResults
from src.parsers.junit_parser import JUnitXMLParser


class TestJUnitXMLParser:
    """Test suite for JUnitXMLParser."""

    def test_parse_single_report_with_passing_tests(self):
        """Test parsing a JUnit XML file with passing tests."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="2" failures="0" errors="0" skipped="0" time="0.123">
    <testcase name="test_example_1" classname="tests.test_module" file="tests/test_module.py" time="0.050"/>
    <testcase name="test_example_2" classname="tests.test_module" file="tests/test_module.py" time="0.073"/>
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = JUnitXMLParser()
            result = parser.parse_single_report(temp_path)

            assert result.total_count == 2
            assert result.pass_count == 2
            assert result.fail_count == 0
            assert result.skip_count == 0
            assert len(result.failures) == 0
            assert result.execution_time == 0.123
        finally:
            Path(temp_path).unlink()

    def test_parse_single_report_with_failures(self):
        """Test parsing a JUnit XML file with test failures."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="3" failures="1" errors="1" skipped="0" time="0.200">
    <testcase name="test_passing" classname="tests.test_module" file="tests/test_module.py" time="0.050"/>
    <testcase name="test_failing" classname="tests.test_module" file="tests/test_module.py" time="0.075">
        <failure type="AssertionError" message="Expected 5 but got 3">
Traceback (most recent call last):
  File "tests/test_module.py", line 10, in test_failing
    assert result == 5
AssertionError: Expected 5 but got 3
        </failure>
    </testcase>
    <testcase name="test_error" classname="tests.test_module" file="tests/test_module.py" time="0.075">
        <error type="ValueError" message="Invalid input">
Traceback (most recent call last):
  File "tests/test_module.py", line 20, in test_error
    process_data(None)
ValueError: Invalid input
        </error>
    </testcase>
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = JUnitXMLParser()
            result = parser.parse_single_report(temp_path)

            assert result.total_count == 3
            assert result.pass_count == 1
            assert result.fail_count == 2
            assert result.skip_count == 0
            assert len(result.failures) == 2
            assert result.execution_time == 0.200

            # Check first failure
            failure1 = result.failures[0]
            assert failure1.test_name == "test_failing"
            assert failure1.test_file == "tests/test_module.py"
            assert failure1.test_class == "tests.test_module"
            assert failure1.failure_type == "AssertionError"
            assert failure1.failure_message == "Expected 5 but got 3"
            assert "assert result == 5" in failure1.stack_trace

            # Check second failure (error)
            failure2 = result.failures[1]
            assert failure2.test_name == "test_error"
            assert failure2.failure_type == "ValueError"
            assert failure2.failure_message == "Invalid input"
        finally:
            Path(temp_path).unlink()

    def test_parse_single_report_with_skipped_tests(self):
        """Test parsing a JUnit XML file with skipped tests."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="2" failures="0" errors="0" skipped="1" time="0.050">
    <testcase name="test_passing" classname="tests.test_module" file="tests/test_module.py" time="0.050"/>
    <testcase name="test_skipped" classname="tests.test_module" file="tests/test_module.py">
        <skipped message="Test skipped"/>
    </testcase>
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = JUnitXMLParser()
            result = parser.parse_single_report(temp_path)

            assert result.total_count == 2
            assert result.pass_count == 1
            assert result.fail_count == 0
            assert result.skip_count == 1
            assert len(result.failures) == 0
        finally:
            Path(temp_path).unlink()

    def test_parse_single_report_file_not_found(self):
        """Test parsing a non-existent file raises FileNotFoundError."""
        parser = JUnitXMLParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_single_report("/nonexistent/path/report.xml")

    def test_parse_single_report_malformed_xml(self):
        """Test parsing malformed XML raises ParseError."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="1">
    <testcase name="test_example"
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = JUnitXMLParser()
            with pytest.raises(Exception):  # ET.ParseError
                parser.parse_single_report(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_reports_aggregates_multiple_files(self):
        """Test parsing multiple JUnit XML files aggregates results correctly."""
        xml_content_1 = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite_1" tests="2" failures="1" errors="0" skipped="0" time="0.100">
    <testcase name="test_1" classname="tests.test_module1" file="tests/test_module1.py" time="0.050"/>
    <testcase name="test_2" classname="tests.test_module1" file="tests/test_module1.py" time="0.050">
        <failure type="AssertionError" message="Test failed">Failure details</failure>
    </testcase>
</testsuite>
"""
        xml_content_2 = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite_2" tests="3" failures="0" errors="0" skipped="1" time="0.150">
    <testcase name="test_3" classname="tests.test_module2" file="tests/test_module2.py" time="0.075"/>
    <testcase name="test_4" classname="tests.test_module2" file="tests/test_module2.py" time="0.075"/>
    <testcase name="test_5" classname="tests.test_module2" file="tests/test_module2.py">
        <skipped message="Skipped"/>
    </testcase>
</testsuite>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write first XML file
            xml_path_1 = Path(temp_dir) / "report1.xml"
            xml_path_1.write_text(xml_content_1)

            # Write second XML file
            xml_path_2 = Path(temp_dir) / "report2.xml"
            xml_path_2.write_text(xml_content_2)

            parser = JUnitXMLParser()
            result = parser.parse_reports(temp_dir)

            assert result.total_count == 5
            assert result.pass_count == 3
            assert result.fail_count == 1
            assert result.skip_count == 1
            assert len(result.failures) == 1
            assert result.execution_time == 0.250

    def test_parse_reports_empty_directory(self):
        """Test parsing an empty directory returns empty results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = JUnitXMLParser()
            result = parser.parse_reports(temp_dir)

            assert result.total_count == 0
            assert result.pass_count == 0
            assert result.fail_count == 0
            assert result.skip_count == 0
            assert len(result.failures) == 0
            assert result.execution_time == 0.0

    def test_parse_reports_nonexistent_directory(self):
        """Test parsing a non-existent directory returns empty results."""
        parser = JUnitXMLParser()
        result = parser.parse_reports("/nonexistent/directory")

        assert result.total_count == 0
        assert result.pass_count == 0
        assert result.fail_count == 0
        assert result.skip_count == 0
        assert len(result.failures) == 0
        assert result.execution_time == 0.0

    def test_parse_reports_handles_malformed_files_gracefully(self):
        """Test that malformed files are logged and skipped during aggregation."""
        xml_content_valid = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="1" failures="0" errors="0" skipped="0" time="0.050">
    <testcase name="test_1" classname="tests.test_module" file="tests/test_module.py" time="0.050"/>
</testsuite>
"""
        xml_content_malformed = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="1">
    <testcase name="test_2"
</testsuite>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write valid XML file
            xml_path_1 = Path(temp_dir) / "report1.xml"
            xml_path_1.write_text(xml_content_valid)

            # Write malformed XML file
            xml_path_2 = Path(temp_dir) / "report2.xml"
            xml_path_2.write_text(xml_content_malformed)

            parser = JUnitXMLParser()
            result = parser.parse_reports(temp_dir)

            # Should only include results from valid file
            assert result.total_count == 1
            assert result.pass_count == 1
            assert result.fail_count == 0
            assert result.skip_count == 0

    def test_parse_single_report_with_testsuites_root(self):
        """Test parsing a JUnit XML file with testsuites as root element."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
    <testsuite name="test_suite_1" tests="1" failures="0" errors="0" skipped="0" time="0.050">
        <testcase name="test_1" classname="tests.test_module1" file="tests/test_module1.py" time="0.050"/>
    </testsuite>
    <testsuite name="test_suite_2" tests="1" failures="0" errors="0" skipped="0" time="0.075">
        <testcase name="test_2" classname="tests.test_module2" file="tests/test_module2.py" time="0.075"/>
    </testsuite>
</testsuites>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = JUnitXMLParser()
            result = parser.parse_single_report(temp_path)

            assert result.total_count == 2
            assert result.pass_count == 2
            assert result.fail_count == 0
            assert result.skip_count == 0
            assert result.execution_time == 0.125
        finally:
            Path(temp_path).unlink()

    def test_parse_single_report_empty_test_suite(self):
        """Test parsing an empty test suite."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="test_suite" tests="0" failures="0" errors="0" skipped="0" time="0.000">
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            parser = JUnitXMLParser()
            result = parser.parse_single_report(temp_path)

            assert result.total_count == 0
            assert result.pass_count == 0
            assert result.fail_count == 0
            assert result.skip_count == 0
            assert len(result.failures) == 0
        finally:
            Path(temp_path).unlink()
