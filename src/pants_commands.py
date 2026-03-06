"""Pants command tools for the MCP server.

This module provides the core Pants command tools that wrap Pants build system
commands with automatic devcontainer execution.
"""

import logging
import time

from src.container_manager import ContainerManager
from src.formatters.enhanced_error_formatter import EnhancedErrorFormatter
from src.models import CommandResult, EnhancedCommandResult, ParsedOutput
from src.pants_command_builder import PantsCommandBuilder
from src.parsers.parser_router import ParserRouter

logger = logging.getLogger(__name__)


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
        command_builder: PantsCommandBuilder | None = None,
        parser_router: ParserRouter | None = None,
        formatter: EnhancedErrorFormatter | None = None,
        report_output_dir: str = "dist/test-reports",
        keep_sandboxes: str = "on_failure",
    ):
        """Initialize PantsCommands.

        Args:
            container_manager: ContainerManager instance (creates new one if None)
            command_builder: PantsCommandBuilder instance (creates new one if None)
            parser_router: ParserRouter instance for parsing command output (optional)
            formatter: EnhancedErrorFormatter instance for formatting results (optional)
            report_output_dir: Directory where Pants generates report files
            keep_sandboxes: Pants sandbox preservation mode ("always", "on_failure", "never")
        """
        self.container_manager = container_manager or ContainerManager()
        self.command_builder = command_builder or PantsCommandBuilder()
        self.parser_router = parser_router
        self.formatter = formatter
        self.report_output_dir = report_output_dir
        self.keep_sandboxes = keep_sandboxes

    def pants_fix(self, target: str | None = None) -> CommandResult | EnhancedCommandResult:
        """Format code and auto-fix linting issues.

        Ensures the container is running, then executes "pants fix <target>"
        inside the container. If parser_router and formatter are configured,
        returns EnhancedCommandResult with extracted sandbox paths.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            EnhancedCommandResult with parsed output if parsers are configured,
            otherwise CommandResult with raw output

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_fix()  # Fix all targets
            >>> result = commands.pants_fix("src/python::")  # Fix specific directory
        """
        # Build base command
        base_command = self.command_builder.build_command("fix", target)

        # Add sandbox preservation flag
        command = f"{base_command} --keep-sandboxes={self.keep_sandboxes}"

        # Execute command and measure time
        start_time = time.time()
        result = self.container_manager.exec(command)
        execution_time = time.time() - start_time

        # If no parser/formatter configured, return basic result
        if not self.parser_router or not self.formatter:
            return result

        # Parse output (mainly for sandbox extraction)
        try:
            parsed_output = self.parser_router.parse_command_output(
                command=command, result=result, report_dir=self.report_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to parse command output: {e}")
            parsed_output = ParsedOutput(parsing_errors=[str(e)])

        # Format summary
        try:
            formatted_summary = self.formatter.format_parsed_output(parsed_output)
        except Exception as e:
            logger.error(f"Failed to format parsed output: {e}")
            formatted_summary = f"Formatting error: {e}\n\nRaw output:\n{result.output}"

        # Return enhanced result
        return EnhancedCommandResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
            success=result.success,
            parsed_output=parsed_output,
            formatted_summary=formatted_summary,
            execution_time=execution_time,
        )

    def pants_lint(self, target: str | None = None) -> CommandResult | EnhancedCommandResult:
        """Run linters on code.

        Ensures the container is running, then executes "pants lint <target>"
        inside the container. If parser_router and formatter are configured,
        returns EnhancedCommandResult with extracted sandbox paths.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            EnhancedCommandResult with parsed output if parsers are configured,
            otherwise CommandResult with raw output

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_lint()  # Lint all targets
            >>> result = commands.pants_lint("src/python::")  # Lint specific directory
        """
        # Build base command
        base_command = self.command_builder.build_command("lint", target)

        # Add sandbox preservation flag
        command = f"{base_command} --keep-sandboxes={self.keep_sandboxes}"

        # Execute command and measure time
        start_time = time.time()
        result = self.container_manager.exec(command)
        execution_time = time.time() - start_time

        # If no parser/formatter configured, return basic result
        if not self.parser_router or not self.formatter:
            return result

        # Parse output (mainly for sandbox extraction)
        try:
            parsed_output = self.parser_router.parse_command_output(
                command=command, result=result, report_dir=self.report_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to parse command output: {e}")
            parsed_output = ParsedOutput(parsing_errors=[str(e)])

        # Format summary
        try:
            formatted_summary = self.formatter.format_parsed_output(parsed_output)
        except Exception as e:
            logger.error(f"Failed to format parsed output: {e}")
            formatted_summary = f"Formatting error: {e}\n\nRaw output:\n{result.output}"

        # Return enhanced result
        return EnhancedCommandResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
            success=result.success,
            parsed_output=parsed_output,
            formatted_summary=formatted_summary,
            execution_time=execution_time,
        )

    def pants_check(self, target: str | None = None) -> CommandResult | EnhancedCommandResult:
        """Run type checking with mypy.

        Ensures the container is running, then executes "pants check <target>"
        inside the container. If parser_router and formatter are configured,
        returns EnhancedCommandResult with parsed MyPy errors and formatted summary.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            EnhancedCommandResult with parsed output if parsers are configured,
            otherwise CommandResult with raw output

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_check()  # Check all targets
            >>> result = commands.pants_check("src/python::")  # Check specific directory
        """
        # Build base command
        base_command = self.command_builder.build_command("check", target)

        # Add sandbox preservation flag
        command = f"{base_command} --keep-sandboxes={self.keep_sandboxes}"

        # Execute command and measure time
        start_time = time.time()
        result = self.container_manager.exec(command)
        execution_time = time.time() - start_time

        # If no parser/formatter configured, return basic result
        if not self.parser_router or not self.formatter:
            return result

        # Parse output
        try:
            parsed_output = self.parser_router.parse_command_output(
                command=command, result=result, report_dir=self.report_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to parse command output: {e}")
            # Return basic result on parsing failure
            parsed_output = ParsedOutput(parsing_errors=[str(e)])

        # Format summary
        try:
            formatted_summary = self.formatter.format_parsed_output(parsed_output)
        except Exception as e:
            logger.error(f"Failed to format parsed output: {e}")
            formatted_summary = f"Formatting error: {e}\n\nRaw output:\n{result.output}"

        # Return enhanced result
        return EnhancedCommandResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
            success=result.success,
            parsed_output=parsed_output,
            formatted_summary=formatted_summary,
            execution_time=execution_time,
        )

    def pants_test(self, target: str | None = None) -> CommandResult | EnhancedCommandResult:
        """Run tests.

        Ensures the container is running, then executes "pants test <target>"
        inside the container. If parser_router and formatter are configured,
        returns EnhancedCommandResult with parsed test results, coverage data,
        and formatted summary.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            EnhancedCommandResult with parsed output if parsers are configured,
            otherwise CommandResult with raw output

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_test()  # Test all targets
            >>> result = commands.pants_test("src/python::")  # Test specific directory
            >>> result = commands.pants_test("src/python/test_myapp.py")  # Test specific file
        """
        # Build base command
        base_command = self.command_builder.build_command("test", target)

        # Add flags for structured output generation
        flags = []

        # Configure JUnit XML report generation
        flags.append("--test-report")
        flags.append(f"--test-report-dir={self.report_output_dir}")

        # Configure coverage
        flags.append("--test-use-coverage")

        # Configure sandbox preservation
        flags.append(f"--keep-sandboxes={self.keep_sandboxes}")

        # Build complete command with flags
        command = f"{base_command} {' '.join(flags)}" if flags else base_command

        # Execute command and measure time
        start_time = time.time()
        result = self.container_manager.exec(command)
        execution_time = time.time() - start_time

        # If no parser/formatter configured, return basic result
        if not self.parser_router or not self.formatter:
            return result

        # Parse output
        try:
            parsed_output = self.parser_router.parse_command_output(
                command=command, result=result, report_dir=self.report_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to parse command output: {e}")
            # Return basic result on parsing failure
            parsed_output = ParsedOutput(parsing_errors=[str(e)])

        # Format summary
        try:
            formatted_summary = self.formatter.format_parsed_output(parsed_output)
        except Exception as e:
            logger.error(f"Failed to format parsed output: {e}")
            formatted_summary = f"Formatting error: {e}\n\nRaw output:\n{result.output}"

        # Return enhanced result
        return EnhancedCommandResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
            success=result.success,
            parsed_output=parsed_output,
            formatted_summary=formatted_summary,
            execution_time=execution_time,
        )

    def pants_package(self, target: str | None = None) -> CommandResult | EnhancedCommandResult:
        """Build packages.

        Ensures the container is running, then executes "pants package <target>"
        inside the container. If parser_router and formatter are configured,
        returns EnhancedCommandResult with extracted sandbox paths.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            EnhancedCommandResult with parsed output if parsers are configured,
            otherwise CommandResult with raw output

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_package()  # Package all targets
            >>> result = commands.pants_package("src/python::")  # Package specific directory
            >>> result = commands.pants_package("src/python:myapp")  # Package specific target
        """
        # Build base command
        base_command = self.command_builder.build_command("package", target)

        # Add sandbox preservation flag
        command = f"{base_command} --keep-sandboxes={self.keep_sandboxes}"

        # Execute command and measure time
        start_time = time.time()
        result = self.container_manager.exec(command)
        execution_time = time.time() - start_time

        # If no parser/formatter configured, return basic result
        if not self.parser_router or not self.formatter:
            return result

        # Parse output (mainly for sandbox extraction)
        try:
            parsed_output = self.parser_router.parse_command_output(
                command=command, result=result, report_dir=self.report_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to parse command output: {e}")
            parsed_output = ParsedOutput(parsing_errors=[str(e)])

        # Format summary
        try:
            formatted_summary = self.formatter.format_parsed_output(parsed_output)
        except Exception as e:
            logger.error(f"Failed to format parsed output: {e}")
            formatted_summary = f"Formatting error: {e}\n\nRaw output:\n{result.output}"

        # Return enhanced result
        return EnhancedCommandResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
            success=result.success,
            parsed_output=parsed_output,
            formatted_summary=formatted_summary,
            execution_time=execution_time,
        )

    def pants_tailor(self, target: str | None = None) -> CommandResult | EnhancedCommandResult:
        """Generate or update BUILD files for source files.

        Ensures the container is running, then executes "pants tailor <target>"
        inside the container. Tailor automatically creates BUILD files with
        appropriate targets for Python files, tests, and other source code.

        Args:
            target: Pants target specification (default: "::")

        Returns:
            EnhancedCommandResult with parsed output if parsers are configured,
            otherwise CommandResult with raw output

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_tailor()  # Tailor all directories
            >>> result = commands.pants_tailor("src/python::")  # Tailor specific directory
        """
        # Build base command
        base_command = self.command_builder.build_command("tailor", target)

        # Add sandbox preservation flag
        command = f"{base_command} --keep-sandboxes={self.keep_sandboxes}"

        # Execute command and measure time
        start_time = time.time()
        result = self.container_manager.exec(command)
        execution_time = time.time() - start_time

        # If no parser/formatter configured, return basic result
        if not self.parser_router or not self.formatter:
            return result

        # Parse output (mainly for sandbox extraction)
        try:
            parsed_output = self.parser_router.parse_command_output(
                command=command, result=result, report_dir=self.report_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to parse command output: {e}")
            parsed_output = ParsedOutput(parsing_errors=[str(e)])

        # Format summary
        try:
            formatted_summary = self.formatter.format_parsed_output(parsed_output)
        except Exception as e:
            logger.error(f"Failed to format parsed output: {e}")
            formatted_summary = f"Formatting error: {e}\n\nRaw output:\n{result.output}"

        # Return enhanced result
        return EnhancedCommandResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
            success=result.success,
            parsed_output=parsed_output,
            formatted_summary=formatted_summary,
            execution_time=execution_time,
        )

    def pants_clear_cache(self) -> CommandResult:
        """Clear Pants cache to resolve filesystem issues.

        Ensures the container is running, then executes "rm -rf .pants.d/pids"
        inside the container. Handles missing cache directory gracefully by
        returning success even if the directory doesn't exist.

        Note: This command does not support enhanced parsing as it's a simple
        filesystem operation.

        Returns:
            CommandResult with the outcome of the cache clearing operation

        Examples:
            >>> commands = PantsCommands()
            >>> result = commands.pants_clear_cache()
            >>> print(result.success)
            True
        """
        # Use -f flag to suppress errors if directory doesn't exist
        command = "rm -rf .pants.d/pids"
        return self.container_manager.exec(command)
