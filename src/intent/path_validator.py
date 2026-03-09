"""Path validator for validating file and directory paths."""

import logging
import time
from pathlib import Path
from typing import Literal

from src.intent.configuration import Configuration
from src.intent.data_models import BuildFileResult, CachedBuildFileResult, ValidationResult

logger = logging.getLogger("kiro.pants.intent")

# Module-level cache for BUILD file detection
_build_file_cache: dict[str, CachedBuildFileResult] = {}


class PathValidator:
    """Validates paths and BUILD file presence before execution.

    Attributes:
        config: Configuration for validation behavior
        repo_root: Repository root directory
    """

    def __init__(self, config: Configuration, repo_root: Path):
        """Initialize with configuration and repository root.

        Args:
            config: Configuration instance
            repo_root: Path to repository root
        """
        self.config = config
        self.repo_root = repo_root

    def validate_path(
        self,
        path: str,
        scope: Literal["all", "directory", "file"],
    ) -> ValidationResult:
        """Validate path exists and is appropriate for scope.

        Args:
            path: Path to validate
            scope: The scope (all, directory, file)

        Returns:
            ValidationResult with success status and error message if failed
        """
        start_time = time.perf_counter()

        # Skip validation if disabled
        if not self.config.enable_path_validation:
            return ValidationResult(valid=True)

        # Validate based on scope
        if scope == "all":
            result = ValidationResult(valid=True)
        elif scope == "file":
            result = self._validate_file(path)
        elif scope == "directory":
            result = self._validate_directory(path)
        else:
            result = ValidationResult(valid=False, error=f"Unknown scope: {scope}")

        # Check timing
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if self.config.log_performance_warnings:
            if scope == "file" and elapsed_ms > self.config.path_validation_timeout:
                logger.warning(
                    "File validation took %.2fms (threshold: %dms)",
                    elapsed_ms,
                    self.config.path_validation_timeout,
                )
            elif scope == "directory" and elapsed_ms > self.config.build_file_check_timeout:
                logger.warning(
                    "Directory validation took %.2fms (threshold: %dms)",
                    elapsed_ms,
                    self.config.build_file_check_timeout,
                )

        return result

    def _file_exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.repo_root / path
        return file_path.exists() and file_path.is_file()

    def _directory_exists(self, path: str) -> bool:
        """Check if directory exists.

        Args:
            path: Directory path to check

        Returns:
            True if directory exists, False otherwise
        """
        dir_path = self.repo_root / path
        return dir_path.exists() and dir_path.is_dir()

    def _validate_file(self, path: str) -> ValidationResult:
        """Validate file exists.

        Args:
            path: File path to validate

        Returns:
            ValidationResult
        """
        file_path = self.repo_root / path
        if not file_path.exists():
            return ValidationResult(valid=False, error=f"Path does not exist: {path}")
        if not file_path.is_file():
            return ValidationResult(valid=False, error=f"Path is not a file: {path}")
        return ValidationResult(valid=True)

    def _validate_directory(self, path: str) -> ValidationResult:
        """Validate directory exists and has BUILD file.

        Args:
            path: Directory path to validate

        Returns:
            ValidationResult
        """
        dir_path = self.repo_root / path

        # Check directory exists
        if not dir_path.exists():
            return ValidationResult(valid=False, error=f"Path does not exist: {path}")
        if not dir_path.is_dir():
            return ValidationResult(valid=False, error=f"Path is not a directory: {path}")

        # Check BUILD file if enabled
        if self.config.enable_build_file_checking:
            build_result = self.check_build_file(path)
            if not build_result.found:
                return ValidationResult(
                    valid=False,
                    error=f"No BUILD file found for {path}. "
                    "Run 'pants tailor' to generate BUILD files",
                    suggestion="pants tailor",
                )

        return ValidationResult(valid=True)

    def check_build_file(self, directory: str) -> BuildFileResult:
        """Check if BUILD file exists in directory or parent directories.

        Args:
            directory: Directory path to check

        Returns:
            BuildFileResult indicating presence and location of BUILD file
        """
        cache_key = str((self.repo_root / directory).resolve())
        current_time = time.time()

        # Check cache
        if cache_key in _build_file_cache:
            cached = _build_file_cache[cache_key]
            age = current_time - cached.timestamp
            if age < self.config.build_file_cache_ttl:
                return cached.result

        # Perform fresh search
        result = self._search_build_file(directory)

        # Cache result
        _build_file_cache[cache_key] = CachedBuildFileResult(
            result=result,
            timestamp=current_time,
        )

        return result

    def _search_build_file(self, directory: str) -> BuildFileResult:
        """Search for BUILD file in directory and parents.

        Args:
            directory: Directory to start search from

        Returns:
            BuildFileResult
        """
        current = (self.repo_root / directory).resolve()

        for _ in range(self.config.max_parent_directory_depth):
            # Check for BUILD files
            for build_name in ["BUILD", "BUILD.pants", "BUILD.bazel"]:
                build_path = current / build_name
                if build_path.exists():
                    return BuildFileResult(found=True, location=str(current))

            # Stop at repo root
            if current == self.repo_root.resolve():
                break

            # Move to parent
            current = current.parent

        return BuildFileResult(found=False)

    def clear_cache(self) -> None:
        """Clear the BUILD file detection cache."""
        global _build_file_cache
        _build_file_cache.clear()
        logger.info("BUILD file cache cleared")

    def validate_path_with_timing(
        self,
        path: str,
        scope: Literal["all", "directory", "file"],
    ) -> tuple[ValidationResult, float]:
        """Validate path with performance tracking.

        Args:
            path: Path to validate
            scope: The scope (all, directory, file)

        Returns:
            Tuple of (ValidationResult, elapsed_time_ms)
        """
        start_time = time.perf_counter()
        result = self.validate_path(path, scope)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return result, elapsed_ms

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics
        """
        if not _build_file_cache:
            return {
                "size": 0,
                "oldest_entry": None,
                "newest_entry": None,
            }

        timestamps = [cached.timestamp for cached in _build_file_cache.values()]
        return {
            "size": len(_build_file_cache),
            "oldest_entry": min(timestamps),
            "newest_entry": max(timestamps),
        }


def clear_build_file_cache() -> None:
    """Clear the global BUILD file cache.

    This is useful after running 'pants tailor' to regenerate BUILD files.
    """
    global _build_file_cache
    _build_file_cache.clear()
    logger.info("BUILD file cache cleared")


def get_build_file_cache_stats() -> dict:
    """Get global BUILD file cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    if not _build_file_cache:
        return {
            "size": 0,
            "oldest_entry": None,
            "newest_entry": None,
        }

    timestamps = [cached.timestamp for cached in _build_file_cache.values()]
    return {
        "size": len(_build_file_cache),
        "oldest_entry": min(timestamps),
        "newest_entry": max(timestamps),
    }
