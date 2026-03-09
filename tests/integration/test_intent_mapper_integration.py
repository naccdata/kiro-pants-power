"""Integration tests for Intent_Mapper component."""

import pytest

from src.intent.configuration import Configuration
from src.intent.intent_mapper import IntentError, IntentMapper
from src.intent.path_validator import PathValidator
from src.models import ValidationError


def test_intent_mapper_with_real_validator(temp_repo):
    """Test Intent_Mapper with real PathValidator."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    # Test scope='all'
    result = mapper.map_intent(scope="all")
    assert result.target_spec == "::"
    assert result.additional_options == []

    # Test scope='directory' with existing directory
    result = mapper.map_intent(scope="directory", path="src/tests", recursive=True)
    assert result.target_spec == "src/tests::"

    # Test scope='file' with existing file
    result = mapper.map_intent(scope="file", path="src/tests/test_example.py")
    assert result.target_spec == "src/tests/test_example.py"


def test_intent_mapper_validation_failure(temp_repo):
    """Test Intent_Mapper with path validation failure."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    # Test with non-existent file
    with pytest.raises(ValidationError, match="Path does not exist"):
        mapper.map_intent(scope="file", path="nonexistent.py")


def test_intent_mapper_with_test_filter(temp_repo):
    """Test Intent_Mapper with test filter."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    result = mapper.map_intent(
        scope="directory",
        path="src/tests",
        test_filter="test_example",
    )
    assert result.target_spec == "src/tests::"
    assert result.additional_options == ["-k", "test_example"]


def test_intent_mapper_defaults(temp_repo):
    """Test Intent_Mapper default resolution."""
    # Create BUILD file in root for this test
    (temp_repo / "BUILD").write_text("python_tests()")

    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    # Test default scope
    result = mapper.map_intent(scope="all")
    assert result.resolved_intent.scope == "all"

    # Test default path for directory scope
    result = mapper.map_intent(scope="directory", path=None)
    assert result.resolved_intent.path == "."
    assert result.target_spec == "::"

    # Test default recursive
    result = mapper.map_intent(scope="directory", path="src/tests", recursive=None)
    assert result.resolved_intent.recursive is True


def test_intent_mapper_validation_disabled(temp_repo):
    """Test Intent_Mapper with validation disabled."""
    config = Configuration(enable_path_validation=False)
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    # Should not raise error even with non-existent path
    result = mapper.map_intent(scope="file", path="nonexistent.py")
    assert result.target_spec == "nonexistent.py"


def test_intent_mapper_root_directory(temp_repo):
    """Test Intent_Mapper with root directory."""
    # Create BUILD file in root for this test
    (temp_repo / "BUILD").write_text("python_tests()")

    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    # Test with empty path
    result = mapper.map_intent(scope="directory", path="")
    assert result.target_spec == "::"

    # Test with "." path
    result = mapper.map_intent(scope="directory", path=".")
    assert result.target_spec == "::"


def test_intent_mapper_non_recursive_directory(temp_repo):
    """Test Intent_Mapper with non-recursive directory."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    result = mapper.map_intent(scope="directory", path="src/tests", recursive=False)
    assert result.target_spec == "src/tests:"
    assert result.resolved_intent.recursive is False


def test_intent_mapper_file_without_path_error(temp_repo):
    """Test Intent_Mapper raises error for file scope without path."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)
    mapper = IntentMapper(config=config, validator=validator)

    with pytest.raises(IntentError, match="requires a path"):
        mapper.map_intent(scope="file", path=None)
