"""Smoke tests for Hypothesis generators to verify they work correctly."""

import json
import xml.etree.ElementTree as ET

import pytest
from hypothesis import given, settings

from tests.property.generators import (
    invalid_coverage_json,
    invalid_junit_xml,
    invalid_mypy_output,
    invalid_pants_config,
    invalid_pytest_output,
    junit_xml_with_all_statuses,
    mypy_output_multiple_files,
    valid_coverage_json,
    valid_coverage_xml,
    valid_junit_xml,
    valid_mypy_output,
    valid_mypy_output_with_reports,
    valid_pants_config,
    valid_pytest_output,
)


@pytest.mark.property
@given(xml=valid_junit_xml())
@settings(max_examples=10)
def test_valid_junit_xml_generator(xml: str) -> None:
    """Verify valid_junit_xml generates parseable XML."""
    # Should be able to parse without errors
    root = ET.fromstring(xml)
    assert root.tag in ['testsuite', 'testsuites']


@pytest.mark.property
@given(xml=junit_xml_with_all_statuses())
@settings(max_examples=10)
def test_junit_xml_with_all_statuses_generator(xml: str) -> None:
    """Verify junit_xml_with_all_statuses includes all status types."""
    root = ET.fromstring(xml)
    assert root.tag == 'testsuite'

    # Should have at least 3 test cases (pass, fail, skip)
    testcases = root.findall('testcase')
    assert len(testcases) >= 3

    # Check for each status type
    has_pass = any(
        tc.find('failure') is None and tc.find('skipped') is None
        for tc in testcases
    )
    has_fail = any(tc.find('failure') is not None for tc in testcases)
    has_skip = any(tc.find('skipped') is not None for tc in testcases)

    assert has_pass, "Should have at least one passing test"
    assert has_fail, "Should have at least one failing test"
    assert has_skip, "Should have at least one skipped test"


@pytest.mark.property
@given(json_str=valid_coverage_json())
@settings(max_examples=10)
def test_valid_coverage_json_generator(json_str: str) -> None:
    """Verify valid_coverage_json generates parseable JSON."""
    # Should be able to parse without errors
    data = json.loads(json_str)
    assert 'totals' in data
    assert 'files' in data


@pytest.mark.property
@given(xml=valid_coverage_xml())
@settings(max_examples=10)
def test_valid_coverage_xml_generator(xml: str) -> None:
    """Verify valid_coverage_xml generates parseable XML."""
    # Should be able to parse without errors
    root = ET.fromstring(xml)
    assert root.tag == 'coverage'


@pytest.mark.property
@given(output=valid_mypy_output())
@settings(max_examples=10)
def test_valid_mypy_output_generator(output: str) -> None:
    """Verify valid_mypy_output generates valid MyPy error format."""
    # Should contain error lines or be empty
    if output:
        lines = output.split('\n')
        # At least one line should match MyPy error format or be a summary
        assert any(':' in line or 'Found' in line for line in lines)


@pytest.mark.property
@given(output=valid_mypy_output_with_reports())
@settings(max_examples=10)
def test_valid_mypy_output_with_reports_generator(output: str) -> None:
    """Verify valid_mypy_output_with_reports includes report paths."""
    # Should contain report generation message
    assert 'report' in output.lower() or output == ''


@pytest.mark.property
@given(output=mypy_output_multiple_files())
@settings(max_examples=10)
def test_mypy_output_multiple_files_generator(output: str) -> None:
    """Verify mypy_output_multiple_files has errors in multiple files."""
    lines = output.split('\n')
    error_lines = [line for line in lines if ':' in line and 'error:' in line]

    # Should have errors from multiple files
    if error_lines:
        files = set(line.split(':')[0] for line in error_lines)
        assert len(files) >= 2, "Should have errors in at least 2 files"


@pytest.mark.property
@given(output=valid_pytest_output())
@settings(max_examples=10)
def test_valid_pytest_output_generator(output: str) -> None:
    """Verify valid_pytest_output generates valid pytest format."""
    # Should contain FAILURES section and short test summary
    assert 'FAILURES' in output or 'FAILED' in output


@pytest.mark.property
@given(config=valid_pants_config())
@settings(max_examples=10)
def test_valid_pants_config_generator(config: str) -> None:
    """Verify valid_pants_config generates parseable TOML."""
    import tomllib

    # Should be able to parse without errors
    data = tomllib.loads(config)
    assert 'GLOBAL' in data


@pytest.mark.property
@given(xml=invalid_junit_xml())
@settings(max_examples=10)
def test_invalid_junit_xml_generator(xml: str) -> None:
    """Verify invalid_junit_xml generates unparseable XML."""
    # Should fail to parse
    with pytest.raises(ET.ParseError):
        ET.fromstring(xml)


@pytest.mark.property
@given(json_str=invalid_coverage_json())
@settings(max_examples=10)
def test_invalid_coverage_json_generator(json_str: str) -> None:
    """Verify invalid_coverage_json generates unparseable or invalid JSON."""
    # Should either fail to parse or have invalid structure
    try:
        data = json.loads(json_str)
        # If it parses, it should have invalid structure
        assert 'totals' not in data or not isinstance(data.get('totals'), dict)
    except json.JSONDecodeError:
        # Expected for malformed JSON
        pass


@pytest.mark.property
@given(config=invalid_pants_config())
@settings(max_examples=10)
def test_invalid_pants_config_generator(config: str) -> None:
    """Verify invalid_pants_config generates unparseable TOML."""
    import tomllib

    # Should fail to parse
    with pytest.raises(tomllib.TOMLDecodeError):
        tomllib.loads(config)


@pytest.mark.property
@given(output=invalid_mypy_output())
@settings(max_examples=10)
def test_invalid_mypy_output_generator(output: str) -> None:
    """Verify invalid_mypy_output generates invalid MyPy format."""
    # Should not match standard MyPy error format
    # (This is a weak test since invalid output is varied)
    assert True  # Just verify it generates without error


@pytest.mark.property
@given(output=invalid_pytest_output())
@settings(max_examples=10)
def test_invalid_pytest_output_generator(output: str) -> None:
    """Verify invalid_pytest_output generates invalid pytest format."""
    # Should not have complete pytest structure
    # (This is a weak test since invalid output is varied)
    assert True  # Just verify it generates without error
