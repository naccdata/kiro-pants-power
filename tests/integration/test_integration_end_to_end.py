"""Integration tests for end-to-end intent-based Pants command execution.

Tests the complete flow from intent to Pants command execution, including
error translation, configuration changes, cache invalidation, and security measures.
"""


import pytest

from src.intent.configuration import Configuration
from src.intent.data_models import IntentContext
from src.intent.error_translator import ErrorTranslator
from src.intent.integration import (
    ErrorResponse,
    SuccessResponse,
    execute_with_error_handling,
    map_intent_to_pants_command,
    sanitize_path,
    sanitize_test_filter,
)
from src.intent.path_validator import PathValidator, clear_build_file_cache
from src.models import CommandResult, ValidationError


def test_end_to_end_all_scope(temp_repo, default_config):
    """Test end-to-end flow with scope='all'."""
    # Map intent to Pants command
    target_spec, options, context = map_intent_to_pants_command(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
    )

    # Verify mapping
    assert target_spec == "::"
    assert options == []
    assert context.scope == "all"
    assert context.path is None


def test_end_to_end_directory_scope_recursive(temp_repo, default_config):
    """Test end-to-end flow with directory scope (recursive)."""
    target_spec, options, context = map_intent_to_pants_command(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
    )

    assert target_spec == "src/tests::"
    assert options == []
    assert context.scope == "directory"
    assert context.path == "src/tests"
    assert context.recursive is True


def test_end_to_end_directory_scope_non_recursive(temp_repo, default_config):
    """Test end-to-end flow with directory scope (non-recursive)."""
    target_spec, options, context = map_intent_to_pants_command(
        scope="directory",
        path="src/tests",
        recursive=False,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
    )

    assert target_spec == "src/tests:"
    assert options == []
    assert context.recursive is False


def test_end_to_end_file_scope(temp_repo, default_config):
    """Test end-to-end flow with file scope."""
    target_spec, options, context = map_intent_to_pants_command(
        scope="file",
        path="src/tests/test_example.py",
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
    )

    assert target_spec == "src/tests/test_example.py"
    assert options == []
    assert context.scope == "file"
    assert context.path == "src/tests/test_example.py"


def test_end_to_end_with_test_filter(temp_repo, default_config):
    """Test end-to-end flow with test filter."""
    target_spec, options, context = map_intent_to_pants_command(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter="test_example",
        config=default_config,
        repo_root=temp_repo,
    )

    assert target_spec == "src/tests::"
    assert options == ["-k", "test_example"]
    assert context.test_filter == "test_example"


def test_end_to_end_with_complex_test_filter(temp_repo, default_config):
    """Test end-to-end flow with complex test filter."""
    target_spec, options, context = map_intent_to_pants_command(
        scope="all",
        path=None,
        recursive=True,
        test_filter="test_create or test_update",
        config=default_config,
        repo_root=temp_repo,
    )

    assert target_spec == "::"
    assert options == ["-k", "test_create or test_update"]
    assert context.test_filter == "test_create or test_update"


def test_error_translation_with_real_pants_errors(temp_repo, default_config):
    """Test error translation with real Pants error messages."""
    translator = ErrorTranslator(default_config)

    # Test "No targets found" error
    context = IntentContext(scope="directory", path="src/tests", recursive=True, test_filter=None)
    pants_error = "No targets found matching the specification"
    translated = translator.translate_error(pants_error, context)

    assert "No tests found" in translated.message
    assert "directory" in translated.message
    assert "src/tests" in translated.message
    assert translated.raw_error == pants_error

    # Test "Unknown target" error
    pants_error = "Unknown target: src/tests:nonexistent"
    translated = translator.translate_error(pants_error, context)

    assert "no testable code" in translated.message.lower()
    assert translated.raw_error == pants_error

    # Test "BUILD file not found" error
    pants_error = "BUILD file not found in directory"
    translated = translator.translate_error(pants_error, context)

    assert "not configured for Pants" in translated.message
    assert "pants tailor" in translated.message.lower()
    assert translated.suggestion == "pants tailor"


def test_configuration_disables_path_validation(temp_repo):
    """Test that configuration can disable path validation."""
    config = Configuration(enable_path_validation=False)

    # Should not raise error even with non-existent path
    target_spec, _options, _context = map_intent_to_pants_command(
        scope="file",
        path="nonexistent.py",
        recursive=True,
        test_filter=None,
        config=config,
        repo_root=temp_repo,
    )

    assert target_spec == "nonexistent.py"


def test_configuration_disables_build_file_checking(temp_repo):
    """Test that configuration can disable BUILD file checking."""
    # Create directory without BUILD file
    no_build_dir = temp_repo / "no_build"
    no_build_dir.mkdir()

    config = Configuration(
        enable_path_validation=True,
        enable_build_file_checking=False,
    )

    # Should not raise error even without BUILD file
    target_spec, _options, _context = map_intent_to_pants_command(
        scope="directory",
        path="no_build",
        recursive=True,
        test_filter=None,
        config=config,
        repo_root=temp_repo,
    )

    assert target_spec == "no_build::"


