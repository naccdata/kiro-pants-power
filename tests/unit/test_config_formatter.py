"""Unit tests for configuration formatter."""

import tomllib

from src.formatters.config_formatter import ConfigurationPrettyPrinter
from src.models import Configuration


class TestConfigurationPrettyPrinter:
    """Test suite for ConfigurationPrettyPrinter."""

    def test_format_simple_config(self) -> None:
        """Test formatting a simple configuration."""
        config = Configuration(
            sections={
                "GLOBAL": {
                    "pants_version": "2.18.0",
                    "backend_packages": ["pants.backend.python"]
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify it's valid TOML
        parsed = tomllib.loads(toml_str)
        assert "GLOBAL" in parsed
        assert parsed["GLOBAL"]["pants_version"] == "2.18.0"

    def test_format_config_with_comments(self) -> None:
        """Test formatting preserves comments."""
        config = Configuration(
            sections={
                "GLOBAL": {
                    "pants_version": "2.18.0"
                },
                "python": {
                    "interpreter_constraints": [">=3.12"]
                }
            },
            comments={
                "GLOBAL": "Global configuration",
                "GLOBAL.pants_version": "Version of Pants to use",
                "python": "Python configuration"
            },
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify comments are present
        assert "# Global configuration" in toml_str
        assert "# Version of Pants to use" in toml_str
        assert "# Python configuration" in toml_str
        
        # Verify it's still valid TOML
        # Remove comments for parsing
        lines = [line for line in toml_str.split("\n") if not line.strip().startswith("#")]
        parsed = tomllib.loads("\n".join(lines))
        assert "GLOBAL" in parsed
        assert "python" in parsed

    def test_format_empty_config(self) -> None:
        """Test formatting an empty configuration."""
        config = Configuration(
            sections={},
            comments={},
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Should produce valid (empty) TOML
        parsed = tomllib.loads(toml_str)
        assert len(parsed) == 0

    def test_format_config_with_arrays(self) -> None:
        """Test formatting config with array values."""
        config = Configuration(
            sections={
                "GLOBAL": {
                    "backend_packages": [
                        "pants.backend.python",
                        "pants.backend.python.lint.black",
                        "pants.backend.python.typecheck.mypy"
                    ]
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify it's valid TOML
        parsed = tomllib.loads(toml_str)
        assert len(parsed["GLOBAL"]["backend_packages"]) == 3

    def test_format_config_with_nested_tables(self) -> None:
        """Test formatting config with nested tables."""
        config = Configuration(
            sections={
                "python.resolves": {
                    "python-default": "python-default.lock"
                },
                "python.resolves_to_interpreter_constraints": {
                    "python-default": [">=3.12"]
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify it's valid TOML
        parsed = tomllib.loads(toml_str)
        assert "python.resolves" in parsed
        assert parsed["python.resolves"]["python-default"] == "python-default.lock"

    def test_format_config_with_multiline_comments(self) -> None:
        """Test formatting preserves multiline comments."""
        config = Configuration(
            sections={
                "GLOBAL": {
                    "pants_version": "2.18.0"
                }
            },
            comments={
                "GLOBAL": "Global configuration\nThis section contains global settings"
            },
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify multiline comments are present
        assert "# Global configuration" in toml_str
        assert "# This section contains global settings" in toml_str

    def test_preserve_comments_with_no_comments(self) -> None:
        """Test preserve_comments with empty comments dict."""
        formatter = ConfigurationPrettyPrinter()
        formatted = "[GLOBAL]\npants_version = \"2.18.0\"\n"
        
        result = formatter.preserve_comments(formatted, {})
        
        # Should return unchanged
        assert result == formatted

    def test_format_config_with_boolean_values(self) -> None:
        """Test formatting config with boolean values."""
        config = Configuration(
            sections={
                "anonymous-telemetry": {
                    "enabled": False
                },
                "cli": {
                    "colors": True
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify it's valid TOML
        parsed = tomllib.loads(toml_str)
        assert parsed["anonymous-telemetry"]["enabled"] is False
        assert parsed["cli"]["colors"] is True

    def test_format_config_with_integer_values(self) -> None:
        """Test formatting config with integer values."""
        config = Configuration(
            sections={
                "test": {
                    "timeout_default": 60,
                    "timeout_maximum": 300
                }
            },
            comments={},
            source_file="pants.toml"
        )
        
        formatter = ConfigurationPrettyPrinter()
        toml_str = formatter.format_config(config)
        
        # Verify it's valid TOML
        parsed = tomllib.loads(toml_str)
        assert parsed["test"]["timeout_default"] == 60
        assert parsed["test"]["timeout_maximum"] == 300
