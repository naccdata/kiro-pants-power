"""MCP server implementation for Pants DevContainer Power.

This module implements the Model Context Protocol (MCP) server that exposes
Pants build system tools with automatic devcontainer integration.

Each tool accepts a workspace_folder parameter that specifies the repository
root containing .devcontainer/. This avoids startup-time workspace resolution
issues and works reliably regardless of how the server process is launched.
"""

import asyncio
import logging
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
    format_success,
    format_validation_error,
)
from src.formatters.enhanced_error_formatter import EnhancedErrorFormatter
from src.intent.tool_executor import ToolExecutor
from src.intent.tool_schemas import (
    TOOL_DESCRIPTIONS,
    get_pants_check_schema,
    get_pants_fix_schema,
    get_pants_lint_schema,
    get_pants_package_schema,
    get_pants_test_schema,
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
from src.parsers.parser_router import ParserRouter
from src.workflow_orchestrator import WorkflowOrchestrator
from src.workflow_tools import WorkflowTools

logger = logging.getLogger(__name__)

# workspace_folder parameter added to every tool schema
WORKSPACE_FOLDER_PARAMETER: dict[str, Any] = {
    "workspace_folder": {
        "type": "string",
        "description": (
            "Absolute path to the repository root that contains .devcontainer/. "
            "This is the workspace where Pants commands will be executed."
        ),
    }
}


def _inject_workspace_param(schema: dict[str, Any]) -> dict[str, Any]:
    """Add workspace_folder to a tool's input schema.

    Args:
        schema: Existing tool input schema

    Returns:
        New schema with workspace_folder added to properties and required
    """
    new_schema = dict(schema)
    new_props = {**WORKSPACE_FOLDER_PARAMETER, **new_schema.get("properties", {})}
    new_schema["properties"] = new_props
    required = list(new_schema.get("required", []))
    if "workspace_folder" not in required:
        required.insert(0, "workspace_folder")
    new_schema["required"] = required
    return new_schema


class WorkspaceSession:
    """Cached components for a validated workspace.

    Holds the initialized ContainerManager, PantsCommands, etc. for a
    specific workspace_folder path so we don't re-create them every call.
    """

    def __init__(self, workspace_folder: Path):
        """Initialize session components for a workspace.

        Args:
            workspace_folder: Validated path to repo root with .devcontainer/

        Raises:
            ContainerError: If devcontainer CLI is missing or .devcontainer/ not found
        """
        self.workspace_folder = workspace_folder
        self.container_manager = ContainerManager(workspace_folder=workspace_folder)
        parser_router = ParserRouter()
        formatter = EnhancedErrorFormatter()
        self.pants_commands = PantsCommands(
            container_manager=self.container_manager,
            parser_router=parser_router,
            formatter=formatter,
        )
        self.container_lifecycle = ContainerLifecycle(
            container_manager=self.container_manager
        )
        self.workflow_tools = WorkflowTools(
            orchestrator=WorkflowOrchestrator(pants_commands=self.pants_commands)
        )
        self.tool_executor = ToolExecutor(
            self.pants_commands, repo_root=workspace_folder
        )


class PantsDevContainerServer:
    """MCP server for Pants DevContainer Power.

    This server exposes MCP tools for managing Pants workflows in devcontainers.
    Each tool call includes a workspace_folder parameter so the server doesn't
    need to resolve the workspace at startup.

    Tools:
    - Pants command tools (fix, lint, check, test, package, tailor)
    - Container lifecycle tools (start, stop, rebuild, exec, shell)
    - Workflow tools (full_quality_check, pants_workflow)
    - Utility tools (pants_clear_cache)
    """

    def __init__(self):
        """Initialize the MCP server."""
        # Cache of WorkspaceSession instances keyed by resolved path string
        self._sessions: dict[str, WorkspaceSession] = {}

        # Initialize MCP server
        self.server = Server("pants-devcontainer-power")

        # Register tools
        self._register_tools()

    def _get_session(self, workspace_folder: str | None) -> WorkspaceSession:
        """Get or create a WorkspaceSession for the given workspace path.

        Args:
            workspace_folder: Path string from the tool call arguments

        Returns:
            Initialized WorkspaceSession

        Raises:
            ValidationError: If workspace_folder is missing or doesn't exist
            ContainerError: If .devcontainer/ not found or CLI missing
        """
        if not workspace_folder:
            raise ValidationError(
                "Parameter 'workspace_folder' is required.\n\n"
                "Provide the absolute path to the repository root that "
                "contains a .devcontainer/ directory."
            )

        path = Path(workspace_folder).resolve()
        key = str(path)

        if key in self._sessions:
            return self._sessions[key]

        if not path.exists():
            raise ValidationError(
                f"Workspace folder does not exist: {workspace_folder}"
            )

        # ContainerManager.__init__ validates .devcontainer/ and CLI
        session = WorkspaceSession(workspace_folder=path)
        self._sessions[key] = session
        return session

    def _register_tools(self) -> None:
        """Register all MCP tools with the server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return [
                Tool(
                    name="pants_fix",
                    description=TOOL_DESCRIPTIONS["pants_fix"],
                    inputSchema=_inject_workspace_param(get_pants_fix_schema()),
                ),
                Tool(
                    name="pants_lint",
                    description=TOOL_DESCRIPTIONS["pants_lint"],
                    inputSchema=_inject_workspace_param(get_pants_lint_schema()),
                ),
                Tool(
                    name="pants_check",
                    description=TOOL_DESCRIPTIONS["pants_check"],
                    inputSchema=_inject_workspace_param(get_pants_check_schema()),
                ),
                Tool(
                    name="pants_test",
                    description=TOOL_DESCRIPTIONS["pants_test"],
                    inputSchema=_inject_workspace_param(get_pants_test_schema()),
                ),
                Tool(
                    name="pants_package",
                    description=TOOL_DESCRIPTIONS["pants_package"],
                    inputSchema=_inject_workspace_param(get_pants_package_schema()),
                ),
                Tool(
                    name="pants_tailor",
                    description="Generate or update BUILD files for source files",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": 'Pants target specification (default: "::")',
                            }
                        },
                    }),
                ),
                Tool(
                    name="container_start",
                    description="Start the devcontainer (idempotent)",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {},
                    }),
                ),
                Tool(
                    name="container_stop",
                    description="Stop the devcontainer",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {},
                    }),
                ),
                Tool(
                    name="container_rebuild",
                    description="Rebuild and restart the devcontainer",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {},
                    }),
                ),
                Tool(
                    name="container_exec",
                    description="Execute arbitrary command in container",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            }
                        },
                        "required": ["command"],
                    }),
                ),
                Tool(
                    name="container_shell",
                    description="Provide instructions for opening interactive shell",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {},
                    }),
                ),
                Tool(
                    name="full_quality_check",
                    description=(
                        "Run complete quality check workflow "
                        "(fix → lint → check → test)"
                    ),
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": (
                                    'Pants target specification (default: "::")'
                                ),
                            }
                        },
                    }),
                ),
                Tool(
                    name="pants_workflow",
                    description="Execute custom workflow sequence",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {
                            "workflow": {
                                "type": "string",
                                "description": (
                                    'Workflow name '
                                    '("fix-lint", "check-test", "fix-lint-check")'
                                ),
                            },
                            "target": {
                                "type": "string",
                                "description": (
                                    'Pants target specification (default: "::")'
                                ),
                            },
                        },
                        "required": ["workflow"],
                    }),
                ),
                Tool(
                    name="pants_clear_cache",
                    description="Clear Pants cache to resolve filesystem issues",
                    inputSchema=_inject_workspace_param({
                        "type": "object",
                        "properties": {},
                    }),
                ),
            ]

        @self.server.call_tool()
        async def call_tool(  # noqa: C901
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent]:
            """Handle tool invocation requests."""
            try:
                # Extract and validate workspace_folder from arguments
                workspace_folder = arguments.pop("workspace_folder", None)
                session = self._get_session(workspace_folder)

                # Route to appropriate handler
                if name == "pants_fix":
                    result = session.tool_executor.execute_pants_fix(arguments)
                    return self._format_command_result(result)

                elif name == "pants_lint":
                    result = session.tool_executor.execute_pants_lint(arguments)
                    return self._format_command_result(result)

                elif name == "pants_check":
                    result = session.tool_executor.execute_pants_check(arguments)
                    return self._format_command_result(result)

                elif name == "pants_test":
                    result = session.tool_executor.execute_pants_test(arguments)
                    return self._format_command_result(result)

                elif name == "pants_package":
                    result = session.tool_executor.execute_pants_package(arguments)
                    return self._format_command_result(result)

                elif name == "pants_tailor":
                    result = session.pants_commands.pants_tailor(
                        arguments.get("target")
                    )
                    return self._format_command_result(result)

                elif name == "container_start":
                    result = session.container_lifecycle.container_start()
                    return self._format_command_result(result)

                elif name == "container_stop":
                    result = session.container_lifecycle.container_stop()
                    return self._format_command_result(result)

                elif name == "container_rebuild":
                    result = session.container_lifecycle.container_rebuild()
                    return self._format_command_result(result)

                elif name == "container_exec":
                    command = arguments.get("command")
                    if not command:
                        raise ValidationError(
                            "Parameter 'command' is required for container_exec"
                        )
                    result = session.container_lifecycle.container_exec(command)
                    return self._format_command_result(result)

                elif name == "container_shell":
                    result = session.container_lifecycle.container_shell()
                    return self._format_command_result(result)

                elif name == "full_quality_check":
                    workflow_result = session.workflow_tools.full_quality_check(
                        arguments.get("target")
                    )
                    return self._format_workflow_result(workflow_result)

                elif name == "pants_workflow":
                    workflow = arguments.get("workflow")
                    if not workflow:
                        raise ValidationError(
                            "Parameter 'workflow' is required for pants_workflow"
                        )
                    workflow_result = session.workflow_tools.pants_workflow(
                        workflow, arguments.get("target")
                    )
                    return self._format_workflow_result(workflow_result)

                elif name == "pants_clear_cache":
                    result = session.pants_commands.pants_clear_cache()
                    return self._format_command_result(result)

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except ValidationError as e:
                return [TextContent(type="text", text=format_validation_error(e))]
            except ContainerError as e:
                return [
                    TextContent(
                        type="text",
                        text=(
                            f"Container error: {e!s}\n\n"
                            "Ensure the workspace_folder path is correct and "
                            "contains a .devcontainer/ directory."
                        ),
                    )
                ]
            except CommandExecutionError as e:
                return [
                    TextContent(
                        type="text",
                        text=format_command_execution_error(e),
                    )
                ]
            except PowerError as e:
                return [TextContent(type="text", text=f"Power error: {e!s}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Unexpected error: {e!s}")]

    def _format_command_result(self, result: CommandResult) -> list[TextContent]:
        """Format CommandResult as MCP TextContent."""
        if result.success:
            text = format_success(result)
        else:
            text = format_command_execution_error(
                CommandExecutionError(f"Command failed: {result.command}"),
                command=result.command,
                exit_code=result.exit_code,
                output=result.output,
                result=result,
            )
        return [TextContent(type="text", text=text)]

    def _format_workflow_result(self, result: WorkflowResult) -> list[TextContent]:
        """Format WorkflowResult as MCP TextContent."""
        text = result.summary

        if result.results:
            text += "\n\n--- Step Details ---\n"
            for i, step_result in enumerate(result.results):
                if i < len(result.steps_completed):
                    step_name = result.steps_completed[i]
                elif result.failed_step:
                    step_name = result.failed_step
                else:
                    step_name = "unknown"
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
        server = PantsDevContainerServer()
        await server.run()
    except Exception as e:
        error_msg = str(e)
        if "connection closed" in error_msg.lower():
            sys.exit(0)
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Synchronous entry point for the MCP server (for use as console script)."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
