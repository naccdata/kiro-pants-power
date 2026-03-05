"""Workflow orchestration for multi-step Pants command sequences.

This module provides the WorkflowOrchestrator class that executes sequences
of Pants commands with proper error handling and progress indication.
"""

import time
from collections.abc import Callable

from src.models import (
    CommandResult,
    EnhancedCommandResult,
    EnhancedWorkflowResult,
    WorkflowResult,
)
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
        progress_callback: Callable[[str, CommandResult | EnhancedCommandResult], None] | None = None
    ) -> WorkflowResult | EnhancedWorkflowResult:
        """Execute workflow steps in sequence, stopping on first failure.

        Args:
            steps: List of command names to execute ("fix", "lint", "check", "test", "package")
            target: Pants target specification (default: "::")
            progress_callback: Optional callback function called after each step completes
                             with signature: callback(step_name: str, result: CommandResult)

        Returns:
            EnhancedWorkflowResult if progress_callback is provided, otherwise WorkflowResult
            Contains all step results, timing information, and overall success status

        Examples:
            >>> orchestrator = WorkflowOrchestrator()
            >>> result = orchestrator.execute_workflow(["fix", "lint"], "src/python::")
            >>> print(result.summary)
            Workflow completed successfully. Steps executed: fix, lint
        """
        steps_completed: list[str] = []
        results: list[CommandResult] = []
        failed_step: str | None = None
        step_timings: dict[str, float] = {}

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

            # Track step start time
            step_start_time = time.time()

            # Execute the step
            method = step_methods[step]
            result = method(target)
            results.append(result)

            # Track step end time and duration
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            step_timings[step] = step_duration

            # Call progress callback if provided
            if progress_callback:
                progress_callback(step, result)

            # Check if step succeeded
            if result.success:
                steps_completed.append(step)
            else:
                # Stop on first failure
                failed_step = step
                break

        # Determine overall success
        overall_success = failed_step is None

        # If progress_callback was provided, return enhanced result
        if progress_callback is not None:
            workflow_summary = self._create_workflow_summary(
                steps_completed=steps_completed,
                failed_step=failed_step,
                step_timings=step_timings,
                results=results
            )

            # Convert results to EnhancedCommandResult if needed
            enhanced_results: list[EnhancedCommandResult] = []
            for result in results:
                if isinstance(result, EnhancedCommandResult):
                    enhanced_results.append(result)
                else:
                    # Wrap regular CommandResult in EnhancedCommandResult
                    from src.models import ParsedOutput
                    enhanced_results.append(
                        EnhancedCommandResult(
                            exit_code=result.exit_code,
                            stdout=result.stdout,
                            stderr=result.stderr,
                            command=result.command,
                            success=result.success,
                            parsed_output=ParsedOutput(),
                            formatted_summary="",
                            execution_time=step_timings.get(
                                steps_completed[enhanced_results.__len__()] if enhanced_results.__len__() < len(steps_completed) else steps[enhanced_results.__len__()],
                                0.0
                            )
                        )
                    )

            return EnhancedWorkflowResult(
                steps_completed=steps_completed,
                failed_step=failed_step,
                results=results,
                overall_success=overall_success,
                step_timings=step_timings,
                enhanced_results=enhanced_results,
                workflow_summary=workflow_summary
            )

        # Otherwise return regular WorkflowResult
        return WorkflowResult(
            steps_completed=steps_completed,
            failed_step=failed_step,
            results=results,
            overall_success=overall_success
        )

    def _create_workflow_summary(
        self,
        steps_completed: list[str],
        failed_step: str | None,
        step_timings: dict[str, float],
        results: list[CommandResult]
    ) -> str:
        """Create a formatted workflow summary with timing and diagnostics.

        Args:
            steps_completed: List of successfully completed steps
            failed_step: Name of the step that failed (if any)
            step_timings: Dictionary mapping step names to execution times
            results: List of command results for all executed steps

        Returns:
            Formatted workflow summary string
        """
        lines = []

        # Overall status
        if failed_step is None:
            lines.append("✓ Workflow completed successfully")
            lines.append(f"  Steps executed: {', '.join(steps_completed)}")
        else:
            lines.append(f"✗ Workflow failed at step: {failed_step}")
            if steps_completed:
                lines.append(f"  Steps completed before failure: {', '.join(steps_completed)}")
            else:
                lines.append("  No steps completed before failure")

        # Timing information for each step
        lines.append("\nStep Timings:")
        for step, duration in step_timings.items():
            status = "✓" if step in steps_completed else "✗"
            lines.append(f"  {status} {step}: {duration:.2f}s")

        # Total execution time
        total_time = sum(step_timings.values())
        lines.append(f"\nTotal execution time: {total_time:.2f}s")

        # Enhanced diagnostics for failed step
        if failed_step is not None:
            failed_result = results[-1]  # Last result is the failed one
            lines.append(f"\nFailed Step Diagnostics ({failed_step}):")
            lines.append(f"  Exit code: {failed_result.exit_code}")

            # Include enhanced diagnostics if available
            if isinstance(failed_result, EnhancedCommandResult) and failed_result.formatted_summary:
                lines.append(f"  Enhanced diagnostics:\n{failed_result.formatted_summary}")
            else:
                # Include stderr excerpt
                if failed_result.stderr:
                    stderr_lines = failed_result.stderr.strip().split('\n')
                    excerpt = '\n'.join(stderr_lines[:10])  # First 10 lines
                    if len(stderr_lines) > 10:
                        excerpt += f"\n  ... ({len(stderr_lines) - 10} more lines)"
                    lines.append(f"  Error output:\n{excerpt}")

        return '\n'.join(lines)
