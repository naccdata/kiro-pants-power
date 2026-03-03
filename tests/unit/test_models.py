"""Unit tests for core data models."""

import pytest
from src.models import (
    CommandResult,
    WorkflowResult,
    PowerError,
    ContainerError,
    CommandExecutionError,
    ValidationError,
)


class TestCommandResult:
    """Tests for CommandResult dataclass."""
    
    def test_command_result_creation(self):
        """Test creating a CommandResult instance."""
        result = CommandResult(
            exit_code=0,
            stdout="Hello",
            stderr="",
            command="echo Hello",
            success=True
        )
        assert result.exit_code == 0
        assert result.stdout == "Hello"
        assert result.stderr == ""
        assert result.command == "echo Hello"
        assert result.success is True
    
    def test_output_property_combines_stdout_and_stderr(self):
        """Test that output property combines stdout and stderr."""
        result = CommandResult(
            exit_code=0,
            stdout="Standard output",
            stderr="Standard error",
            command="test",
            success=True
        )
        assert result.output == "Standard output\nStandard error"
    
    def test_output_property_strips_whitespace(self):
        """Test that output property strips leading/trailing whitespace."""
        result = CommandResult(
            exit_code=0,
            stdout="  output  ",
            stderr="  error  ",
            command="test",
            success=True
        )
        assert result.output == "output  \n  error"
    
    def test_output_property_with_empty_stderr(self):
        """Test output property when stderr is empty."""
        result = CommandResult(
            exit_code=0,
            stdout="Only stdout",
            stderr="",
            command="test",
            success=True
        )
        assert result.output == "Only stdout"
    
    def test_output_property_with_empty_stdout(self):
        """Test output property when stdout is empty."""
        result = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Only stderr",
            command="test",
            success=False
        )
        assert result.output == "Only stderr"


class TestWorkflowResult:
    """Tests for WorkflowResult dataclass."""
    
    def test_workflow_result_creation(self):
        """Test creating a WorkflowResult instance."""
        result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        assert result.steps_completed == ["fix", "lint"]
        assert result.failed_step is None
        assert result.results == []
        assert result.overall_success is True
    
    def test_summary_property_for_successful_workflow(self):
        """Test summary property for a successful workflow."""
        result = WorkflowResult(
            steps_completed=["fix", "lint", "check"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        summary = result.summary
        assert "completed successfully" in summary
        assert "fix, lint, check" in summary
    
    def test_summary_property_for_failed_workflow(self):
        """Test summary property for a failed workflow."""
        result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step="check",
            results=[],
            overall_success=False
        )
        summary = result.summary
        assert "failed at step: check" in summary
        assert "fix, lint" in summary
    
    def test_summary_property_with_no_completed_steps(self):
        """Test summary property when first step fails."""
        result = WorkflowResult(
            steps_completed=[],
            failed_step="fix",
            results=[],
            overall_success=False
        )
        summary = result.summary
        assert "failed at step: fix" in summary


class TestErrorExceptions:
    """Tests for error exception classes."""
    
    def test_power_error_is_exception(self):
        """Test that PowerError is an Exception."""
        error = PowerError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_container_error_inherits_from_power_error(self):
        """Test that ContainerError inherits from PowerError."""
        error = ContainerError("Container failed")
        assert isinstance(error, PowerError)
        assert isinstance(error, Exception)
        assert str(error) == "Container failed"
    
    def test_command_execution_error_inherits_from_power_error(self):
        """Test that CommandExecutionError inherits from PowerError."""
        error = CommandExecutionError("Command failed")
        assert isinstance(error, PowerError)
        assert isinstance(error, Exception)
        assert str(error) == "Command failed"
    
    def test_validation_error_inherits_from_power_error(self):
        """Test that ValidationError inherits from PowerError."""
        error = ValidationError("Invalid parameter")
        assert isinstance(error, PowerError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid parameter"
    
    def test_can_catch_all_errors_with_power_error(self):
        """Test that all custom errors can be caught with PowerError."""
        errors = [
            ContainerError("Container error"),
            CommandExecutionError("Command error"),
            ValidationError("Validation error"),
        ]
        
        for error in errors:
            try:
                raise error
            except PowerError as e:
                assert str(e) in ["Container error", "Command error", "Validation error"]
