"""Configuration management for the intent-based API layer."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from src.intent.data_models import TranslationRule


@dataclass
class Configuration:
    """Configuration for intent-based API behavior.

    Attributes:
        enable_path_validation: Whether to validate paths before execution
        enable_build_file_checking: Whether to check for BUILD files
        build_file_cache_ttl: Cache TTL in seconds for BUILD file detection
        max_parent_directory_depth: Max parent directories to search for BUILD files
        enable_error_translation: Whether to translate Pants errors
        custom_translation_rules: Custom error translation rules
        path_validation_timeout: Timeout in milliseconds for path validation
        build_file_check_timeout: Timeout in milliseconds for BUILD file checks
        log_performance_warnings: Whether to log performance warnings
        default_scope: Default scope when not specified
        default_recursive: Default recursive flag when not specified
    """

    enable_path_validation: bool = True
    enable_build_file_checking: bool = True
    build_file_cache_ttl: int = 60
    max_parent_directory_depth: int = 5
    enable_error_translation: bool = True
    custom_translation_rules: list[TranslationRule] = field(default_factory=list)
    path_validation_timeout: int = 10
    build_file_check_timeout: int = 50
    log_performance_warnings: bool = True
    default_scope: str = "all"
    default_recursive: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "Configuration":
        """Create configuration from dictionary.

        Args:
            data: Dictionary with configuration values

        Returns:
            Configuration instance
        """
        # Filter out keys that aren't valid Configuration fields
        valid_keys = {
            "enable_path_validation",
            "enable_build_file_checking",
            "build_file_cache_ttl",
            "max_parent_directory_depth",
            "enable_error_translation",
            "custom_translation_rules",
            "path_validation_timeout",
            "build_file_check_timeout",
            "log_performance_warnings",
            "default_scope",
            "default_recursive",
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    @classmethod
    def from_file(cls, path: str) -> "Configuration":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Configuration instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
                if data is None:
                    data = {}
                return cls.from_dict(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}") from e

    @classmethod
    def from_env(cls) -> "Configuration":
        """Create configuration from environment variables.

        Environment variables:
            KIRO_PANTS_VALIDATE_PATHS: Enable/disable path validation
            KIRO_PANTS_CHECK_BUILD_FILES: Enable/disable BUILD file checking
            KIRO_PANTS_CACHE_TTL: Cache TTL in seconds
            KIRO_PANTS_TRANSLATE_ERRORS: Enable/disable error translation

        Returns:
            Configuration instance with values from environment
        """
        config = cls()

        if "KIRO_PANTS_VALIDATE_PATHS" in os.environ:
            config.enable_path_validation = (
                os.environ["KIRO_PANTS_VALIDATE_PATHS"].lower() == "true"
            )

        if "KIRO_PANTS_CHECK_BUILD_FILES" in os.environ:
            config.enable_build_file_checking = (
                os.environ["KIRO_PANTS_CHECK_BUILD_FILES"].lower() == "true"
            )

        if "KIRO_PANTS_CACHE_TTL" in os.environ:
            config.build_file_cache_ttl = int(os.environ["KIRO_PANTS_CACHE_TTL"])

        if "KIRO_PANTS_TRANSLATE_ERRORS" in os.environ:
            config.enable_error_translation = (
                os.environ["KIRO_PANTS_TRANSLATE_ERRORS"].lower() == "true"
            )

        return config


class ConfigurationManager:
    """Manages configuration for the intent-based API layer.

    Attributes:
        config: Current configuration instance
    """

    def __init__(self, config_path: str | None = None):
        """Initialize with optional config file path.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = self._load_config(config_path)

    def _load_config(self, path: str | None) -> Configuration:
        """Load configuration from file or use defaults.

        Args:
            path: Optional path to configuration file

        Returns:
            Configuration instance
        """
        # Start with environment variables
        config = Configuration.from_env()

        # Override with file if provided
        if path and Path(path).exists():
            try:
                file_config = Configuration.from_file(path)
                # Merge file config with env config (env takes precedence)
                env_overrides: dict[str, bool | int] = {}
                if "KIRO_PANTS_VALIDATE_PATHS" in os.environ:
                    env_overrides["enable_path_validation"] = config.enable_path_validation
                if "KIRO_PANTS_CHECK_BUILD_FILES" in os.environ:
                    env_overrides["enable_build_file_checking"] = config.enable_build_file_checking
                if "KIRO_PANTS_CACHE_TTL" in os.environ:
                    env_overrides["build_file_cache_ttl"] = config.build_file_cache_ttl
                if "KIRO_PANTS_TRANSLATE_ERRORS" in os.environ:
                    env_overrides["enable_error_translation"] = config.enable_error_translation

                # Apply file config first, then env overrides
                for key, value in env_overrides.items():
                    setattr(file_config, key, value)
                return file_config
            except (FileNotFoundError, ValueError):
                # Fall back to env config if file loading fails
                pass

        return config

    def get_config(self) -> Configuration:
        """Get current configuration.

        Returns:
            Current configuration instance
        """
        return self.config

    def update_config(self, updates: dict) -> None:
        """Update configuration at runtime.

        Args:
            updates: Dictionary of configuration updates
        """
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


def validate_configuration(config: Configuration) -> list[str]:
    """Validate configuration constraints.

    Args:
        config: Configuration instance to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Validate cache TTL is non-negative
    if config.build_file_cache_ttl < 0:
        errors.append(
            f"build_file_cache_ttl must be non-negative, got {config.build_file_cache_ttl}"
        )

    # Validate max_parent_directory_depth is between 1 and 20
    if config.max_parent_directory_depth < 1 or config.max_parent_directory_depth > 20:
        errors.append(
            f"max_parent_directory_depth must be between 1 and 20, "
            f"got {config.max_parent_directory_depth}"
        )

    # Validate timeout values are at least 1ms
    if config.path_validation_timeout < 1:
        errors.append(
            f"path_validation_timeout must be at least 1ms, got {config.path_validation_timeout}"
        )

    if config.build_file_check_timeout < 1:
        errors.append(
            f"build_file_check_timeout must be at least 1ms, got {config.build_file_check_timeout}"
        )

    # Validate default_scope is valid
    valid_scopes = {"all", "directory", "file"}
    if config.default_scope not in valid_scopes:
        errors.append(f"default_scope must be one of {valid_scopes}, got '{config.default_scope}'")

    return errors
