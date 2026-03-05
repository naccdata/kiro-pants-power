"""Configuration file formatter for Pants TOML files."""


import tomli_w  # type: ignore[import-not-found]

from src.models import Configuration


class ConfigurationPrettyPrinter:
    """Pretty printer for Pants configuration files.

    This formatter converts Configuration objects back into valid TOML
    format, preserving comments and formatting where possible.
    """

    def format_config(self, config: Configuration) -> str:
        """Format a Configuration object back to TOML string.

        Args:
            config: Configuration object to format

        Returns:
            Valid TOML string representation
        """
        # Use tomli_w to generate valid TOML
        toml_str: str = tomli_w.dumps(config.sections)

        # Try to preserve comments if we have them
        if config.comments:
            toml_str = self.preserve_comments(toml_str, config.comments)

        return toml_str

    def preserve_comments(self, formatted: str, comments: dict[str, str]) -> str:
        """Preserve comments from original file in formatted output.

        This method attempts to reinsert comments from the original file
        into the formatted TOML output. Comments are matched by section
        and option names.

        Args:
            formatted: The formatted TOML string without comments
            comments: Dictionary mapping section/option names to comments

        Returns:
            TOML string with comments preserved
        """
        lines = formatted.split("\n")
        result_lines: list[str] = []

        current_section = ""

        for line in lines:
            stripped = line.strip()

            # Check if this is a section header
            if stripped.startswith("[") and stripped.endswith("]"):
                section_name = stripped[1:-1].strip()
                current_section = section_name

                # Add comment before section if it exists
                if section_name in comments:
                    comment_lines = comments[section_name].split("\n")
                    for comment_line in comment_lines:
                        result_lines.append(f"# {comment_line}")

                result_lines.append(line)

            # Check if this is an option line
            elif "=" in stripped and not stripped.startswith("#"):
                option_name = stripped.split("=")[0].strip()
                key = f"{current_section}.{option_name}" if current_section else option_name

                # Add comment before option if it exists
                if key in comments:
                    comment_lines = comments[key].split("\n")
                    for comment_line in comment_lines:
                        result_lines.append(f"# {comment_line}")

                result_lines.append(line)

            # Keep other lines as-is
            else:
                result_lines.append(line)

        return "\n".join(result_lines)
