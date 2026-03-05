"""Unit tests for WorkflowOrchestrator."""

from typing import Any
from unittest.mock import Mock

import pytest

from src.models import CommandResult
from src.pants_commands import PantsCommands
from src.workflow_orchestrator import WorkflowOrchestrator


class TestWorkflowOrchestrator:
    """Test suite for WorkflowOrchestrator class."""

    @pytest.fixture
    def mock_pants_commands(self) -> Mock:
        """Create a mock PantsCommands instance."""
        return Mock(spec=PantsCommands)

    @pytest.fixture
    def orchestrator(self, mock_pants_commands: Any) -> WorkflowOrchestrator:
        """Create a WorkflowOrchestrator with mocked dependencies."""
        return WorkflowOrchestrator(pants_commands=mock_pants_commands)

    def test_get_workflow_steps_fix_lint(self, orchestrator: WorkflowOrchestrator) -> None:
        """Test get_workflow_steps returns correct steps for fix-lint workflow."""
        steps = orchestrator.get_workflow_steps("fix-lint")
        assert steps == ["fix", "lint"]

    def test_get_workflow_steps_check_test(self, orchestrator: WorkflowOrchestrator) -> None:
        """Test get_workflow_steps returns correct steps for check-test workflow."""
        steps = orchestrator.get_workflow_steps("check-test")
        assert steps == ["check", "test"]

    def test_get_workflow_steps_fix_lint_check(
        self, orchestrator: WorkflowOrchestrator
    ) -> None:
        """Test get_workflow_steps returns correct steps for fix-lint-check workflow."""
        steps = orchestrator.get_workflow_steps("fix-lint-check")
        assert steps == ["fix", "lint", "check"]

    def test_get_workflow_steps_invalid_workflow(
        self, orchestrator: WorkflowOrchestrator
    ) -> None:
        """Test get_workflow_steps raises ValueError for unknown workflow."""
        with pytest.raises(ValueError) as exc_info:
            orchestrator.get_workflow_steps("invalid-workflow")

        assert "Unknown workflow: invalid-workflow" in str(exc_info.value)
        assert "Valid workflows:" in str(exc_info.value)

    def test_execute_workflow_all_steps_succeed(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow completes all steps when all succeed."""
        # Setup mock to return success for all commands
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0,
            stdout="Fixed 5 files",
            stderr="",
            command="pants fix ::",
            success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0,
            stdout="All checks passed",
            stderr="",
            command="pants lint ::",
            success=True
        )

        result = orchestrator.execute_workflow(["fix", "lint"])

        assert result.overall_success is True
        assert result.steps_completed == ["fix", "lint"]
        assert result.failed_step is None
        assert len(result.results) == 2
        assert "Workflow completed successfully" in result.summary

    def test_execute_workflow_stops_on_first_failure(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow stops at first failing step."""
        # Setup mock: fix succeeds, lint fails
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0,
            stdout="Fixed 5 files",
            stderr="",
            command="pants fix ::",
            success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Linting errors found",
            command="pants lint ::",
            success=False
        )

        result = orchestrator.execute_workflow(["fix", "lint", "check"])

        assert result.overall_success is False
        assert result.steps_completed == ["fix"]
        assert result.failed_step == "lint"
        assert len(result.results) == 2  # fix and lint (check not executed)
        assert "Workflow failed at step: lint" in result.summary

        # Verify check was not called
        mock_pants_commands.pants_check.assert_not_called()

    def test_execute_workflow_failure_at_first_step(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow stops immediately when first step fails."""
        # Setup mock: fix fails
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Fix failed",
            command="pants fix ::",
            success=False
        )

        result = orchestrator.execute_workflow(["fix", "lint", "check"])

        assert result.overall_success is False
        assert result.steps_completed == []
        assert result.failed_step == "fix"
        assert len(result.results) == 1

        # Verify subsequent steps were not called
        mock_pants_commands.pants_lint.assert_not_called()
        mock_pants_commands.pants_check.assert_not_called()

    def test_execute_workflow_failure_at_middle_step(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow stops at middle step failure."""
        # Setup mock: fix succeeds, lint succeeds, check fails
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint ::", success=True
        )
        mock_pants_commands.pants_check.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Type errors",
            command="pants check ::",
            success=False
        )

        result = orchestrator.execute_workflow(["fix", "lint", "check", "test"])

        assert result.overall_success is False
        assert result.steps_completed == ["fix", "lint"]
        assert result.failed_step == "check"
        assert len(result.results) == 3

        # Verify test was not called
        mock_pants_commands.pants_test.assert_not_called()

    def test_execute_workflow_with_target_parameter(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow passes target parameter to all steps."""
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix src::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint src::", success=True
        )

        result = orchestrator.execute_workflow(["fix", "lint"], target="src::")

        assert result.overall_success is True
        mock_pants_commands.pants_fix.assert_called_once_with("src::")
        mock_pants_commands.pants_lint.assert_called_once_with("src::")

    def test_execute_workflow_with_progress_callback(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow calls progress callback after each step with result."""
        # Setup mock to return success
        fix_result = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        lint_result = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint ::", success=True
        )
        mock_pants_commands.pants_fix.return_value = fix_result
        mock_pants_commands.pants_lint.return_value = lint_result

        # Create mock progress callback
        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint"],
            progress_callback=progress_callback
        )

        assert result.overall_success is True

        # Verify progress callback was called for each step with step name and result
        assert progress_callback.call_count == 2
        progress_callback.assert_any_call("fix", fix_result)
        progress_callback.assert_any_call("lint", lint_result)

    def test_execute_workflow_progress_callback_on_failure(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test progress callback is called even when step fails."""
        # Setup mock: fix succeeds, lint fails
        fix_result = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        lint_result = CommandResult(
            exit_code=1, stdout="", stderr="Errors", command="pants lint ::", success=False
        )
        mock_pants_commands.pants_fix.return_value = fix_result
        mock_pants_commands.pants_lint.return_value = lint_result

        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint", "check"],
            progress_callback=progress_callback
        )

        assert result.overall_success is False

        # Verify progress callback was called for fix and lint (not check)
        assert progress_callback.call_count == 2
        progress_callback.assert_any_call("fix", fix_result)
        progress_callback.assert_any_call("lint", lint_result)

    def test_execute_workflow_invalid_step_name(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow raises ValueError for invalid step name."""
        with pytest.raises(ValueError) as exc_info:
            orchestrator.execute_workflow(["fix", "invalid-step"])

        assert "Unknown step: invalid-step" in str(exc_info.value)
        assert "Valid steps:" in str(exc_info.value)

    def test_execute_workflow_all_pants_commands(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow supports all Pants command types."""
        # Setup all commands to succeed
        for command in ["fix", "lint", "check", "test", "package"]:
            method = getattr(mock_pants_commands, f"pants_{command}")
            method.return_value = CommandResult(
                exit_code=0,
                stdout=f"{command} succeeded",
                stderr="",
                command=f"pants {command} ::",
                success=True
            )

        result = orchestrator.execute_workflow(["fix", "lint", "check", "test", "package"])

        assert result.overall_success is True
        assert result.steps_completed == ["fix", "lint", "check", "test", "package"]
        assert len(result.results) == 5

    def test_workflow_result_summary_success(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test WorkflowResult.summary for successful workflow."""
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint ::", success=True
        )

        result = orchestrator.execute_workflow(["fix", "lint"])

        assert "Workflow completed successfully" in result.summary
        assert "fix, lint" in result.summary

    def test_workflow_result_summary_failure(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test WorkflowResult.summary for failed workflow."""
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=1, stdout="", stderr="Errors", command="pants lint ::", success=False
        )

        result = orchestrator.execute_workflow(["fix", "lint", "check"])

        assert "Workflow failed at step: lint" in result.summary
        assert "Steps completed before failure: fix" in result.summary

    def test_execute_workflow_returns_enhanced_result_with_callback(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow returns EnhancedWorkflowResult when callback provided."""
        from src.models import EnhancedWorkflowResult

        # Setup mock to return success
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint ::", success=True
        )

        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint"],
            progress_callback=progress_callback
        )

        # Should return EnhancedWorkflowResult when callback is provided
        assert isinstance(result, EnhancedWorkflowResult)
        assert hasattr(result, 'step_timings')
        assert hasattr(result, 'enhanced_results')
        assert hasattr(result, 'workflow_summary')

    def test_execute_workflow_returns_regular_result_without_callback(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test execute_workflow returns WorkflowResult when no callback provided."""
        from src.models import EnhancedWorkflowResult, WorkflowResult

        # Setup mock to return success
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )

        result = orchestrator.execute_workflow(["fix"])

        # Should return regular WorkflowResult when no callback
        assert isinstance(result, WorkflowResult)
        assert not isinstance(result, EnhancedWorkflowResult)

    def test_enhanced_workflow_result_includes_step_timings(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test EnhancedWorkflowResult includes timing for each step."""
        from src.models import EnhancedWorkflowResult

        # Setup mock to return success
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint ::", success=True
        )

        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint"],
            progress_callback=progress_callback
        )

        assert isinstance(result, EnhancedWorkflowResult)
        assert "fix" in result.step_timings
        assert "lint" in result.step_timings
        assert result.step_timings["fix"] >= 0
        assert result.step_timings["lint"] >= 0

    def test_enhanced_workflow_result_includes_workflow_summary(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test EnhancedWorkflowResult includes formatted workflow summary."""
        from src.models import EnhancedWorkflowResult

        # Setup mock to return success
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=0, stdout="Linted", stderr="", command="pants lint ::", success=True
        )

        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint"],
            progress_callback=progress_callback
        )

        assert isinstance(result, EnhancedWorkflowResult)
        assert result.workflow_summary
        assert "Workflow completed successfully" in result.workflow_summary
        assert "fix, lint" in result.workflow_summary
        assert "Step Timings:" in result.workflow_summary
        assert "Total execution time:" in result.workflow_summary

    def test_enhanced_workflow_summary_on_failure(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test workflow summary includes failure diagnostics."""
        from src.models import EnhancedWorkflowResult

        # Setup mock: fix succeeds, lint fails
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Linting errors found",
            command="pants lint ::",
            success=False
        )

        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint", "check"],
            progress_callback=progress_callback
        )

        assert isinstance(result, EnhancedWorkflowResult)
        assert "Workflow failed at step: lint" in result.workflow_summary
        assert "Steps completed before failure: fix" in result.workflow_summary
        assert "Failed Step Diagnostics (lint):" in result.workflow_summary
        assert "Exit code: 1" in result.workflow_summary
        assert "Linting errors found" in result.workflow_summary

    def test_enhanced_workflow_step_timings_on_failure(
        self, orchestrator: WorkflowOrchestrator, mock_pants_commands: Any
    ) -> None:
        """Test step timings include failed step."""
        from src.models import EnhancedWorkflowResult

        # Setup mock: fix succeeds, lint fails
        mock_pants_commands.pants_fix.return_value = CommandResult(
            exit_code=0, stdout="Fixed", stderr="", command="pants fix ::", success=True
        )
        mock_pants_commands.pants_lint.return_value = CommandResult(
            exit_code=1, stdout="", stderr="Errors", command="pants lint ::", success=False
        )

        progress_callback = Mock()

        result = orchestrator.execute_workflow(
            ["fix", "lint", "check"],
            progress_callback=progress_callback
        )

        assert isinstance(result, EnhancedWorkflowResult)
        # Should have timings for both fix and lint (including failed step)
        assert "fix" in result.step_timings
        assert "lint" in result.step_timings
        # Should NOT have timing for check (not executed)
        assert "check" not in result.step_timings
