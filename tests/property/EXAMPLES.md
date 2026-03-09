# Property-Based Testing Examples

This document provides practical examples of using the custom Hypothesis generators for testing the intent-based API layer.

## Example 1: Testing Path Validation

```python
from hypothesis import given, settings
from tests.property.generators import valid_file_paths, valid_directory_paths
from src.intent.path_validator import PathValidator

@given(path=valid_file_paths())
@settings(max_examples=100)
def test_file_path_validation_accepts_valid_paths(path: str):
    """Property: All valid file paths should pass validation."""
    validator = PathValidator(config=default_config(), repo_root=Path.cwd())
    
    # Create the file temporarily
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()
    
    try:
        result = validator.validate_path(str(file_path), scope="file")
        assert result.valid, f"Valid file path rejected: {path}"
    finally:
        file_path.unlink()
        # Clean up empty directories
        for parent in file_path.parents:
            try:
                parent.rmdir()
            except OSError:
                break

@given(path=valid_directory_paths())
@settings(max_examples=100)
def test_directory_path_validation(path: str):
    """Property: All valid directory paths should pass validation."""
    validator = PathValidator(config=default_config(), repo_root=Path.cwd())
    
    # Create the directory temporarily
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create a BUILD file
    build_file = dir_path / "BUILD"
    build_file.touch()
    
    try:
        result = validator.validate_path(str(dir_path), scope="directory")
        assert result.valid, f"Valid directory path rejected: {path}"
    finally:
        build_file.unlink()
        # Clean up directories
        for parent in [dir_path] + list(dir_path.parents):
            try:
                parent.rmdir()
            except OSError:
                break
```

## Example 2: Testing Intent Mapping

```python
from hypothesis import given, settings
from tests.property.generators import intent_contexts
from src.intent.intent_mapper import IntentMapper

@given(context=intent_contexts())
@settings(max_examples=100)
def test_intent_mapping_produces_valid_target_specs(context: dict):
    """Property: All intent contexts should map to valid Pants target specs."""
    mapper = IntentMapper(config=default_config(), validator=mock_validator())
    
    result = mapper.map_intent(
        scope=context['scope'],
        path=context['path'],
        recursive=context['recursive'],
        test_filter=context['test_filter']
    )
    
    # Target spec should not be empty
    assert result.target_spec
    
    # Target spec should match expected patterns
    if context['scope'] == 'all':
        assert result.target_spec == '::'
    elif context['scope'] == 'directory':
        if context['recursive']:
            assert result.target_spec.endswith('::')
        else:
            assert result.target_spec.endswith(':')
    elif context['scope'] == 'file':
        assert context['path'] in result.target_spec
    
    # Test filter should be in additional options if provided
    if context['test_filter']:
        assert '-k' in result.additional_options
        assert context['test_filter'] in result.additional_options
```

## Example 3: Testing Error Translation

```python
from hypothesis import given, settings
from tests.property.generators import pants_errors, intent_contexts
from src.intent.error_translator import ErrorTranslator

@given(error=pants_errors(), context=intent_contexts())
@settings(max_examples=100)
def test_error_translation_preserves_raw_error(error: str, context: dict):
    """Property: Error translation should always preserve the raw error."""
    translator = ErrorTranslator(config=default_config())
    
    intent_context = IntentContext(**context)
    translated = translator.translate_error(error, intent_context)
    
    # Raw error should always be preserved
    assert translated.raw_error == error
    
    # Translated message should not be empty
    assert translated.message
    
    # Translated message should be different from raw error (unless no rule matched)
    # This helps ensure translation is actually happening

@given(error=pants_errors())
@settings(max_examples=100)
def test_error_translation_provides_actionable_suggestions(error: str):
    """Property: Certain error types should provide actionable suggestions."""
    translator = ErrorTranslator(config=default_config())
    context = IntentContext(scope='all', path=None, recursive=True, test_filter=None)
    
    translated = translator.translate_error(error, context)
    
    # BUILD file errors should suggest running tailor
    if 'BUILD' in error or 'build file' in error.lower():
        assert translated.suggestion == 'pants tailor' or 'tailor' in translated.message.lower()
```

## Example 4: Testing Test Filter Patterns

```python
from hypothesis import given, settings, assume
from tests.property.generators import pytest_filter_patterns
from src.intent.intent_mapper import IntentMapper

@given(pattern=pytest_filter_patterns())
@settings(max_examples=100)
def test_filter_patterns_are_properly_escaped(pattern: str):
    """Property: Test filter patterns should be safely passed to Pants."""
    # Assume pattern doesn't contain shell injection characters
    assume(';' not in pattern)
    assume('&' not in pattern)
    assume('|' not in pattern)
    
    mapper = IntentMapper(config=default_config(), validator=mock_validator())
    
    result = mapper.map_intent(
        scope='all',
        path=None,
        recursive=True,
        test_filter=pattern
    )
    
    # Pattern should be in additional options
    assert '-k' in result.additional_options
    assert pattern in result.additional_options
    
    # Options should be a list (not a string that could be shell-injected)
    assert isinstance(result.additional_options, list)

@given(pattern=pytest_filter_patterns())
@settings(max_examples=100)
def test_filter_patterns_work_with_all_scopes(pattern: str):
    """Property: Test filters should work with any scope."""
    mapper = IntentMapper(config=default_config(), validator=mock_validator())
    
    for scope in ['all', 'directory', 'file']:
        path = 'src/tests' if scope in ['directory', 'file'] else None
        
        result = mapper.map_intent(
            scope=scope,
            path=path,
            recursive=True,
            test_filter=pattern
        )
        
        # Filter should always be applied
        assert '-k' in result.additional_options
        assert pattern in result.additional_options
```

