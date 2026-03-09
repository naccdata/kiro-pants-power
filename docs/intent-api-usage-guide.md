# Intent-Based API Usage Guide

## Overview

The intent-based API layer provides a simple, user-friendly interface for running Pants commands without needing to understand Pants target syntax. Instead of specifying targets like `src/tests::` or `src/app:main`, you specify your intent using clear parameters like scope and path.

## Quick Start

### Basic Usage

```python
from src.intent.integration import map_intent_to_pants_command

# Test all code in the repository
result = map_intent_to_pants_command(
    scope="all"
)
# Returns: target_spec="::", additional_options=[]

# Test a specific directory recursively
result = map_intent_to_pants_command(
    scope="directory",
    path="src/tests",
    recursive=True
)
# Returns: target_spec="src/tests::", additional_options=[]

# Test a specific file
result = map_intent_to_pants_command(
    scope="file",
    path="src/tests/test_auth.py"
)
# Returns: target_spec="src/tests/test_auth.py", additional_options=[]
```

## Core Concepts

### Scopes

The `scope` parameter defines what you want to operate on:

- **`all`**: Operate on all code in the repository recursively
- **`directory`**: Operate on code in a specific directory
- **`file`**: Operate on a specific file

### Paths

The `path` parameter specifies the location:

- Required for `directory` and `file` scopes
- Not used for `all` scope
- Should be relative to the repository root
- Examples: `"src/app"`, `"tests/unit/test_main.py"`

### Recursive Flag

The `recursive` parameter controls subdirectory inclusion (directory scope only):

- `True` (default): Include all subdirectories
- `False`: Only include the specified directory

### Test Filters

The `test_filter` parameter allows filtering specific tests:

- Uses pytest-style syntax
- Examples: `"test_create"`, `"test_create or test_update"`, `"not test_slow"`
- Works with all scopes

## Examples by Scope

### Scope: All

Test everything in the repository:

```python
result = map_intent_to_pants_command(scope="all")
# target_spec: "::"
```

Test everything, but only tests matching a pattern:

```python
result = map_intent_to_pants_command(
    scope="all",
    test_filter="test_integration"
)
# target_spec: "::"
# additional_options: ["-k", "test_integration"]
```

### Scope: Directory

Test all code in a directory and its subdirectories:

```python
result = map_intent_to_pants_command(
    scope="directory",
    path="src/app",
    recursive=True
)
# target_spec: "src/app::"
```

Test only the specified directory (not subdirectories):

```python
result = map_intent_to_pants_command(
    scope="directory",
    path="src/app",
    recursive=False
)
# target_spec: "src/app:"
```

Test a directory with a test filter:

```python
result = map_intent_to_pants_command(
    scope="directory",
    path="tests/unit",
    recursive=True,
    test_filter="test_auth"
)
# target_spec: "tests/unit::"
# additional_options: ["-k", "test_auth"]
```

### Scope: File

Test a specific file:

```python
result = map_intent_to_pants_command(
    scope="file",
    path="tests/unit/test_auth.py"
)
# target_spec: "tests/unit/test_auth.py"
```

Test specific functions in a file:

```python
result = map_intent_to_pants_command(
    scope="file",
    path="tests/unit/test_auth.py",
    test_filter="test_login or test_logout"
)
# target_spec: "tests/unit/test_auth.py"
# additional_options: ["-k", "test_login or test_logout"]
```

## Smart Defaults

The system applies smart defaults when parameters are omitted:

```python
# No scope provided → defaults to "all"
result = map_intent_to_pants_command()
# Equivalent to: scope="all"

# Directory scope without path → defaults to current directory
result = map_intent_to_pants_command(scope="directory")
# Equivalent to: scope="directory", path="."

# Directory scope without recursive → defaults to True
result = map_intent_to_pants_command(scope="directory", path="src")
# Equivalent to: scope="directory", path="src", recursive=True
```

## Path Validation

The system automatically validates paths before execution:

### File Validation

```python
# Valid file
result = map_intent_to_pants_command(
    scope="file",
    path="src/main.py"
)
# ✓ Succeeds if file exists

# Invalid file
result = map_intent_to_pants_command(
    scope="file",
    path="src/missing.py"
)
# ✗ Raises ValidationError: "Path does not exist: src/missing.py"
```

### Directory Validation

```python
# Valid directory with BUILD file
result = map_intent_to_pants_command(
    scope="directory",
    path="src/app"
)
# ✓ Succeeds if directory exists and has BUILD file

# Directory without BUILD file
result = map_intent_to_pants_command(
    scope="directory",
    path="src/new_module"
)
# ✗ Raises ValidationError: "No BUILD file found for src/new_module. Run 'pants tailor' to generate BUILD files"
```

### BUILD File Detection

The system searches parent directories for BUILD files:

