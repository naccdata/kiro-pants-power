"""Workflow tools for the MCP server.

This module provides workflow orchestration tools that execute multi-step
Pants command sequences with proper error handling and progress indication.
"""

from collections.abc import Callable

from src.models import WorkflowResult
from src.workflow_orchestrator import WorkflowOrchestrator


class WorkflowTools:
    """Provides workflow orchestration tools.

    This class implements workflow tools that execute sequences of Pants commands
    with automatic container management and progress reporting.

    Attributes:
        orchestrator: WorkflowOrchestrator instance for executing workflows
    """

    def __init__(self, orchestrator: WorkflowOrchestrator | None = None):
        """Initialize WorkflowTools.

        Args:
            orchestrator: WorkflowOrchestrator instance (creates new one if None)
        """
        self.orchestrator = orchestrator or WorkflowOrchestrator()

    def full_quality_check(
        self,
        target: str | None = None,
        progress_callback: Callable[[str], None] | None = None
    ) -> WorkflowResult:
        """Run complete quality check workflow (fix → lint → check → test).

        This workflow executes all quality checks in sequence, stopping on first failure.
        It ensures code is formatted, linted, type-checked, and tested.

        Args:
            target: Pants target specification (default: "::")
            progress_callback: Optional callback function to report progress

        Returns:
            WorkflowResult with all step results and overall success status

        Examples:
            >>> tools = WorkflowTools()
            >>> result = tools.full_quality_check()  # Check all targets
            >>> result = tools.full_quality_check("src/python::")  # Check specific directory
            >>> print(result.summary)
            Workflow completed successfully. Steps executed: fix, lint, check, test
        """
        steps = ["fix", "lint", "check", "test"]
        return self.orchestrator.execute_workflow(steps, target, progress_callback)

    def pants_workflow(
        self,
        workflow: str,
        target: str | None = None,
        progress_callback: Callable[[str], None] | None = None
    ) -> WorkflowResult:
        """Execute custom workflow sequence.

        This tool validates the workflow name and executes the corresponding
        sequence of Pants commands.

        Args:
            workflow: Workflow name ("fix-lint", "check-test", "fix-lint-check")
            target: Pants target specification (default: "::")
            progress_callback: Optional callback function to report progress

        Returns:
            WorkflowResult with all step results and overall success status

        Raises:
            ValueError: If workflow name is not recognized

        Examples:
            >>> tools = WorkflowTools()
            >>> result = tools.pants_workflow("fix-lint")
            >>> result = tools.pants_workflow("check-test", "src/python::")
            >>> result = tools.pants_workflow("fix-lint-check")
        """
        # Validate workflow parameter and get steps
        steps = self.orchestrator.get_workflow_steps(workflow)

        # Execute workflow
        return self.orchestrator.execute_workflow(steps, target, progress_callback)
