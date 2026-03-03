"""Message formatting utilities for errors and success messages."""

from src.models import CommandExecutionError, CommandResult, ContainerError, ValidationError


def format_container_error(error: ContainerError, command: str = "", output: str = "") -> str:
    """Format a ContainerError with troubleshooting guidance.

    Args:
        error: The ContainerError exception
        command: The command that failed (if available)
        output: The output from the failed command (if available)

    Returns:
        A formatted error message with troubleshooting guidance
    """
    if command:
        formatted = f"Container operation failed: {command}"
    else:
        formatted = "Container operation failed"

    if output:
        formatted += f"\n\nOutput:\n{output}"

    # Add troubleshooting guidance
    formatted += "\n\nTroubleshooting:"
    formatted += "\n1. Check if Docker Desktop is running"
    formatted += "\n2. Verify Docker daemon is accessible: docker ps"
    formatted += "\n3. Check Docker permissions: docker run hello-world"
    formatted += "\n4. Ensure devcontainer CLI is installed: npm install -g @devcontainers/cli"
    formatted += "\n5. Verify .devcontainer/ directory exists with valid devcontainer.json"

    return formatted


def format_command_execution_error(
    error: CommandExecutionError,
    command: str = "",
    exit_code: int | None = None,
    output: str = ""
) -> str:
    """Format a CommandExecutionError with command details.

    Args:
        error: The CommandExecutionError exception
        command: The command that failed (if available)
        exit_code: The exit code from the failed command (if available)
        output: The output from the failed command (if available)

    Returns:
        A formatted error message with command details
    """
    formatted = f"Command execution failed: {command}" if command else "Command execution failed"

    if exit_code is not None:
        formatted += f"\n\nExit code: {exit_code}"

    if output:
        formatted += f"\n\nOutput:\n{output}"

    return formatted


def format_validation_error(
    error: ValidationError,
    parameter_name: str = "",
    parameter_value: str = "",
    valid_examples: list[str] | None = None
) -> str:
    """Format a ValidationError with examples of valid values.

    Args:
        error: The ValidationError exception
        parameter_name: The name of the invalid parameter (if available)
        parameter_value: The invalid value provided (if available)
        valid_examples: List of valid example values (if available)

    Returns:
        A formatted error message with validation guidance
    """
    if parameter_name and parameter_value:
        formatted = f"Parameter validation failed: {parameter_name} = '{parameter_value}'"
    elif parameter_name:
        formatted = f"Parameter validation failed: {parameter_name}"
    else:
        formatted = "Parameter validation failed"

    if valid_examples:
        formatted += "\n\nValid values:"
        for example in valid_examples:
            formatted += f"\n- {example}"

    return formatted


def format_success(result: CommandResult) -> str:
    """Format a successful CommandResult with output.

    Args:
        result: The CommandResult from a successful command execution

    Returns:
        A formatted success message with relevant output
    """
    if not result.output or result.output.strip() == "":
        # Handle empty output gracefully
        return f"Command completed successfully: {result.command}"

    # Include the output for commands that produce output
    return f"Command completed successfully: {result.command}\n\n{result.output}"
