"""Unit tests for configuration parser."""

import tempfile
from pathlib import Path

import pytest

from src.models import Configuration, ConfigValidationError
from src.parsers.config_parser import ConfigurationParser


class TestConfigurationParser:
    """Test suite for ConfigurationParser."""

    def test_parse_valid_config(self) -> None:
        """Test parsing a valid pants.toml file."""
        config_content = """
[GLOBAL]
pants_version = "2.18.0"
backend_packages = ["pants.backend.python"]

[python]
interpreter_constraints = [">=3.12"]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            parser = ConfigurationParser()
            config = parser.parse_config(config_path)
            
            assert isinstance(config, Configuration)
            assert "GLOBAL" in config.sections
            assert "python" in config.sections
            assert config.sections["GLOBAL"]["pants_version"] == "2.18.0"
            assert config.sections["python"]["interpreter_constraints"] == [">=3.12"]
            assert config.source_file == config_path
        finally:
            Path(config_path).unlink()

    def test_parse_config_with_comments(self) -> None:
        """Test parsing a config file with comments."""
        config_content = """
# Global configuration
[GLOBAL]
# Version of Pants to use
pants_version = "2.18.0"

# Python configuration
[python]
interpreter_constraints = [">=3.12"]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            parser = ConfigurationParser()
            config = parser.parse_config(config_path)
            
            assert "GLOBAL" in config.comments
            assert "Global configuration" in config.comments["GLOBAL"]
            assert "GLOBAL.pants_version" in config.comments
            assert "Version of Pants to use" in config.comments["GLOBAL.pants_version"]
        finally:
            Path(config_path).unlink()

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing a file that doesn't exist."""
        parser = ConfigurationParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_config("/nonexistent/path/pants.toml")

    def test_parse_invalid_toml(self) -> None:
        """Test parsing invalid TOML syntax."""
        config_content = """
[GLOBAL
pants_version = "2.18.0"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            parser = ConfigurationParser()
            
            with pytest.raises(ValueError) as exc_info:
                parser.parse_config(config_path)
            
            assert "Invalid TOML syntax" in str(exc_info.value)
        finally:
            Path(config_path).unlink()

    def test_parse_empty_config(self) -> None:
        """Test parsing an empty config file."""
        config_content = ""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            parser = ConfigurationParser()
            config = parser.parse_config(config_path)
            
            assert isinstance(config, Configuration)
            assert len(config.sections) == 0
        finally:
            Path(config_path).unlink()

    def test_validate_valid_config(self) -> None:
        """Test validation of a valid configuration."""
        config = Configuration(
            sections={
                "GLOBAL": {
                    "pants_version": "2.18.0",
                    "backend_packages": ["pants.backend.python"]
                },
                "python": {
                    "interpreter_constraints": [">=3.12"]
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        parser = ConfigurationParser()
        errors = parser.validate_config(config)
        
        # Should have no errors for known sections
        assert len(errors) == 0

    def test_validate_unknown_section(self) -> None:
        """Test validation detects unknown sections."""
        config = Configuration(
            sections={
                "UNKNOWN_SECTION": {
                    "some_option": "value"
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        parser = ConfigurationParser()
        errors = parser.validate_config(config)
        
        # Should detect unknown section
        assert len(errors) > 0
        assert any("UNKNOWN_SECTION" in error.section for error in errors)

    def test_validate_subsystem_sections(self) -> None:
        """Test validation allows subsystem sections with dots or dashes."""
        config = Configuration(
            sections={
                "python-bootstrap": {
                    "search_path": ["<PATH>"]
                },
                "pants.backend.python": {
                    "enabled": True
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        parser = ConfigurationParser()
        errors = parser.validate_config(config)
        
        # Should not flag subsystem sections as errors
        assert len(errors) == 0

    def test_parse_multiline_values(self) -> None:
        """Test parsing config with multiline array values."""
        config_content = """
[GLOBAL]
backend_packages = [
    "pants.backend.python",
    "pants.backend.python.lint.black",
    "pants.backend.python.typecheck.mypy",
]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            parser = ConfigurationParser()
            config = parser.parse_config(config_path)
            
            assert len(config.sections["GLOBAL"]["backend_packages"]) == 3
            assert "pants.backend.python" in config.sections["GLOBAL"]["backend_packages"]
        finally:
            Path(config_path).unlink()

    def test_parse_nested_tables(self) -> None:
        """Test parsing config with nested tables."""
        config_content = """
[python.resolves]
python-default = "python-default.lock"

[python.resolves_to_interpreter_constraints]
python-default = [">=3.12"]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            parser = ConfigurationParser()
            config = parser.parse_config(config_path)
            
            # TOML parses [python.resolves] as nested dict under python
            assert "python" in config.sections
            assert "resolves" in config.sections["python"]
            assert config.sections["python"]["resolves"]["python-default"] == "python-default.lock"
        finally:
            Path(config_path).unlink()
