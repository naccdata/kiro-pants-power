"""Performance tests for intent-based API layer.

These tests verify that performance targets are met:
- File existence check < 10ms
- Directory existence check < 10ms
- BUILD file detection < 50ms
- Overall validation < 100ms
"""

import time
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import pytest

from src.intent.configuration import Configuration
from src.intent.path_validator import PathValidator


@pytest.fixture
def temp_repo() -> Generator[Path, None, None]:
    """Create a temporary repository structure for testing."""
    with TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create directory structure
        src_dir = repo_root / "src"
        src_dir.mkdir()

        tests_dir = repo_root / "tests"
        tests_dir.mkdir()

        # Create some files
        (src_dir / "main.py").touch()
        (tests_dir / "test_main.py").touch()

        # Create BUILD files
        (src_dir / "BUILD").touch()
        (tests_dir / "BUILD").touch()

        yield repo_root


@pytest.mark.performance
def test_file_existence_check_performance(temp_repo: Path) -> None:
    """Verify file existence check completes within 10ms."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    file_path = temp_repo / "src" / "main.py"

    # Warm up
    validator.validate_path(str(file_path), scope="file")

    # Measure performance
    start = time.perf_counter()
    result = validator.validate_path(str(file_path), scope="file")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.valid
    assert elapsed_ms < 10, f"File check took {elapsed_ms:.2f}ms (target: < 10ms)"


@pytest.mark.performance
def test_directory_existence_check_performance(temp_repo: Path) -> None:
    """Verify directory existence check completes within 10ms."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    dir_path = temp_repo / "src"

    # Warm up
    validator.validate_path(str(dir_path), scope="directory")

    # Measure performance
    start = time.perf_counter()
    result = validator.validate_path(str(dir_path), scope="directory")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.valid
    assert elapsed_ms < 10, f"Directory check took {elapsed_ms:.2f}ms (target: < 10ms)"


@pytest.mark.performance
def test_build_file_detection_performance(temp_repo: Path) -> None:
    """Verify BUILD file detection completes within 50ms."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    dir_path = temp_repo / "src"

    # Warm up
    validator.check_build_file(str(dir_path))

    # Measure performance
    start = time.perf_counter()
    result = validator.check_build_file(str(dir_path))
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.found
    assert elapsed_ms < 50, f"BUILD file check took {elapsed_ms:.2f}ms (target: < 50ms)"


@pytest.mark.performance
def test_build_file_detection_with_parent_search_performance(temp_repo: Path) -> None:
    """Verify BUILD file detection with parent search completes within 50ms."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    # Create nested directory without BUILD file
    nested_dir = temp_repo / "src" / "app" / "models"
    nested_dir.mkdir(parents=True)

    # Warm up
    validator.check_build_file(str(nested_dir))

    # Measure performance (should find BUILD in parent)
    start = time.perf_counter()
    result = validator.check_build_file(str(nested_dir))
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.found
    assert result.location is not None
    assert Path(result.location).resolve() == (temp_repo / "src").resolve()
    assert elapsed_ms < 50, f"BUILD file search took {elapsed_ms:.2f}ms (target: < 50ms)"


@pytest.mark.performance
def test_overall_validation_performance(temp_repo: Path) -> None:
    """Verify overall validation completes within 100ms."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    dir_path = temp_repo / "src"

    # Warm up
    validator.validate_path(str(dir_path), scope="directory")

    # Measure performance
    start = time.perf_counter()
    result = validator.validate_path(str(dir_path), scope="directory")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.valid
    assert elapsed_ms < 100, f"Overall validation took {elapsed_ms:.2f}ms (target: < 100ms)"


@pytest.mark.performance
def test_cache_improves_performance(temp_repo: Path) -> None:
    """Verify caching improves BUILD file detection performance."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    dir_path = temp_repo / "src"

    # First call (cache miss)
    start = time.perf_counter()
    result1 = validator.check_build_file(str(dir_path))
    first_call_ms = (time.perf_counter() - start) * 1000

    # Second call (cache hit)
    start = time.perf_counter()
    result2 = validator.check_build_file(str(dir_path))
    second_call_ms = (time.perf_counter() - start) * 1000

    assert result1.found
    assert result2.found
    assert second_call_ms < first_call_ms, "Cached call should be faster"
    assert second_call_ms < 1, f"Cached call took {second_call_ms:.2f}ms (should be < 1ms)"


@pytest.mark.performance
def test_validation_with_disabled_checks_is_fast(temp_repo: Path) -> None:
    """Verify validation with disabled checks is very fast."""
    config = Configuration(enable_path_validation=False, enable_build_file_checking=False)
    validator = PathValidator(config=config, repo_root=temp_repo)

    dir_path = temp_repo / "src"

    # Measure performance
    start = time.perf_counter()
    result = validator.validate_path(str(dir_path), scope="directory")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.valid
    assert elapsed_ms < 1, f"Disabled validation took {elapsed_ms:.2f}ms (should be < 1ms)"


@pytest.mark.performance
def test_multiple_validations_performance(temp_repo: Path) -> None:
    """Verify multiple validations maintain good performance."""
    config = Configuration()
    validator = PathValidator(config=config, repo_root=temp_repo)

    paths = [
        temp_repo / "src",
        temp_repo / "tests",
        temp_repo / "src" / "main.py",
        temp_repo / "tests" / "test_main.py",
    ]

    # Warm up
    for path in paths:
        path_scope: Literal["file", "directory"] = "file" if path.is_file() else "directory"
        validator.validate_path(str(path), scope=path_scope)

    # Measure performance for batch
    start = time.perf_counter()
    for path in paths:
        path_scope = "file" if path.is_file() else "directory"
        result = validator.validate_path(str(path), scope=path_scope)
        assert result.valid
    elapsed_ms = (time.perf_counter() - start) * 1000

    avg_ms = elapsed_ms / len(paths)
    assert avg_ms < 50, f"Average validation took {avg_ms:.2f}ms (target: < 50ms per validation)"
