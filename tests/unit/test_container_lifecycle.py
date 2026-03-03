"""Unit tests for container lifecycle tools."""

from typing import Any
from unittest.mock import Mock

import pytest

from src.container_lifecycle import ContainerLifecycle
from src.models import CommandResult, ValidationError


class TestContainerLifecycle:
    """Test suite for ContainerLifecycle class."""

    @pytest.fixture
    def mock_container_manager(self) -> Mock:
        """Create a mock ContainerManager."""
        return Mock()

    @pytest.fixture
    def lifecycle(self, mock_container_manager: Mock) -> ContainerLifecycle:
        """Create ContainerLifecycle instance with mock manager."""
        return ContainerLifecycle(container_manager=mock_container_manager)

    def test_container_start_calls_manager_start(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test that container_start calls ContainerManager.start."""
        # Arrange
        expected_result = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True,
        )
        mock_container_manager.start.return_value = expected_result

        # Act
        result = lifecycle.container_start()

        # Assert
        mock_container_manager.start.assert_called_once()
        assert result == expected_result
        assert result.success is True

    def test_container_stop_calls_manager_stop(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test that container_stop calls ContainerManager.stop."""
        # Arrange
        expected_result = CommandResult(
            exit_code=0,
            stdout="Container stopped",
            stderr="",
            command="devcontainer exec hostname | xargs docker rm -f",
            success=True,
        )
        mock_container_manager.stop.return_value = expected_result

        # Act
        result = lifecycle.container_stop()

        # Assert
        mock_container_manager.stop.assert_called_once()
        assert result == expected_result
        assert result.success is True

    def test_container_rebuild_calls_manager_rebuild(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test that container_rebuild calls ContainerManager.rebuild."""
        # Arrange
        expected_result = CommandResult(
            exit_code=0,
            stdout="Container rebuilt",
            stderr="",
            command="devcontainer build && devcontainer up",
            success=True,
        )
        mock_container_manager.rebuild.return_value = expected_result

        # Act
        result = lifecycle.container_rebuild()

        # Assert
        mock_container_manager.rebuild.assert_called_once()
        assert result == expected_result
        assert result.success is True

    def test_container_exec_with_valid_command(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test container_exec with a valid command."""
        # Arrange
        command = "ls -la"
        expected_result = CommandResult(
            exit_code=0,
            stdout="file1.txt\nfile2.txt",
            stderr="",
            command=f"devcontainer exec {command}",
            success=True,
        )
        mock_container_manager.exec.return_value = expected_result

        # Act
        result = lifecycle.container_exec(command)

        # Assert
        mock_container_manager.exec.assert_called_once_with(command)
        assert result == expected_result
        assert result.success is True

    def test_container_exec_with_empty_command_raises_validation_error(
        self, lifecycle: Any
    ) -> None:
        """Test that container_exec raises ValidationError for empty command."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            lifecycle.container_exec("")

        assert "Invalid command parameter" in str(exc_info.value)
        assert "cannot be empty" in str(exc_info.value)

    def test_container_exec_with_whitespace_only_command_raises_validation_error(
        self, lifecycle: Any
    ) -> None:
        """Test that container_exec raises ValidationError for whitespace-only command."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            lifecycle.container_exec("   ")

        assert "Invalid command parameter" in str(exc_info.value)

    def test_container_exec_with_complex_command(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test container_exec with a complex command."""
        # Arrange
        command = "python -m pytest tests/ --verbose"
        expected_result = CommandResult(
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            command=f"devcontainer exec {command}",
            success=True,
        )
        mock_container_manager.exec.return_value = expected_result

        # Act
        result = lifecycle.container_exec(command)

        # Assert
        mock_container_manager.exec.assert_called_once_with(command)
        assert result == expected_result

    def test_container_shell_returns_instructions(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test that container_shell returns instructions for opening a shell."""
        # Arrange
        mock_container_manager.workspace_folder = "/home/user/project"

        # Act
        result = lifecycle.container_shell()

        # Assert
        assert result.success is True
        assert result.exit_code == 0
        assert "devcontainer exec --workspace-folder" in result.stdout
        assert "/bin/zsh -l" in result.stdout
        assert "Interactive shells cannot be opened via MCP" in result.stdout
        assert "/home/user/project" in result.command

    def test_container_shell_includes_workspace_folder(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test that container_shell includes the correct workspace folder."""
        # Arrange
        mock_container_manager.workspace_folder = "/custom/workspace"

        # Act
        result = lifecycle.container_shell()

        # Assert
        assert "/custom/workspace" in result.command
        assert "/custom/workspace" in result.stdout

    def test_container_start_with_failure(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test container_start when start fails."""
        # Arrange
        expected_result = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Container failed to start",
            command="devcontainer up",
            success=False,
        )
        mock_container_manager.start.return_value = expected_result

        # Act
        result = lifecycle.container_start()

        # Assert
        assert result.success is False
        assert result.exit_code == 1

    def test_container_exec_passes_command_unchanged(
        self, lifecycle: Any, mock_container_manager: Any
    ) -> None:
        """Test that container_exec passes the command to manager unchanged."""
        # Arrange
        command = "echo 'hello world' && ls -la"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0, stdout="", stderr="", command=command, success=True
        )

        # Act
        lifecycle.container_exec(command)

        # Assert
        # Verify the exact command was passed
        mock_container_manager.exec.assert_called_once_with(command)
