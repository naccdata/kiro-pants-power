# Migration Guide: Raw Pants Syntax to Intent-Based API

## Overview

This guide helps you migrate from using raw Pants target syntax to the intent-based API. The intent-based API provides a simpler, more intuitive interface while maintaining full Pants functionality.

## Why Migrate?

**Benefits of Intent-Based API**:
- No need to learn Pants target syntax
- Clear, self-documenting code
- Automatic path validation
- User-friendly error messages
- Smart defaults reduce boilerplate
- Type-safe parameters

**Before (Raw Pants)**:
```python
# What does "::" mean? What about ":" vs "::"?
pants_command("test", "::")
pants_command("test", "src/tests::")
pants_command("test", "src/tests:")
```

**After (Intent-Based)**:
```python
# Clear and self-documenting
map_intent_to_pants_command(scope="all")
map_intent_to_pants_command(scope="directory", path="src/tests", recursive=True)
map_intent_to_pants_command(scope="directory", path="src/tests", recursive=False)
```

## Migration Mapping

### Basic Target Specifications

| Raw Pants Syntax | Intent-Based API | Description |
|------------------|------------------|-------------|
| `::` | `scope="all"` | All targets recursively |
| `src/tests::` | `scope="directory", path="src/tests", recursive=True` | Directory recursively |
| `src/tests:` | `scope="directory", path="src/tests", recursive=False` | Directory non-recursively |
| `src/test.py` | `scope="file", path="src/test.py"` | Specific file |
| `src/app:main` | Not supported (use file scope) | Explicit target |

### With Test Filters

| Raw Pants Syntax | Intent-Based API |
|------------------|------------------|
| `:: -k test_auth` | `scope="all", test_filter="test_auth"` |
| `src/tests:: -k "test_create or test_update"` | `scope="directory", path="src/tests", test_filter="test_create or test_update"` |
| `src/test.py -k test_login` | `scope="file", path="src/test.py", test_filter="test_login"` |

## Step-by-Step Migration

### Step 1: Identify Current Usage

Find all places where you're using raw Pants syntax:

```bash
# Search for Pants command patterns
grep -r "pants test" .
grep -r "::" .
grep -r "target.*:" .
```

### Step 2: Replace Simple Cases

Start with the simplest cases:

**Before**:
```python
def run_all_tests():
    return execute_pants_command("test", "::")
```

**After**:
```python
from src.intent.integration import map_intent_to_pants_command

def run_all_tests():
    result = map_intent_to_pants_command(scope="all")
    return execute_pants_command("test", result.target_spec, result.additional_options)
```

### Step 3: Replace Directory Targets

**Before**:
```python
def test_directory(path, recursive=True):
    suffix = "::" if recursive else ":"
    target = f"{path}{suffix}"
    return execute_pants_command("test", target)
```

**After**:
```python
from src.intent.integration import map_intent_to_pants_command

def test_directory(path, recursive=True):
    result = map_intent_to_pants_command(
        scope="directory",
        path=path,
        recursive=recursive
    )
    return execute_pants_command("test", result.target_spec, result.additional_options)
```

### Step 4: Replace File Targets

**Before**:
```python
def test_file(file_path):
    return execute_pants_command("test", file_path)
```

**After**:
```python
from src.intent.integration import map_intent_to_pants_command

def test_file(file_path):
    result = map_intent_to_pants_command(
        scope="file",
        path=file_path
    )
    return execute_pants_command("test", result.target_spec, result.additional_options)
```

### Step 5: Add Test Filters

**Before**:
```python
def test_with_filter(target, filter_pattern):
    return execute_pants_command("test", target, "-k", filter_pattern)
```

**After**:
```python
from src.intent.integration import map_intent_to_pants_command

def test_with_filter(scope, path, filter_pattern):
    result = map_intent_to_pants_command(
        scope=scope,
        path=path,
        test_filter=filter_pattern
    )
    return execute_pants_command("test", result.target_spec, *result.additional_options)
```

### Step 6: Add Error Handling

**Before**:
```python
def test_directory(path):
    target = f"{path}::"
    try:
        return execute_pants_command("test", target)
    except Exception as e:
        print(f"Error: {e}")
        return None
```

**After**:
```python
from src.intent.integration import execute_with_error_handling

def test_directory(path):
    response = execute_with_error_handling(
        scope="directory",
        path=path,
        recursive=True
    )
    
    if response.success:
        return response.output
    else:
        print(f"Error: {response.message}")
        if response.suggestion:
            print(f"Suggestion: {response.suggestion}")
        return None
```

## Common Migration Patterns

### Pattern 1: Dynamic Target Construction

**Before**:
```python
def build_target(base_path, recursive, filter_pattern=None):
    suffix = "::" if recursive else ":"
    target = f"{base_path}{suffix}"
    
    args = ["test", target]
    if filter_pattern:
        args.extend(["-k", filter_pattern])
    
    return execute_pants_command(*args)
```

