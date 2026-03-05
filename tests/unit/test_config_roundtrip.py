"""Round-trip tests for configuration parser and formatter."""

import tempfile
from pathlib import Path

from src.formatters.config_formatter import ConfigurationPrettyPrinter
from src.parsers.config_parser import ConfigurationParser


class TestConfigurationRoundTrip:
    """Test suite for configuration round-trip (parse → format → parse)."""

    def test_roundtrip_simple_config(self) -> None:
        """Test round-trip for a simple configuration."""
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
            formatter = ConfigurationPrettyPrinter()

            # Parse original
            config1 = parser.parse_config(config_path)

            # Format to TOML
            toml_str = formatter.format_config(config1)

            # Write formatted TOML to new file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
                f2.write(toml_str)
                config_path2 = f2.name

            try:
                # Parse formatted TOML
                config2 = parser.parse_config(config_path2)

                # Verify sections are equivalent
                assert config1.sections == config2.sections
            finally:
                Path(config_path2).unlink()
        finally:
            Path(config_path).unlink()

    def test_roundtrip_config_with_arrays(self) -> None:
        """Test round-trip for config with array values."""
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
            formatter = ConfigurationPrettyPrinter()

            config1 = parser.parse_config(config_path)
            toml_str = formatter.format_config(config1)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
                f2.write(toml_str)
                config_path2 = f2.name

            try:
                config2 = parser.parse_config(config_path2)
                assert config1.sections == config2.sections
                assert len(config2.sections["GLOBAL"]["backend_packages"]) == 3
            finally:
                Path(config_path2).unlink()
        finally:
            Path(config_path).unlink()

    def test_roundtrip_config_with_nested_tables(self) -> None:
        """Test round-trip for config with nested tables."""
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
            formatter = ConfigurationPrettyPrinter()

            config1 = parser.parse_config(config_path)
            toml_str = formatter.format_config(config1)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
                f2.write(toml_str)
                config_path2 = f2.name

            try:
                config2 = parser.parse_config(config_path2)
                assert config1.sections == config2.sections
            finally:
                Path(config_path2).unlink()
        finally:
            Path(config_path).unlink()

    def test_roundtrip_config_with_boolean_and_integer_values(self) -> None:
        """Test round-trip for config with various value types."""
        config_content = """
[anonymous-telemetry]
enabled = false

[test]
timeout_default = 60
timeout_maximum = 300

[cli]
colors = true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = ConfigurationParser()
            formatter = ConfigurationPrettyPrinter()

            config1 = parser.parse_config(config_path)
            toml_str = formatter.format_config(config1)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
                f2.write(toml_str)
                config_path2 = f2.name

            try:
                config2 = parser.parse_config(config_path2)
                assert config1.sections == config2.sections
                assert config2.sections["anonymous-telemetry"]["enabled"] is False
                assert config2.sections["test"]["timeout_default"] == 60
                assert config2.sections["cli"]["colors"] is True
            finally:
                Path(config_path2).unlink()
        finally:
            Path(config_path).unlink()

    def test_roundtrip_empty_config(self) -> None:
        """Test round-trip for an empty configuration."""
        config_content = ""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = ConfigurationParser()
            formatter = ConfigurationPrettyPrinter()

            config1 = parser.parse_config(config_path)
            toml_str = formatter.format_config(config1)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
                f2.write(toml_str)
                config_path2 = f2.name

            try:
                config2 = parser.parse_config(config_path2)
                assert config1.sections == config2.sections
                assert len(config2.sections) == 0
            finally:
                Path(config_path2).unlink()
        finally:
            Path(config_path).unlink()
