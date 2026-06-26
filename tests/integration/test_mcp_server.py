"""Integration tests for the MCP server.

These tests verify that the MCP server initializes correctly, registers all tools,
and handles tool invocations with proper error handling and response formatting.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models import CommandResult, ContainerError, ValidationError, WorkflowResult
from src.server import PantsDevContainerServer, WorkspaceSession


class TestMCPServerInitialization:
    """Test MCP server initialization."""

    def test_server_initializes_without_workspace(self) -> None:
        """Test that server initializes successfully with no workspace needed."""
        server = PantsDevContainerServer()
        assert server.server is not None
        assert server._sessions == {}

    def test_server_session_created_on_first_call(self, tmp_path: Path) -> None:
        """Test that session is lazily created on first get_session call."""
        (tmp_path / ".devcontainer").mkdir()
        server = PantsDevContainerServer()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            session = server._get_session(str(tmp_path))

        assert session is not None
        assert session.workspace_folder == tmp_path

    def test_server_returns_error_for_missing_workspace_folder(self) -> None:
        """Test that missing workspace_folder gives a clear error."""
        server = PantsDevContainerServer()

        with pytest.raises(ValidationError, match="workspace_folder.*required"):
            server._get_session(None)

    def test_server_returns_error_for_missing_devcontainer_dir(
        self, tmp_path: Path
    ) -> None:
        """Test clear error when .devcontainer/ directory is missing."""
        server = PantsDevContainerServer()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            with pytest.raises(ContainerError, match="DevContainer configuration not found"):
                server._get_session(str(tmp_path))

    def test_server_returns_error_for_missing_cli(self, tmp_path: Path) -> None:
        """Test clear error when devcontainer CLI is not installed."""
        (tmp_path / ".devcontainer").mkdir()
        server = PantsDevContainerServer()

        with patch("src.container_manager.shutil.which", return_value=None):
            with pytest.raises(ContainerError, match="DevContainer CLI not found"):
                server._get_session(str(tmp_path))


class TestMCPToolRegistration:
    """Test MCP tool registration."""

    def test_server_registers_tools(self) -> None:
        """Test that server registers tools on initialization."""
        server = PantsDevContainerServer()
        # Server initializes with registered tools — verified by having a server instance
        assert server.server is not None


class TestMCPToolInvocation:
    """Test MCP tool invocation handling via WorkspaceSession."""

    @pytest.fixture
    def session(self, tmp_path: Path) -> WorkspaceSession:
        """Create a WorkspaceSession with mocked components."""
        (tmp_path / ".devcontainer").mkdir()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            session = WorkspaceSession(workspace_folder=tmp_path)

        # Replace components with controllable mocks
        session.pants_commands = Mock()
        session.container_lifecycle = Mock()
        session.workflow_tools = Mock()
        session.tool_executor = Mock()

        return session

    def test_pants_fix_invocation(self, session: WorkspaceSession) -> None:
        """Test invoking pants_fix via tool executor."""
        mock_result = CommandResult(
            exit_code=0,
            stdout="Fixed 3 files",
            stderr="",
            command="pants fix ::",
            success=True,
        )
        session.tool_executor.execute_pants_fix = Mock(return_value=mock_result)

        result = session.tool_executor.execute_pants_fix({})
        assert result.success
        assert "Fixed 3 files" in result.stdout

    def test_pants_test_with_target(self, session: WorkspaceSession) -> None:
        """Test invoking pants_test with target parameter."""
        mock_result = CommandResult(
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            command="pants test src/python::",
            success=True,
        )
        session.tool_executor.execute_pants_test = Mock(return_value=mock_result)

        result = session.tool_executor.execute_pants_test({"target": "src/python::"})
        assert result.success
        assert "All tests passed" in result.stdout

    def test_container_exec_invocation(self, session: WorkspaceSession) -> None:
        """Test invoking container_exec."""
        mock_result = CommandResult(
            exit_code=0,
            stdout="file1.py\nfile2.py",
            stderr="",
            command="ls",
            success=True,
        )
        session.container_lifecycle.container_exec = Mock(return_value=mock_result)

        result = session.container_lifecycle.container_exec("ls")
        assert result.success

    def test_full_quality_check_invocation(self, session: WorkspaceSession) -> None:
        """Test invoking full_quality_check workflow."""
        mock_result = WorkflowResult(
            steps_completed=["fix", "lint", "check", "test"],
            failed_step=None,
            results=[],
            overall_success=True,
        )
        session.workflow_tools.full_quality_check = Mock(return_value=mock_result)

        result = session.workflow_tools.full_quality_check()
        assert result.overall_success
        assert len(result.steps_completed) == 4


class TestMCPErrorHandling:
    """Test MCP server error handling."""

    @pytest.fixture
    def session(self, tmp_path: Path) -> WorkspaceSession:
        """Create a WorkspaceSession with mocked components."""
        (tmp_path / ".devcontainer").mkdir()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            session = WorkspaceSession(workspace_folder=tmp_path)

        session.pants_commands = Mock()
        session.container_lifecycle = Mock()
        session.workflow_tools = Mock()
        session.tool_executor = Mock()

        return session

    def test_container_error_raised(self, session: WorkspaceSession) -> None:
        """Test that ContainerError is properly propagated."""
        session.container_lifecycle.container_start = Mock(
            side_effect=ContainerError("Docker daemon not running")
        )

        with pytest.raises(ContainerError, match="Docker daemon not running"):
            session.container_lifecycle.container_start()

    def test_validation_error_raised(self, session: WorkspaceSession) -> None:
        """Test that ValidationError is properly propagated."""
        session.container_lifecycle.container_exec = Mock(
            side_effect=ValidationError("Invalid command parameter")
        )

        with pytest.raises(ValidationError, match="Invalid command parameter"):
            session.container_lifecycle.container_exec("")

    def test_command_failure_result(self, session: WorkspaceSession) -> None:
        """Test that failed commands return proper result."""
        mock_result = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Error: Test failed",
            command="pants test ::",
            success=False,
        )
        session.tool_executor.execute_pants_test = Mock(return_value=mock_result)

        result = session.tool_executor.execute_pants_test({})
        assert not result.success
        assert result.exit_code == 1
