"""Unit tests for tool executor."""

from unittest.mock import MagicMock

import pytest

from src.intent.tool_executor import ToolExecutor
from src.models import CommandResult


class TestToolExecutor:
    """Tests for ToolExecutor class."""

    @pytest.fixture
    def mock_pants_commands(self):
        """Create mock PantsCommands instance."""
        mock = MagicMock()
        mock.pants_test.return_value = CommandResult(
            command="pants test",
            exit_code=0,
            stdout="Tests passed",
            stderr="",
            success=True,
        )
        mock.pants_lint.return_value = CommandResult(
            command="pants lint",
            exit_code=0,
            stdout="Lint passed",
            stderr="",
            success=True,
        )
        mock.pants_check.return_value = CommandResult(
            command="pants check",
            exit_code=0,
            stdout="Check passed",
            stderr="",
            success=True,
        )
        mock.pants_fix.return_value = CommandResult(
            command="pants fix",
            exit_code=0,
            stdout="Fix passed",
            stderr="",
            success=True,
        )
        mock.pants_package.return_value = CommandResult(
            command="pants package",
            exit_code=0,
            stdout="Package passed",
            stderr="",
            success=True,
        )
        return mock

    @pytest.fixture
    def tool_executor(self, mock_pants_commands):
        """Create ToolExecutor instance."""
        return ToolExecutor(mock_pants_commands)

    def test_execute_pants_test_with_legacy_target(self, tool_executor, mock_pants_commands):
        """Test executing pants_test with legacy target parameter."""
        arguments = {"target": "src/tests::"}

        result = tool_executor.execute_pants_test(arguments)

        assert result.exit_code == 0
        mock_pants_commands.pants_test.assert_called_once_with("src/tests::")

    def test_execute_pants_lint_with_legacy_target(self, tool_executor, mock_pants_commands):
        """Test executing pants_lint with legacy target parameter."""
        arguments = {"target": "src/app::"}

        result = tool_executor.execute_pants_lint(arguments)

        assert result.exit_code == 0
        mock_pants_commands.pants_lint.assert_called_once_with("src/app::")

    def test_execute_pants_check_with_legacy_target(self, tool_executor, mock_pants_commands):
        """Test executing pants_check with legacy target parameter."""
        arguments = {"target": "::"}

        result = tool_executor.execute_pants_check(arguments)

        assert result.exit_code == 0
        mock_pants_commands.pants_check.assert_called_once_with("::")

    def test_execute_pants_fix_with_legacy_target(self, tool_executor, mock_pants_commands):
        """Test executing pants_fix with legacy target parameter."""
        arguments = {"target": "src/::"}

        result = tool_executor.execute_pants_fix(arguments)

        assert result.exit_code == 0
        mock_pants_commands.pants_fix.assert_called_once_with("src/::")

    def test_execute_pants_package_with_legacy_target(self, tool_executor, mock_pants_commands):
        """Test executing pants_package with legacy target parameter."""
        arguments = {"target": "src/app:main"}

        result = tool_executor.execute_pants_package(arguments)

        assert result.exit_code == 0
        mock_pants_commands.pants_package.assert_called_once_with("src/app:main")

    def test_execute_pants_test_with_none_target_uses_legacy(
        self, tool_executor, mock_pants_commands
    ):
        """Test that None target value uses legacy mode."""
        arguments = {"target": None}

        result = tool_executor.execute_pants_test(arguments)

        # Should use legacy mode with None
        assert result.exit_code == 0
        mock_pants_commands.pants_test.assert_called_once_with(None)

    def test_execute_with_empty_arguments_uses_intent_mode(
        self, tool_executor, mock_pants_commands
    ):
        """Test that empty arguments uses intent mode with defaults."""
        arguments = {}

        result = tool_executor.execute_pants_test(arguments)

        # Should use intent mode (will call pants_test with resolved target)
        assert result is not None
        # Intent mode will be called (exact behavior depends on integration module)

    def test_legacy_mode_logs_deprecation_warning(self, tool_executor, mock_pants_commands, caplog):
        """Test that legacy mode logs deprecation warning."""
        import logging

        arguments = {"target": "src/tests::"}

        with caplog.at_level(logging.WARNING):
            tool_executor.execute_pants_test(arguments)

        # Check that deprecation warning was logged
        assert any("deprecated" in record.message.lower() for record in caplog.records)
        assert any("target" in record.message.lower() for record in caplog.records)


class TestToolExecutorIntentMode:
    """Tests for intent-based mode execution."""

    @pytest.fixture
    def mock_pants_commands(self):
        """Create mock PantsCommands instance."""
        mock = MagicMock()
        mock.pants_test.return_value = CommandResult(
            command="pants test",
            exit_code=0,
            stdout="Tests passed",
            stderr="",
            success=True,
        )
        return mock

    @pytest.fixture
    def tool_executor(self, mock_pants_commands):
        """Create ToolExecutor instance."""
        return ToolExecutor(mock_pants_commands)

    def test_intent_mode_with_scope_all(self, tool_executor, mock_pants_commands):
        """Test intent mode with scope=all."""
        arguments = {"scope": "all"}

        result = tool_executor.execute_pants_test(arguments)

        # Should execute successfully
        assert result is not None

    def test_intent_mode_with_scope_directory(self, tool_executor, mock_pants_commands):
        """Test intent mode with scope=directory."""
        arguments = {"scope": "directory", "path": "src/tests", "recursive": True}

        result = tool_executor.execute_pants_test(arguments)

        # Should execute successfully
        assert result is not None

    def test_intent_mode_with_test_filter(self, tool_executor, mock_pants_commands):
        """Test intent mode with test_filter."""
        arguments = {"scope": "all", "test_filter": "test_create"}

        result = tool_executor.execute_pants_test(arguments)

        # Should execute successfully
        assert result is not None
