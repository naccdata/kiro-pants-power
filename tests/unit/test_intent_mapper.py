"""Unit tests for IntentMapper."""

import pytest

from src.intent.intent_mapper import IntentError, IntentMapper


def test_map_intent_scope_all(mock_validator, default_config):
    """Test mapping scope='all' to '::'."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    result = mapper.map_intent(scope="all")

    assert result.target_spec == "::"
    assert result.additional_options == []
    assert result.resolved_intent.scope == "all"


def test_map_intent_directory_recursive(mock_validator, default_config):
    """Test mapping directory with recursive=True."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    result = mapper.map_intent(scope="directory", path="src/tests", recursive=True)

    assert result.target_spec == "src/tests::"
    assert result.additional_options == []


def test_map_intent_directory_non_recursive(mock_validator, default_config):
    """Test mapping directory with recursive=False."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    result = mapper.map_intent(scope="directory", path="src/tests", recursive=False)

    assert result.target_spec == "src/tests:"
    assert result.additional_options == []


def test_map_intent_file(mock_validator, default_config):
    """Test mapping file scope."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    result = mapper.map_intent(scope="file", path="src/tests/test_example.py")

    assert result.target_spec == "src/tests/test_example.py"
    assert result.additional_options == []


def test_map_intent_with_test_filter(mock_validator, default_config):
    """Test mapping with test filter."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    result = mapper.map_intent(scope="all", test_filter="test_create")

    assert result.target_spec == "::"
    assert result.additional_options == ["-k", "test_create"]


def test_map_intent_file_without_path_raises_error(mock_validator, default_config):
    """Test that file scope without path raises IntentError."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)

    with pytest.raises(IntentError, match="requires a path"):
        mapper.map_intent(scope="file", path=None)


def test_resolve_defaults_scope(mock_validator, default_config):
    """Test default scope is applied."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    resolved = mapper.resolve_defaults(scope=None, path=None, recursive=None)

    assert resolved.scope == "all"
    assert "scope" in resolved.defaults_applied


def test_resolve_defaults_directory_path(mock_validator, default_config):
    """Test default path for directory scope."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    resolved = mapper.resolve_defaults(scope="directory", path=None, recursive=None)

    assert resolved.path == "."
    assert "path" in resolved.defaults_applied


def test_resolve_defaults_recursive(mock_validator, default_config):
    """Test default recursive flag."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    resolved = mapper.resolve_defaults(
        scope="directory",
        path="src/tests",
        recursive=None,
    )

    assert resolved.recursive is True
    assert "recursive" in resolved.defaults_applied


def test_map_intent_empty_path_directory(mock_validator, default_config):
    """Test empty path with directory scope defaults to current directory."""
    mapper = IntentMapper(config=default_config, validator=mock_validator)
    result = mapper.map_intent(scope="directory", path=None)

    assert result.target_spec == "::"
    assert result.resolved_intent.path == "."
