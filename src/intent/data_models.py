"""Data models for the intent-based API layer."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class IntentContext:
    """User's original intent parameters.

    Attributes:
        scope: What to test (all, directory, file)
        path: Optional path to directory or file
        recursive: Whether to include subdirectories
        test_filter: Optional test name pattern filter
    """

    scope: Literal["all", "directory", "file"]
    path: str | None
    recursive: bool
    test_filter: str | None


@dataclass
class ResolvedIntent:
    """Intent after applying defaults.

    Attributes:
        scope: Resolved scope value
        path: Resolved path value
        recursive: Resolved recursive flag
        test_filter: Resolved test filter
        defaults_applied: Dictionary of which defaults were used
    """

    scope: str
    path: str | None
    recursive: bool
    test_filter: str | None
    defaults_applied: dict[str, str | bool]


@dataclass
class MappingResult:
    """Result of intent-to-target mapping.

    Attributes:
        target_spec: Pants target specification
        additional_options: Additional Pants CLI options
        resolved_intent: The resolved intent with defaults applied
    """

    target_spec: str
    additional_options: list[str]
    resolved_intent: ResolvedIntent


@dataclass
class ValidationResult:
    """Result of path validation.

    Attributes:
        valid: Whether the path is valid
        error: Optional error message if validation failed
        suggestion: Optional suggested command to fix the issue
        warnings: Optional list of warning messages
    """

    valid: bool
    error: str | None = None
    suggestion: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class BuildFileResult:
    """Result of BUILD file detection.

    Attributes:
        found: Whether a BUILD file was found
        location: Optional directory where BUILD file was found
        timestamp: Timestamp for caching purposes
    """

    found: bool
    location: str | None = None
    timestamp: float = 0.0


@dataclass
class CachedBuildFileResult:
    """Cached BUILD file detection result.

    Attributes:
        result: The BUILD file detection result
        timestamp: When this result was cached
    """

    result: BuildFileResult
    timestamp: float


@dataclass
class TranslatedError:
    """Translated error message.

    Attributes:
        message: User-friendly error message
        raw_error: Original Pants error
        rule_applied: Pattern of rule that matched
        suggestion: Optional suggested fix
    """

    message: str
    raw_error: str
    rule_applied: str | None
    suggestion: str | None = None


@dataclass
class TranslationRule:
    """Rule for translating Pants errors.

    Attributes:
        pattern: Regex pattern to match in Pants error
        template: Message template for user-friendly message
        priority: Higher priority rules checked first
    """

    pattern: str
    template: str
    priority: int = 5

    def matches(self, error: str) -> bool:
        """Check if this rule matches the error.

        Args:
            error: The error message to check

        Returns:
            True if the pattern matches the error
        """
        import re

        return re.search(self.pattern, error) is not None

    def apply(self, error: str, context: IntentContext) -> str:
        """Apply translation using template and context.

        Args:
            error: The error message to translate
            context: The intent context for variable substitution

        Returns:
            The translated error message
        """
        import re

        match = re.search(self.pattern, error)
        if not match:
            return self.template

        return self.template.format(
            scope=context.scope,
            path=context.path or "repository",
            **match.groupdict(),
        )
