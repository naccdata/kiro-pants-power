"""Unit tests for message formatting utilities."""

from src.formatters import (
    format_command_execution_error,
    format_container_error,
    format_success,
    format_validation_error,
)
from src.models import CommandExecutionError, CommandResult, ContainerError, ValidationError


class TestFormatContainerError:
    """Tests for format_container_error function."""

    def test_format_with_command_and_output(self) -> None:
        """Test formatting container error with command and output."""
        error = ContainerError("Container start failed")
        command = "devcontainer up --workspace-folder ."
        output = "Error: Cannot connect to Docker daemon. Is Docker running?"

        result = format_container_error(error, command, output)

        assert "Container operation failed: devcontainer up --workspace-folder ." in result
        assert "Output:" in result
        assert "Cannot connect to Docker daemon" in result
        assert "Troubleshooting:" in result
        assert "Docker Desktop is running" in result
        assert "docker ps" in result

    def test_format_with_command_only(self) -> None:
        """Test formatting container error with command but no output."""
        error = ContainerError("Container start failed")
        command = "devcontainer up"

        result = format_container_error(error, command)

        assert "Container operation failed: devcontainer up" in result
        assert "Troubleshooting:" in result
        assert "Output:" not in result

    def test_format_with_no_details(self) -> None:
        """Test formatting container error with minimal information."""
        error = ContainerError("Unknown error")

        result = format_container_error(error)

        assert "Container operation failed" in result
        assert "Troubleshooting:" in result
        assert "devcontainer CLI is installed" in result

    def test_includes_all_troubleshooting_steps(self) -> None:
        """Test that all troubleshooting steps are included."""
        error = ContainerError("Error")

        result = format_container_error(error)

        assert "Docker Desktop is running" in result
        assert "docker ps" in result
        assert "docker run hello-world" in result
        assert "npm install -g @devcontainers/cli" in result
        assert ".devcontainer/" in result


class TestFormatCommandExecutionError:
    """Tests for format_command_execution_error function."""

    def test_format_with_all_details(self) -> None:
        """Test formatting command execution error with all details."""
        error = CommandExecutionError("Command failed")
        command = "pants test common/test/python::"
        exit_code = 1
        output = "[stderr] ERROR: Test failed: test_identifier_validation"

        result = format_command_execution_error(error, command, exit_code, output)

        assert "Command execution failed: pants test common/test/python::" in result
        assert "Exit code: 1" in result
        assert "Output:" in result
        assert "test_identifier_validation" in result

    def test_format_with_command_only(self) -> None:
        """Test formatting command execution error with command only."""
        error = CommandExecutionError("Command failed")
        command = "pants lint ::"

        result = format_command_execution_error(error, command)

        assert "Command execution failed: pants lint ::" in result
        assert "Exit code:" not in result
        assert "Output:" not in result

    def test_format_with_exit_code_zero(self) -> None:
        """Test formatting with exit code 0 (edge case)."""
        error = CommandExecutionError("Unexpected error")
        command = "pants check ::"
        exit_code = 0

        result = format_command_execution_error(error, command, exit_code)

        assert "Exit code: 0" in result

    def test_format_with_no_details(self) -> None:
        """Test formatting command execution error with minimal information."""
        error = CommandExecutionError("Unknown error")

        result = format_command_execution_error(error)

        assert "Command execution failed" in result


class TestFormatValidationError:
    """Tests for format_validation_error function."""

    def test_format_with_all_details(self) -> None:
        """Test formatting validation error with all details."""
        error = ValidationError("Invalid target")
        parameter_name = "target"
        parameter_value = "common/src/python"
        valid_examples = [
            '"::" for all targets',
            '"path/to/dir::" for directory and subdirectories',
            '"path/to/dir:target" for specific target',
        ]

        result = format_validation_error(
            error, parameter_name, parameter_value, valid_examples
        )

        assert "Parameter validation failed: target = 'common/src/python'" in result
        assert "Valid values:" in result
        assert '"::" for all targets' in result
        assert "path/to/dir::" in result

    def test_format_with_parameter_name_only(self) -> None:
        """Test formatting validation error with parameter name only."""
        error = ValidationError("Invalid parameter")
        parameter_name = "workflow"

        result = format_validation_error(error, parameter_name)

        assert "Parameter validation failed: workflow" in result
        assert "Valid values:" not in result

    def test_format_with_examples_only(self) -> None:
        """Test formatting validation error with examples but no parameter details."""
        error = ValidationError("Invalid input")
        valid_examples = ["option1", "option2", "option3"]

        result = format_validation_error(error, valid_examples=valid_examples)

        assert "Parameter validation failed" in result
        assert "Valid values:" in result
        assert "option1" in result
        assert "option2" in result
        assert "option3" in result

    def test_format_with_no_details(self) -> None:
        """Test formatting validation error with minimal information."""
        error = ValidationError("Validation failed")

        result = format_validation_error(error)

        assert "Parameter validation failed" in result
        assert "Valid values:" not in result


class TestFormatSuccess:
    """Tests for format_success function."""

    def test_format_with_output(self) -> None:
        """Test formatting success message with command output."""
        result = CommandResult(
            exit_code=0,
            stdout="All tests passed\n5 tests completed",
            stderr="",
            command="pants test ::",
            success=True,
        )

        formatted = format_success(result)

        assert "Command completed successfully: pants test ::" in formatted
        assert "All tests passed" in formatted
        assert "5 tests completed" in formatted

    def test_format_with_empty_output(self) -> None:
        """Test formatting success message with no output."""
        result = CommandResult(
            exit_code=0,
            stdout="",
            stderr="",
            command="pants fix ::",
            success=True,
        )

        formatted = format_success(result)

        assert "Command completed successfully: pants fix ::" in formatted
        assert formatted.count("\n") == 0  # No extra newlines for empty output

    def test_format_with_whitespace_only_output(self) -> None:
        """Test formatting success message with whitespace-only output."""
        result = CommandResult(
            exit_code=0,
            stdout="   \n  \n  ",
            stderr="",
            command="pants clear-cache",
            success=True,
        )

        formatted = format_success(result)

        assert "Command completed successfully: pants clear-cache" in formatted
        # Should handle whitespace-only output as empty
        assert formatted.count("\n") == 0

    def test_format_with_stderr_output(self) -> None:
        """Test formatting success message with stderr output."""
        result = CommandResult(
            exit_code=0,
            stdout="",
            stderr="Warning: deprecated option used",
            command="pants lint ::",
            success=True,
        )

        formatted = format_success(result)

        assert "Command completed successfully: pants lint ::" in formatted
        assert "Warning: deprecated option used" in formatted

    def test_format_with_both_stdout_and_stderr(self) -> None:
        """Test formatting success message with both stdout and stderr."""
        result = CommandResult(
            exit_code=0,
            stdout="Tests completed",
            stderr="Warning: slow test detected",
            command="pants test ::",
            success=True,
        )

        formatted = format_success(result)

        assert "Command completed successfully: pants test ::" in formatted
        assert "Tests completed" in formatted
        assert "Warning: slow test detected" in formatted
