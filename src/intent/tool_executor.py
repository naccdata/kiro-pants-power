"""Tool executor with intent-based API and backward compatibility."""

import logging
from pathlib import Path
from typing import Any

from src.intent.configuration import Configuration
from src.intent.integration import (
    ErrorResponse,
    SuccessResponse,
    execute_with_error_handling,
)
from src.models import CommandResult
from src.pants_commands import PantsCommands

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes Pants commands with intent-based API and backward compatibility."""

    def __init__(
        self,
        pants_commands: PantsCommands,
        config: Configuration | None = None,
        repo_root: Path | None = None,
    ):
        """
        Initialize tool executor.

        Args:
            pants_commands: PantsCommands instance for executing Pants operations
            config: Configuration instance (creates default if None)
            repo_root: Repository root directory (uses cwd if None)
        """
        self.pants_commands = pants_commands
        self.config = config or Configuration()
        self.repo_root = repo_root or Path.cwd()

    def execute_pants_test(self, arguments: dict[str, Any]) -> CommandResult:
        """
        Execute pants_test with intent-based or legacy parameters.

        Args:
            arguments: Tool arguments (intent-based or legacy)

        Returns:
            CommandResult from Pants execution
        """
        return self._execute_with_intent_or_legacy("test", arguments, supports_test_filter=True)

    def execute_pants_lint(self, arguments: dict[str, Any]) -> CommandResult:
        """
        Execute pants_lint with intent-based or legacy parameters.

        Args:
            arguments: Tool arguments (intent-based or legacy)

        Returns:
            CommandResult from Pants execution
        """
        return self._execute_with_intent_or_legacy("lint", arguments)

    def execute_pants_check(self, arguments: dict[str, Any]) -> CommandResult:
        """
        Execute pants_check with intent-based or legacy parameters.

        Args:
            arguments: Tool arguments (intent-based or legacy)

        Returns:
            CommandResult from Pants execution
        """
        return self._execute_with_intent_or_legacy("check", arguments)

    def execute_pants_fix(self, arguments: dict[str, Any]) -> CommandResult:
        """
        Execute pants_fix with intent-based or legacy parameters.

        Args:
            arguments: Tool arguments (intent-based or legacy)

        Returns:
            CommandResult from Pants execution
        """
        return self._execute_with_intent_or_legacy("fix", arguments)

    def execute_pants_package(self, arguments: dict[str, Any]) -> CommandResult:
        """
        Execute pants_package with intent-based or legacy parameters.

        Args:
            arguments: Tool arguments (intent-based or legacy)

        Returns:
            CommandResult from Pants execution
        """
        return self._execute_with_intent_or_legacy("package", arguments)

    def _execute_with_intent_or_legacy(
        self,
        command: str,
        arguments: dict[str, Any],
        supports_test_filter: bool = False,
    ) -> CommandResult:
        """
        Execute Pants command with intent-based or legacy mode.

        Args:
            command: Pants command name (test, lint, check, fix, package)
            arguments: Tool arguments
            supports_test_filter: Whether command supports test_filter parameter

        Returns:
            CommandResult from Pants execution
        """
        # Check if using legacy mode (target parameter provided and not None)
        if "target" in arguments:
            return self._execute_legacy_mode(command, arguments)

        # Use intent-based mode
        return self._execute_intent_mode(command, arguments, supports_test_filter)

    def _execute_legacy_mode(self, command: str, arguments: dict[str, Any]) -> CommandResult:
        """
        Execute Pants command in legacy mode using target parameter.

        Args:
            command: Pants command name
            arguments: Tool arguments with 'target' parameter

        Returns:
            CommandResult from Pants execution
        """
        target = arguments.get("target")

        # Log deprecation warning
        logger.warning(
            f"Using deprecated 'target' parameter for pants_{command}. "
            "Consider using intent-based parameters (scope/path/recursive) instead."
        )

        # Execute using legacy method
        if command == "test":
            return self.pants_commands.pants_test(target)
        elif command == "lint":
            return self.pants_commands.pants_lint(target)
        elif command == "check":
            return self.pants_commands.pants_check(target)
        elif command == "fix":
            return self.pants_commands.pants_fix(target)
        elif command == "package":
            return self.pants_commands.pants_package(target)
        else:
            raise ValueError(f"Unknown command: {command}")

    def _execute_intent_mode(
        self,
        command: str,
        arguments: dict[str, Any],
        supports_test_filter: bool = False,
    ) -> CommandResult:
        """
        Execute Pants command in intent-based mode.

        Args:
            command: Pants command name
            arguments: Tool arguments with intent-based parameters
            supports_test_filter: Whether command supports test_filter parameter

        Returns:
            CommandResult from Pants execution
        """
        # Extract intent parameters
        scope = arguments.get("scope")
        path = arguments.get("path")
        recursive = arguments.get("recursive")
        test_filter = arguments.get("test_filter") if supports_test_filter else None

        # Execute with error handling
        response = execute_with_error_handling(
            scope=scope,
            path=path,
            recursive=recursive,
            test_filter=test_filter,
            config=self.config,
            repo_root=self.repo_root,
            pants_executor=lambda cmd, target_spec, options: self._execute_pants_command(
                command, target_spec, options
            ),
            command=command,
        )

        # Convert response to CommandResult
        if isinstance(response, SuccessResponse):
            return CommandResult(
                command=f"pants {command}",
                exit_code=0,
                stdout=response.output,
                stderr="",
                success=True,
            )
        elif isinstance(response, ErrorResponse):
            return CommandResult(
                command=f"pants {command}",
                exit_code=1,
                stdout="",
                stderr=response.message,
                success=False,
            )
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")

    def _execute_pants_command(
        self, command: str, target_spec: str, options: list[str]
    ) -> CommandResult:
        """
        Execute Pants command with target spec and options.

        Args:
            command: Pants command name
            target_spec: Resolved Pants target specification
            options: Additional Pants CLI options

        Returns:
            CommandResult from Pants execution
        """
        # For now, we'll use the legacy methods with the resolved target
        # In the future, we could extend PantsCommands to accept options
        if command == "test":
            # TODO: Pass options to pants_test when it supports them
            return self.pants_commands.pants_test(target_spec)
        elif command == "lint":
            return self.pants_commands.pants_lint(target_spec)
        elif command == "check":
            return self.pants_commands.pants_check(target_spec)
        elif command == "fix":
            return self.pants_commands.pants_fix(target_spec)
        elif command == "package":
            return self.pants_commands.pants_package(target_spec)
        else:
            raise ValueError(f"Unknown command: {command}")
