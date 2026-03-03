"""Container lifecycle tools for the MCP server.

This module provides container lifecycle management tools that wrap devcontainer
CLI commands for starting, stopping, rebuilding, and executing commands in containers.
"""


from src.container_manager import ContainerManager
from src.models import CommandResult, ValidationError


class ContainerLifecycle:
    """Provides container lifecycle management tools.

    This class implements container lifecycle tools (start, stop, rebuild, exec, shell)
    that manage the devcontainer lifecycle and execute arbitrary commands.

    Attributes:
        container_manager: ContainerManager instance for container operations
    """

    def __init__(self, container_manager: ContainerManager | None = None):
        """Initialize ContainerLifecycle.

        Args:
            container_manager: ContainerManager instance (creates new one if None)
        """
        self.container_manager = container_manager or ContainerManager()

    def container_start(self) -> CommandResult:
        """Start the devcontainer (idempotent).

        This operation is idempotent - it's safe to call multiple times.
        If the container is already running, it returns success without restarting.

        Returns:
            CommandResult with the outcome of the start operation

        Examples:
            >>> lifecycle = ContainerLifecycle()
            >>> result = lifecycle.container_start()
            >>> print(result.success)
            True
        """
        return self.container_manager.start()

    def container_stop(self) -> CommandResult:
        """Stop the devcontainer.

        Returns:
            CommandResult with the outcome of the stop operation

        Examples:
            >>> lifecycle = ContainerLifecycle()
            >>> result = lifecycle.container_stop()
            >>> print(result.success)
            True
        """
        return self.container_manager.stop()

    def container_rebuild(self) -> CommandResult:
        """Rebuild and restart the devcontainer.

        This rebuilds the container image from scratch and then starts it.
        Use this when you've made changes to the devcontainer configuration
        or need to start from a clean state.

        Returns:
            CommandResult with the outcome of the rebuild operation

        Examples:
            >>> lifecycle = ContainerLifecycle()
            >>> result = lifecycle.container_rebuild()
            >>> print(result.success)
            True
        """
        return self.container_manager.rebuild()

    def container_exec(self, command: str) -> CommandResult:
        """Execute arbitrary command in container.

        Validates the command parameter, ensures the container is running,
        and executes the command inside the container.

        Args:
            command: Shell command to execute in the container

        Returns:
            CommandResult with the outcome of the command execution

        Raises:
            ValidationError: If command parameter is empty or invalid

        Examples:
            >>> lifecycle = ContainerLifecycle()
            >>> result = lifecycle.container_exec("ls -la")
            >>> result = lifecycle.container_exec("python --version")
        """
        # Validate command parameter
        if not command or not command.strip():
            raise ValidationError(
                "Invalid command parameter\n\n"
                "The command parameter cannot be empty.\n\n"
                "Examples of valid commands:\n"
                "  - ls -la\n"
                "  - python --version\n"
                "  - pytest tests/\n"
            )

        return self.container_manager.exec(command)

    def container_shell(self) -> CommandResult:
        """Provide instructions for opening interactive shell.

        Since MCP cannot open interactive shells, this returns instructions
        for the user to run the command manually in their terminal.

        Returns:
            CommandResult with instructions for opening a shell

        Examples:
            >>> lifecycle = ContainerLifecycle()
            >>> result = lifecycle.container_shell()
            >>> print(result.stdout)
            To open an interactive shell in the devcontainer, run:
            devcontainer exec --workspace-folder . /bin/zsh -l
        """
        workspace = self.container_manager.workspace_folder
        shell_command = f"devcontainer exec --workspace-folder {workspace} /bin/zsh -l"

        message = (
            "To open an interactive shell in the devcontainer, run:\n\n"
            f"  {shell_command}\n\n"
            "Note: Interactive shells cannot be opened via MCP.\n"
            "Please run this command in your terminal."
        )

        return CommandResult(
            exit_code=0,
            stdout=message,
            stderr="",
            command=shell_command,
            success=True
        )
