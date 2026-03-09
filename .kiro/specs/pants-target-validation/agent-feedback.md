# Kiro Pants Power - Improvement Recommendations

## Problem Statement

The kiro-pants-power currently passes target specifications directly to Pants without validation or correction. This leads to confusing errors when invalid target syntax is used, particularly for AI agents that may not be familiar with Pants conventions.

### Example Error

```
Command execution failed: devcontainer exec --workspace-folder /Users/bjkeller/Documents/workspace/naccdata/flywheel-gear-extensions pants test common/test/python/projects:test_study --test-report --test-report-dir=dist/test-reports --test-use-coverage --keep-sandboxes=on_failure

Exit code: 1

Output: 23:32:44.64 [ERROR] 1 Exception encountered:

Engine traceback:
  in test goal

ResolveError: The address common/test/python/projects:test_study from CLI arguments does not exist.

The target name ':test_study' is not defined in the directory common/test/python/projects. Did you mean one of these target names?

:tests
```

**Root Cause:** The subagent tried to use `:test_study` as a target name, but the actual target defined in the BUILD file is `:tests`.

## Pants Target Conventions (Background)

Pants uses specific target syntax:

1. **`:target_name`** - Specific target defined in BUILD file (e.g., `:tests`, `:lib`)
2. **`::`** - All targets in directory and all subdirectories
3. **`path/to/file.py`** - Specific file path
4. **`path/to/dir::`** - All targets in specific directory and subdirectories
5. **`path/to/dir:target_name`** - Specific target in specific directory

### Common Mistakes

- Using `:test_study` when the target is actually `:tests`
- Using `:test_file_name` instead of the actual target name
- Forgetting the `::` suffix for directory patterns
- Not knowing what targets are defined in BUILD files

## Proposed Improvements

### 1. Target Validation and Auto-Correction

**Enhancement:** Add intelligent target validation before executing Pants commands.

**Implementation Ideas:**

```python
def validate_and_correct_target(target: str, workspace_path: str) -> tuple[str, list[str]]:
    """
    Validate target syntax and suggest corrections.
    
    Returns:
        tuple: (corrected_target, warnings)
    """
    warnings = []
    
    # Pattern 1: Check if target looks like a file name being used as target name
    # e.g., ":test_study" should probably be "::test_study.py" or ":tests"
    if target.startswith(':') and not target.endswith('::'):
        target_name = target[1:]
        if 'test_' in target_name or '_test' in target_name:
            warnings.append(
                f"Target '{target}' looks like a test file name. "
                f"Did you mean ':tests' (the standard test target) or "
                f"'test_{target_name}.py' (specific file)?"
            )
            # Auto-correct to common pattern
            suggested_target = target.rsplit(':', 1)[0] + ':tests'
            return suggested_target, warnings
    
    # Pattern 2: Check for missing :: suffix on directory paths
    if '/' in target and not target.endswith('::') and ':' not in target:
        warnings.append(
            f"Target '{target}' looks like a directory path. "
            f"Did you mean '{target}::' to include all targets in that directory?"
        )
        return f"{target}::", warnings
    
    return target, warnings
```

**Benefits:**
- Catches common mistakes before they reach Pants
- Provides helpful suggestions
- Can auto-correct obvious errors
- Reduces frustration for AI agents and developers

### 2. Enhanced Error Messages

**Enhancement:** Parse Pants error output and provide clearer, more actionable error messages.

**Implementation Ideas:**

```python
def enhance_pants_error(error_output: str, original_target: str) -> str:
    """Parse Pants error and provide enhanced error message."""
    if "does not exist" in error_output and "Did you mean" in error_output:
        # Extract suggestions from Pants output
        suggestions = extract_suggestions(error_output)
        
        return f"""
Target Error: '{original_target}' does not exist.

Common Pants Target Patterns:
• ':tests' - Run all tests in a directory (most common for test directories)
• '::' - All targets in directory and subdirectories
• 'path/to/file.py' - Specific file
• 'path/to/dir::' - All targets in specific directory

Pants suggested these alternatives:
{format_suggestions(suggestions)}

Tip: Check the BUILD file in the target directory to see available target names.
"""
    
    return error_output
```

**Benefits:**
- Clearer error messages for AI agents
- Educational - teaches correct Pants conventions
- Reduces back-and-forth debugging

### 3. Target Discovery Tool

**Enhancement:** Add a new tool to discover available targets in a directory.

**New Tool: `pants_list_targets`**

