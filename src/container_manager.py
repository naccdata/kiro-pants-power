"""Container lifecycle management for devcontainers."""

import os
import shutil
from pathlib import Path
from typing import Optional

from src.command_executor import CommandExecutor
from src.models import CommandResult, ContainerError


class ContainerManager:
    """Manages devcontainer lifecycle operations.
    
    This class handles starting, stopping, rebuilding, and executing commands
    within devcontainers using the devcontainer CLI.
    
    Attributes:
        executor: CommandExecutor instance for running shell commands
        workspace_folder: Path to the workspace root directory
    """
    
    def __init__(self, executor: Optional[CommandExecutor] = None, workspace_folder: Optional[Path] = None):
        """Initialize the ContainerManager.
        
        Args:
            executor: CommandExecutor instance (creates new one if None)
            workspace_folder: Workspace root path (uses current directory if None)
        """
        self.executor = executor or CommandExecutor()
        self.workspace_folder = workspace_folder or self._get_workspace_folder()
        
        # Check if devcontainer CLI is installed
        if not self._check_devcontainer_cli():
            raise ContainerError(
                "DevContainer CLI not found\n\n"
                "The devcontainer CLI is required to use this power.\n\n"
                "Install it with: npm install -g @devcontainers/cli\n\n"
                "For more information: https://containers.dev/supporting"
            )
        
        # Check if .devcontainer directory exists
        devcontainer_dir = self.workspace_folder / ".devcontainer"
        if not devcontainer_dir.exists():
            raise ContainerError(
                "DevContainer configuration not found\n\n"
                f"This power requires a .devcontainer/ directory with devcontainer.json.\n\n"
                f"Current directory: {self.workspace_folder}\n\n"
                "Please run this power from a repository with devcontainer configuration."
            )
    
    def _check_devcontainer_cli(self) -> bool:
        """Check if the devcontainer CLI is installed.
        
        Returns:
            True if devcontainer CLI is found in PATH, False otherwise
        """
        return shutil.which("devcontainer") is not None
    
    def _get_workspace_folder(self) -> Path:
        """Get the repository root directory.
        
        Returns:
            Path to the workspace folder (current working directory)
        """
        return Path.cwd()
    
    def _get_env(self) -> dict:
        """Get environment variables for devcontainer commands.
        
        Returns:
            Dictionary with WORKSPACE_FOLDER and DOCKER_CLI_HINTS set
        """
        env = os.environ.copy()
        env["WORKSPACE_FOLDER"] = str(self.workspace_folder)
        env["DOCKER_CLI_HINTS"] = "false"
        return env

    def ensure_running(self) -> bool:
        """Ensure the devcontainer is running, starting it if needed.
        
        This method is idempotent - it's safe to call multiple times.
        If the container is already running, it returns True without restarting.
        
        Returns:
            True if container is running or was successfully started, False otherwise
        """
        command = f"devcontainer up --workspace-folder {self.workspace_folder}"
        
        try:
            # Execute with custom environment variables
            result = self.executor.execute(command, cwd=str(self.workspace_folder))
            
            if result.success:
                return True
            else:
                # Provide troubleshooting guidance
                error_msg = (
                    f"Container start failed: devcontainer up exited with code {result.exit_code}\n\n"
                    f"Output:\n{result.output}\n\n"
                    "Troubleshooting:\n"
                    "1. Check if Docker Desktop is running\n"
                    "2. Verify Docker daemon is accessible: docker ps\n"
                    "3. Check Docker permissions: docker run hello-world\n"
                    "4. Ensure devcontainer CLI is installed: npm install -g @devcontainers/cli\n"
                    "5. Check for port conflicts or resource constraints\n"
                    "6. Verify .devcontainer/devcontainer.json is valid"
                )
                raise ContainerError(error_msg)
                
        except ContainerError:
            # Re-raise ContainerError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise ContainerError(
                f"Failed to start container: {str(e)}\n\n"
                "Please check that Docker is running and the devcontainer CLI is properly installed."
            ) from e

    def start(self) -> CommandResult:
        """Start the devcontainer.
        
        This is an idempotent operation - safe to call multiple times.
        
        Returns:
            CommandResult with the outcome of the start operation
        """
        command = f"devcontainer up --workspace-folder {self.workspace_folder}"
        
        try:
            result = self.executor.execute(command, cwd=str(self.workspace_folder))
            
            if not result.success:
                error_msg = (
                    f"Container start failed: devcontainer up exited with code {result.exit_code}\n\n"
                    f"Output:\n{result.output}\n\n"
                    "Troubleshooting:\n"
                    "1. Check if Docker Desktop is running\n"
                    "2. Verify Docker daemon is accessible: docker ps\n"
                    "3. Check Docker permissions: docker run hello-world\n"
                    "4. Ensure devcontainer CLI is installed: npm install -g @devcontainers/cli"
                )
                raise ContainerError(error_msg)
            
            return result
            
        except ContainerError:
            raise
        except Exception as e:
            raise ContainerError(f"Failed to start container: {str(e)}") from e

    def stop(self) -> CommandResult:
        """Stop the devcontainer.
        
        Returns:
            CommandResult with the outcome of the stop operation
        """
        # Get container hostname, then stop it using docker
        command = f"devcontainer exec --workspace-folder {self.workspace_folder} hostname | xargs docker rm -f"
        
        try:
            result = self.executor.execute(command, cwd=str(self.workspace_folder))
            return result
            
        except Exception as e:
            raise ContainerError(f"Failed to stop container: {str(e)}") from e

    def rebuild(self) -> CommandResult:
        """Rebuild and restart the devcontainer.
        
        This method rebuilds the container image and then starts the container.
        
        Returns:
            CommandResult with the outcome of the rebuild operation
        """
        try:
            # First, build the container
            build_command = f"devcontainer build --workspace-folder {self.workspace_folder}"
            build_result = self.executor.execute(build_command, cwd=str(self.workspace_folder))
            
            if not build_result.success:
                error_msg = (
                    f"Container build failed: devcontainer build exited with code {build_result.exit_code}\n\n"
                    f"Output:\n{build_result.output}"
                )
                raise ContainerError(error_msg)
            
            # Then, start the container
            up_command = f"devcontainer up --workspace-folder {self.workspace_folder}"
            up_result = self.executor.execute(up_command, cwd=str(self.workspace_folder))
            
            if not up_result.success:
                error_msg = (
                    f"Container start after build failed: devcontainer up exited with code {up_result.exit_code}\n\n"
                    f"Output:\n{up_result.output}"
                )
                raise ContainerError(error_msg)
            
            # Return combined result
            return CommandResult(
                exit_code=up_result.exit_code,
                stdout=f"{build_result.stdout}\n{up_result.stdout}",
                stderr=f"{build_result.stderr}\n{up_result.stderr}",
                command=f"{build_command} && {up_command}",
                success=True
            )
            
        except ContainerError:
            raise
        except Exception as e:
            raise ContainerError(f"Failed to rebuild container: {str(e)}") from e

    def exec(self, command: str) -> CommandResult:
        """Execute a command in the running devcontainer.
        
        This method ensures the container is running before executing the command.
        
        Args:
            command: The shell command to execute in the container
            
        Returns:
            CommandResult with the outcome of the command execution
        """
        # Ensure container is running first
        if not self.ensure_running():
            raise ContainerError("Failed to ensure container is running before executing command")
        
        # Execute the command in the container
        exec_command = f"devcontainer exec --workspace-folder {self.workspace_folder} {command}"
        
        try:
            result = self.executor.execute(exec_command, cwd=str(self.workspace_folder))
            return result
            
        except Exception as e:
            raise ContainerError(f"Failed to execute command in container: {str(e)}") from e
