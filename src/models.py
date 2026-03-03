"""Core data models for the Pants DevContainer Power."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CommandResult:
    """Result of executing a shell command.
    
    Attributes:
        exit_code: The exit code returned by the command
        stdout: Standard output from the command
        stderr: Standard error from the command
        command: The command that was executed
        success: Whether the command succeeded (exit_code == 0)
    """
    exit_code: int
    stdout: str
    stderr: str
    command: str
    success: bool
    
    @property
    def output(self) -> str:
        """Combined stdout and stderr output.
        
        Returns:
            Concatenated stdout and stderr, stripped of leading/trailing whitespace
        """
        return f"{self.stdout}\n{self.stderr}".strip()


@dataclass
class WorkflowResult:
    """Result of executing a multi-step workflow.
    
    Attributes:
        steps_completed: List of step names that were completed
        failed_step: Name of the step that failed, or None if all succeeded
        results: List of CommandResult objects for each step executed
        overall_success: Whether the entire workflow succeeded
    """
    steps_completed: List[str]
    failed_step: Optional[str]
    results: List[CommandResult]
    overall_success: bool
    
    @property
    def summary(self) -> str:
        """Human-readable summary of workflow execution.
        
        Returns:
            A formatted string describing the workflow outcome
        """
        if self.overall_success:
            steps_str = ", ".join(self.steps_completed)
            return f"Workflow completed successfully. Steps executed: {steps_str}"
        else:
            completed_str = ", ".join(self.steps_completed)
            return (
                f"Workflow failed at step: {self.failed_step}\n"
                f"Steps completed before failure: {completed_str}"
            )


# Error exception classes

class PowerError(Exception):
    """Base exception for all power-related errors."""
    pass


class ContainerError(PowerError):
    """Exception raised when container operations fail.
    
    This includes failures in starting, stopping, rebuilding, or
    executing commands in the devcontainer.
    """
    pass


class CommandExecutionError(PowerError):
    """Exception raised when command execution fails.
    
    This includes failures in executing Pants commands or other
    shell commands within the container.
    """
    pass


class ValidationError(PowerError):
    """Exception raised when parameter validation fails.
    
    This includes invalid target specifications, workflow names,
    or other input parameters.
    """
    pass
