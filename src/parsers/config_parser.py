"""Configuration file parser for Pants TOML files."""

import tomllib
from pathlib import Path

from src.models import Configuration, ConfigValidationError


class ConfigurationParser:
    """Parser for Pants configuration files (pants.toml).

    This parser reads TOML configuration files and converts them into
    structured Configuration objects. It handles syntax errors gracefully
    and provides descriptive error messages with line numbers.
    """

    def parse_config(self, config_path: str) -> Configuration:
        """Parse a Pants configuration file into a Configuration object.

        Args:
            config_path: Path to the pants.toml file

        Returns:
            Configuration object with parsed sections and options

        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the TOML file is invalid, with descriptive error
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            # Extract line number from error message if available
            error_msg = str(e)
            raise ValueError(
                f"Invalid TOML syntax in {config_path}: {error_msg}"
            ) from e

        # Parse comments from the original file
        comments = self._extract_comments(path)

        return Configuration(
            sections=data,
            comments=comments,
            source_file=str(path)
        )

    def _extract_comments(self, config_path: Path) -> dict[str, str]:
        """Extract comments from the TOML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dictionary mapping section/option names to their comments
        """
        comments: dict[str, str] = {}

        try:
            with open(config_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            # If we can't read comments, just return empty dict
            return comments

        current_comment_lines: list[str] = []
        current_section = ""

        for line in lines:
            stripped = line.strip()

            # Track comment lines
            if stripped.startswith("#"):
                current_comment_lines.append(stripped[1:].strip())
            # Section header
            elif stripped.startswith("[") and stripped.endswith("]"):
                section_name = stripped[1:-1].strip()
                current_section = section_name
                if current_comment_lines:
                    comments[section_name] = "\n".join(current_comment_lines)
                    current_comment_lines = []
            # Option line
            elif "=" in stripped and not stripped.startswith("#"):
                option_name = stripped.split("=")[0].strip()
                key = f"{current_section}.{option_name}" if current_section else option_name
                if current_comment_lines:
                    comments[key] = "\n".join(current_comment_lines)
                    current_comment_lines = []
            # Empty line resets comment accumulation
            elif not stripped:
                current_comment_lines = []

        return comments

    def validate_config(self, config: Configuration) -> list[ConfigValidationError]:
        """Validate configuration against known Pants schema.

        This performs basic validation against known Pants configuration
        sections and options. Note: This is a simplified validator and
        doesn't cover all Pants configuration options.

        Args:
            config: Configuration object to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[ConfigValidationError] = []

        # Known Pants configuration sections (not exhaustive)
        known_sections = {
            "GLOBAL",
            "source",
            "python",
            "python-infer",
            "pytest",
            "mypy",
            "coverage-py",
            "test",
            "anonymous-telemetry",
            "cli",
            "stats",
        }

        # Check for unknown sections
        for section in config.sections:
            # Skip subsystem sections (e.g., "python-bootstrap")
            # and backend sections (e.g., "pants.backend.python")
            if "." in section or "-" in section:
                # These are likely valid subsystem or backend configs
                continue

            if section not in known_sections:
                errors.append(
                    ConfigValidationError(
                        section=section,
                        option="",
                        message=f"Unknown configuration section: {section}",
                        line_number=None
                    )
                )

        # Validate specific section options (basic validation)
        if "GLOBAL" in config.sections:
            global_section = config.sections["GLOBAL"]

            # Check for common typos or invalid options
            for option in global_section:
                if option not in {
                    "pants_version",
                    "backend_packages",
                    "plugins",
                    "colors",
                    "level",
                    "show_log_target",
                }:
                    # This is a warning, not necessarily an error
                    # since Pants has many options
                    pass

        return errors
