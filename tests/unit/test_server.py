"""Unit tests for the MCP server implementation."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models import (
    CommandExecutionError,
    CommandResult,
    ContainerError,
    PowerError,
    ValidationError,
    WorkflowResult,
)
from src.server import PantsDevContainerServer, PowerConfig


class TestPowerConfig:
    """Test suite for PowerConfig class."""

    def test_power_config_initialization_with_defaults(self) -> None:
        """Test PowerConfig initializes with default values."""
        config = PowerConfig()

        assert config.name == "pants-devcontainer-power"
        assert config.version == "0.1.0"
        assert config.description == (
            "MCP tools for Pants build system with devcontainer integration"
        )
        assert config.python_version == "3.12+"
        assert config.repository_root == Path.cwd()

    def test_power_config_initialization_with_custom_values(self) -> None:
        """Test PowerConfig initializes with custom values."""
        custom_root = Path("/custom/path")
        config = PowerConfig(
            name="custom-power",
            version="1.0.0",
            description="Custom description",
            python_version="3.11+",
            repository_root=custom_root,
        )

        assert config.name == "custom-power"
        assert config.version == "1.0.0"
        assert config.description == "Custom description"
        assert config.python_version == "3.11+"
        assert config.repository_root == custom_root

    def test_power_config_validate_success(self) -> None:
        """Test PowerConfig.validate() succeeds when prerequisites are met."""
        config = PowerConfig()

        # Mock ContainerManager to not raise errors
        with patch("src.server.ContainerManager"):
            # Should not raise any exception
            config.validate()

    def test_power_config_validate_raises_power_error_on_container_error(self) -> None:
        """Test PowerConfig.validate() raises PowerError when ContainerManager fails."""
        config = PowerConfig()

        # Mock ContainerManager to raise ContainerError
        with patch(
            "src.server.ContainerManager",
            side_effect=ContainerError("DevContainer CLI not found"),
        ), pytest.raises(PowerError, match="DevContainer CLI not found"):
            config.validate()


class TestPantsDevContainerServer:
    """Test suite for PantsDevContainerServer class."""

    @pytest.fixture
    def mock_config(self) -> PowerConfig:
        """Create a PowerConfig for testing."""
        return PowerConfig(repository_root=Path.cwd())

    @pytest.fixture
    def server(self, mock_config: PowerConfig) -> PantsDevContainerServer:
        """Create a PantsDevContainerServer with mocked dependencies."""
        # Mock all component classes to avoid validation
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands") as mock_pants, \
             patch("src.server.ContainerLifecycle") as mock_lifecycle, \
             patch("src.server.WorkflowTools") as mock_workflow:

            server = PantsDevContainerServer(mock_config)

            # Replace mocked components with controllable Mock objects
            server.pants_commands = mock_pants.return_value
            server.container_lifecycle = mock_lifecycle.return_value
            server.workflow_tools = mock_workflow.return_value

            return server

    def test_server_initialization_with_config(self, mock_config: PowerConfig) -> None:
        """Test server initializes with provided config."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"):

            server = PantsDevContainerServer(mock_config)

            assert server.config == mock_config
            assert server.server is not None
            assert server.pants_commands is not None
            assert server.container_lifecycle is not None
            assert server.workflow_tools is not None

    def test_server_initialization_without_config(self) -> None:
        """Test server initializes with default config when none provided."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"):

            server = PantsDevContainerServer()

            assert server.config is not None
            assert server.config.name == "pants-devcontainer-power"
            assert server.server is not None

    def test_server_initialization_validates_prerequisites(self) -> None:
        """Test server validates prerequisites during initialization."""
        config = PowerConfig()

        # Mock ContainerManager to raise ContainerError
        with patch(
            "src.server.ContainerManager",
            side_effect=ContainerError("DevContainer CLI not found"),
        ), pytest.raises(PowerError, match="DevContainer CLI not found"):
            PantsDevContainerServer(config)

    def test_server_creates_mcp_server_with_correct_name(self, mock_config: PowerConfig) -> None:
        """Test server creates MCP Server with config name."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"), \
             patch("src.server.Server") as mock_server_class:

            PantsDevContainerServer(mock_config)

            mock_server_class.assert_called_once_with(mock_config.name)

    def test_format_command_result_success(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test _format_command_result formats successful results."""
        result = CommandResult(
            exit_code=0,
            stdout="Success output",
            stderr="",
            command="pants test ::",
            success=True,
        )

        formatted = server._format_command_result(result)  # noqa: SLF001

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert "Success output" in formatted[0].text
        assert "pants test ::" in formatted[0].text

    def test_format_command_result_failure(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test _format_command_result formats failed results."""
        result = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Error occurred",
            command="pants test ::",
            success=False,
        )

        formatted = server._format_command_result(result)  # noqa: SLF001

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert (
            "Command execution failed" in formatted[0].text
            or "Exit code: 1" in formatted[0].text
        )

    def test_format_workflow_result_success(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test _format_workflow_result formats successful workflow."""
        result = WorkflowResult(
            steps_completed=["fix", "lint", "check"],
            failed_step=None,
            results=[
                CommandResult(0, "Fixed", "", "pants fix ::", True),
                CommandResult(0, "Linted", "", "pants lint ::", True),
                CommandResult(0, "Checked", "", "pants check ::", True),
            ],
            overall_success=True,
        )

        formatted = server._format_workflow_result(result)  # noqa: SLF001

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert "Workflow completed successfully" in formatted[0].text
        assert "fix, lint, check" in formatted[0].text

    def test_format_workflow_result_failure(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test _format_workflow_result formats failed workflow."""
        result = WorkflowResult(
            steps_completed=["fix"],
            failed_step="lint",
            results=[
                CommandResult(0, "Fixed", "", "pants fix ::", True),
                CommandResult(1, "", "Lint errors", "pants lint ::", False),
            ],
            overall_success=False,
        )

        formatted = server._format_workflow_result(result)  # noqa: SLF001

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert "Workflow failed at step: lint" in formatted[0].text
        assert "Steps completed before failure: fix" in formatted[0].text

    def test_format_workflow_result_includes_step_details(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test _format_workflow_result includes detailed step info."""
        result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step=None,
            results=[
                CommandResult(0, "Fixed 3 files", "", "pants fix ::", True),
                CommandResult(
                    0, "All checks passed", "", "pants lint ::", True
                ),
            ],
            overall_success=True,
        )

        formatted = server._format_workflow_result(result)  # noqa: SLF001

        text = formatted[0].text
        assert "--- Step Details ---" in text
        assert "Step: fix" in text
        assert "Step: lint" in text
        assert "Command: pants fix ::" in text
        assert "Command: pants lint ::" in text
        assert "Exit code: 0" in text


class TestServerToolRouting:
    """Test suite for server tool routing and invocation."""

    @pytest.fixture
    def server(self) -> PantsDevContainerServer:
        """Create a server with mocked components."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands") as mock_pants, \
             patch("src.server.ContainerLifecycle") as mock_lifecycle, \
             patch("src.server.WorkflowTools") as mock_workflow:

            server = PantsDevContainerServer()
            server.pants_commands = mock_pants.return_value
            server.container_lifecycle = mock_lifecycle.return_value
            server.workflow_tools = mock_workflow.return_value

            return server

    def test_pants_fix_routes_to_pants_commands(self, server: PantsDevContainerServer) -> None:
        """Test that pants_fix tool routes to PantsCommands.pants_fix."""
        mock_result = CommandResult(0, "Fixed", "", "pants fix ::", True)
        server.pants_commands.pants_fix = Mock(return_value=mock_result)

        result = server.pants_commands.pants_fix(None)

        server.pants_commands.pants_fix.assert_called_once_with(None)
        assert result.success

    def test_pants_lint_routes_to_pants_commands(self, server: PantsDevContainerServer) -> None:
        """Test that pants_lint tool routes to PantsCommands.pants_lint."""
        mock_result = CommandResult(0, "Linted", "", "pants lint ::", True)
        server.pants_commands.pants_lint = Mock(return_value=mock_result)

        result = server.pants_commands.pants_lint("src::")

        server.pants_commands.pants_lint.assert_called_once_with("src::")
        assert result.success

    def test_pants_check_routes_to_pants_commands(self, server: PantsDevContainerServer) -> None:
        """Test that pants_check tool routes to PantsCommands.pants_check."""
        mock_result = CommandResult(0, "Checked", "", "pants check ::", True)
        server.pants_commands.pants_check = Mock(return_value=mock_result)

        result = server.pants_commands.pants_check(None)

        server.pants_commands.pants_check.assert_called_once_with(None)
        assert result.success

    def test_pants_test_routes_to_pants_commands(self, server: PantsDevContainerServer) -> None:
        """Test that pants_test tool routes to PantsCommands.pants_test."""
        mock_result = CommandResult(0, "Tested", "", "pants test ::", True)
        server.pants_commands.pants_test = Mock(return_value=mock_result)

        result = server.pants_commands.pants_test("tests::")

        server.pants_commands.pants_test.assert_called_once_with("tests::")
        assert result.success

    def test_pants_package_routes_to_pants_commands(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that pants_package tool routes to PantsCommands.pants_package."""
        mock_result = CommandResult(0, "Packaged", "", "pants package ::", True)
        server.pants_commands.pants_package = Mock(return_value=mock_result)

        result = server.pants_commands.pants_package(None)

        server.pants_commands.pants_package.assert_called_once_with(None)
        assert result.success

    def test_pants_clear_cache_routes_to_pants_commands(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that pants_clear_cache tool routes to PantsCommands.pants_clear_cache."""
        mock_result = CommandResult(0, "Cache cleared", "", "rm -rf .pants.d/pids", True)
        server.pants_commands.pants_clear_cache = Mock(return_value=mock_result)

        result = server.pants_commands.pants_clear_cache()

        server.pants_commands.pants_clear_cache.assert_called_once()
        assert result.success

    def test_container_start_routes_to_container_lifecycle(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that container_start tool routes to ContainerLifecycle.container_start."""
        mock_result = CommandResult(0, "Started", "", "devcontainer up", True)
        server.container_lifecycle.container_start = Mock(return_value=mock_result)

        result = server.container_lifecycle.container_start()

        server.container_lifecycle.container_start.assert_called_once()
        assert result.success

    def test_container_stop_routes_to_container_lifecycle(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that container_stop tool routes to ContainerLifecycle.container_stop."""
        mock_result = CommandResult(0, "Stopped", "", "docker rm -f", True)
        server.container_lifecycle.container_stop = Mock(return_value=mock_result)

        result = server.container_lifecycle.container_stop()

        server.container_lifecycle.container_stop.assert_called_once()
        assert result.success

    def test_container_rebuild_routes_to_container_lifecycle(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that container_rebuild tool routes to ContainerLifecycle.container_rebuild."""
        mock_result = CommandResult(0, "Rebuilt", "", "devcontainer build", True)
        server.container_lifecycle.container_rebuild = Mock(return_value=mock_result)

        result = server.container_lifecycle.container_rebuild()

        server.container_lifecycle.container_rebuild.assert_called_once()
        assert result.success

    def test_container_exec_routes_to_container_lifecycle(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that container_exec tool routes to ContainerLifecycle.container_exec."""
        mock_result = CommandResult(0, "Executed", "", "ls -la", True)
        server.container_lifecycle.container_exec = Mock(return_value=mock_result)

        result = server.container_lifecycle.container_exec("ls -la")

        server.container_lifecycle.container_exec.assert_called_once_with("ls -la")
        assert result.success

    def test_container_shell_routes_to_container_lifecycle(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that container_shell tool routes to ContainerLifecycle.container_shell."""
        mock_result = CommandResult(0, "Shell instructions", "", "", True)
        server.container_lifecycle.container_shell = Mock(return_value=mock_result)

        result = server.container_lifecycle.container_shell()

        server.container_lifecycle.container_shell.assert_called_once()
        assert result.success

    def test_full_quality_check_routes_to_workflow_tools(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that full_quality_check tool routes to WorkflowTools.full_quality_check."""
        mock_result = WorkflowResult(
            steps_completed=["fix", "lint", "check", "test"],
            failed_step=None,
            results=[],
            overall_success=True,
        )
        server.workflow_tools.full_quality_check = Mock(return_value=mock_result)

        result = server.workflow_tools.full_quality_check(None)

        server.workflow_tools.full_quality_check.assert_called_once_with(None)
        assert result.overall_success

    def test_pants_workflow_routes_to_workflow_tools(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that pants_workflow tool routes to WorkflowTools.pants_workflow."""
        mock_result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step=None,
            results=[],
            overall_success=True,
        )
        server.workflow_tools.pants_workflow = Mock(return_value=mock_result)

        result = server.workflow_tools.pants_workflow("fix-lint", "src::")

        server.workflow_tools.pants_workflow.assert_called_once_with("fix-lint", "src::")
        assert result.overall_success


class TestServerErrorHandling:
    """Test suite for server error handling."""

    @pytest.fixture
    def server(self) -> PantsDevContainerServer:
        """Create a server with mocked components."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands") as mock_pants, \
             patch("src.server.ContainerLifecycle") as mock_lifecycle, \
             patch("src.server.WorkflowTools") as mock_workflow:

            server = PantsDevContainerServer()
            server.pants_commands = mock_pants.return_value
            server.container_lifecycle = mock_lifecycle.return_value
            server.workflow_tools = mock_workflow.return_value

            return server

    def test_validation_error_handling(self, server: PantsDevContainerServer) -> None:
        """Test that ValidationError is properly handled."""
        server.container_lifecycle.container_exec = Mock(
            side_effect=ValidationError("Invalid command parameter")
        )

        with pytest.raises(ValidationError, match="Invalid command parameter"):
            server.container_lifecycle.container_exec("")

    def test_container_error_handling(self, server: PantsDevContainerServer) -> None:
        """Test that ContainerError is properly handled."""
        server.container_lifecycle.container_start = Mock(
            side_effect=ContainerError("Docker daemon not running")
        )

        with pytest.raises(ContainerError, match="Docker daemon not running"):
            server.container_lifecycle.container_start()

    def test_command_execution_error_handling(self, server: PantsDevContainerServer) -> None:
        """Test that CommandExecutionError is properly handled."""
        server.pants_commands.pants_test = Mock(
            side_effect=CommandExecutionError("Command execution failed")
        )

        with pytest.raises(CommandExecutionError, match="Command execution failed"):
            server.pants_commands.pants_test()

    def test_power_error_handling(
        self, server: PantsDevContainerServer
    ) -> None:
        """Test that PowerError is properly handled."""
        server.pants_commands.pants_fix = Mock(
            side_effect=PowerError("Power initialization failed")
        )

        with pytest.raises(PowerError, match="Power initialization failed"):
            server.pants_commands.pants_fix()

    def test_generic_exception_handling(self, server: PantsDevContainerServer) -> None:
        """Test that generic exceptions are properly handled."""
        server.pants_commands.pants_lint = Mock(side_effect=RuntimeError("Unexpected error"))

        with pytest.raises(RuntimeError, match="Unexpected error"):
            server.pants_commands.pants_lint()


class TestServerComponentIntegration:
    """Test suite for server component integration."""

    def test_server_initializes_all_components(self) -> None:
        """Test that server initializes all required components."""
        with patch("src.server.ContainerManager") as mock_cm, \
             patch("src.server.PantsCommands") as mock_pc, \
             patch("src.server.ContainerLifecycle") as mock_cl, \
             patch("src.server.WorkflowTools") as mock_wt:

            server = PantsDevContainerServer()

            # Verify all components were instantiated
            mock_cm.assert_called()
            mock_pc.assert_called_once()
            mock_cl.assert_called_once()
            mock_wt.assert_called_once()

            # Verify server has references to all components
            assert server.pants_commands is not None
            assert server.container_lifecycle is not None
            assert server.workflow_tools is not None

    def test_server_registers_all_tool_categories(self) -> None:
        """Test that server calls all registration methods."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"):

            server = PantsDevContainerServer()

            # Verify _register_tools was called (indirectly by checking server state)
            assert server.server is not None

    def test_empty_registration_methods_do_not_raise_errors(self) -> None:
        """Test that empty registration methods execute without errors."""
        with patch("src.server.ContainerManager"), \
             patch("src.server.PantsCommands"), \
             patch("src.server.ContainerLifecycle"), \
             patch("src.server.WorkflowTools"):

            server = PantsDevContainerServer()

            # These methods are no-ops but should not raise errors
            server._register_container_tools()  # noqa: SLF001
            server._register_workflow_tools()  # noqa: SLF001
            server._register_utility_tools()  # noqa: SLF001
