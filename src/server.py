"""MCP server implementation for Pants DevContainer Power.

This module implements the Model Context Protocol (MCP) server that exposes
Pants build system tools with automatic devcontainer integration.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.container_lifecycle import ContainerLifecycle
from src.container_manager import ContainerManager
from src.formatters import (
    format_command_execution_error,
    format_container_error,
    format_success,
    format_validation_error,
)
from src.models import (
    CommandExecutionError,
    CommandResult,
    ContainerError,
    PowerError,
    ValidationError,
    WorkflowResult,
)
from src.pants_commands import PantsCommands
from src.workflow_tools import WorkflowTools


class PowerConfig:
    """Configuration for the Pants DevContainer Power.

    Attributes:
        name: Power name
        version: Power version
        description: Power description
        python_version: Required Python version
        repository_root: Path to repository root
    """

    def __init__(
        self,
        name: str = "pants-devcontainer-power",
        version: str = "0.1.0",
        description: str = "MCP tools for Pants build system with devcontainer integration",
        python_version: str = "3.12+",
        repository_root: Path | None = None,
    ):
        """Initialize PowerConfig.

        Args:
            name: Power name
            version: Power version
            description: Power description
            python_version: Required Python version
            repository_root: Path to repository root (uses current directory if None)
        """
        self.name = name
        self.version = version
        self.description = description
        self.python_version = python_version
        self.repository_root = repository_root or Path.cwd()

    def validate(self) -> None:
        """Validate that prerequisites are met.

        Raises:
            PowerError: If devcontainer CLI is not installed or .devcontainer/ is missing
        """
        # This validation is now handled by ContainerManager.__init__
        # We create a temporary ContainerManager to trigger validation
        try:
            ContainerManager(workspace_folder=self.repository_root)
        except ContainerError as e:
            raise PowerError(str(e)) from e


class PantsDevContainerServer:
    """MCP server for Pants DevContainer Power.

    This server exposes MCP tools for managing Pants workflows in devcontainers:
    - Pants command tools (fix, lint, check, test, package)
    - Container lifecycle tools (start, stop, rebuild, exec, shell)
    - Workflow tools (full_quality_check, pants_workflow)
    - Utility tools (pants_clear_cache)

    Attributes:
        config: PowerConfig instance
        server: MCP Server instance
        pants_commands: PantsCommands instance for Pants operations
        container_lifecycle: ContainerLifecycle instance for container operations
        workflow_tools: WorkflowTools instance for workflow orchestration
    """

    def __init__(self, config: PowerConfig | None = None):
        """Initialize the MCP server.

        Args:
            config: PowerConfig instance (creates default if None)

        Raises:
            PowerError: If prerequisites are not met
        """
        self.config = config or PowerConfig()

        # Validate prerequisites on startup
        self.config.validate()

        # Initialize MCP server
        self.server = Server(self.config.name)

        # Initialize components
        self.pants_commands = PantsCommands()
        self.container_lifecycle = ContainerLifecycle()
        self.workflow_tools = WorkflowTools()

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all MCP tools with the server."""
        # Register Pants command tools
        self._register_pants_tools()

        # Register container lifecycle tools
        self._register_container_tools()

        # Register workflow tools
        self._register_workflow_tools()

        # Register utility tools
        self._register_utility_tools()

    def _register_pants_tools(self) -> None:
        """Register Pants command tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return [
                Tool(
                    name="pants_fix",
                    description="Format code and auto-fix linting issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="pants_lint",
                    description="Run linters on code",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="pants_check",
                    description="Run type checking with mypy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="pants_test",
                    description="Run tests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="pants_package",
                    description="Build packages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="pants_tailor",
                    description="Generate or update BUILD files for source files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="container_start",
                    description="Start the devcontainer (idempotent)",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="container_stop",
                    description="Stop the devcontainer",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="container_rebuild",
                    description="Rebuild and restart the devcontainer",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="container_exec",
                    description="Execute arbitrary command in container",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            }
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="container_shell",
                    description="Provide instructions for opening interactive shell",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="full_quality_check",
                    description="Run complete quality check workflow (fix → lint → check → test)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    },
                ),
                Tool(
                    name="pants_workflow",
                    description="Execute custom workflow sequence",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow": {
                                "type": "string",
                                "description": (
                                    'Workflow name ("fix-lint", "check-test", "fix-lint-check")'
                                ),
                            },
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            },
                        },
                        "required": ["workflow"],
                    },
                ),
                Tool(
                    name="pants_clear_cache",
                    description="Clear Pants cache to resolve filesystem issues",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool invocation requests.

            Args:
                name: Tool name
                arguments: Tool parameters

            Returns:
                List of TextContent with tool results

            Raises:
                ValueError: If tool name is not recognized
            """
            try:
                # Route to appropriate tool function
                if name == "pants_fix":
                    result = self.pants_commands.pants_fix(arguments.get("target"))
                    return self._format_command_result(result)

                elif name == "pants_lint":
                    result = self.pants_commands.pants_lint(arguments.get("target"))
                    return self._format_command_result(result)

                elif name == "pants_check":
                    result = self.pants_commands.pants_check(arguments.get("target"))
                    return self._format_command_result(result)

                elif name == "pants_test":
                    result = self.pants_commands.pants_test(arguments.get("target"))
                    return self._format_command_result(result)

                elif name == "pants_package":
                    result = self.pants_commands.pants_package(arguments.get("target"))
                    return self._format_command_result(result)

                elif name == "pants_tailor":
                    result = self.pants_commands.pants_tailor(arguments.get("target"))
                    return self._format_command_result(result)

                elif name == "container_start":
                    result = self.container_lifecycle.container_start()
                    return self._format_command_result(result)

                elif name == "container_stop":
                    result = self.container_lifecycle.container_stop()
                    return self._format_command_result(result)

                elif name == "container_rebuild":
                    result = self.container_lifecycle.container_rebuild()
                    return self._format_command_result(result)

                elif name == "container_exec":
                    command = arguments.get("command")
                    if not command:
                        raise ValidationError("Parameter 'command' is required for container_exec")
                    result = self.container_lifecycle.container_exec(command)
                    return self._format_command_result(result)

                elif name == "container_shell":
                    result = self.container_lifecycle.container_shell()
                    return self._format_command_result(result)

                elif name == "full_quality_check":
                    workflow_result = self.workflow_tools.full_quality_check(
                        arguments.get("target")
                    )
                    return self._format_workflow_result(workflow_result)

                elif name == "pants_workflow":
                    workflow = arguments.get("workflow")
                    if not workflow:
                        raise ValidationError("Parameter 'workflow' is required for pants_workflow")
                    workflow_result = self.workflow_tools.pants_workflow(
                        workflow, arguments.get("target")
                    )
                    return self._format_workflow_result(workflow_result)

                elif name == "pants_clear_cache":
                    result = self.pants_commands.pants_clear_cache()
                    return self._format_command_result(result)

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except ValidationError as e:
                return [TextContent(type="text", text=format_validation_error(e))]
            except ContainerError as e:
                return [TextContent(type="text", text=format_container_error(e))]
            except CommandExecutionError as e:
                return [TextContent(type="text", text=format_command_execution_error(e))]
            except PowerError as e:
                return [TextContent(type="text", text=f"Power error: {e!s}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Unexpected error: {e!s}")]

    def _register_container_tools(self) -> None:
        """Register container lifecycle tools.

        Note: Container tools are registered in _register_pants_tools
        to keep all tools in a single list_tools handler.
        """
        pass

    def _register_workflow_tools(self) -> None:
        """Register workflow orchestration tools.

        Note: Workflow tools are registered in _register_pants_tools
        to keep all tools in a single list_tools handler.
        """
        pass

    def _register_utility_tools(self) -> None:
        """Register utility tools.

        Note: Utility tools are registered in _register_pants_tools
        to keep all tools in a single list_tools handler.
        """
        pass

    def _format_command_result(self, result: CommandResult) -> list[TextContent]:
        """Format CommandResult as MCP TextContent.

        Args:
            result: CommandResult to format

        Returns:
            List containing single TextContent with formatted result
        """
        if result.success:
            text = format_success(result)
        else:
            text = format_command_execution_error(
                CommandExecutionError(f"Command failed: {result.command}"),
                command=result.command,
                exit_code=result.exit_code,
                output=result.output,
            )

        return [TextContent(type="text", text=text)]

    def _format_workflow_result(self, result: WorkflowResult) -> list[TextContent]:
        """Format WorkflowResult as MCP TextContent.

        Args:
            result: WorkflowResult to format

        Returns:
            List containing single TextContent with formatted result
        """
        text = result.summary

        # Add detailed output from each step
        if result.results:
            text += "\n\n--- Step Details ---\n"
            for i, step_result in enumerate(result.results):
                step_name = (
                    result.steps_completed[i] if i < len(result.steps_completed) else "unknown"
                )
                text += f"\nStep: {step_name}\n"
                text += f"Command: {step_result.command}\n"
                text += f"Exit code: {step_result.exit_code}\n"
                if step_result.output:
                    text += f"Output:\n{step_result.output}\n"

        return [TextContent(type="text", text=text)]

    async def run(self) -> None:
        """Run the MCP server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def async_main() -> None:
    """Async main entry point for the MCP server."""
    try:
        config = PowerConfig()
        server = PantsDevContainerServer(config)
        await server.run()
    except PowerError as e:
        # Check if this is a "devcontainer not found" error - exit gracefully
        error_msg = str(e)
        if (
            "DevContainer configuration not found" in error_msg
            or "DevContainer CLI not found" in error_msg
        ):
            # Exit silently with success code - this workspace doesn't need this power
            sys.exit(0)
        # For other PowerErrors, log and exit with error code
        print(f"Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Synchronous entry point for the MCP server (for use as console script)."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