def test_configuration_disables_error_translation(temp_repo, default_config):
    """Test that configuration can disable error translation."""
    config = Configuration(enable_error_translation=False)
    translator = ErrorTranslator(config)

    context = IntentContext(scope="all", path=None, recursive=True, test_filter=None)
    pants_error = "No targets found matching the specification"
    translated = translator.translate_error(pants_error, context)

    # Should return raw error unchanged
    assert translated.message == pants_error
    assert translated.raw_error == pants_error
    assert translated.rule_applied is None


def test_cache_invalidation_after_pants_tailor(temp_repo, default_config):
    """Test cache invalidation after running pants tailor."""
    validator = PathValidator(default_config, temp_repo)

    # Create directory without BUILD file
    new_dir = temp_repo / "new_tests"
    new_dir.mkdir()

    # First check - should not find BUILD file
    result1 = validator.check_build_file("new_tests")
    assert result1.found is False

    # Simulate running pants tailor by creating BUILD file
    (new_dir / "BUILD").write_text("python_tests()")

    # Without cache clear, should still return cached result
    result2 = validator.check_build_file("new_tests")
    assert result2.found is False  # Still cached

    # Clear cache (simulating post-tailor cache clear)
    clear_build_file_cache()

    # Now should find BUILD file
    result3 = validator.check_build_file("new_tests")
    assert result3.found is True
    assert "new_tests" in result3.location


def test_all_scope_types_with_various_paths(temp_repo, default_config):
    """Test all scope types with various path combinations."""
    # Create BUILD file in src directory for this test
    (temp_repo / "src" / "BUILD").write_text("python_tests()")

    test_cases = [
        # (scope, path, recursive, expected_target)
        ("all", None, True, "::"),
        ("all", None, False, "::"),
        ("directory", "src", True, "src::"),
        ("directory", "src", False, "src:"),
        ("directory", "src/tests", True, "src/tests::"),
        ("directory", "src/tests", False, "src/tests:"),
        ("file", "src/tests/test_example.py", True, "src/tests/test_example.py"),
        ("file", "src/tests/test_example.py", False, "src/tests/test_example.py"),
    ]

    for scope, path, recursive, expected_target in test_cases:
        target_spec, _options, _context = map_intent_to_pants_command(
            scope=scope,
            path=path,
            recursive=recursive,
            test_filter=None,
            config=default_config,
            repo_root=temp_repo,
        )
        assert target_spec == expected_target, (
            f"Failed for scope={scope}, path={path}, recursive={recursive}"
        )


def test_security_path_traversal_prevention(temp_repo, default_config):
    """Test that path traversal attacks are prevented."""
    # Attempt to escape repository with ../
    with pytest.raises(ValidationError, match="Path outside repository"):
        sanitize_path("../../etc/passwd", temp_repo)

    # Attempt with absolute path outside repo
    with pytest.raises(ValidationError, match="Path outside repository"):
        sanitize_path("/etc/passwd", temp_repo)


def test_security_command_injection_prevention(temp_repo, default_config):
    """Test that command injection in test filters is prevented."""
    dangerous_filters = [
        "test_name; rm -rf /",
        "test_name && malicious_command",
        "test_name | cat /etc/passwd",
        "test_name $(whoami)",
        "test_name `whoami`",
        "test_name > /tmp/output",
        "test_name < /etc/passwd",
        "test_name & background_process",
    ]

    for dangerous_filter in dangerous_filters:
        with pytest.raises(ValidationError, match="Invalid character in test filter"):
            sanitize_test_filter(dangerous_filter)


def test_security_valid_test_filters_allowed(temp_repo, default_config):
    """Test that valid test filters are allowed."""
    valid_filters = [
        "test_example",
        "test_create",
        "test_create or test_update",
        "test_create and test_update",
        "not test_slow",
        "test_create or test_update and not test_slow",
        "test_with_underscore_123",
        "TestClass",
    ]

    for valid_filter in valid_filters:
        # Should not raise exception
        result = sanitize_test_filter(valid_filter)
        assert result == valid_filter


def test_execute_with_error_handling_success(temp_repo, default_config):
    """Test execute_with_error_handling with successful execution."""
    # Mock Pants executor that returns success
    def mock_executor(command, target_spec, options):
        return CommandResult(
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            command=f"pants {command} {target_spec}",
            success=True,
        )

    response = execute_with_error_handling(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, SuccessResponse)
    assert response.success is True
    assert "All tests passed" in response.output
    assert response.target_spec == "::"


