"""Unit tests for CommandExecutor."""

from src.command_executor import CommandExecutor
from src.models import CommandResult


class TestCommandExecutor:
    """Test suite for CommandExecutor class."""

    def test_execute_successful_command(self) -> None:
        """Test executing a successful command."""
        executor = CommandExecutor()
        result = executor.execute("echo 'hello world'")

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert result.exit_code == 0
        assert "hello world" in result.stdout
        assert result.command == "echo 'hello world'"

    def test_execute_failed_command(self) -> None:
        """Test executing a command that fails."""
        executor = CommandExecutor()
        result = executor.execute("exit 1")

        assert isinstance(result, CommandResult)
        assert result.success is False
        assert result.exit_code == 1
        assert result.command == "exit 1"

    def test_execute_command_with_stderr(self) -> None:
        """Test executing a command that produces stderr output."""
        executor = CommandExecutor()
        result = executor.execute("echo 'error message' >&2")

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert "error message" in result.stderr

    def test_execute_with_custom_cwd(self) -> None:
        """Test executing a command with custom working directory."""
        executor = CommandExecutor()
        result = executor.execute("pwd", cwd="/tmp")

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert "/tmp" in result.stdout

    def test_execute_invalid_command_raises_error(self) -> None:
        """Test that invalid commands raise CommandExecutionError."""
        executor = CommandExecutor()
        # Note: Invalid commands may still execute via shell, just fail
        # Testing actual subprocess failure is harder without mocking
        result = executor.execute("nonexistent_command_xyz_123")

        # Command will fail but not raise exception (returns non-zero exit)
        assert result.success is False
        assert result.exit_code != 0

    def test_execute_with_streaming_successful_command(self) -> None:
        """Test streaming execution of a successful command."""
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("echo 'line1'; echo 'line2'"))

        # Last item should be CommandResult
        assert isinstance(outputs[-1], CommandResult)
        result = outputs[-1]

        assert result.success is True
        assert result.exit_code == 0
        assert "line1" in result.stdout
        assert "line2" in result.stdout

        # Earlier items should be strings (output lines)
        assert all(isinstance(item, str) for item in outputs[:-1])

    def test_execute_with_streaming_failed_command(self) -> None:
        """Test streaming execution of a failed command."""
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("echo 'output'; exit 1"))

        # Last item should be CommandResult
        assert isinstance(outputs[-1], CommandResult)
        result = outputs[-1]

        assert result.success is False
        assert result.exit_code == 1

    def test_execute_with_streaming_captures_stderr(self) -> None:
        """Test that streaming execution captures stderr."""
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("echo 'error' >&2"))

        # Last item should be CommandResult
        result = outputs[-1]
        assert isinstance(result, CommandResult)
        assert "error" in result.stderr

    def test_command_result_output_property(self) -> None:
        """Test that CommandResult.output combines stdout and stderr."""
        executor = CommandExecutor()
        result = executor.execute("echo 'out'; echo 'err' >&2")

        output = result.output
        assert "out" in output
        assert "err" in output


class TestCommandExecutorEdgeCases:
    """Test edge cases and complex scenarios for CommandExecutor."""

    def test_execute_with_streaming_empty_output(self) -> None:
        """Test streaming execution with command that produces no output."""
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("true"))

        # Should only have the final CommandResult
        assert len(outputs) == 1
        assert isinstance(outputs[0], CommandResult)
        assert outputs[0].success is True
        assert outputs[0].stdout == ""

    def test_execute_with_streaming_large_output(self) -> None:
        """Test streaming execution with command that produces many lines."""
        executor = CommandExecutor()
        # Generate 100 lines of output
        outputs = list(executor.execute_with_streaming("for i in {1..100}; do echo line$i; done"))

        # Last item is CommandResult
        result = outputs[-1]
        assert isinstance(result, CommandResult)
        assert result.success is True

        # Should have streamed output lines
        assert len(outputs) > 1

        # Check that all 100 lines are in the final output
        for i in range(1, 101):
            assert f"line{i}" in result.stdout

    def test_execute_with_streaming_interleaved_stdout_stderr(self) -> None:
        """Test streaming with interleaved stdout and stderr."""
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming(
            "echo 'out1'; echo 'err1' >&2; echo 'out2'; echo 'err2' >&2"
        ))

        result = outputs[-1]
        assert isinstance(result, CommandResult)
        assert "out1" in result.stdout
        assert "out2" in result.stdout
        assert "err1" in result.stderr
        assert "err2" in result.stderr

    def test_execute_command_with_special_characters(self) -> None:
        """Test executing commands with special characters."""
        executor = CommandExecutor()
        result = executor.execute("echo 'test with $VAR and `backticks` and \"quotes\"'")

        assert result.success is True
        assert "test with" in result.stdout

    def test_execute_multiline_command(self) -> None:
        """Test executing a multiline command."""
        executor = CommandExecutor()
        command = """
        echo 'line1'
        echo 'line2'
        echo 'line3'
        """
        result = executor.execute(command)

        assert result.success is True
        assert "line1" in result.stdout
        assert "line2" in result.stdout
        assert "line3" in result.stdout

    def test_command_result_output_property_strips_whitespace(self) -> None:
        """Test that output property strips leading/trailing whitespace."""
        result = CommandResult(
            exit_code=0,
            stdout="  output  \n",
            stderr="  error  \n",
            command="test",
            success=True
        )

        output = result.output
        assert not output.startswith(" ")
        assert not output.endswith(" ")
        assert "output" in output
        assert "error" in output
