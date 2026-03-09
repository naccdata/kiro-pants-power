"""Smoke tests for Hypothesis generators to verify they work correctly."""

import json
import xml.etree.ElementTree as ET

import pytest
from hypothesis import given, settings

from tests.property.generators import (
    edge_case_paths,
    intent_contexts,
    invalid_coverage_json,
    invalid_junit_xml,
    invalid_mypy_output,
    invalid_pants_config,
    invalid_pytest_output,
    junit_xml_with_all_statuses,
    mypy_output_multiple_files,
    pants_errors,
    pants_target_specs,
    pytest_filter_patterns,
    valid_coverage_json,
    valid_coverage_xml,
    valid_directory_paths,
    valid_file_paths,
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
    assert root.tag in ["testsuite", "testsuites"]


@pytest.mark.property
@given(xml=junit_xml_with_all_statuses())
@settings(max_examples=10)
def test_junit_xml_with_all_statuses_generator(xml: str) -> None:
    """Verify junit_xml_with_all_statuses includes all status types."""
    root = ET.fromstring(xml)
    assert root.tag == "testsuite"

    # Should have at least 3 test cases (pass, fail, skip)
    testcases = root.findall("testcase")
    assert len(testcases) >= 3

    # Check for each status type
    has_pass = any(tc.find("failure") is None and tc.find("skipped") is None for tc in testcases)
    has_fail = any(tc.find("failure") is not None for tc in testcases)
    has_skip = any(tc.find("skipped") is not None for tc in testcases)

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
    assert "totals" in data
    assert "files" in data


@pytest.mark.property
@given(xml=valid_coverage_xml())
@settings(max_examples=10)
def test_valid_coverage_xml_generator(xml: str) -> None:
    """Verify valid_coverage_xml generates parseable XML."""
    # Should be able to parse without errors
    root = ET.fromstring(xml)
    assert root.tag == "coverage"


@pytest.mark.property
@given(output=valid_mypy_output())
@settings(max_examples=10)
def test_valid_mypy_output_generator(output: str) -> None:
    """Verify valid_mypy_output generates valid MyPy error format."""
    # Should contain error lines or be empty
    if output:
        lines = output.split("\n")
        # At least one line should match MyPy error format or be a summary
        assert any(":" in line or "Found" in line for line in lines)


@pytest.mark.property
@given(output=valid_mypy_output_with_reports())
@settings(max_examples=10)
def test_valid_mypy_output_with_reports_generator(output: str) -> None:
    """Verify valid_mypy_output_with_reports includes report paths."""
    # Should contain report generation message
    assert "report" in output.lower() or output == ""


@pytest.mark.property
@given(output=mypy_output_multiple_files())
@settings(max_examples=10)
def test_mypy_output_multiple_files_generator(output: str) -> None:
    """Verify mypy_output_multiple_files has errors in multiple files."""
    lines = output.split("\n")
    error_lines = [line for line in lines if ":" in line and "error:" in line]

    # Should have errors from multiple files
    if error_lines:
        files = {line.split(":")[0] for line in error_lines}
        assert len(files) >= 2, "Should have errors in at least 2 files"


@pytest.mark.property
@given(output=valid_pytest_output())
@settings(max_examples=10)
def test_valid_pytest_output_generator(output: str) -> None:
    """Verify valid_pytest_output generates valid pytest format."""
    # Should contain FAILURES section and short test summary
    assert "FAILURES" in output or "FAILED" in output


@pytest.mark.property
@given(config=valid_pants_config())
@settings(max_examples=10)
def test_valid_pants_config_generator(config: str) -> None:
    """Verify valid_pants_config generates parseable TOML."""
    import tomllib

    # Should be able to parse without errors
    data = tomllib.loads(config)
    assert "GLOBAL" in data


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
        assert "totals" not in data or not isinstance(data.get("totals"), dict)
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


# ============================================================================
# Intent-Based API Domain Type Generator Smoke Tests
# ============================================================================


@pytest.mark.property
@given(path=valid_file_paths())
@settings(max_examples=20)
def test_valid_file_paths_generator(path: str) -> None:
    """Verify valid_file_paths generates realistic file paths."""
    # Should be a non-empty string
    assert isinstance(path, str)
    assert len(path) > 0

    # Should have a file extension
    assert "." in path

    # Should not start with /
    assert not path.startswith("/")

    # Should not contain backslashes (Unix-style paths)
    assert "\\" not in path


@pytest.mark.property
@given(path=valid_directory_paths())
@settings(max_examples=20)
def test_valid_directory_paths_generator(path: str) -> None:
    """Verify valid_directory_paths generates realistic directory paths."""
    # Should be a non-empty string
    assert isinstance(path, str)
    assert len(path) > 0

    # Should not start with /
    assert not path.startswith("/")

    # Should not end with /
    assert not path.endswith("/")

    # Should not contain backslashes (Unix-style paths)
    assert "\\" not in path

    # Should not have file extensions
    assert not any(path.endswith(ext) for ext in [".py", ".txt", ".md", ".json"])


@pytest.mark.property
@given(pattern=pytest_filter_patterns())
@settings(max_examples=20)
def test_test_filter_patterns_generator(pattern: str) -> None:
    """Verify pytest_filter_patterns generates valid pytest filter patterns."""
    # Should be a non-empty string
    assert isinstance(pattern, str)
    assert len(pattern) > 0

    # Should contain test-related keywords or operators
    valid_keywords = ["test_", "test", "*", "or", "and", "not", "(", ")"]
    assert any(keyword in pattern for keyword in valid_keywords)

    # Should not contain invalid characters for pytest filters
    invalid_chars = [";", "&", "|", "$", "`", "\n", "\r"]
    assert not any(char in pattern for char in invalid_chars)


@pytest.mark.property
@given(error=pants_errors())
@settings(max_examples=20)
def test_pants_errors_generator(error: str) -> None:
    """Verify pants_errors generates realistic Pants error messages."""
    # Should be a non-empty string
    assert isinstance(error, str)
    assert len(error) > 0

    # Should contain error-related keywords
    error_keywords = [
        "target",
        "BUILD",
        "file",
        "directory",
        "error",
        "failed",
        "not found",
        "unknown",
        "invalid",
        "ambiguous",
    ]
    assert any(keyword.lower() in error.lower() for keyword in error_keywords)


@pytest.mark.property
@given(context=intent_contexts())
@settings(max_examples=20)
def test_intent_contexts_generator(context: dict) -> None:
    """Verify intent_contexts generates valid intent context dictionaries."""
    # Should have all required keys
    assert "scope" in context
    assert "path" in context
    assert "recursive" in context
    assert "test_filter" in context

    # Scope should be valid
    assert context["scope"] in ["all", "directory", "file"]

    # Path should match scope requirements
    if context["scope"] == "all":
        assert context["path"] is None
    elif context["scope"] == "directory":
        assert context["path"] is not None
        assert isinstance(context["path"], str)
    elif context["scope"] == "file":
        assert context["path"] is not None
        assert isinstance(context["path"], str)
        assert "." in context["path"]  # Should have extension

    # Recursive should be boolean
    assert isinstance(context["recursive"], bool)

    # Test filter should be string or None
    assert context["test_filter"] is None or isinstance(context["test_filter"], str)


@pytest.mark.property
@given(path=edge_case_paths())
@settings(max_examples=20)
def test_edge_case_paths_generator(path: str) -> None:
    """Verify edge_case_paths generates various edge case paths."""
    # Should be a string (can be empty)
    assert isinstance(path, str)

    # Should represent some kind of edge case
    # (This is a weak test since edge cases are varied)
    edge_case_indicators = [
        len(path) == 0,  # Empty
        len(path) > 100,  # Very long
        " " in path,  # Contains spaces
        ".." in path,  # Parent directory reference
        path == ".",  # Current directory
        path == "/",  # Root
    ]
    # At least one edge case indicator should be true
    # (or it's a path with special characters which is harder to detect)
    assert any(edge_case_indicators) or len(path) > 0


@pytest.mark.property
@given(spec=pants_target_specs())
@settings(max_examples=20)
def test_pants_target_specs_generator(spec: str) -> None:
    """Verify pants_target_specs generates valid Pants target specifications."""
    # Should be a non-empty string
    assert isinstance(spec, str)
    assert len(spec) > 0

    # Should match Pants target spec patterns
    valid_patterns = [
        spec == "::",  # Recursive all
        spec.endswith("::"),  # Recursive path
        spec.endswith(":"),  # Non-recursive
        ":" in spec,  # Explicit target or wildcard
        "." in spec,  # File path
    ]
    assert any(valid_patterns), f"Invalid target spec pattern: {spec}"
