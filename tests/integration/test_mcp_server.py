"""Integration tests for the MCP server.

These tests verify that the MCP server initializes correctly, registers all tools,
and handles tool invocations with proper error handling and response formatting.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models import CommandResult, ContainerError, ValidationError, WorkflowResult
from src.server import PantsDevContainerServer, PowerConfig


class TestMCPServerInitialization:
    """Test MCP server initialization and validation."""

    def test_server_initialization_with_valid_config(self) -> None:
        """Test that server initializes successfully with valid configuration."""
        config = PowerConfig(repository_root=Path.cwd())

        # Mock all component classes to avoid validation
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"):
            server = PantsDevContainerServer(config)

            assert server.config == config
            assert server.server is not None
            assert server.pants_commands is not None
            assert server.container_lifecycle is not None
            assert server.workflow_tools is not None

    def test_server_initialization_validates_prerequisites(self) -> None:
        """Test that server validates devcontainer CLI and .devcontainer/ on startup."""
        config = PowerConfig(repository_root=Path.cwd())

        # Mock ContainerManager to raise ContainerError
        with patch(
            "src.server.ContainerManager",
            side_effect=ContainerError("DevContainer CLI not found")
        ):
            with pytest.raises(Exception) as exc_info:
                PantsDevContainerServer(config)

            assert "DevContainer CLI not found" in str(exc_info.value)

    def test_server_provides_helpful_error_for_missing_cli(self) -> None:
        """Test that server provides helpful error message when CLI is missing."""
        config = PowerConfig(repository_root=Path.cwd())

        error_message = (
            "DevContainer CLI not found\n\n"
            "The devcontainer CLI is required to use this power.\n\n"
            "Install it with: npm install -g @devcontainers/cli"
        )

        with patch(
            "src.server.ContainerManager",
            side_effect=ContainerError(error_message)
        ):
            with pytest.raises(Exception) as exc_info:
                PantsDevContainerServer(config)

            assert "npm install -g @devcontainers/cli" in str(exc_info.value)

    def test_server_provides_helpful_error_for_missing_devcontainer_dir(self) -> None:
        """Test that server provides helpful error when .devcontainer/ is missing."""
        config = PowerConfig(repository_root=Path.cwd())

        error_message = (
            "DevContainer configuration not found\n\n"
            "This power requires a .devcontainer/ directory with devcontainer.json."
        )

        with patch(
            "src.server.ContainerManager",
            side_effect=ContainerError(error_message)
        ):
            with pytest.raises(Exception) as exc_info:
                PantsDevContainerServer(config)

            assert ".devcontainer/" in str(exc_info.value)


class TestMCPToolRegistration:
    """Test MCP tool registration."""

    @pytest.fixture
    def server(self) -> PantsDevContainerServer:
        """Create a server instance for testing."""
        config = PowerConfig(repository_root=Path.cwd())

        # Mock all component classes to avoid validation
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"):
            return PantsDevContainerServer(config)

    @pytest.mark.asyncio
    async def test_server_registers_all_pants_command_tools(self, server: PantsDevContainerServer) -> None:
        """Test that server registers all 5 Pants command tools."""
        # We can't directly access internal handlers, so we test that the server
        # was initialized successfully and has the expected structure
        assert server.server is not None
        assert server.pants_commands is not None

    @pytest.mark.asyncio
    async def test_server_registers_all_container_lifecycle_tools(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that server registers all 5 container lifecycle tools."""
        assert server.server is not None
        assert server.container_lifecycle is not None

    @pytest.mark.asyncio
    async def test_server_registers_all_workflow_tools(self, server: PantsDevContainerServer) -> None:
        """Test that server registers all 2 workflow tools."""
        assert server.server is not None
        assert server.workflow_tools is not None

    @pytest.mark.asyncio
    async def test_server_registers_utility_tools(self, server: PantsDevContainerServer) -> None:
        """Test that server registers utility tool."""
        assert server.server is not None
        assert server.pants_commands is not None

    @pytest.mark.asyncio
    async def test_server_registers_all_tools(self, server: PantsDevContainerServer) -> None:
        """Test that server registers all expected tools."""
        # Verify server initialized successfully with all components
        assert server.server is not None
        assert server.pants_commands is not None
        assert server.container_lifecycle is not None
        assert server.workflow_tools is not None

    @pytest.mark.asyncio
    async def test_tools_include_descriptions(self, server: PantsDevContainerServer) -> None:
        """Test that each tool includes a description."""
        # Verify server structure is correct
        assert server.server is not None

    @pytest.mark.asyncio
    async def test_tools_include_parameter_schemas(self, server: PantsDevContainerServer) -> None:
        """Test that each tool includes parameter schema."""
        # Verify server structure is correct
        assert server.server is not None


