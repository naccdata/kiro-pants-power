"""Unit tests for CommandExecutor streaming with buffering integration."""

from src.command_executor import CommandExecutor
from src.models import CommandResult


class TestCommandExecutorBuffering:
    """Test suite for CommandExecutor buffering integration."""

    def test_streaming_preserves_output_for_parsing(self) -> None:
        """Test that streaming mode buffers complete output for final parsing.

        This verifies Requirement 8.3: Buffer output for both real-time display
        and final parsing.
        """
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("echo 'line1'; echo 'line2'; echo 'line3'"))

        # Last item should be CommandResult with complete buffered output
        result = outputs[-1]
        assert isinstance(result, CommandResult)

        # Verify all output is captured in the final result
        assert "line1" in result.stdout
        assert "line2" in result.stdout
        assert "line3" in result.stdout

        # Verify streaming still works (output lines yielded before result)
        assert len(outputs) > 1
        assert all(isinstance(item, str) for item in outputs[:-1])

    def test_streaming_with_stderr_buffering(self) -> None:
        """Test that stderr is properly buffered during streaming.

        This verifies that both stdout and stderr are captured in the buffer
        and available in the final CommandResult.
        """
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming(
            "echo 'stdout1'; echo 'stderr1' >&2; echo 'stdout2'; echo 'stderr2' >&2"
        ))

        result = outputs[-1]
        assert isinstance(result, CommandResult)

        # Verify stdout is complete
        assert "stdout1" in result.stdout
        assert "stdout2" in result.stdout

        # Verify stderr is complete
        assert "stderr1" in result.stderr
        assert "stderr2" in result.stderr

        # Verify stderr lines were also streamed
        streamed_lines = [item for item in outputs[:-1] if isinstance(item, str)]
        assert any("stderr1" in line for line in streamed_lines)
        assert any("stderr2" in line for line in streamed_lines)

    def test_streaming_empty_output_buffering(self) -> None:
        """Test buffering with command that produces no output."""
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("true"))

        # Should only have the final CommandResult
        assert len(outputs) == 1
        result = outputs[0]
        assert isinstance(result, CommandResult)
        assert result.success is True
        assert result.stdout == ""
        assert result.stderr == ""

    def test_streaming_maintains_backward_compatibility(self) -> None:
        """Test that the buffering integration maintains backward compatibility.

        Existing code that uses execute_with_streaming should continue to work
        without modification.
        """
        executor = CommandExecutor()
        outputs = list(executor.execute_with_streaming("echo 'test output'"))

        # Should yield strings followed by CommandResult (existing behavior)
        assert len(outputs) >= 1
        assert isinstance(outputs[-1], CommandResult)

        result = outputs[-1]
        assert result.success is True
        assert "test output" in result.stdout
        assert result.command == "echo 'test output'"

    def test_streaming_large_output_buffering(self) -> None:
        """Test that large outputs are properly buffered.

        This ensures the buffer can handle substantial output without data loss.
        """
        executor = CommandExecutor()
        # Generate 50 lines of output
        outputs = list(executor.execute_with_streaming("for i in {1..50}; do echo line$i; done"))

        result = outputs[-1]
        assert isinstance(result, CommandResult)
        assert result.success is True

        # Verify all 50 lines are in the buffered output
        for i in range(1, 51):
            assert f"line{i}" in result.stdout

        # Verify streaming occurred (should have many output items)
        assert len(outputs) > 1
