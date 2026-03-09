# Intent-Based API Troubleshooting Guide

## Common Issues and Solutions

### Path Validation Errors

#### Issue: "Path does not exist: {path}"

**Cause**: The specified file or directory doesn't exist in the repository.

**Solutions**:
1. Verify the path is correct and relative to repository root
2. Check for typos in the path
3. Ensure the file/directory hasn't been moved or deleted
4. Use `ls` or `find` to locate the correct path

**Example**:
```python
# ✗ Wrong
map_intent_to_pants_command(scope="file", path="/absolute/path/file.py")

# ✓ Correct
map_intent_to_pants_command(scope="file", path="src/app/file.py")
```

#### Issue: "No BUILD file found for {path}"

**Cause**: The directory doesn't have a BUILD file, which Pants requires.

**Solutions**:
1. Run `pants tailor` to generate BUILD files:
   ```bash
   pants tailor
   ```

2. Manually create a BUILD file in the directory

3. If the directory should use a parent's BUILD file, ensure the parent has one

4. Disable BUILD file checking if not needed:
   ```python
   config = Configuration(enable_build_file_checking=False)
   ```

**Example**:
```bash
# Generate BUILD files for all directories
pants tailor

# Generate BUILD files for specific directory
pants tailor --check src/new_module
```

### Scope and Path Errors

#### Issue: "scope='file' requires a path parameter"

**Cause**: File scope was specified without providing a path.

**Solution**: Always provide a path when using file scope:

```python
# ✗ Wrong
map_intent_to_pants_command(scope="file")

# ✓ Correct
map_intent_to_pants_command(scope="file", path="src/main.py")
```

#### Issue: Unexpected target specification

**Cause**: Scope and path combination doesn't match expectations.

**Solutions**:
1. Verify scope matches your intent:
   - Use `"all"` for entire repository
   - Use `"directory"` for a specific directory
   - Use `"file"` for a specific file

2. Check recursive flag for directory scope:
   - `recursive=True` → `path::`
   - `recursive=False` → `path:`

**Example**:
```python
# Test only src/tests directory (not subdirectories)
map_intent_to_pants_command(
    scope="directory",
    path="src/tests",
    recursive=False  # Important!
)
```

### Test Filter Issues

#### Issue: Test filter not working as expected

**Cause**: Test filter syntax might be incorrect or tests don't match the pattern.

**Solutions**:
1. Use pytest-style filter syntax:
   - Simple: `"test_create"`
   - Wildcard: `"test_create*"` or `"*auth*"`
   - Boolean: `"test_create or test_update"`
   - Negation: `"not test_slow"`

2. Verify test names match the filter

3. Test the filter with pytest directly first:
   ```bash
   pytest -k "test_create" tests/
   ```

**Example**:
```python
# ✗ Wrong - invalid syntax
map_intent_to_pants_command(
    scope="all",
    test_filter="test_create AND test_update"  # Wrong operator
)

# ✓ Correct
map_intent_to_pants_command(
    scope="all",
    test_filter="test_create and test_update"  # Lowercase 'and'
)
```

### Performance Issues

#### Issue: Validation is slow

**Cause**: Path validation or BUILD file detection is taking too long.

**Diagnosis**:
```python
from src.intent.monitoring import get_metrics

metrics = get_metrics()
print(f"Average validation time: {metrics.get_average_validation_time():.2f}ms")
print(f"Cache hit rate: {metrics.get_cache_hit_rate():.1f}%")
```

**Solutions**:
1. Check cache hit rate - low rate indicates cache isn't helping:
   ```python
   # Increase cache TTL
   config = Configuration(build_file_cache_ttl=300)  # 5 minutes
   ```

2. Disable validation for known-good paths:
   ```python
   config = Configuration(enable_path_validation=False)
   ```

3. Disable BUILD file checking if not needed:
   ```python
   config = Configuration(enable_build_file_checking=False)
   ```

4. Profile specific operations:
   ```python
   import time
   start = time.perf_counter()
   result = validator.validate_path(path, scope)
   elapsed_ms = (time.perf_counter() - start) * 1000
   print(f"Validation took {elapsed_ms:.2f}ms")
   ```

#### Issue: Cache not improving performance

**Cause**: Cache TTL might be too short or cache is being cleared.

**Solutions**:
1. Increase cache TTL:
   ```python
   config = Configuration(build_file_cache_ttl=600)  # 10 minutes
   ```

2. Check if cache is being cleared unexpectedly:
   ```python
   validator.get_cache_stats()  # Check cache size
   ```

3. Avoid clearing cache unnecessarily:
   ```python
   # Only clear after running pants tailor
   validator.clear_cache()
   ```

### Configuration Issues

#### Issue: Configuration not taking effect

**Cause**: Configuration might not be passed to components correctly.

**Solutions**:
1. Ensure configuration is passed to all components:
   ```python
   config = Configuration(enable_path_validation=False)
   validator = PathValidator(config=config, repo_root=Path.cwd())
   mapper = IntentMapper(config=config, validator=validator)
   ```

2. Check environment variables aren't overriding:
   ```bash
   env | grep KIRO_PANTS
   ```

