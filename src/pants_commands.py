"""Pants command tools for the MCP server.

This module provides the core Pants command tools that wrap Pants build system
commands with automatic devcontainer execution.
"""


from src.container_manager import ContainerManager
from src.models import CommandResult
from src.pants_command_builder import PantsCommandBuilder


class PantsCommands:
    """Provides Pants command execution tools.

    This class implements the core Pants command tools (fix, lint, check, test, package)
    that ensure the container is running and execute Pants commands inside it.

    Attributes:
        container_manager: ContainerManager instance for container operations
        command_builder: PantsCommandBuilder instance for building Pants commands
    """

    def __init__(
        self,
        container_manager: ContainerManager | None = None,
        command_builder: PantsCommandBuilder | None = None
    ):
        """Initialize PantsCommands.

        Args:
            container_manager: ContainerManager instance (creates new one if None)
            command_builder: PantsCommandBuilder instance (creates new one if None)
        """
        self.container_manager = container_manager or ContainerManager()
        self.command_builder = command_builder or PantsCommandBuilder()

    def pants_fix(self, target: str | None = None) -> CommandResult:
        """Format code and auto-fix linting issues.

        Ensures the container is running, then executes "pants fix <target>"
        inside the container.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            CommandResult with the outcome of the fix command

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_fix()  # Fix all targets
            >>> result = commands.pants_fix("src/python::")  # Fix specific directory
        """
        command = self.command_builder.build_command("fix", target)
        return self.container_manager.exec(command)

    def pants_lint(self, target: str | None = None) -> CommandResult:
        """Run linters on code.

        Ensures the container is running, then executes "pants lint <target>"
        inside the container.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            CommandResult with the outcome of the lint command

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_lint()  # Lint all targets
            >>> result = commands.pants_lint("src/python::")  # Lint specific directory
        """
        command = self.command_builder.build_command("lint", target)
        return self.container_manager.exec(command)

    def pants_check(self, target: str | None = None) -> CommandResult:
        """Run type checking with mypy.

        Ensures the container is running, then executes "pants check <target>"
        inside the container.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            CommandResult with the outcome of the check command

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_check()  # Check all targets
            >>> result = commands.pants_check("src/python::")  # Check specific directory
        """
        command = self.command_builder.build_command("check", target)
        return self.container_manager.exec(command)

    def pants_test(self, target: str | None = None) -> CommandResult:
        """Run tests.

        Ensures the container is running, then executes "pants test <target>"
        inside the container.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            CommandResult with the outcome of the test command

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_test()  # Test all targets
            >>> result = commands.pants_test("src/python::")  # Test specific directory
            >>> result = commands.pants_test("src/python/test_myapp.py")  # Test specific file
        """
        command = self.command_builder.build_command("test", target)
        return self.container_manager.exec(command)

    def pants_package(self, target: str | None = None) -> CommandResult:
        """Build packages.

        Ensures the container is running, then executes "pants package <target>"
        inside the container.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            CommandResult with the outcome of the package command

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_package()  # Package all targets
            >>> result = commands.pants_package("src/python::")  # Package specific directory
            >>> result = commands.pants_package("src/python:myapp")  # Package specific target
        """
        command = self.command_builder.build_command("package", target)
        return self.container_manager.exec(command)
