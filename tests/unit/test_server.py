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
from src.server import PantsDevContainerServer, WorkspaceSession, _inject_workspace_param


class TestInjectWorkspaceParam:
    """Test suite for _inject_workspace_param helper."""

    def test_adds_workspace_folder_to_empty_schema(self) -> None:
        """Test adding workspace_folder to a schema with no properties."""
        schema = {"type": "object", "properties": {}}
        result = _inject_workspace_param(schema)

        assert "workspace_folder" in result["properties"]
        assert result["required"] == ["workspace_folder"]

    def test_adds_workspace_folder_to_schema_with_existing_required(self) -> None:
        """Test adding workspace_folder to schema that already has required fields."""
        schema = {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "A command"},
            },
            "required": ["command"],
        }
        result = _inject_workspace_param(schema)

        assert "workspace_folder" in result["properties"]
        assert "command" in result["properties"]
        assert result["required"] == ["workspace_folder", "command"]

    def test_does_not_duplicate_workspace_folder_in_required(self) -> None:
        """Test that workspace_folder isn't duplicated if already in required."""
        schema = {
            "type": "object",
            "properties": {},
            "required": ["workspace_folder"],
        }
        result = _inject_workspace_param(schema)
        assert result["required"].count("workspace_folder") == 1

    def test_does_not_mutate_original_schema(self) -> None:
        """Test that the original schema dict is not mutated."""
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        _inject_workspace_param(schema)
        assert "workspace_folder" not in schema["properties"]


class TestWorkspaceSession:
    """Test suite for WorkspaceSession class."""

    def test_session_initializes_components(self, tmp_path: Path) -> None:
        """Test that WorkspaceSession creates all components."""
        # Create .devcontainer/ so ContainerManager doesn't complain
        (tmp_path / ".devcontainer").mkdir()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            session = WorkspaceSession(workspace_folder=tmp_path)

        assert session.workspace_folder == tmp_path
        assert session.container_manager is not None
        assert session.pants_commands is not None
        assert session.container_lifecycle is not None
        assert session.workflow_tools is not None
        assert session.tool_executor is not None

    def test_session_raises_container_error_without_devcontainer_dir(
        self, tmp_path: Path
    ) -> None:
        """Test that session raises ContainerError if .devcontainer/ is missing."""
        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            with pytest.raises(ContainerError, match="DevContainer configuration not found"):
                WorkspaceSession(workspace_folder=tmp_path)

    def test_session_raises_container_error_without_cli(self, tmp_path: Path) -> None:
        """Test that session raises ContainerError if devcontainer CLI is missing."""
        (tmp_path / ".devcontainer").mkdir()

        with patch("src.container_manager.shutil.which", return_value=None):
            with pytest.raises(ContainerError, match="DevContainer CLI not found"):
                WorkspaceSession(workspace_folder=tmp_path)


class TestPantsDevContainerServer:
    """Test suite for PantsDevContainerServer class."""

    def test_server_initializes_without_error(self) -> None:
        """Test server initializes successfully with no startup validation."""
        server = PantsDevContainerServer()
        assert server.server is not None
        assert server._sessions == {}

    def test_server_creates_mcp_server_with_correct_name(self) -> None:
        """Test server creates MCP Server with expected name."""
        with patch("src.server.Server") as mock_server_class:
            PantsDevContainerServer()
            mock_server_class.assert_called_once_with("pants-devcontainer-power")

    def test_get_session_returns_cached_session(self, tmp_path: Path) -> None:
        """Test that _get_session caches and reuses sessions."""
        (tmp_path / ".devcontainer").mkdir()
        server = PantsDevContainerServer()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            session1 = server._get_session(str(tmp_path))
            session2 = server._get_session(str(tmp_path))

        assert session1 is session2

    def test_get_session_raises_validation_error_when_missing(self) -> None:
        """Test that _get_session raises ValidationError for None workspace."""
        server = PantsDevContainerServer()

        with pytest.raises(ValidationError, match="workspace_folder.*required"):
            server._get_session(None)

    def test_get_session_raises_validation_error_for_empty_string(self) -> None:
        """Test that _get_session raises ValidationError for empty workspace."""
        server = PantsDevContainerServer()

        with pytest.raises(ValidationError, match="workspace_folder.*required"):
            server._get_session("")

    def test_get_session_raises_validation_error_for_nonexistent_path(self) -> None:
        """Test that _get_session raises ValidationError for non-existent path."""
        server = PantsDevContainerServer()

        with pytest.raises(ValidationError, match="does not exist"):
            server._get_session("/nonexistent/path/that/does/not/exist")

    def test_get_session_raises_container_error_for_missing_devcontainer(
        self, tmp_path: Path
    ) -> None:
        """Test that _get_session raises ContainerError when .devcontainer/ missing."""
        server = PantsDevContainerServer()

        with patch("src.container_manager.shutil.which", return_value="/usr/bin/devcontainer"):
            with pytest.raises(ContainerError, match="DevContainer configuration not found"):
                server._get_session(str(tmp_path))


class TestServerFormatting:
    """Test suite for server result formatting methods."""

    @pytest.fixture
    def server(self) -> PantsDevContainerServer:
        """Create a server instance for testing."""
        return PantsDevContainerServer()

    def test_format_command_result_success(self, server: PantsDevContainerServer) -> None:
        """Test _format_command_result formats successful results."""
        result = CommandResult(
            exit_code=0,
            stdout="Success output",
            stderr="",
            command="pants test ::",
            success=True,
        )

        formatted = server._format_command_result(result)

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert "Success output" in formatted[0].text
        assert "pants test ::" in formatted[0].text

    def test_format_command_result_failure(self, server: PantsDevContainerServer) -> None:
        """Test _format_command_result formats failed results."""
        result = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Error occurred",
            command="pants test ::",
            success=False,
        )

        formatted = server._format_command_result(result)

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert (
            "Command execution failed" in formatted[0].text
            or "Exit code: 1" in formatted[0].text
        )

    def test_format_workflow_result_success(self, server: PantsDevContainerServer) -> None:
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

        formatted = server._format_workflow_result(result)

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert "Workflow completed successfully" in formatted[0].text
        assert "fix, lint, check" in formatted[0].text

    def test_format_workflow_result_failure(self, server: PantsDevContainerServer) -> None:
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

        formatted = server._format_workflow_result(result)

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
                CommandResult(0, "All checks passed", "", "pants lint ::", True),
            ],
            overall_success=True,
        )

        formatted = server._format_workflow_result(result)

        text = formatted[0].text
        assert "--- Step Details ---" in text
        assert "Step: fix" in text
        assert "Step: lint" in text
        assert "Command: pants fix ::" in text
        assert "Command: pants lint ::" in text
        assert "Exit code: 0" in text
