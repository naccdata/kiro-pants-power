"""Integration module for end-to-end intent-based Pants command execution."""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.intent.configuration import Configuration
from src.intent.data_models import IntentContext
from src.intent.error_translator import ErrorTranslator
from src.intent.intent_mapper import IntentError, IntentMapper
from src.intent.path_validator import PathValidator
from src.models import CommandExecutionError, ValidationError

logger = logging.getLogger("kiro.pants.intent")


class MappingError(Exception):
    """Exception raised when intent mapping fails."""

    pass


class PantsExecutionError(Exception):
    """Exception raised when Pants command execution fails.

    Attributes:
        stderr: Standard error output from Pants
        stdout: Standard output from Pants
        exit_code: Exit code from Pants command
    """

    def __init__(self, message: str, stderr: str = "", stdout: str = "", exit_code: int = 1):
        """Initialize with error details.

        Args:
            message: Error message
            stderr: Standard error output
            stdout: Standard output
            exit_code: Exit code from command
        """
        super().__init__(message)
        self.stderr = stderr
        self.stdout = stdout
        self.exit_code = exit_code


@dataclass
class SuccessResponse:
    """Standardized success response.

    Attributes:
        success: Always True for success responses
        output: Command output
        target_spec: Pants target specification that was executed
        additional_options: Additional options that were used
    """

    success: bool = True
    output: str = ""
    target_spec: str = ""
    additional_options: list[str] | None = None


@dataclass
class ErrorResponse:
    """Standardized error response.

    Attributes:
        success: Always False for error responses
        error_type: Type of error (validation, mapping, pants, configuration, internal)
        message: User-friendly error message
        raw_error: Optional original error for debugging
        suggestion: Optional suggested fix
        context: Optional additional context
    """

    success: bool = False
    error_type: str = ""
    message: str = ""
    raw_error: str | None = None
    suggestion: str | None = None
    context: dict[str, Any] | None = None


def sanitize_path(path: str, repo_root: Path) -> Path:
    """Sanitize path to prevent directory traversal attacks.

    Args:
        path: Path to sanitize
        repo_root: Repository root directory

    Returns:
        Sanitized absolute path

    Raises:
        ValidationError: If path escapes repository
    """
    # Resolve to absolute path
    abs_path = (repo_root / path).resolve()

    # Ensure path is within repo
    try:
        abs_path.relative_to(repo_root.resolve())
    except ValueError as e:
        raise ValidationError(f"Path outside repository: {path}") from e

    return abs_path


def sanitize_test_filter(test_filter: str) -> str:
    """Sanitize test filter to prevent command injection.

    Allows only alphanumeric characters, underscores, spaces, parentheses,
    and the logical operators 'and', 'or', 'not'.

    Args:
        test_filter: Test filter pattern to sanitize

    Returns:
        Sanitized test filter

    Raises:
        ValidationError: If test filter contains invalid characters
    """
    # Check for shell metacharacters that could be dangerous
    dangerous_chars = [";", "&", "|", "$", "`", "\\", "<", ">", "!", "#"]
    for char in dangerous_chars:
        if char in test_filter:
            raise ValidationError(
                f"Invalid character in test filter: '{char}'. "
                f"Test filter can only contain alphanumeric characters, "
                f"underscores, spaces, parentheses, and logical operators (and, or, not)."
            )

    # Additional validation: check overall pattern
    # Allow simple patterns and patterns with logical operators
    simple_pattern = r"^[a-zA-Z0-9_\s()]+$"
    complex_pattern = r"^[a-zA-Z0-9_\s()]+(\s+(and|or|not)\s+[a-zA-Z0-9_\s()]+)*$"

    if not (re.match(simple_pattern, test_filter) or re.match(complex_pattern, test_filter)):
        raise ValidationError(
            f"Invalid test filter pattern: {test_filter}. "
            f"Use alphanumeric characters, underscores, and logical operators (and, or, not)."
        )

    return test_filter