3. Verify configuration values:
   ```python
   print(f"Path validation: {config.enable_path_validation}")
   print(f"BUILD checking: {config.enable_build_file_checking}")
   ```

#### Issue: Environment variables not working

**Cause**: Environment variable names might be incorrect or not loaded.

**Solutions**:
1. Use correct environment variable names:
   - `KIRO_PANTS_VALIDATE_PATHS`
   - `KIRO_PANTS_CHECK_BUILD_FILES`
   - `KIRO_PANTS_CACHE_TTL`
   - `KIRO_PANTS_TRANSLATE_ERRORS`

2. Ensure variables are exported:
   ```bash
   export KIRO_PANTS_VALIDATE_PATHS=false
   ```

3. Load configuration from environment:
   ```python
   config = Configuration.from_env()
   ```

### Error Translation Issues

#### Issue: Errors not being translated

**Cause**: Error translation might be disabled or error doesn't match any rules.

**Solutions**:
1. Ensure error translation is enabled:
   ```python
   config = Configuration(enable_error_translation=True)
   ```

2. Check if error matches translation rules:
   ```python
   translator = ErrorTranslator(config=config)
   translated = translator.translate_error(pants_error, intent_context)
   print(f"Rule applied: {translated.rule_applied}")
   ```

3. Add custom translation rule if needed:
   ```python
   custom_rule = TranslationRule(
        pattern=r"your error pattern",
        template="Your user-friendly message",
        priority=10
   )
   translator.add_translation_rule(custom_rule)
   ```

#### Issue: Raw error not preserved

**Cause**: This should never happen - it's a bug if raw error is missing.

**Solution**: Report this as a bug. Raw errors should always be preserved in `TranslatedError.raw_error`.

### Integration Issues

#### Issue: "ValidationError" not caught

**Cause**: ValidationError might not be imported or caught correctly.

**Solution**: Use proper exception handling:

```python
from src.intent.data_models import ValidationError

try:
    result = map_intent_to_pants_command(scope="file", path="missing.py")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

#### Issue: Pants command execution fails

**Cause**: The generated target spec might be incorrect or Pants might have issues.

**Diagnosis**:
1. Check the generated target spec:
   ```python
   result = map_intent_to_pants_command(scope="directory", path="src")
   print(f"Target spec: {result.target_spec}")
   print(f"Options: {result.additional_options}")
   ```

2. Test the target spec directly with Pants:
   ```bash
   pants test src::
   ```

**Solutions**:
1. Verify the target spec is valid Pants syntax
2. Check Pants configuration (pants.toml)
3. Ensure BUILD files are up to date
4. Check Pants logs for detailed errors

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.intent")
logger.setLevel(logging.DEBUG)
```

### Inspect Intent Resolution

```python
from src.intent.intent_mapper import IntentMapper

mapper = IntentMapper(config=config, validator=validator)
resolved = mapper.resolve_defaults(scope=None, path=None, recursive=None)
print(f"Resolved intent: {resolved}")
print(f"Defaults applied: {resolved.defaults_applied}")
```

### Check Path Validator State

```python
from src.intent.path_validator import PathValidator

validator = PathValidator(config=config, repo_root=Path.cwd())

# Check cache stats
stats = validator.get_cache_stats()
print(f"Cache size: {stats['size']}")
print(f"Cache entries: {stats['entries']}")

# Test specific path
result = validator.validate_path("src/app", scope="directory")
print(f"Valid: {result.valid}")
print(f"Error: {result.error}")
print(f"Suggestion: {result.suggestion}")
```

### Monitor Metrics

```python
from src.intent.monitoring import get_metrics, reset_metrics

# Reset metrics to start fresh
reset_metrics()

# Run operations
map_intent_to_pants_command(scope="all")
map_intent_to_pants_command(scope="directory", path="src")

# Check metrics
metrics = get_metrics()
print(metrics.to_dict())
```

### Test Individual Components

```python
# Test Intent Mapper
from src.intent.intent_mapper import IntentMapper
mapper = IntentMapper(config=config, validator=mock_validator)
result = mapper.map_intent(scope="all")
print(f"Mapping result: {result}")

# Test Path Validator
from src.intent.path_validator import PathValidator
validator = PathValidator(config=config, repo_root=Path.cwd())
result = validator.validate_path("src", scope="directory")
print(f"Validation result: {result}")

# Test Error Translator
from src.intent.error_translator import ErrorTranslator
translator = ErrorTranslator(config=config)
translated = translator.translate_error("No targets found", intent_context)
print(f"Translated: {translated.message}")
```

## Getting Help

If you're still experiencing issues:

1. Check the [Usage Guide](./intent-api-usage-guide.md) for correct usage patterns
2. Review the [API Reference](./intent-api-reference.md) for detailed documentation
3. Run the test suite to verify the system is working:
   ```bash
   pytest tests/unit/test_intent_mapper.py -v
   pytest tests/integration/test_integration_end_to_end.py -v
   ```
4. Enable debug logging to see detailed execution flow
5. Check metrics to identify performance bottlenecks
6. Report bugs with:
   - Python version
   - Pants version
   - Configuration used
   - Full error message and stack trace
   - Minimal reproduction example