```python
def pants_list_targets(directory: str = ".") -> dict:
    """
    List all available Pants targets in a directory.
    
    Parameters:
        directory: Directory path to list targets for (default: current directory)
    
    Returns:
        Dictionary with target information:
        {
            "directory": "common/test/python/projects",
            "targets": [
                {"name": "tests", "type": "python_tests", "description": "..."},
                {"name": "lib", "type": "python_sources", "description": "..."}
            ],
            "common_patterns": [
                "common/test/python/projects:tests",
                "common/test/python/projects::",
                "common/test/python/projects/test_study.py"
            ]
        }
    """
    # Run: pants list directory::
    # Parse output and return structured information
```

**Benefits:**
- AI agents can discover valid targets before attempting to use them
- Reduces trial-and-error
- Provides examples of correct usage

### 4. Improved Tool Documentation

**Enhancement:** Add Pants target convention guidance directly in tool descriptions.

**Example for `pants_test` tool:**

```python
{
    "name": "pants_test",
    "description": """
Run tests with pytest.

IMPORTANT - Pants Target Syntax:
For test directories, use one of these patterns:
• 'path/to/test/dir::' - All tests in directory (RECOMMENDED)
• 'path/to/test/dir:tests' - Standard test target name
• 'path/to/test_file.py' - Specific test file

Common Mistakes to Avoid:
• DON'T use ':test_file_name' - target names are defined in BUILD files
• DON'T forget '::' suffix for directory patterns
• DO check BUILD file for actual target names (usually ':tests' or ':lib')

Examples:
• pants_test(target="common/test/python/projects::") ✓
• pants_test(target="common/test/python/projects:tests") ✓
• pants_test(target="common/test/python/projects/test_study.py") ✓
• pants_test(target="common/test/python/projects:test_study") ✗ (wrong target name)
""",
    "parameters": {
        "target": {
            "type": "string",
            "description": "Pants target specification (default: '::')",
            "default": "::"
        }
    }
}
```

**Benefits:**
- AI agents see guidance every time they consider using the tool
- Examples show correct usage patterns
- Warnings about common mistakes

### 5. Smart Defaults for Test Commands

**Enhancement:** When running tests, default to common patterns if target looks suspicious.

**Implementation Ideas:**

```python
def smart_test_target(target: str) -> str:
    """Apply smart defaults for test commands."""
    # If target looks like it's trying to specify a test file as a target name
    if target.startswith(':test_') or target.endswith(':test'):
        # Extract directory path
        dir_path = target.rsplit(':', 1)[0] if ':' in target else '.'
        # Default to directory pattern
        return f"{dir_path}::" if dir_path != '.' else "::"
    
    return target
```

**Benefits:**
- Reduces errors from common mistakes
- More forgiving for AI agents
- Still allows explicit target specification

## Recommended Implementation Priority

1. **High Priority:**
   - Enhanced error messages (immediate value, low effort)
   - Improved tool documentation (helps AI agents learn correct patterns)

2. **Medium Priority:**
   - Target validation and auto-correction (prevents errors before they happen)
   - Smart defaults for test commands (reduces friction)

3. **Lower Priority:**
   - Target discovery tool (nice to have, but agents can learn patterns from docs)

## Testing Strategy

1. **Unit Tests:**
   - Test target validation logic with various invalid inputs
   - Test error message enhancement with real Pants error output
   - Test smart defaults with common mistake patterns

2. **Integration Tests:**
   - Test with actual Pants commands in devcontainer
   - Verify auto-correction produces valid targets
   - Verify enhanced errors are helpful

3. **AI Agent Testing:**
   - Test with spec-task-execution subagent
   - Verify subagent can recover from target errors
   - Measure reduction in target-related errors

## Alternative Approach: Repository-Specific Configuration

Instead of generic Pants target handling, the power could read repository-specific configuration:

```yaml
# .kiro/pants-power-config.yaml
target_conventions:
  test_directories:
    - "common/test/python"
    - "gear/*/test/python"
  default_test_target: ":tests"
  target_aliases:
    # Map common mistakes to correct targets
    ":test_study": ":tests"
    ":test_*": ":tests"
```

This would allow the power to be more intelligent about the specific repository structure.

## Conclusion

The kiro-pants-power is working correctly as a Pants command wrapper, but it could be significantly more helpful by:

1. Validating and correcting common target syntax mistakes
2. Providing clearer, more educational error messages
3. Including comprehensive Pants target guidance in tool descriptions
4. Offering target discovery capabilities

These improvements would make the power more robust for AI agents while still maintaining compatibility with standard Pants conventions.