```python
# Directory structure:
# src/
#   BUILD
#   app/
#     models/
#       user.py

result = map_intent_to_pants_command(
    scope="directory",
    path="src/app/models"
)
# ✓ Succeeds - finds BUILD in parent directory (src/)
```

## Error Translation

Pants errors are automatically translated to user-friendly messages:

### Example 1: No Targets Found

```python
# Pants error: "No targets found for target spec 'src/empty::'"
# Translated: "No tests found in directory src/empty"
```

### Example 2: Unknown Target

```python
# Pants error: "Unknown target: src/missing.py"
# Translated: "Path contains no testable code: src/missing.py"
```

### Example 3: BUILD File Not Found

```python
# Pants error: "BUILD file not found in directory src/new"
# Translated: "Directory not configured for Pants. Run 'pants tailor' to set up BUILD files"
```

## Configuration

Customize behavior using the Configuration class:

```python
from src.intent.configuration import Configuration

# Disable path validation (faster, but less safe)
config = Configuration(enable_path_validation=False)

# Disable BUILD file checking
config = Configuration(enable_build_file_checking=False)

# Disable error translation
config = Configuration(enable_error_translation=False)

# Adjust cache TTL
config = Configuration(build_file_cache_ttl=120)  # 2 minutes

# Adjust performance thresholds
config = Configuration(
    path_validation_timeout=20,  # ms
    build_file_check_timeout=100  # ms
)
```

### Environment Variables

Configuration can also be set via environment variables:

```bash
export KIRO_PANTS_VALIDATE_PATHS=false
export KIRO_PANTS_CHECK_BUILD_FILES=false
export KIRO_PANTS_CACHE_TTL=120
export KIRO_PANTS_TRANSLATE_ERRORS=false
```

## Advanced Usage

### Using with Error Handling

```python
from src.intent.integration import execute_with_error_handling

# Wrap execution with automatic error handling
response = execute_with_error_handling(
    scope="directory",
    path="src/tests",
    recursive=True,
    test_filter="test_integration"
)

if response.success:
    print(f"Success: {response.message}")
    print(f"Output: {response.output}")
else:
    print(f"Error: {response.message}")
    print(f"Suggestion: {response.suggestion}")
```

### Custom Error Translation Rules

```python
from src.intent.error_translator import ErrorTranslator, TranslationRule

translator = ErrorTranslator(config=config)

# Add custom translation rule
custom_rule = TranslationRule(
    pattern=r"timeout.*exceeded",
    template="Command timed out. Try running on a smaller scope.",
    priority=15
)
translator.add_translation_rule(custom_rule)
```

### Performance Monitoring

```python
from src.intent.monitoring import get_metrics, reset_metrics

# Get current metrics
metrics = get_metrics()
print(f"Cache hit rate: {metrics.get_cache_hit_rate():.1f}%")
print(f"Average validation time: {metrics.get_average_validation_time():.2f}ms")
print(f"Total validations: {metrics.total_validations}")

# Reset metrics
reset_metrics()
```

## Best Practices

1. **Use specific scopes when possible**: Testing a specific directory or file is faster than testing everything

2. **Leverage test filters**: Use test filters to run only relevant tests

3. **Enable caching**: Keep BUILD file caching enabled for better performance

4. **Run pants tailor regularly**: Ensure BUILD files are up to date

5. **Use validation in development**: Keep path validation enabled during development to catch errors early

6. **Disable validation in CI**: Consider disabling validation in CI if paths are guaranteed to be correct

7. **Monitor performance**: Use metrics to identify performance bottlenecks

## Troubleshooting

### "Path does not exist"

**Problem**: The specified path doesn't exist in the repository.

**Solution**: Check the path spelling and ensure it's relative to the repository root.

### "No BUILD file found"

**Problem**: The directory doesn't have a BUILD file.

**Solution**: Run `pants tailor` to generate BUILD files:

```bash
pants tailor
```

### "No tests found"

**Problem**: The specified scope doesn't contain any tests.

**Solution**: 
- Verify the path is correct
- Check that test files follow naming conventions
- Ensure BUILD files are up to date

### Slow validation

**Problem**: Path validation is taking too long.

**Solution**:
- Check cache hit rate with `get_metrics()`
- Increase cache TTL if needed
- Consider disabling validation for known-good paths

## Migration from Raw Pants Syntax

If you're currently using raw Pants target syntax, here's how to migrate:

| Raw Pants Syntax | Intent-Based API |
|------------------|------------------|
| `::` | `scope="all"` |
| `src/tests::` | `scope="directory", path="src/tests", recursive=True` |
| `src/tests:` | `scope="directory", path="src/tests", recursive=False` |
| `src/test.py` | `scope="file", path="src/test.py"` |
| `:: -k test_auth` | `scope="all", test_filter="test_auth"` |

## API Reference

See the [API Reference](./intent-api-reference.md) for detailed documentation of all classes and methods.
