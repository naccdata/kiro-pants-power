"""Unit tests for ErrorTranslator."""


from src.intent.data_models import IntentContext, TranslationRule
from src.intent.error_translator import ErrorTranslator


def test_translate_no_targets_found(default_config, sample_pants_errors):
    """Test translation of 'No targets found' error."""
    translator = ErrorTranslator(config=default_config)
    context = IntentContext(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error(sample_pants_errors["no_targets"], context)

    assert "No tests found" in result.message
    assert "directory" in result.message
    assert "src/tests" in result.message
    assert result.raw_error == sample_pants_errors["no_targets"]
    assert result.rule_applied is not None


def test_translate_unknown_target(default_config, sample_pants_errors):
    """Test translation of 'Unknown target' error."""
    translator = ErrorTranslator(config=default_config)
    context = IntentContext(
        scope="file",
        path="src/tests/test_missing.py",
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error(sample_pants_errors["unknown_target"], context)

    assert "no testable code" in result.message
    assert result.raw_error == sample_pants_errors["unknown_target"]


def test_translate_build_not_found(default_config, sample_pants_errors):
    """Test translation of 'BUILD file not found' error."""
    translator = ErrorTranslator(config=default_config)
    context = IntentContext(
        scope="directory",
        path="src/tests",
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error(sample_pants_errors["build_not_found"], context)

    assert "not configured for Pants" in result.message
    assert "pants tailor" in result.message
    assert result.suggestion == "pants tailor"


def test_translate_no_such_file(default_config, sample_pants_errors):
    """Test translation of 'No such file or directory' error."""
    translator = ErrorTranslator(config=default_config)
    context = IntentContext(
        scope="file",
        path="src/missing.py",
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error(sample_pants_errors["no_such_file"], context)

    assert "does not exist" in result.message
    assert result.raw_error == sample_pants_errors["no_such_file"]


def test_translate_unknown_error(default_config):
    """Test translation of unknown error falls back to generic message."""
    translator = ErrorTranslator(config=default_config)
    context = IntentContext(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
    )

    unknown_error = "Some completely unknown error message"
    result = translator.translate_error(unknown_error, context)

    assert "Pants command failed" in result.message
    assert unknown_error in result.message
    assert result.raw_error == unknown_error
    assert result.rule_applied is None


def test_raw_error_always_preserved(default_config, sample_pants_errors):
    """Test that raw error is always preserved in translation."""
    translator = ErrorTranslator(config=default_config)
    context = IntentContext(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
    )

    for _error_type, error_msg in sample_pants_errors.items():
        result = translator.translate_error(error_msg, context)
        assert result.raw_error == error_msg


def test_translation_disabled(default_config, sample_pants_errors):
    """Test error translation can be disabled."""
    config = default_config
    config.enable_error_translation = False

    translator = ErrorTranslator(config=config)
    context = IntentContext(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error(sample_pants_errors["no_targets"], context)

    # Should return raw error unchanged
    assert result.message == sample_pants_errors["no_targets"]
    assert result.raw_error == sample_pants_errors["no_targets"]
    assert result.rule_applied is None


def test_add_custom_translation_rule(default_config):
    """Test adding custom translation rule."""
    translator = ErrorTranslator(config=default_config)

    custom_rule = TranslationRule(
        pattern=r"Custom error pattern",
        template="Custom translated message",
        priority=15,
    )
    translator.add_translation_rule(custom_rule)

    context = IntentContext(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error("Custom error pattern detected", context)

    assert result.message == "Custom translated message"
    assert result.rule_applied == r"Custom error pattern"


def test_translation_rule_priority(default_config):
    """Test that higher priority rules are applied first."""
    translator = ErrorTranslator(config=default_config)

    # Add a higher priority rule that matches the same pattern
    high_priority_rule = TranslationRule(
        pattern=r"No targets? found",
        template="High priority message",
        priority=20,
    )
    translator.add_translation_rule(high_priority_rule)

    context = IntentContext(
        scope="all",
        path=None,
        recursive=True,
        test_filter=None,
    )

    result = translator.translate_error("No targets found", context)

    # Should use the higher priority rule
    assert result.message == "High priority message"
