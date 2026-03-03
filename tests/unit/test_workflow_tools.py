"""Unit tests for workflow tools."""

from typing import Any
from unittest.mock import Mock

import pytest

from src.models import CommandResult, WorkflowResult
from src.workflow_tools import WorkflowTools


class TestWorkflowTools:
    """Test suite for WorkflowTools class."""

    @pytest.fixture
    def mock_orchestrator(self) -> Mock:
        """Create a mock WorkflowOrchestrator."""
        return Mock()

    @pytest.fixture
    def workflow_tools(self, mock_orchestrator: Any) -> WorkflowTools:
        """Create WorkflowTools instance with mock orchestrator."""
        return WorkflowTools(orchestrator=mock_orchestrator)

    def test_full_quality_check_with_default_target(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check with default target."""
        # Arrange
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint", "check", "test"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check()

        # Assert
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint", "check", "test"],
            None,
            None
        )
        assert result == expected_result
        assert result.overall_success is True

    def test_full_quality_check_with_custom_target(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check with custom target."""
        # Arrange
        target = "src/python::"
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint", "check", "test"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check(target)

        # Assert
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint", "check", "test"],
            target,
            None
        )
        assert result == expected_result

    def test_full_quality_check_with_progress_callback(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check with progress callback."""
        # Arrange
        progress_callback = Mock()
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint", "check", "test"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check(progress_callback=progress_callback)

        # Assert
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint", "check", "test"],
            None,
            progress_callback
        )
        assert result == expected_result

    def test_full_quality_check_stops_on_fix_failure(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check stops when fix step fails."""
        # Arrange
        expected_result = WorkflowResult(
            steps_completed=[],
            failed_step="fix",
            results=[
                CommandResult(
                    exit_code=1,
                    stdout="",
                    stderr="Fix failed",
                    command="pants fix ::",
                    success=False
                )
            ],
            overall_success=False
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check()

        # Assert
        assert result.overall_success is False
        assert result.failed_step == "fix"
        assert result.steps_completed == []

    def test_full_quality_check_stops_on_lint_failure(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check stops when lint step fails."""
        # Arrange
        expected_result = WorkflowResult(
            steps_completed=["fix"],
            failed_step="lint",
            results=[
                CommandResult(
                    exit_code=0,
                    stdout="Fix succeeded",
                    stderr="",
                    command="pants fix ::",
                    success=True
                ),
                CommandResult(
                    exit_code=1,
                    stdout="",
                    stderr="Lint failed",
                    command="pants lint ::",
                    success=False
                )
            ],
            overall_success=False
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check()

        # Assert
        assert result.overall_success is False
        assert result.failed_step == "lint"
        assert result.steps_completed == ["fix"]

    def test_full_quality_check_stops_on_check_failure(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check stops when check step fails."""
        # Arrange
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step="check",
            results=[
                CommandResult(
                    exit_code=0, stdout="", stderr="", command="pants fix ::", success=True
                ),
                CommandResult(
                    exit_code=0, stdout="", stderr="", command="pants lint ::", success=True
                ),
                CommandResult(
                    exit_code=1,
                    stdout="",
                    stderr="Type check failed",
                    command="pants check ::",
                    success=False
                )
            ],
            overall_success=False
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check()

        # Assert
        assert result.overall_success is False
        assert result.failed_step == "check"
        assert result.steps_completed == ["fix", "lint"]

    def test_full_quality_check_stops_on_test_failure(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test full_quality_check stops when test step fails."""
        # Arrange
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint", "check"],
            failed_step="test",
            results=[
                CommandResult(
                    exit_code=0, stdout="", stderr="", command="pants fix ::", success=True
                ),
                CommandResult(
                    exit_code=0, stdout="", stderr="", command="pants lint ::", success=True
                ),
                CommandResult(
                    exit_code=0, stdout="", stderr="", command="pants check ::", success=True
                ),
                CommandResult(
                    exit_code=1,
                    stdout="",
                    stderr="Tests failed",
                    command="pants test ::",
                    success=False
                )
            ],
            overall_success=False
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.full_quality_check()

        # Assert
        assert result.overall_success is False
        assert result.failed_step == "test"
        assert result.steps_completed == ["fix", "lint", "check"]

    def test_pants_workflow_fix_lint(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow with fix-lint workflow."""
        # Arrange
        mock_orchestrator.get_workflow_steps.return_value = ["fix", "lint"]
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.pants_workflow("fix-lint")

        # Assert
        mock_orchestrator.get_workflow_steps.assert_called_once_with("fix-lint")
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint"],
            None,
            None
        )
        assert result == expected_result

    def test_pants_workflow_check_test(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow with check-test workflow."""
        # Arrange
        mock_orchestrator.get_workflow_steps.return_value = ["check", "test"]
        expected_result = WorkflowResult(
            steps_completed=["check", "test"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.pants_workflow("check-test")

        # Assert
        mock_orchestrator.get_workflow_steps.assert_called_once_with("check-test")
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["check", "test"],
            None,
            None
        )
        assert result == expected_result

    def test_pants_workflow_fix_lint_check(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow with fix-lint-check workflow."""
        # Arrange
        mock_orchestrator.get_workflow_steps.return_value = ["fix", "lint", "check"]
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint", "check"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.pants_workflow("fix-lint-check")

        # Assert
        mock_orchestrator.get_workflow_steps.assert_called_once_with("fix-lint-check")
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint", "check"],
            None,
            None
        )
        assert result == expected_result

    def test_pants_workflow_with_custom_target(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow with custom target."""
        # Arrange
        target = "src/python::"
        mock_orchestrator.get_workflow_steps.return_value = ["fix", "lint"]
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.pants_workflow("fix-lint", target)

        # Assert
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint"],
            target,
            None
        )
        assert result == expected_result

    def test_pants_workflow_with_progress_callback(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow with progress callback."""
        # Arrange
        progress_callback = Mock()
        mock_orchestrator.get_workflow_steps.return_value = ["fix", "lint"]
        expected_result = WorkflowResult(
            steps_completed=["fix", "lint"],
            failed_step=None,
            results=[],
            overall_success=True
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.pants_workflow("fix-lint", progress_callback=progress_callback)

        # Assert
        mock_orchestrator.execute_workflow.assert_called_once_with(
            ["fix", "lint"],
            None,
            progress_callback
        )
        assert result == expected_result

    def test_pants_workflow_with_invalid_workflow_name(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow with invalid workflow name."""
        # Arrange
        mock_orchestrator.get_workflow_steps.side_effect = ValueError(
            "Unknown workflow: invalid-workflow\n"
            "Valid workflows: fix-lint, check-test, fix-lint-check"
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            workflow_tools.pants_workflow("invalid-workflow")

        assert "Unknown workflow: invalid-workflow" in str(exc_info.value)
        assert "Valid workflows:" in str(exc_info.value)
        mock_orchestrator.get_workflow_steps.assert_called_once_with("invalid-workflow")

    def test_pants_workflow_stops_on_failure(
        self, workflow_tools: WorkflowTools, mock_orchestrator: Any
    ) -> None:
        """Test pants_workflow stops on step failure."""
        # Arrange
        mock_orchestrator.get_workflow_steps.return_value = ["fix", "lint"]
        expected_result = WorkflowResult(
            steps_completed=["fix"],
            failed_step="lint",
            results=[
                CommandResult(
                    exit_code=0, stdout="", stderr="", command="pants fix ::", success=True
                ),
                CommandResult(
                    exit_code=1,
                    stdout="",
                    stderr="Lint failed",
                    command="pants lint ::",
                    success=False
                )
            ],
            overall_success=False
        )
        mock_orchestrator.execute_workflow.return_value = expected_result

        # Act
        result = workflow_tools.pants_workflow("fix-lint")

        # Assert
        assert result.overall_success is False
        assert result.failed_step == "lint"
        assert result.steps_completed == ["fix"]
