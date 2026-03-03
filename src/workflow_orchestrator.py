"""Workflow orchestration for multi-step Pants command sequences.

This module provides the WorkflowOrchestrator class that executes sequences
of Pants commands with proper error handling and progress indication.
"""

from collections.abc import Callable

from src.models import CommandResult, WorkflowResult
from src.pants_commands import PantsCommands


class WorkflowOrchestrator:
    """Orchestrates multi-step workflows with Pants commands.

    This class executes sequences of Pants commands in order, stopping on
    first failure and providing progress indication for each step.

    Attributes:
        pants_commands: PantsCommands instance for executing Pants commands
    """

    def __init__(self, pants_commands: PantsCommands | None = None):
        """Initialize WorkflowOrchestrator.

        Args:
            pants_commands: PantsCommands instance (creates new one if None)
        """
        self.pants_commands = pants_commands or PantsCommands()

    def get_workflow_steps(self, workflow_name: str) -> list[str]:
        """Map workflow name to list of command steps.

        Args:
            workflow_name: Name of the workflow ("fix-lint", "check-test", "fix-lint-check")

        Returns:
            List of command names to execute in sequence

        Raises:
            ValueError: If workflow_name is not recognized

        Examples:
            >>> orchestrator = WorkflowOrchestrator()
            >>> orchestrator.get_workflow_steps("fix-lint")
            ['fix', 'lint']
            >>> orchestrator.get_workflow_steps("check-test")
            ['check', 'test']
        """
        workflows = {
            "fix-lint": ["fix", "lint"],
            "check-test": ["check", "test"],
            "fix-lint-check": ["fix", "lint", "check"],
        }

        if workflow_name not in workflows:
            valid_workflows = ", ".join(workflows.keys())
            raise ValueError(
                f"Unknown workflow: {workflow_name}\n"
                f"Valid workflows: {valid_workflows}"
            )

        return workflows[workflow_name]

    def execute_workflow(
        self,
        steps: list[str],
        target: str | None = None,
        progress_callback: Callable[[str], None] | None = None
    ) -> WorkflowResult:
        """Execute workflow steps in sequence, stopping on first failure.

        Args:
            steps: List of command names to execute ("fix", "lint", "check", "test", "package")
            target: Pants target specification (default: "::")
            progress_callback: Optional callback function to report progress

        Returns:
            WorkflowResult with all step results and overall success status

        Examples:
            >>> orchestrator = WorkflowOrchestrator()
            >>> result = orchestrator.execute_workflow(["fix", "lint"], "src/python::")
            >>> print(result.summary)
            Workflow completed successfully. Steps executed: fix, lint
        """
        steps_completed: list[str] = []
        results: list[CommandResult] = []
        failed_step: str | None = None

        # Map step names to PantsCommands methods
        step_methods = {
            "fix": self.pants_commands.pants_fix,
            "lint": self.pants_commands.pants_lint,
            "check": self.pants_commands.pants_check,
            "test": self.pants_commands.pants_test,
            "package": self.pants_commands.pants_package,
        }

        for step in steps:
            # Validate step name
            if step not in step_methods:
                valid_steps = ", ".join(step_methods.keys())
                raise ValueError(
                    f"Unknown step: {step}\n"
                    f"Valid steps: {valid_steps}"
                )

            # Stream progress indication
            progress_message = f"Executing step: {step}"
            if progress_callback:
                progress_callback(progress_message)

            # Execute the step
            method = step_methods[step]
            result = method(target)
            results.append(result)

            # Check if step succeeded
            if result.success:
                steps_completed.append(step)
            else:
                # Stop on first failure
                failed_step = step
                break

        # Determine overall success
        overall_success = failed_step is None

        return WorkflowResult(
            steps_completed=steps_completed,
            failed_step=failed_step,
            results=results,
            overall_success=overall_success
        )
