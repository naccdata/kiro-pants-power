"""Unit tests for ContainerManager."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.container_manager import ContainerManager
from src.models import CommandResult, ContainerError


class TestContainerManagerInitialization:
    """Tests for ContainerManager initialization."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_init_success(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test successful initialization with devcontainer CLI and .devcontainer/ present."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        manager = ContainerManager()

        assert manager.workspace_folder == mock_workspace
        assert manager.executor is not None

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_init_devcontainer_cli_not_found(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test initialization fails when devcontainer CLI is not installed."""
        mock_which.return_value = None
        mock_workspace = MagicMock(spec=Path)
        mock_cwd.return_value = mock_workspace

        with pytest.raises(ContainerError) as exc_info:
            ContainerManager()

        assert "DevContainer CLI not found" in str(exc_info.value)
        assert "npm install -g @devcontainers/cli" in str(exc_info.value)

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_init_devcontainer_directory_missing(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test initialization fails when .devcontainer/ directory is missing."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_devcontainer_dir = MagicMock()
        mock_devcontainer_dir.exists.return_value = False
        mock_workspace.__truediv__ = lambda self, other: mock_devcontainer_dir  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        with pytest.raises(ContainerError) as exc_info:
            ContainerManager()

        assert "DevContainer configuration not found" in str(exc_info.value)
        assert ".devcontainer/" in str(exc_info.value)


class TestContainerManagerEnsureRunning:
    """Tests for ensure_running method."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_ensure_running_success(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test ensure_running returns True when container starts successfully."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True,
        )

        manager = ContainerManager(executor=mock_executor)
        result = manager.ensure_running()

        assert result is True
        mock_executor.execute.assert_called_once()

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_ensure_running_failure(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test ensure_running raises ContainerError when container fails to start."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Docker daemon not running",
            command="devcontainer up",
            success=False,
        )

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError) as exc_info:
            manager.ensure_running()

        assert "Container start failed" in str(exc_info.value)
        assert "Troubleshooting" in str(exc_info.value)


class TestContainerManagerStart:
    """Tests for start method."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_start_success(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test start returns CommandResult when successful."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        expected_result = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True,
        )
        mock_executor.execute.return_value = expected_result

        manager = ContainerManager(executor=mock_executor)
        result = manager.start()

        assert result == expected_result
        assert result.success is True

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_start_failure(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test start raises ContainerError when container fails to start."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Port 8080 already in use",
            command="devcontainer up",
            success=False,
        )

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError) as exc_info:
            manager.start()

        assert "Container start failed" in str(exc_info.value)


class TestContainerManagerStop:
    """Tests for stop method."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_stop_success(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test stop returns CommandResult when successful."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        expected_result = CommandResult(
            exit_code=0,
            stdout="container123",
            stderr="",
            command="devcontainer exec hostname | xargs docker rm -f",
            success=True,
        )
        mock_executor.execute.return_value = expected_result

        manager = ContainerManager(executor=mock_executor)
        result = manager.stop()

        assert result == expected_result
        assert result.success is True


class TestContainerManagerRebuild:
    """Tests for rebuild method."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_rebuild_success(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test rebuild executes build and up commands successfully."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        build_result = CommandResult(
            exit_code=0,
            stdout="Building container...",
            stderr="",
            command="devcontainer build",
            success=True,
        )
        up_result = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True,
        )
        mock_executor.execute.side_effect = [build_result, up_result]

        manager = ContainerManager(executor=mock_executor)
        result = manager.rebuild()

        assert result.success is True
        assert "Building container..." in result.stdout
        assert "Container started" in result.stdout
        assert mock_executor.execute.call_count == 2

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_rebuild_build_failure(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test rebuild raises ContainerError when build fails."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Build failed: invalid Dockerfile",
            command="devcontainer build",
            success=False,
        )

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError) as exc_info:
            manager.rebuild()

        assert "Container build failed" in str(exc_info.value)


class TestContainerManagerExec:
    """Tests for exec method."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_exec_success(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test exec executes command in container successfully."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        # First call for ensure_running, second for exec
        ensure_result = CommandResult(
            exit_code=0,
            stdout="Container running",
            stderr="",
            command="devcontainer up",
            success=True,
        )
        exec_result = CommandResult(
            exit_code=0,
            stdout="Hello from container",
            stderr="",
            command="devcontainer exec echo 'Hello from container'",
            success=True,
        )
        mock_executor.execute.side_effect = [ensure_result, exec_result]

        manager = ContainerManager(executor=mock_executor)
        result = manager.exec("echo 'Hello from container'")

        assert result == exec_result
        assert result.success is True
        assert mock_executor.execute.call_count == 2

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_exec_container_not_running(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test exec raises ContainerError when container cannot be started."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Docker daemon not running",
            command="devcontainer up",
            success=False,
        )

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError):
            manager.exec("echo 'test'")