**After**:
```python
def build_target(base_path, recursive, filter_pattern=None):
    result = map_intent_to_pants_command(
        scope="directory",
        path=base_path,
        recursive=recursive,
        test_filter=filter_pattern
    )
    
    return execute_pants_command("test", result.target_spec, *result.additional_options)
```

### Pattern 2: Path Validation

**Before**:
```python
import os

def test_if_exists(path):
    if not os.path.exists(path):
        raise ValueError(f"Path does not exist: {path}")
    
    target = f"{path}::"
    return execute_pants_command("test", target)
```

**After**:
```python
from src.intent.data_models import ValidationError

def test_if_exists(path):
    try:
        result = map_intent_to_pants_command(
            scope="directory",
            path=path,
            recursive=True
        )
        return execute_pants_command("test", result.target_spec)
    except ValidationError as e:
        raise ValueError(str(e))
```

### Pattern 3: Multiple Commands

**Before**:
```python
def run_checks(path):
    target = f"{path}::"
    
    lint_result = execute_pants_command("lint", target)
    test_result = execute_pants_command("test", target)
    check_result = execute_pants_command("check", target)
    
    return {
        "lint": lint_result,
        "test": test_result,
        "check": check_result
    }
```

**After**:
```python
def run_checks(path):
    result = map_intent_to_pants_command(
        scope="directory",
        path=path,
        recursive=True
    )
    
    target = result.target_spec
    options = result.additional_options
    
    return {
        "lint": execute_pants_command("lint", target, *options),
        "test": execute_pants_command("test", target, *options),
        "check": execute_pants_command("check", target, *options)
    }
```

## Backward Compatibility

If you need to support both old and new syntax during migration:

```python
def test_target(target=None, scope=None, path=None, recursive=True, test_filter=None):
    """Support both raw Pants syntax and intent-based API."""
    
    if target is not None:
        # Legacy mode - use raw target
        args = ["test", target]
        if test_filter:
            args.extend(["-k", test_filter])
        return execute_pants_command(*args)
    else:
        # Intent mode - use intent-based API
        result = map_intent_to_pants_command(
            scope=scope,
            path=path,
            recursive=recursive,
            test_filter=test_filter
        )
        return execute_pants_command("test", result.target_spec, *result.additional_options)
```

## Testing Your Migration

### Unit Tests

Update your tests to use the intent-based API:

**Before**:
```python
def test_run_all_tests():
    result = run_all_tests()
    assert result.success
    assert "::" in result.command
```

**After**:
```python
def test_run_all_tests():
    result = run_all_tests()
    assert result.success
    # Intent-based API handles target spec internally
```

### Integration Tests

Test the migration with real Pants commands:

```python
def test_migration_produces_same_results():
    # Old way
    old_result = execute_pants_command("test", "src/tests::")
    
    # New way
    intent_result = map_intent_to_pants_command(
        scope="directory",
        path="src/tests",
        recursive=True
    )
    new_result = execute_pants_command("test", intent_result.target_spec)
    
    # Should produce same results
    assert old_result.exit_code == new_result.exit_code
```

## Rollback Plan

If you need to rollback:

1. Keep old code commented out during migration:
   ```python
   # Old way (kept for rollback)
   # target = f"{path}::"
   # result = execute_pants_command("test", target)
   
   # New way
   result = map_intent_to_pants_command(scope="directory", path=path)
   ```

2. Use feature flags:
   ```python
   USE_INTENT_API = os.getenv("USE_INTENT_API", "true") == "true"
   
   if USE_INTENT_API:
       result = map_intent_to_pants_command(scope="directory", path=path)
   else:
       target = f"{path}::"
       result = execute_pants_command("test", target)
   ```

3. Maintain backward compatibility wrapper (see above)

## Migration Checklist

- [ ] Identify all raw Pants syntax usage
- [ ] Replace simple `::` cases with `scope="all"`
- [ ] Replace directory targets with `scope="directory"`
- [ ] Replace file targets with `scope="file"`
- [ ] Add test filters using `test_filter` parameter
- [ ] Add error handling with `execute_with_error_handling`
- [ ] Update tests to use intent-based API
- [ ] Remove raw Pants syntax comments
- [ ] Update documentation
- [ ] Train team on new API

## Getting Help

If you encounter issues during migration:

1. Check the [Usage Guide](./intent-api-usage-guide.md)
2. Review the [Troubleshooting Guide](./intent-api-troubleshooting.md)
3. Look at examples in the test suite
4. Ask for help with specific migration scenarios

## Next Steps

After migration:

1. Remove backward compatibility code
2. Update team documentation
3. Add intent-based API to coding standards
4. Consider disabling raw Pants syntax in linters
5. Share migration experience with the team
