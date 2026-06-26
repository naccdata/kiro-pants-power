# Pants Output Capture — Investigation Results

## Summary

Investigation completed using `kiro-pants-power-testing` workspace with Pants 2.29.

**Finding:** Pants 2.29 outputs detailed mypy errors to stdout when run via `devcontainer exec`. The dynamic UI does NOT suppress the detail — both `pants check` and `pants --no-dynamic-ui check` produce identical output including file paths, line numbers, and error codes.

**Root cause of the original issue:** The `ParserRouter` and `EnhancedErrorFormatter` were never instantiated in `server.py`'s `_try_initialize`. `PantsCommands` was created with `parser_router=None`, so `pants_check` always returned a bare `CommandResult` without invoking the parser. The raw output *did* contain the mypy detail, but it was presented as unstructured text under a generic "Output:" label.

**Fix applied:** Wired up `ParserRouter()` and `EnhancedErrorFormatter()` in the server initialization.

## Verified Output Format

Running `devcontainer exec --workspace-folder . pants check src/type_errors_live.py` produces:

```
16:37:55.76 [ERROR] Completed: Typecheck using MyPy - mypy - mypy failed (exit code 1).
src/type_errors_live.py:9: error: Incompatible return value type (got "int", expected "str")  [return-value]
src/type_errors_live.py:14: error: Argument 1 to "returns_wrong_type" has incompatible type "str"; expected "int"  [arg-type]
src/type_errors_live.py:17: error: Missing return statement  [return]
Found 3 errors in 1 file (checked 1 source file)
✕ mypy failed.
```

This matches the existing `MyPyOutputParser` regex patterns. The parser correctly extracts all 3 errors with file path, line number, and error code.

## Parser Verification

The `ERROR_PATTERN_NO_COLUMN` regex matches lines like:
```
src/type_errors_live.py:9: error: Incompatible return value type (got "int", expected "str")  [return-value]
```

The parser produces:
```
Type Checking: 3 errors found

Errors by file:
  src/type_errors_live.py: 3 errors
    - Line 9: [return-value] Incompatible return value type (got "int", expected "str")
    - Line 14: [arg-type] Argument 1 to "returns_wrong_type" has incompatible type "str"; expected "int"
    - Line 17: [return] Missing return statement
```

## What Was NOT the Problem

- Pants' dynamic UI suppressing output — disproven
- `--no-dynamic-ui` being required — not needed
- Mypy output going to a different stream — disproven
- Pants version incompatibility with the regex — disproven
- Sandbox logs being the only source of detail — disproven

## Testing Workspace

The `kiro-pants-power-testing` sibling directory contains test scenarios for:

| File | Scenario |
|---|---|
| `src/type_errors_live.py` | Active mypy failures (3 errors) |
| `src/good_module.py` | Clean code (passes all checks) |
| `src/lint_issues.py` | Formatting/lint issues |
| `test/test_broken_imports.py` | Import of nonexistent symbol |
| `test/test_failing.py` | Deliberate assertion failures |
| `test/test_good_module.py` | Passing tests |