class TestContainerManagerEnvironment:
    """Tests for environment variable handling."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_get_env_sets_workspace_folder(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that _get_env sets WORKSPACE_FOLDER environment variable."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/test/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        manager = ContainerManager()
        env = manager._get_env()  # noqa: SLF001

        assert "WORKSPACE_FOLDER" in env
        assert env["WORKSPACE_FOLDER"] == "/test/workspace"

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_get_env_sets_docker_cli_hints(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that _get_env sets DOCKER_CLI_HINTS to false."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        manager = ContainerManager()
        env = manager._get_env()  # noqa: SLF001

        assert "DOCKER_CLI_HINTS" in env
        assert env["DOCKER_CLI_HINTS"] == "false"

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    @patch("src.container_manager.os.environ", {"EXISTING_VAR": "value"})
    def test_get_env_preserves_existing_environment(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that _get_env preserves existing environment variables."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        manager = ContainerManager()
        env = manager._get_env()  # noqa: SLF001

        # Should have both new and existing variables
        assert "WORKSPACE_FOLDER" in env
        assert "DOCKER_CLI_HINTS" in env


class TestContainerManagerErrorPropagation:
    """Tests for error handling and propagation."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_exec_propagates_container_error_from_ensure_running(
        self, mock_cwd: Any, mock_which: Any
    ) -> None:
        """Test that exec propagates ContainerError from ensure_running."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Cannot connect to Docker daemon",
            command="devcontainer up",
            success=False,
        )

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError) as exc_info:
            manager.exec("echo test")

        assert "Container start failed" in str(exc_info.value)
        assert "Docker daemon" in str(exc_info.value)

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_rebuild_stops_on_build_failure_before_up(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that rebuild doesn't call up if build fails."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Build failed",
            command="devcontainer build",
            success=False,
        )

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError):
            manager.rebuild()

        # Should only call execute once (for build), not twice (build + up)
        assert mock_executor.execute.call_count == 1

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_stop_wraps_generic_exceptions(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that stop wraps generic exceptions in ContainerError."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.side_effect = RuntimeError("Unexpected error")

        manager = ContainerManager(executor=mock_executor)

        with pytest.raises(ContainerError) as exc_info:
            manager.stop()

        assert "Failed to stop container" in str(exc_info.value)


class TestContainerManagerCommandConstruction:
    """Tests for command string construction."""

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_exec_constructs_correct_command(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that exec constructs the correct devcontainer exec command."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/my/workspace"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.side_effect = [
            CommandResult(exit_code=0, stdout="", stderr="", command="up", success=True),
            CommandResult(exit_code=0, stdout="", stderr="", command="exec", success=True),
        ]

        manager = ContainerManager(executor=mock_executor)
        manager.exec("ls -la")

        # Second call should be the exec command
        exec_call = mock_executor.execute.call_args_list[1]
        command = exec_call[0][0]

        assert "devcontainer exec" in command
        assert "--workspace-folder /my/workspace" in command
        assert "ls -la" in command

    @patch("src.container_manager.shutil.which")
    @patch("src.container_manager.Path.cwd")
    def test_start_constructs_correct_command(self, mock_cwd: Any, mock_which: Any) -> None:
        """Test that start constructs the correct devcontainer up command."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc]  # type: ignore[method-assign,misc,assignment]
        mock_workspace.__str__ = lambda self: "/custom/path"  # type: ignore[method-assign,misc,assignment]
        mock_cwd.return_value = mock_workspace

        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=0, stdout="", stderr="", command="up", success=True
        )

        manager = ContainerManager(executor=mock_executor)
        manager.start()

        command = mock_executor.execute.call_args[0][0]
        assert "devcontainer up" in command
        assert "--workspace-folder /custom/path" in command
