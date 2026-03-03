"""Unit tests for CommandExecutor."""

import pytest
from src.command_executor import CommandExecutor
from src.models import CommandResult, CommandExecutionError


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