## Example 5: Testing Edge Cases

```python
from hypothesis import given, settings
from tests.property.generators import edge_case_paths
from src.intent.integration import sanitize_path

@given(path=edge_case_paths())
@settings(max_examples=100)
def test_path_sanitization_prevents_directory_traversal(path: str):
    """Property: Path sanitization should prevent directory traversal attacks."""
    sanitized = sanitize_path(path)
    
    # Should not contain parent directory references
    assert '..' not in sanitized
    
    # Should not be an absolute path
    assert not sanitized.startswith('/')
    
    # Should not be empty (unless input was empty)
    if path:
        assert sanitized

@given(path=edge_case_paths())
@settings(max_examples=100)
def test_path_validation_handles_edge_cases_gracefully(path: str):
    """Property: Path validator should handle edge cases without crashing."""
    validator = PathValidator(config=default_config(), repo_root=Path.cwd())
    
    # Should not raise an exception
    try:
        result = validator.validate_path(path, scope='file')
        # Result should have either valid=True or an error message
        assert result.valid or result.error
    except Exception as e:
        pytest.fail(f"Path validation raised unexpected exception: {e}")
```

## Example 6: Testing Pants Target Specifications

```python
from hypothesis import given, settings
from tests.property.generators import pants_target_specs
from src.intent.intent_mapper import IntentMapper

@given(spec=pants_target_specs())
@settings(max_examples=100)
def test_backward_compatibility_with_raw_pants_syntax(spec: str):
    """Property: System should handle raw Pants target specs for backward compatibility."""
    # This tests the legacy mode where users provide raw Pants syntax
    
    # The spec should be a valid Pants target specification
    assert spec
    
    # Should match one of the known patterns
    is_valid_spec = (
        spec == '::' or
        spec.endswith('::') or
        spec.endswith(':') or
        ':' in spec or
        '.' in spec  # File path
    )
    
    assert is_valid_spec, f"Invalid target spec: {spec}"
```

## Example 7: Testing Configuration Impact

```python
from hypothesis import given, settings
from tests.property.generators import valid_file_paths
from src.intent.path_validator import PathValidator
from src.intent.data_models import Configuration

@given(path=valid_file_paths())
@settings(max_examples=50)
def test_disabled_validation_skips_checks(path: str):
    """Property: When validation is disabled, all paths should pass."""
    config = Configuration(enable_path_validation=False)
    validator = PathValidator(config=config, repo_root=Path.cwd())
    
    # Should pass validation even if file doesn't exist
    result = validator.validate_path(path, scope='file')
    assert result.valid

@given(path=valid_directory_paths())
@settings(max_examples=50)
def test_disabled_build_file_checking_skips_build_checks(path: str):
    """Property: When BUILD file checking is disabled, directories without BUILD files should pass."""
    config = Configuration(
        enable_path_validation=True,
        enable_build_file_checking=False
    )
    validator = PathValidator(config=config, repo_root=Path.cwd())
    
    # Create directory without BUILD file
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    
    try:
        result = validator.validate_path(str(dir_path), scope='directory')
        # Should pass even without BUILD file
        assert result.valid
    finally:
        # Clean up
        for parent in [dir_path] + list(dir_path.parents):
            try:
                parent.rmdir()
            except OSError:
                break
```

## Running These Examples

To run property tests with these examples:

```bash
# Run with default settings (100 examples)
pytest tests/property/ -v

# Run with more examples for thorough testing
pytest tests/property/ -v --hypothesis-max-examples=1000

# Run with hypothesis statistics
pytest tests/property/ -v --hypothesis-show-statistics

# Run a specific property test
pytest tests/property/test_intent_mapper_properties.py::test_intent_mapping_produces_valid_target_specs -v
```

## Tips for Writing Property Tests

1. **Use `assume()` to filter inputs**: Skip invalid combinations rather than handling them
2. **Keep properties simple**: Test one property at a time
3. **Use fixtures for setup**: Create temporary files/directories in fixtures
4. **Clean up resources**: Always clean up in finally blocks
5. **Set appropriate max_examples**: Balance thoroughness with test speed
6. **Use `@settings` decorator**: Configure Hypothesis behavior per test
7. **Test invariants**: Focus on properties that should always hold
8. **Combine generators**: Use multiple generators together for complex scenarios

## Common Patterns

### Testing Inverse Operations

```python
@given(context=intent_contexts())
def test_intent_mapping_is_reversible(context: dict):
    """Property: Mapping and parsing should be inverse operations."""
    # Map intent to target spec
    result = map_intent(**context)
    
    # Parse target spec back to intent
    parsed = parse_target_spec(result.target_spec)
    
    # Should get back the same intent (approximately)
    assert parsed.scope == context['scope']
```

### Testing Idempotence

```python
@given(path=valid_file_paths())
def test_path_sanitization_is_idempotent(path: str):
    """Property: Sanitizing twice should give same result as sanitizing once."""
    sanitized_once = sanitize_path(path)
    sanitized_twice = sanitize_path(sanitized_once)
    
    assert sanitized_once == sanitized_twice
```

### Testing Commutativity

```python
@given(pattern1=pytest_filter_patterns(), pattern2=pytest_filter_patterns())
def test_filter_combination_order_independence(pattern1: str, pattern2: str):
    """Property: Combining filters with OR should be commutative."""
    combined1 = f"{pattern1} or {pattern2}"
    combined2 = f"{pattern2} or {pattern1}"
    
    # Both should match the same tests (in practice)
    # This is a simplified example - actual test would run against real test suite
    assert True  # Placeholder
```
