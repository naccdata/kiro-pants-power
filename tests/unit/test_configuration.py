"""Unit tests for Configuration and ConfigurationManager."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.intent.configuration import Configuration, ConfigurationManager, validate_configuration


class TestConfiguration:
    """Test Configuration data class."""

    def test_default_values(self):
        """Test that Configuration has correct default values."""
        config = Configuration()

        assert config.enable_path_validation is True
        assert config.enable_build_file_checking is True
        assert config.build_file_cache_ttl == 60
        assert config.max_parent_directory_depth == 5
        assert config.enable_error_translation is True
        assert config.custom_translation_rules == []
        assert config.path_validation_timeout == 10
        assert config.build_file_check_timeout == 50
        assert config.log_performance_warnings is True
        assert config.default_scope == "all"
        assert config.default_recursive is True

    def test_from_dict(self):
        """Test creating Configuration from dictionary."""
        data = {
            "enable_path_validation": False,
            "build_file_cache_ttl": 120,
            "default_scope": "directory",
        }
        config = Configuration.from_dict(data)

        assert config.enable_path_validation is False
        assert config.build_file_cache_ttl == 120
        assert config.default_scope == "directory"
        # Other fields should have defaults
        assert config.enable_build_file_checking is True
        assert config.max_parent_directory_depth == 5

    def test_from_dict_filters_invalid_keys(self):
        """Test that from_dict filters out invalid keys."""
        data = {
            "enable_path_validation": False,
            "invalid_key": "should_be_ignored",
            "another_invalid": 123,
        }
        config = Configuration.from_dict(data)

        assert config.enable_path_validation is False
        assert not hasattr(config, "invalid_key")
        assert not hasattr(config, "another_invalid")

    def test_from_file_yaml(self):
        """Test loading Configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "enable_path_validation": False,
                    "build_file_cache_ttl": 90,
                    "max_parent_directory_depth": 10,
                },
                f,
            )
            temp_path = f.name

        try:
            config = Configuration.from_file(temp_path)
            assert config.enable_path_validation is False
            assert config.build_file_cache_ttl == 90
            assert config.max_parent_directory_depth == 10
        finally:
            Path(temp_path).unlink()

    def test_from_file_not_found(self):
        """Test that from_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            Configuration.from_file("/nonexistent/config.yaml")

    def test_from_file_invalid_yaml(self):
        """Test that from_file raises ValueError for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                Configuration.from_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_from_file_empty_yaml(self):
        """Test that from_file handles empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            config = Configuration.from_file(temp_path)
            # Should return config with defaults
            assert config.enable_path_validation is True
            assert config.build_file_cache_ttl == 60
        finally:
            Path(temp_path).unlink()

    def test_from_env_no_env_vars(self):
        """Test from_env with no environment variables set."""
        # Clear any existing env vars
        env_vars = [
            "KIRO_PANTS_VALIDATE_PATHS",
            "KIRO_PANTS_CHECK_BUILD_FILES",
            "KIRO_PANTS_CACHE_TTL",
            "KIRO_PANTS_TRANSLATE_ERRORS",
        ]
        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.pop(var, None)

        try:
            config = Configuration.from_env()
            # Should have defaults
            assert config.enable_path_validation is True
            assert config.enable_build_file_checking is True
            assert config.build_file_cache_ttl == 60
            assert config.enable_error_translation is True
        finally:
            # Restore original values
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_from_env_with_env_vars(self):
        """Test from_env with environment variables set."""
        os.environ["KIRO_PANTS_VALIDATE_PATHS"] = "false"
        os.environ["KIRO_PANTS_CHECK_BUILD_FILES"] = "false"
        os.environ["KIRO_PANTS_CACHE_TTL"] = "120"
        os.environ["KIRO_PANTS_TRANSLATE_ERRORS"] = "false"

        try:
            config = Configuration.from_env()
            assert config.enable_path_validation is False
            assert config.enable_build_file_checking is False
            assert config.build_file_cache_ttl == 120
            assert config.enable_error_translation is False
        finally:
            # Clean up
            for var in [
                "KIRO_PANTS_VALIDATE_PATHS",
                "KIRO_PANTS_CHECK_BUILD_FILES",
                "KIRO_PANTS_CACHE_TTL",
                "KIRO_PANTS_TRANSLATE_ERRORS",
            ]:
                os.environ.pop(var, None)


class TestConfigurationManager:
    """Test ConfigurationManager class."""

    def test_init_no_config_file(self):
        """Test ConfigurationManager initialization without config file."""
        manager = ConfigurationManager()
        config = manager.get_config()

        assert isinstance(config, Configuration)
        assert config.enable_path_validation is True

    def test_init_with_config_file(self):
        """Test ConfigurationManager initialization with config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"enable_path_validation": False, "build_file_cache_ttl": 200}, f)
            temp_path = f.name

        try:
            manager = ConfigurationManager(config_path=temp_path)
            config = manager.get_config()

            assert config.enable_path_validation is False
            assert config.build_file_cache_ttl == 200
        finally:
            Path(temp_path).unlink()

    def test_init_with_nonexistent_file(self):
        """Test ConfigurationManager falls back to defaults for nonexistent file."""
        manager = ConfigurationManager(config_path="/nonexistent/config.yaml")
        config = manager.get_config()

        # Should fall back to defaults
        assert isinstance(config, Configuration)
        assert config.enable_path_validation is True

    def test_env_overrides_file(self):
        """Test that environment variables override file configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"enable_path_validation": True, "build_file_cache_ttl": 60}, f)
            temp_path = f.name

        os.environ["KIRO_PANTS_VALIDATE_PATHS"] = "false"
        os.environ["KIRO_PANTS_CACHE_TTL"] = "300"

        try:
            manager = ConfigurationManager(config_path=temp_path)
            config = manager.get_config()

            # Env vars should override file
            assert config.enable_path_validation is False
            assert config.build_file_cache_ttl == 300
        finally:
            Path(temp_path).unlink()
            os.environ.pop("KIRO_PANTS_VALIDATE_PATHS", None)
            os.environ.pop("KIRO_PANTS_CACHE_TTL", None)

    def test_get_config(self):
        """Test get_config returns current configuration."""
        manager = ConfigurationManager()
        config = manager.get_config()

        assert isinstance(config, Configuration)
        assert config is manager.config

    def test_update_config(self):
        """Test update_config modifies configuration at runtime."""
        manager = ConfigurationManager()
        original_ttl = manager.config.build_file_cache_ttl

        manager.update_config({"build_file_cache_ttl": 999})

        assert manager.config.build_file_cache_ttl == 999
        assert manager.config.build_file_cache_ttl != original_ttl

    def test_update_config_multiple_fields(self):
        """Test update_config with multiple fields."""
        manager = ConfigurationManager()

        manager.update_config(
            {
                "enable_path_validation": False,
                "build_file_cache_ttl": 180,
                "default_scope": "directory",
            }
        )

        assert manager.config.enable_path_validation is False
        assert manager.config.build_file_cache_ttl == 180
        assert manager.config.default_scope == "directory"

    def test_update_config_ignores_invalid_keys(self):
        """Test update_config ignores invalid keys."""
        manager = ConfigurationManager()

        manager.update_config({"invalid_key": "value", "build_file_cache_ttl": 250})

        assert manager.config.build_file_cache_ttl == 250
        assert not hasattr(manager.config, "invalid_key")


class TestValidateConfiguration:
    """Test validate_configuration function."""

    def test_valid_configuration(self):
        """Test that valid configuration returns no errors."""
        config = Configuration()
        errors = validate_configuration(config)

        assert errors == []

    def test_negative_cache_ttl(self):
        """Test validation fails for negative cache TTL."""
        config = Configuration(build_file_cache_ttl=-1)
        errors = validate_configuration(config)

        assert len(errors) == 1
        assert "build_file_cache_ttl must be non-negative" in errors[0]

    def test_max_depth_too_low(self):
        """Test validation fails for max_parent_directory_depth < 1."""
        config = Configuration(max_parent_directory_depth=0)
        errors = validate_configuration(config)

        assert len(errors) == 1
        assert "max_parent_directory_depth must be between 1 and 20" in errors[0]

    def test_max_depth_too_high(self):
        """Test validation fails for max_parent_directory_depth > 20."""
        config = Configuration(max_parent_directory_depth=21)
        errors = validate_configuration(config)

        assert len(errors) == 1
        assert "max_parent_directory_depth must be between 1 and 20" in errors[0]

    def test_path_validation_timeout_too_low(self):
        """Test validation fails for path_validation_timeout < 1ms."""
        config = Configuration(path_validation_timeout=0)
        errors = validate_configuration(config)

        assert len(errors) == 1
        assert "path_validation_timeout must be at least 1ms" in errors[0]

    def test_build_file_check_timeout_too_low(self):
        """Test validation fails for build_file_check_timeout < 1ms."""
        config = Configuration(build_file_check_timeout=0)
        errors = validate_configuration(config)

        assert len(errors) == 1
        assert "build_file_check_timeout must be at least 1ms" in errors[0]

    def test_invalid_default_scope(self):
        """Test validation fails for invalid default_scope."""
        config = Configuration(default_scope="invalid")
        errors = validate_configuration(config)

        assert len(errors) == 1
        assert "default_scope must be one of" in errors[0]
        assert "invalid" in errors[0]

    def test_multiple_validation_errors(self):
        """Test validation returns all errors for multiple violations."""
        config = Configuration(
            build_file_cache_ttl=-5,
            max_parent_directory_depth=25,
            path_validation_timeout=0,
            default_scope="bad_scope",
        )
        errors = validate_configuration(config)

        assert len(errors) == 4
        assert any("build_file_cache_ttl" in e for e in errors)
        assert any("max_parent_directory_depth" in e for e in errors)
        assert any("path_validation_timeout" in e for e in errors)
        assert any("default_scope" in e for e in errors)

    def test_edge_case_valid_values(self):
        """Test validation passes for edge case valid values."""
        config = Configuration(
            build_file_cache_ttl=0,  # Zero is valid (no caching)
            max_parent_directory_depth=1,  # Minimum valid
            path_validation_timeout=1,  # Minimum valid
            build_file_check_timeout=1,  # Minimum valid
        )
        errors = validate_configuration(config)

        assert errors == []

    def test_edge_case_max_depth_20(self):
        """Test validation passes for max_parent_directory_depth=20."""
        config = Configuration(max_parent_directory_depth=20)
        errors = validate_configuration(config)

        assert errors == []
