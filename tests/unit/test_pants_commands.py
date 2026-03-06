"""Unit tests for Pants command tools."""

from typing import Any
from unittest.mock import Mock

import pytest

from src.models import CommandResult, ContainerError
from src.pants_commands import PantsCommands


class TestPantsCommands:
    """Test suite for PantsCommands class."""

    @pytest.fixture
    def mock_container_manager(self) -> Mock:
        """Create a mock ContainerManager."""
        manager = Mock()
        manager.exec = Mock()
        return manager

    @pytest.fixture
    def mock_command_builder(self) -> Mock:
        """Create a mock PantsCommandBuilder."""
        builder = Mock()
        builder.build_command = Mock()
        return builder

    @pytest.fixture
    def pants_commands(
        self, mock_container_manager: Mock, mock_command_builder: Mock
    ) -> PantsCommands:
        """Create a PantsCommands instance with mocked dependencies."""
        return PantsCommands(
            container_manager=mock_container_manager, command_builder=mock_command_builder
        )

    # Tests for pants_fix

    def test_pants_fix_with_default_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_fix with no target uses default '::'."""
        # Setup
        mock_command_builder.build_command.return_value = "pants fix ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0, stdout="Fixed 5 files", stderr="", command="pants fix ::", success=True
        )

        # Execute
        result = pants_commands.pants_fix()

        # Verify
        mock_command_builder.build_command.assert_called_once_with("fix", None)
        mock_container_manager.exec.assert_called_once_with(
            "pants fix :: --keep-sandboxes=on_failure"
        )
        assert result.success
        assert result.exit_code == 0

    def test_pants_fix_with_custom_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_fix with custom target specification."""
        # Setup
        target = "src/python::"
        mock_command_builder.build_command.return_value = f"pants fix {target}"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Fixed 3 files",
            stderr="",
            command=f"pants fix {target}",
            success=True,
        )

        # Execute
        result = pants_commands.pants_fix(target)

        # Verify
        mock_command_builder.build_command.assert_called_once_with("fix", target)
        mock_container_manager.exec.assert_called_once_with(
            f"pants fix {target} --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_fix_container_failure(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_fix when container operations fail."""
        # Setup
        mock_command_builder.build_command.return_value = "pants fix ::"
        mock_container_manager.exec.side_effect = ContainerError("Container not running")

        # Execute and verify
        with pytest.raises(ContainerError, match="Container not running"):
            pants_commands.pants_fix()

    # Tests for pants_lint

    def test_pants_lint_with_default_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_lint with no target uses default '::'."""
        # Setup
        mock_command_builder.build_command.return_value = "pants lint ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="All linters passed",
            stderr="",
            command="pants lint ::",
            success=True,
        )

        # Execute
        result = pants_commands.pants_lint()

        # Verify
        mock_command_builder.build_command.assert_called_once_with("lint", None)
        mock_container_manager.exec.assert_called_once_with(
            "pants lint :: --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_lint_with_custom_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_lint with custom target specification."""
        # Setup
        target = "src/python/myapp.py"
        mock_command_builder.build_command.return_value = f"pants lint {target}"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Linting passed",
            stderr="",
            command=f"pants lint {target}",
            success=True,
        )

        # Execute
        result = pants_commands.pants_lint(target)

        # Verify
        mock_command_builder.build_command.assert_called_once_with("lint", target)
        mock_container_manager.exec.assert_called_once_with(
            f"pants lint {target} --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_lint_failure(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_lint when linting fails."""
        # Setup
        mock_command_builder.build_command.return_value = "pants lint ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Linting errors found",
            command="pants lint ::",
            success=False,
        )

        # Execute
        result = pants_commands.pants_lint()

        # Verify
        assert not result.success
        assert result.exit_code == 1
        assert "Linting errors found" in result.stderr

    # Tests for pants_check

    def test_pants_check_with_default_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_check with no target uses default '::'."""
        # Setup
        mock_command_builder.build_command.return_value = "pants check ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Type checking passed",
            stderr="",
            command="pants check ::",
            success=True,
        )

        # Execute
        result = pants_commands.pants_check()

        # Verify
        mock_command_builder.build_command.assert_called_once_with("check", None)
        mock_container_manager.exec.assert_called_once_with(
            "pants check :: --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_check_with_custom_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_check with custom target specification."""
        # Setup
        target = "src/python:myapp"
        mock_command_builder.build_command.return_value = f"pants check {target}"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Type checking passed",
            stderr="",
            command=f"pants check {target}",
            success=True,
        )

        # Execute
        result = pants_commands.pants_check(target)

        # Verify
        mock_command_builder.build_command.assert_called_once_with("check", target)
        mock_container_manager.exec.assert_called_once_with(
            f"pants check {target} --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_check_type_errors(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_check when type errors are found."""
        # Setup
        mock_command_builder.build_command.return_value = "pants check ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Type errors found in myapp.py",
            command="pants check ::",
            success=False,
        )

        # Execute
        result = pants_commands.pants_check()

        # Verify
        assert not result.success
        assert result.exit_code == 1
        assert "Type errors found" in result.stderr

    # Tests for pants_test

    def test_pants_test_with_default_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_test with no target uses default '::'."""
        # Setup
        mock_command_builder.build_command.return_value = "pants test ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0, stdout="All tests passed", stderr="", command="pants test ::", success=True
        )

        # Execute
        result = pants_commands.pants_test()

        # Verify
        mock_command_builder.build_command.assert_called_once_with("test", None)
        expected_cmd = (
            "pants test :: --test-report --test-report-dir=dist/test-reports "
            "--use-coverage --keep-sandboxes=on_failure"
        )
        mock_container_manager.exec.assert_called_once_with(expected_cmd)
        assert result.success

    def test_pants_test_with_custom_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_test with custom target specification."""
        # Setup
        target = "src/python/test_myapp.py"
        mock_command_builder.build_command.return_value = f"pants test {target}"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Tests passed",
            stderr="",
            command=f"pants test {target}",
            success=True,
        )

        # Execute
        result = pants_commands.pants_test(target)

        # Verify
        mock_command_builder.build_command.assert_called_once_with("test", target)
        expected_cmd = (
            f"pants test {target} --test-report --test-report-dir=dist/test-reports "
            "--use-coverage --keep-sandboxes=on_failure"
        )
        mock_container_manager.exec.assert_called_once_with(expected_cmd)
        assert result.success

    def test_pants_test_failure(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_test when tests fail."""
        # Setup
        mock_command_builder.build_command.return_value = "pants test ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Test failed: test_identifier_validation",
            command="pants test ::",
            success=False,
        )

        # Execute
        result = pants_commands.pants_test()

        # Verify
        assert not result.success
        assert result.exit_code == 1
        assert "Test failed" in result.stderr

    # Tests for pants_package

    def test_pants_package_with_default_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_package with no target uses default '::'."""
        # Setup
        mock_command_builder.build_command.return_value = "pants package ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Built 3 packages",
            stderr="",
            command="pants package ::",
            success=True,
        )

        # Execute
        result = pants_commands.pants_package()

        # Verify
        mock_command_builder.build_command.assert_called_once_with("package", None)
        mock_container_manager.exec.assert_called_once_with(
            "pants package :: --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_package_with_custom_target(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_package with custom target specification."""
        # Setup
        target = "src/python:myapp"
        mock_command_builder.build_command.return_value = f"pants package {target}"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="Built package: myapp",
            stderr="",
            command=f"pants package {target}",
            success=True,
        )

        # Execute
        result = pants_commands.pants_package(target)

        # Verify
        mock_command_builder.build_command.assert_called_once_with("package", target)
        mock_container_manager.exec.assert_called_once_with(
            f"pants package {target} --keep-sandboxes=on_failure"
        )
        assert result.success

    def test_pants_package_failure(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_package when packaging fails."""
        # Setup
        mock_command_builder.build_command.return_value = "pants package ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=1,
            stdout="",
            stderr="Build failed: missing dependency",
            command="pants package ::",
            success=False,
        )

        # Execute
        result = pants_commands.pants_package()

        # Verify
        assert not result.success
        assert result.exit_code == 1
        assert "Build failed" in result.stderr

    # Integration-style tests

    def test_all_commands_use_container_exec(
        self, pants_commands: Any, mock_container_manager: Any
    ) -> None:
        """Test that all Pants commands use ContainerManager.exec."""
        # Setup
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0, stdout="", stderr="", command="", success=True
        )

        # Execute all commands
        pants_commands.pants_fix()
        pants_commands.pants_lint()
        pants_commands.pants_check()
        pants_commands.pants_test()
        pants_commands.pants_package()
        pants_commands.pants_clear_cache()

        # Verify exec was called 6 times
        assert mock_container_manager.exec.call_count == 6

    def test_all_commands_use_command_builder(
        self, pants_commands: Any, mock_command_builder: Any, mock_container_manager: Any
    ) -> None:
        """Test that all Pants commands use PantsCommandBuilder."""
        # Setup
        mock_command_builder.build_command.return_value = "pants cmd ::"
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0, stdout="", stderr="", command="", success=True
        )

        # Execute all commands
        pants_commands.pants_fix()
        pants_commands.pants_lint()
        pants_commands.pants_check()
        pants_commands.pants_test()
        pants_commands.pants_package()

        # Verify build_command was called 5 times with correct subcommands
        assert mock_command_builder.build_command.call_count == 5
        calls = mock_command_builder.build_command.call_args_list
        assert calls[0][0][0] == "fix"
        assert calls[1][0][0] == "lint"
        assert calls[2][0][0] == "check"
        assert calls[3][0][0] == "test"
        assert calls[4][0][0] == "package"

    # Tests for pants_clear_cache

    def test_pants_clear_cache_successful(
        self, pants_commands: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_clear_cache successfully clears cache."""
        # Setup
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="",
            stderr="",
            command="rm -rf .pants.d/pids",
            success=True,
        )

        # Execute
        result = pants_commands.pants_clear_cache()

        # Verify
        mock_container_manager.exec.assert_called_once_with("rm -rf .pants.d/pids")
        assert result.success
        assert result.exit_code == 0

    def test_pants_clear_cache_missing_directory(
        self, pants_commands: Any, mock_container_manager: Any
    ) -> None:
        """Test pants_clear_cache handles missing cache directory gracefully."""
        # Setup - rm -rf returns success even if directory doesn't exist
        mock_container_manager.exec.return_value = CommandResult(
            exit_code=0,
            stdout="",
            stderr="",
            command="rm -rf .pants.d/pids",
            success=True,
        )

        # Execute
        result = pants_commands.pants_clear_cache()

        # Verify - should succeed without error
        assert result.success
        assert result.exit_code == 0
