"""Intent mapper for translating user intents to Pants target specifications."""

import logging
from typing import Literal

from src.intent.configuration import Configuration
from src.intent.data_models import MappingResult, ResolvedIntent
from src.intent.path_validator import PathValidator
from src.models import ValidationError

logger = logging.getLogger("kiro.pants.intent")


class IntentError(Exception):
    """Base exception for intent-related errors."""

    pass


class IntentMapper:
    """Translates user intents into Pants target specifications.

    Attributes:
        config: Configuration for intent mapping behavior
        validator: Path validator for validating paths before mapping
    """

    def __init__(self, config: Configuration, validator: PathValidator):
        """Initialize with configuration and path validator.

        Args:
            config: Configuration instance
            validator: PathValidator instance
        """
        self.config = config
        self.validator = validator

    def map_intent(
        self,
        scope: Literal["all", "directory", "file"],
        path: str | None = None,
        recursive: bool = True,
        test_filter: str | None = None,
    ) -> MappingResult:
        """Map user intent to Pants target specification.

        Args:
            scope: What to test (all, directory, file)
            path: Optional path to directory or file
            recursive: Whether to include subdirectories (for directory scope)
            test_filter: Optional test name pattern filter

        Returns:
            MappingResult containing target spec and additional options

        Raises:
            ValidationError: If path validation fails
            IntentError: If intent parameters are invalid
        """
        # Step 1: Resolve intent with defaults
        resolved = self.resolve_defaults(scope, path, recursive, test_filter)

        # Step 2: Validate path if enabled
        if self.config.enable_path_validation and resolved.path is not None:
            # Cast scope to Literal type for validation
            scope_literal: Literal["all", "directory", "file"] = resolved.scope  # type: ignore[assignment]
            validation_result = self.validator.validate_path(resolved.path, scope_literal)
            if not validation_result.valid:
                raise ValidationError(validation_result.error or "Path validation failed")

        # Step 3: Map to target spec
        target_spec = self._map_scope_to_target(
            resolved.scope,
            resolved.path,
            resolved.recursive,
        )

        # Step 4: Add test filter options
        additional_options = self._add_test_filter([], resolved.test_filter)

        # Step 5: Log the mapping
        logger.info(
            "Intent mapped: scope=%s, path=%s, recursive=%s, target_spec=%s",
            resolved.scope,
            resolved.path,
            resolved.recursive,
            target_spec,
        )

        return MappingResult(
            target_spec=target_spec,
            additional_options=additional_options,
            resolved_intent=resolved,
        )

    def resolve_defaults(
        self,
        scope: str | None,
        path: str | None,
        recursive: bool | None,
        test_filter: str | None = None,
    ) -> ResolvedIntent:
        """Apply smart defaults to incomplete intent parameters.

        Args:
            scope: Optional scope value
            path: Optional path value
            recursive: Optional recursive flag
            test_filter: Optional test filter

        Returns:
            ResolvedIntent with all parameters filled in

        Raises:
            IntentError: If intent parameters are invalid
        """
        defaults_applied: dict[str, str | bool] = {}

        # Apply scope default
        if scope is None:
            scope = self.config.default_scope
            defaults_applied["scope"] = self.config.default_scope

        # Validate and apply path defaults
        if scope == "file" and path is None:
            raise IntentError("scope='file' requires a path parameter")

        if scope == "directory" and path is None:
            path = "."
            defaults_applied["path"] = "."

        if scope == "all" and path is not None:
            logger.warning("scope='all' ignores path parameter: %s", path)
            path = None

        # Apply recursive default
        if recursive is None:
            recursive = self.config.default_recursive
            defaults_applied["recursive"] = self.config.default_recursive

        return ResolvedIntent(
            scope=scope,
            path=path,
            recursive=recursive,
            test_filter=test_filter,
            defaults_applied=defaults_applied,
        )

    def _map_scope_to_target(self, scope: str, path: str | None, recursive: bool) -> str:
        """Map scope to Pants target specification.

        Args:
            scope: The scope (all, directory, file)
            path: Optional path
            recursive: Whether to include subdirectories

        Returns:
            Pants target specification string

        Raises:
            IntentError: If scope is unknown
        """
        if scope == "all":
            return "::"

        if scope == "directory":
            if not path or path == ".":
                return "::"
            suffix = "::" if recursive else ":"
            return f"{path.rstrip('/')}{suffix}"

        if scope == "file":
            return path or ""

        raise IntentError(f"Unknown scope: {scope}")

    def _add_test_filter(
        self,
        base_options: list[str],
        test_filter: str | None,
    ) -> list[str]:
        """Add pytest-style test filtering to Pants command.

        Args:
            base_options: Base list of options
            test_filter: Optional test filter pattern

        Returns:
            Updated list of options with test filter added
        """
        if test_filter:
            return [*base_options, "-k", test_filter]
        return base_options