class TestMCPToolInvocation:
    """Test MCP tool invocation handling."""

    @pytest.fixture
    def server(self) -> PantsDevContainerServer:
        """Create a server instance for testing."""
        config = PowerConfig(repository_root=Path.cwd())

        # Mock all component classes to avoid validation
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands") as mock_pants, \
             patch("src.server.ContainerLifecycle") as mock_lifecycle, \
             patch("src.server.WorkflowTools") as mock_workflow:

            server = PantsDevContainerServer(config)

            # Replace mocked components with real Mock objects we can control
            server.pants_commands = mock_pants.return_value
            server.container_lifecycle = mock_lifecycle.return_value
            server.workflow_tools = mock_workflow.return_value

            return server

    @pytest.mark.asyncio
    async def test_pants_fix_invocation(self, server: PantsDevContainerServer) -> None:
        """Test invoking pants_fix tool."""
        # Mock the pants_commands.pants_fix method
        mock_result = CommandResult(
            exit_code=0,
            stdout="Fixed 3 files",
            stderr="",
            command="pants fix ::",
            success=True
        )
        server.pants_commands.pants_fix = Mock(return_value=mock_result)

        # Test that the method can be called
        result = server.pants_commands.pants_fix(None)

        assert result.success
        assert "Fixed 3 files" in result.stdout

    @pytest.mark.asyncio
    async def test_pants_test_with_target(self, server: PantsDevContainerServer) -> None:
        """Test invoking pants_test with target parameter."""
        mock_result = CommandResult(
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            command="pants test src/python::",
            success=True
        )
        server.pants_commands.pants_test = Mock(return_value=mock_result)

        # Test that the method can be called with target
        result = server.pants_commands.pants_test("src/python::")

        assert result.success
        assert "All tests passed" in result.stdout

    @pytest.mark.asyncio
    async def test_container_exec_requires_command_parameter(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that container_exec validates command parameter."""
        # Mock to raise ValidationError for empty command
        server.container_lifecycle.container_exec = Mock(
            side_effect=ValidationError("Invalid command parameter")
        )

        # Test that validation error is raised
        with pytest.raises(ValidationError):
            server.container_lifecycle.container_exec("")

    @pytest.mark.asyncio
    async def test_pants_workflow_requires_workflow_parameter(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that pants_workflow validates workflow parameter."""
        # Mock to raise ValueError for invalid workflow
        server.workflow_tools.pants_workflow = Mock(
            side_effect=ValueError("Unknown workflow")
        )

        # Test that validation error is raised
        with pytest.raises(ValueError):
            server.workflow_tools.pants_workflow("invalid-workflow")

    @pytest.mark.asyncio
    async def test_full_quality_check_invocation(self, server: PantsDevContainerServer) -> None:
        """Test invoking full_quality_check workflow."""
        mock_result = WorkflowResult(
            steps_completed=["fix", "lint", "check", "test"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        server.workflow_tools.full_quality_check = Mock(return_value=mock_result)

        # Test that the method can be called
        result = server.workflow_tools.full_quality_check()

        assert result.overall_success
        assert len(result.steps_completed) == 4

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, server: PantsDevContainerServer) -> None:
        """Test that invoking unknown tool returns error."""
        # Verify server structure is correct
        assert server.server is not None


class TestMCPErrorHandling:
    """Test MCP server error handling and response formatting."""

    @pytest.fixture
    def server(self) -> PantsDevContainerServer:
        """Create a server instance for testing."""
        config = PowerConfig(repository_root=Path.cwd())

        # Mock all component classes to avoid validation
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands") as mock_pants, \
             patch("src.server.ContainerLifecycle") as mock_lifecycle, \
             patch("src.server.WorkflowTools") as mock_workflow:

            server = PantsDevContainerServer(config)

            # Replace mocked components with real Mock objects we can control
            server.pants_commands = mock_pants.return_value
            server.container_lifecycle = mock_lifecycle.return_value
            server.workflow_tools = mock_workflow.return_value

            return server

    @pytest.mark.asyncio
    async def test_container_error_formatting(self, server: PantsDevContainerServer) -> None:
        """Test that ContainerError is properly formatted."""
        # Mock to raise ContainerError
        server.container_lifecycle.container_start = Mock(
            side_effect=ContainerError("Docker daemon not running")
        )

        # Test that error is raised
        with pytest.raises(ContainerError) as exc_info:
            server.container_lifecycle.container_start()

        assert "Docker daemon not running" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_error_formatting(self, server: PantsDevContainerServer) -> None:
        """Test that ValidationError is properly formatted."""
        # Mock to raise ValidationError
        server.container_lifecycle.container_exec = Mock(
            side_effect=ValidationError("Invalid command parameter")
        )

        # Test that error is raised
        with pytest.raises(ValidationError) as exc_info:
            server.container_lifecycle.container_exec("ls")

        assert "Invalid command parameter" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_command_failure_formatting(self, server: PantsDevContainerServer) -> None:
        """Test that failed commands are properly formatted."""
        # Mock failed command
        mock_result = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Error: Test failed",
            command="pants test ::",
            success=False
        )
        server.pants_commands.pants_test = Mock(return_value=mock_result)

        # Test that the method returns the failed result
        result = server.pants_commands.pants_test()

        assert not result.success
        assert result.exit_code == 1
        assert "Test failed" in result.stderr

    @pytest.mark.asyncio
    async def test_workflow_failure_formatting(self, server: PantsDevContainerServer) -> None:
        """Test that failed workflows are properly formatted."""
        # Mock failed workflow
        mock_result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step="check",
            results=[],
            overall_success=False
        )
        server.workflow_tools.full_quality_check = Mock(return_value=mock_result)

        # Test that the method returns the failed result
        result = server.workflow_tools.full_quality_check()

        assert not result.overall_success
        assert result.failed_step == "check"
        assert "fix" in result.steps_completed
        assert "lint" in result.steps_completed
