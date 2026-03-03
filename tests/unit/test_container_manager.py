"""Unit tests for ContainerManager."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.container_manager import ContainerManager
from src.models import CommandResult, ContainerError


class TestContainerManagerInitialization:
    """Tests for ContainerManager initialization."""
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_init_success(self, mock_cwd, mock_which):
        """Test successful initialization with devcontainer CLI and .devcontainer/ present."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_cwd.return_value = mock_workspace
        
        manager = ContainerManager()
        
        assert manager.workspace_folder == mock_workspace
        assert manager.executor is not None
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_init_devcontainer_cli_not_found(self, mock_cwd, mock_which):
        """Test initialization fails when devcontainer CLI is not installed."""
        mock_which.return_value = None
        mock_workspace = MagicMock(spec=Path)
        mock_cwd.return_value = mock_workspace
        
        with pytest.raises(ContainerError) as exc_info:
            ContainerManager()
        
        assert "DevContainer CLI not found" in str(exc_info.value)
        assert "npm install -g @devcontainers/cli" in str(exc_info.value)
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_init_devcontainer_directory_missing(self, mock_cwd, mock_which):
        """Test initialization fails when .devcontainer/ directory is missing."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_devcontainer_dir = MagicMock()
        mock_devcontainer_dir.exists.return_value = False
        mock_workspace.__truediv__ = lambda self, other: mock_devcontainer_dir
        mock_cwd.return_value = mock_workspace
        
        with pytest.raises(ContainerError) as exc_info:
            ContainerManager()
        
        assert "DevContainer configuration not found" in str(exc_info.value)
        assert ".devcontainer/" in str(exc_info.value)


class TestContainerManagerEnsureRunning:
    """Tests for ensure_running method."""
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_ensure_running_success(self, mock_cwd, mock_which):
        """Test ensure_running returns True when container starts successfully."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True
        )
        
        manager = ContainerManager(executor=mock_executor)
        result = manager.ensure_running()
        
        assert result is True
        mock_executor.execute.assert_called_once()
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_ensure_running_failure(self, mock_cwd, mock_which):
        """Test ensure_running raises ContainerError when container fails to start."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Docker daemon not running",
            command="devcontainer up",
            success=False
        )
        
        manager = ContainerManager(executor=mock_executor)
        
        with pytest.raises(ContainerError) as exc_info:
            manager.ensure_running()
        
        assert "Container start failed" in str(exc_info.value)
        assert "Troubleshooting" in str(exc_info.value)


class TestContainerManagerStart:
    """Tests for start method."""
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_start_success(self, mock_cwd, mock_which):
        """Test start returns CommandResult when successful."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        expected_result = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True
        )
        mock_executor.execute.return_value = expected_result
        
        manager = ContainerManager(executor=mock_executor)
        result = manager.start()
        
        assert result == expected_result
        assert result.success is True
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_start_failure(self, mock_cwd, mock_which):
        """Test start raises ContainerError when container fails to start."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Port 8080 already in use",
            command="devcontainer up",
            success=False
        )
        
        manager = ContainerManager(executor=mock_executor)
        
        with pytest.raises(ContainerError) as exc_info:
            manager.start()
        
        assert "Container start failed" in str(exc_info.value)


class TestContainerManagerStop:
    """Tests for stop method."""
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_stop_success(self, mock_cwd, mock_which):
        """Test stop returns CommandResult when successful."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        expected_result = CommandResult(
            exit_code=0,
            stdout="container123",
            stderr="",
            command="devcontainer exec hostname | xargs docker rm -f",
            success=True
        )
        mock_executor.execute.return_value = expected_result
        
        manager = ContainerManager(executor=mock_executor)
        result = manager.stop()
        
        assert result == expected_result
        assert result.success is True


class TestContainerManagerRebuild:
    """Tests for rebuild method."""
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_rebuild_success(self, mock_cwd, mock_which):
        """Test rebuild executes build and up commands successfully."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        build_result = CommandResult(
            exit_code=0,
            stdout="Building container...",
            stderr="",
            command="devcontainer build",
            success=True
        )
        up_result = CommandResult(
            exit_code=0,
            stdout="Container started",
            stderr="",
            command="devcontainer up",
            success=True
        )
        mock_executor.execute.side_effect = [build_result, up_result]
        
        manager = ContainerManager(executor=mock_executor)
        result = manager.rebuild()
        
        assert result.success is True
        assert "Building container..." in result.stdout
        assert "Container started" in result.stdout
        assert mock_executor.execute.call_count == 2
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_rebuild_build_failure(self, mock_cwd, mock_which):
        """Test rebuild raises ContainerError when build fails."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Build failed: invalid Dockerfile",
            command="devcontainer build",
            success=False
        )
        
        manager = ContainerManager(executor=mock_executor)
        
        with pytest.raises(ContainerError) as exc_info:
            manager.rebuild()
        
        assert "Container build failed" in str(exc_info.value)


class TestContainerManagerExec:
    """Tests for exec method."""
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_exec_success(self, mock_cwd, mock_which):
        """Test exec executes command in container successfully."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        # First call for ensure_running, second for exec
        ensure_result = CommandResult(
            exit_code=0,
            stdout="Container running",
            stderr="",
            command="devcontainer up",
            success=True
        )
        exec_result = CommandResult(
            exit_code=0,
            stdout="Hello from container",
            stderr="",
            command="devcontainer exec echo 'Hello from container'",
            success=True
        )
        mock_executor.execute.side_effect = [ensure_result, exec_result]
        
        manager = ContainerManager(executor=mock_executor)
        result = manager.exec("echo 'Hello from container'")
        
        assert result == exec_result
        assert result.success is True
        assert mock_executor.execute.call_count == 2
    
    @patch('src.container_manager.shutil.which')
    @patch('src.container_manager.Path.cwd')
    def test_exec_container_not_running(self, mock_cwd, mock_which):
        """Test exec raises ContainerError when container cannot be started."""
        mock_which.return_value = "/usr/local/bin/devcontainer"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_workspace.__str__ = lambda self: "/workspace"
        mock_cwd.return_value = mock_workspace
        
        mock_executor = Mock()
        mock_executor.execute.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Docker daemon not running",
            command="devcontainer up",
            success=False
        )
        
        manager = ContainerManager(executor=mock_executor)
        
        with pytest.raises(ContainerError):
            manager.exec("echo 'test'")
