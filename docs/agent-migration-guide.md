# Agent Migration Guide: Using the Pants Power Effectively

## Purpose

This guide is for AI agents that use the Pants DevContainer Power MCP tools. It explains how to use the current intent-based API and how to handle error output correctly.

## API Modes

The Pants Power tools support two parameter modes:

### Intent-Based Mode (Preferred)

Use `scope`, `path`, and `recursive` parameters. This provides better error messages, path validation, and clearer intent.

```json
// Run check on a specific directory
{"scope": "directory", "path": "gear/gather_form_data", "recursive": true}

// Run check on a specific file
{"scope": "file", "path": "gear/gather_form_data/src/python/run.py"}

// Run check on everything
{"scope": "all"}
```

### Legacy Mode (Deprecated)

Uses the `target` parameter with raw Pants target syntax. This mode still works but produces less helpful error messages and skips path validation.

```json
// Legacy - avoid this
{"target": "gear/gather_form_data::"}
```

## Migration from Legacy to Intent-Based

| Legacy `target` value | Intent-based equivalent |
|---|---|
| `"::"` | `{"scope": "all"}` |
| `"gear/gather_form_data::"` | `{"scope": "directory", "path": "gear/gather_form_data", "recursive": true}` |
| `"gear/gather_form_data:"` | `{"scope": "directory", "path": "gear/gather_form_data", "recursive": false}` |
| `"gear/gather_form_data/src/python/run.py"` | `{"scope": "file", "path": "gear/gather_form_data/src/python/run.py"}` |

### Key differences

1. **No `::` or `:` suffixes needed** — the `recursive` flag handles this
2. **Paths are validated** — you get clear errors if a path doesn't exist or has no BUILD file
3. **Error messages reference your intent** — instead of cryptic Pants target errors

### For `pants_test` specifically

The intent-based API adds a `test_filter` parameter equivalent to pytest's `-k` flag:

```json
// Run specific tests matching a pattern
{"scope": "directory", "path": "gear/gather_form_data/test/python", "recursive": true, "test_filter": "test_export"}
```

## Understanding Error Output

### Structured errors (when available)

When the power's parser can extract structured detail, you'll see output like:

```
Type Checking: 3 errors found

Errors by file:
gear/gather_form_data/src/python/main.py: 2 errors
  - Line 42, Column 10: [arg-type] Argument 1 has incompatible type "str"; expected "int"
  - Line 58, Column 5: [return-value] Incompatible return value type (got "None", expected "str")
gear/gather_form_data/test/python/test_export.py: 1 errors
  - Line 15: [attr-defined] Module has no attribute "old_function"
```

### Fallback errors (when detail is not captured)

Sometimes Pants only outputs a summary line. In this case you'll see:

```
Type Checking Failed (no structured detail captured)

Raw output:
✕ mypy failed.
```

### What to do when you get fallback errors

1. **Do NOT retry the same command** — you'll get the same result
2. **Narrow the scope** — check source and test directories separately:
   ```json
   {"scope": "directory", "path": "gear/gather_form_data/src/python", "recursive": true}
   ```
   ```json
   {"scope": "directory", "path": "gear/gather_form_data/test/python", "recursive": true}
   ```
3. **Check individual files** — if the directory scope still lacks detail:
   ```json
   {"scope": "file", "path": "gear/gather_form_data/test/python/test_export.py"}
   ```
4. **Common cause: test files referencing removed code** — when you rename or remove functions/modules, the test files that imported them will fail type checking

## Workflow Tools

### `full_quality_check`

Runs fix → lint → check → test in sequence. Stops on first failure.

```json
{"target": "gear/gather_form_data::"}
```

The response shows each step's result. If it fails at "check", look at that step's output for details.

### `pants_workflow`

Runs a named subset:

```json
{"workflow": "fix-lint", "target": "gear/gather_form_data::"}
{"workflow": "check-test", "target": "gear/gather_form_data::"}
{"workflow": "fix-lint-check", "target": "gear/gather_form_data::"}
```

## Best Practices for Agents

### Before running quality checks

1. Make sure all file edits are saved/written
2. If you've renamed or removed functions, check that imports and test references are updated

### Interpreting failures

1. Read the full output — don't just look at the exit code
2. If structured errors are present, fix them directly
3. If only a summary is shown, narrow scope to find the specific files

### Efficient error resolution

1. **One `full_quality_check` first** — get the full picture
2. **Fix issues by category** — fix all type errors before re-running, not one at a time
3. **Re-run only what failed** — if lint passed but check failed, use `pants_workflow("check-test")` for the retry, not `full_quality_check` again

### When check fails without detail

In rare cases the parser may not produce structured output (e.g., an unexpected output format from a future Pants version). If you see the fallback message:

```
Type Checking Failed (no structured detail captured)

Raw output:
✕ mypy failed.
```

The efficient strategy:

1. Separate source from tests:
   - `pants_check` with `scope="directory"` on `<module>/src/python`
   - `pants_check` with `scope="directory"` on `<module>/test/python`
2. Whichever fails, narrow further if needed
3. Most common root cause after refactoring: test files importing removed symbols

### Avoid these patterns

- **Don't call `container_exec` with raw pants commands** when a dedicated tool exists — use `pants_check`, `pants_lint`, etc.
- **Don't retry the same failing command more than once** — if it fails with the same output twice, change your approach
- **Don't use `2>&1 | tail` tricks via `container_exec`** — the power already captures both streams and parses them
- **Don't pass `--no-local-cache`** — cached results aren't the issue when output is missing
