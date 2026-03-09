"""Unit tests for data models."""


from src.intent.data_models import (
    BuildFileResult,
    IntentContext,
    MappingResult,
    ResolvedIntent,
    TranslatedError,
    TranslationRule,
    ValidationResult,
)


def test_intent_context_creation():
    """Test IntentContext can be created with all fields."""
    context = IntentContext(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
    )
    assert context.scope == "all"
    assert context.path is None
    assert context.recursive is True
    assert context.test_filter is None


def test_resolved_intent_creation():
    """Test ResolvedIntent can be created with defaults_applied."""
    resolved = ResolvedIntent(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
        defaults_applied={"recursive": True},
    )
    assert resolved.scope == "directory"
    assert resolved.path == "src/tests"
    assert resolved.defaults_applied == {"recursive": True}


def test_mapping_result_creation():
    """Test MappingResult can be created."""
    resolved = ResolvedIntent(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
        defaults_applied={},
    )
    result = MappingResult(
        target_spec="::",
        additional_options=[],
        resolved_intent=resolved,
    )
    assert result.target_spec == "::"
    assert result.additional_options == []


def test_validation_result_success():
    """Test ValidationResult for successful validation."""
    result = ValidationResult(valid=True)
    assert result.valid is True
    assert result.error is None
    assert result.suggestion is None


def test_validation_result_failure():
    """Test ValidationResult for failed validation."""
    result = ValidationResult(
        valid=False,
        error="Path does not exist",
        suggestion="pants tailor",
    )
    assert result.valid is False
    assert result.error == "Path does not exist"
    assert result.suggestion == "pants tailor"


def test_build_file_result_found():
    """Test BuildFileResult when BUILD file is found."""
    result = BuildFileResult(found=True, location="/path/to/dir")
    assert result.found is True
    assert result.location == "/path/to/dir"


def test_build_file_result_not_found():
    """Test BuildFileResult when BUILD file is not found."""
    result = BuildFileResult(found=False)
    assert result.found is False
    assert result.location is None


def test_translated_error_creation():
    """Test TranslatedError can be created."""
    error = TranslatedError(
        message="User-friendly message",
        raw_error="Raw Pants error",
        rule_applied="pattern",
        suggestion="pants tailor",
    )
    assert error.message == "User-friendly message"
    assert error.raw_error == "Raw Pants error"
    assert error.rule_applied == "pattern"
    assert error.suggestion == "pants tailor"


def test_translation_rule_matches():
    """Test TranslationRule.matches() method."""
    rule = TranslationRule(
        pattern=r"No targets? found",
        template="No tests found",
        priority=10,
    )
    assert rule.matches("No targets found") is True
    assert rule.matches("No target found") is True
    assert rule.matches("Some other error") is False


def test_translation_rule_apply():
    """Test TranslationRule.apply() method."""
    rule = TranslationRule(
        pattern=r"No targets? found",
        template="No tests found in {scope} {path}",
        priority=10,
    )
    context = IntentContext(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
    )
    result = rule.apply("No targets found", context)
    assert result == "No tests found in directory src/tests"