def test_execute_with_error_handling_validation_error(temp_repo, default_config):
    """Test execute_with_error_handling with validation error."""
    def mock_executor(command, target_spec, options):
        return CommandResult(exit_code=0, stdout="", stderr="", command="", success=True)

    response = execute_with_error_handling(
        scope="file",
        path="nonexistent.py",
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, ErrorResponse)
    assert response.success is False
    assert response.error_type == "validation"
    assert "does not exist" in response.message


def test_execute_with_error_handling_pants_error(temp_repo, default_config):
    """Test execute_with_error_handling with Pants execution error."""
    # Mock Pants executor that returns failure
    def mock_executor(command, target_spec, options):
        return CommandResult(
            exit_code=1,
            stdout="",
            stderr="No targets found matching the specification",
            command=f"pants {command} {target_spec}",
            success=False,
        )

    response = execute_with_error_handling(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, ErrorResponse)
    assert response.success is False
    assert response.error_type == "pants"
    assert "No tests found" in response.message
    assert response.raw_error is not None


def test_execute_with_error_handling_pants_error_with_stdout(temp_repo, default_config):
    """Test execute_with_error_handling includes stdout in error messages."""
    # Create a test file so path validation passes
    test_file = temp_repo / "test_example.py"
    test_file.write_text("def test_function(): pass")
    
    # Mock Pants executor that returns failure with detailed output in stdout
    def mock_executor(command, target_spec, options):
        return CommandResult(
            exit_code=1,
            stdout="FAILED test_example.py::test_function - AssertionError: expected 5 but got 3\n"
                   "Traceback (most recent call last):\n"
                   "  File 'test_example.py', line 10, in test_function\n"
                   "    assert result == 5\n"
                   "AssertionError: expected 5 but got 3",
            stderr="✕ test_example.py:tests failed in 2.5s.",
            command=f"pants {command} {target_spec}",
            success=False,
        )

    response = execute_with_error_handling(
        scope="file",
        path="test_example.py",
        recursive=False,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, ErrorResponse)
    assert response.success is False
    assert response.error_type == "pants"
    # Verify stdout content is included in the error message
    assert "AssertionError" in response.message or "AssertionError" in response.raw_error
    assert "Traceback" in response.message or "Traceback" in response.raw_error
    # Verify stderr is also included
    assert "failed" in response.message or "failed" in response.raw_error


def test_execute_with_error_handling_mapping_error(temp_repo, default_config):
    """Test execute_with_error_handling with mapping error."""
    def mock_executor(command, target_spec, options):
        return CommandResult(exit_code=0, stdout="", stderr="", command="", success=True)

    # File scope without path should cause IntentError
    response = execute_with_error_handling(
        scope="file",
        path=None,
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, ErrorResponse)
    assert response.success is False
    assert response.error_type == "mapping"
    assert "path" in response.message.lower()


def test_execute_with_error_handling_with_test_filter(temp_repo, default_config):
    """Test execute_with_error_handling with test filter."""
    def mock_executor(command, target_spec, options):
        # Verify options include test filter
        assert "-k" in options
        assert "test_example" in options
        return CommandResult(
            exit_code=0,
            stdout="Tests passed",
            stderr="",
            command=f"pants {command} {target_spec}",
            success=True,
        )

    response = execute_with_error_handling(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter="test_example",
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, SuccessResponse)
    assert response.success is True
    assert response.additional_options == ["-k", "test_example"]


def test_multiple_scopes_in_sequence(temp_repo, default_config):
    """Test executing multiple different scopes in sequence."""
    def mock_executor(command, target_spec, options):
        return CommandResult(
            exit_code=0,
            stdout=f"Executed {target_spec}",
            stderr="",
            command=f"pants {command} {target_spec}",
            success=True,
        )

    # Execute all scope
    response1 = execute_with_error_handling(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
    )
    assert response1.success is True
    assert response1.target_spec == "::"

    # Execute directory scope
    response2 = execute_with_error_handling(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
    )
    assert response2.success is True
    assert response2.target_spec == "src/tests::"

    # Execute file scope
    response3 = execute_with_error_handling(
        scope="file",
        path="src/tests/test_example.py",
        recursive=True,
        test_filter=None,
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
    )
    assert response3.success is True
    assert response3.target_spec == "src/tests/test_example.py"


def test_error_context_preservation(temp_repo, default_config):
    """Test that error responses preserve context information."""
    def mock_executor(command, target_spec, options):
        return CommandResult(
            exit_code=1,
            stdout="",
            stderr="No targets found",
            command=f"pants {command} {target_spec}",
            success=False,
        )

    response = execute_with_error_handling(
        scope="directory",
        path="src/tests",
        recursive=False,
        test_filter="test_example",
        config=default_config,
        repo_root=temp_repo,
        pants_executor=mock_executor,
        command="test",
    )

    assert isinstance(response, ErrorResponse)
    assert response.context is not None
    assert response.context["target_spec"] == "src/tests:"
    assert response.context["command"] == "test"
