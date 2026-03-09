"""Shared fixtures for pytest tests."""

from unittest.mock import Mock

import pytest

from src.intent.configuration import Configuration
from src.intent.data_models import ValidationResult
from src.intent.path_validator import PathValidator


@pytest.fixture
def mock_validator():
    """Mock validator that always returns valid.

    Returns:
        Mock PathValidator that validates all paths as valid
    """
    validator = Mock(spec=PathValidator)
    validator.validate_path.return_value = ValidationResult(valid=True)
    return validator


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository structure.

    Args:
        tmp_path: pytest's tmp_path fixture

    Returns:
        Path to temporary repository root
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    # Create directory structure
    src_dir = repo / "src"
    src_dir.mkdir()

    tests_dir = src_dir / "tests"
    tests_dir.mkdir()

    # Create BUILD file
    (tests_dir / "BUILD").write_text("python_tests()")

    # Create a test file
    (tests_dir / "test_example.py").write_text(
        "def test_example():\n    assert True\n"
    )

    return repo


@pytest.fixture
def default_config():
    """Default configuration for testing.

    Returns:
        Configuration instance with default values
    """
    return Configuration(
        enable_path_validation=True,
        enable_build_file_checking=True,
        enable_error_translation=True,
        build_file_cache_ttl=60,
        max_parent_directory_depth=5,
        path_validation_timeout=10,
        build_file_check_timeout=50,
        log_performance_warnings=True,
        default_scope="all",
        default_recursive=True,
    )


@pytest.fixture
def sample_pants_errors():
    """Sample Pants error messages for testing.

    Returns:
        Dictionary of error types to error messages
    """
    return {
        "no_targets": "No targets found matching the specification",
        "unknown_target": "Unknown target: src/tests:nonexistent",
        "build_not_found": "BUILD file not found in directory",
        "no_such_file": "No such file or directory: src/missing.py",
    }


@pytest.fixture
def real_validator(default_config, temp_repo):
    """Create a real PathValidator with a temporary repository.

    Args:
        default_config: Default configuration fixture
        temp_repo: Temporary repository fixture

    Returns:
        PathValidator instance configured with temp repository
    """
    return PathValidator(config=default_config, repo_root=temp_repo)