def map_intent_to_pants_command(
    scope: Literal["all", "directory", "file"] | None,
    path: str | None,
    recursive: bool | None,
    test_filter: str | None,
    config: Configuration,
    repo_root: Path,
) -> tuple[str, list[str], IntentContext]:
    """Map user intent to Pants command specification.

    This is the main integration function that combines Intent_Mapper,
    Path_Validator, and Configuration to produce a complete Pants command.

    Args:
        scope: What to test (all, directory, file)
        path: Optional path to directory or file
        recursive: Whether to include subdirectories
        test_filter: Optional test name pattern filter
        config: Configuration instance
        repo_root: Repository root directory

    Returns:
        Tuple of (target_spec, additional_options, intent_context)

    Raises:
        ValidationError: If path validation fails or security checks fail
        IntentError: If intent parameters are invalid
        MappingError: If intent mapping fails
    """
    try:
        # Security: Sanitize inputs
        if path is not None:
            sanitize_path(path, repo_root)

        if test_filter is not None:
            test_filter = sanitize_test_filter(test_filter)

        # Initialize components
        validator = PathValidator(config, repo_root)
        mapper = IntentMapper(config, validator)

        # Map intent to Pants command
        # Cast scope to proper type if provided
        scope_value: Literal["all", "directory", "file"] = scope or "all"
        result = mapper.map_intent(
            scope=scope_value,
            path=path,
            recursive=recursive if recursive is not None else True,
            test_filter=test_filter,
        )

        # Create intent context for error translation
        intent_context = IntentContext(
            scope=result.resolved_intent.scope,  # type: ignore[arg-type]
            path=result.resolved_intent.path,
            recursive=result.resolved_intent.recursive,
            test_filter=result.resolved_intent.test_filter,
        )

        return result.target_spec, result.additional_options, intent_context

    except ValidationError:
        # Re-raise validation errors as-is
        raise
    except IntentError:
        # Re-raise intent errors as-is
        raise
    except Exception as e:
        # Wrap unexpected errors as mapping errors
        logger.exception("Unexpected error during intent mapping")
        raise MappingError(f"Failed to map intent to Pants command: {e}") from e


def execute_with_error_handling(
    scope: Literal["all", "directory", "file"] | None,
    path: str | None,
    recursive: bool | None,
    test_filter: str | None,
    config: Configuration,
    repo_root: Path,
    pants_executor: Callable[[str, str, list[str]], Any],
    command: str = "test",
) -> SuccessResponse | ErrorResponse:
    """Execute Pants command with comprehensive error handling.

    This function wraps the entire flow: intent mapping, Pants execution,
    and error translation.

    Args:
        scope: What to test (all, directory, file)
        path: Optional path to directory or file
        recursive: Whether to include subdirectories
        test_filter: Optional test name pattern filter
        config: Configuration instance
        repo_root: Repository root directory
        pants_executor: Callable that executes Pants commands
        command: Pants command to execute (default: "test")

    Returns:
        SuccessResponse or ErrorResponse
    """
    try:
        # Step 1: Map intent to Pants command
        target_spec, additional_options, intent_context = map_intent_to_pants_command(
            scope=scope,
            path=path,
            recursive=recursive,
            test_filter=test_filter,
            config=config,
            repo_root=repo_root,
        )

        # Step 2: Execute Pants command
        try:
            result = pants_executor(command, target_spec, additional_options)

            # Check if result indicates success
            if (hasattr(result, "success") and result.success) or (
                hasattr(result, "exit_code") and result.exit_code == 0
            ):
                output = result.stdout if hasattr(result, "stdout") else str(result)
                return SuccessResponse(
                    success=True,
                    output=output,
                    target_spec=target_spec,
                    additional_options=additional_options,
                )
            else:
                # Command executed but failed
                stderr = result.stderr if hasattr(result, "stderr") else ""
                raise PantsExecutionError(
                    "Pants command failed",
                    stderr=stderr,
                    stdout=result.stdout if hasattr(result, "stdout") else "",
                    exit_code=result.exit_code if hasattr(result, "exit_code") else 1,
                )

        except (CommandExecutionError, PantsExecutionError) as e:
            # Pants execution failed - translate error
            error_translator = ErrorTranslator(config)
            stderr = e.stderr if hasattr(e, "stderr") else str(e)
            stdout = e.stdout if hasattr(e, "stdout") else ""
            
            # Combine stdout and stderr for full error context
            # Pants writes detailed output (test failures, stack traces) to stdout
            full_error = f"{stdout}\n{stderr}".strip() if stdout else stderr
            
            translated = error_translator.translate_error(full_error, intent_context)

            return ErrorResponse(
                success=False,
                error_type="pants",
                message=translated.message,
                raw_error=translated.raw_error,
                suggestion=translated.suggestion,
                context={"target_spec": target_spec, "command": command},
            )

    except ValidationError as e:
        # Path validation failed
        return ErrorResponse(
            success=False,
            error_type="validation",
            message=str(e),
            suggestion=getattr(e, "suggestion", None),
            context={"scope": scope, "path": path},
        )

    except IntentError as e:
        # Intent parameters invalid
        return ErrorResponse(
            success=False,
            error_type="mapping",
            message=str(e),
            context={"scope": scope, "path": path, "recursive": recursive},
        )

    except MappingError as e:
        # Intent mapping failed
        return ErrorResponse(
            success=False,
            error_type="mapping",
            message=str(e),
            context={"scope": scope, "path": path, "recursive": recursive},
        )

    except Exception as e:
        # Unexpected error
        logger.exception("Unexpected error in intent execution")
        return ErrorResponse(
            success=False,
            error_type="internal",
            message="An unexpected error occurred",
            raw_error=str(e),
        )
