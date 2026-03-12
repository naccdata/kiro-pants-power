# Debugging Power Changes

## How to Track Down Unexpected Behavior Changes

When a power that was working correctly suddenly starts behaving differently, here's a systematic approach to investigate:

### 1. Check Git History

Start by looking at recent commits to see what changed:

```bash
# See recent commits
git log --oneline --since="2026-03-01" | head -20

# Check specific file changes
git log --oneline --since="2026-03-01" -- "*.py"

# View details of a specific commit
git show <commit-hash>

# See what changed in a specific file
git diff <old-commit> <new-commit> -- path/to/file.py
```

### 2. Identify Refactors and Major Changes

Look for commits with keywords like:
- "refactor"
- "restructure"
- "rewrite"
- "integrate"
- "new API"

These often introduce architectural changes that can have unintended side effects.

### 3. Trace the Code Path

When you find a suspicious commit, trace how data flows through the system:

1. **Entry point**: Where does the MCP tool call enter? (Usually `server.py`)
2. **Routing**: How is the call routed to the actual implementation?
3. **Execution**: What executes the command?
4. **Result handling**: How are results processed and returned?
5. **Error handling**: How are errors caught and formatted?

### 4. Look for New Abstraction Layers

Refactors often introduce new layers that can lose information:

- New classes that wrap existing functionality
- New error handling that catches and re-throws exceptions
- New formatters that transform output
- New validators that filter data

**Key question**: Is data being lost between layers?

### 5. Check What Gets Passed Between Layers

Common issues:
- Only passing `stderr` when `stdout` also contains important data
- Catching exceptions but only preserving the message, not the full context
- Transforming errors into user-friendly messages but losing technical details
- Filtering output to remove "noise" but also removing useful information

### 6. Compare Before and After

Use git to compare the old and new implementations:

```bash
# Compare a specific function between commits
git diff <old-commit> <new-commit> -- path/to/file.py

# Show the old version of a file
git show <old-commit>:path/to/file.py

# Show the new version
git show <new-commit>:path/to/file.py
```

### 7. Write Tests to Verify the Fix

Once you identify the issue:

1. Write a test that reproduces the problem
2. Verify the test fails with the current code
3. Apply your fix
4. Verify the test passes
5. Run all existing tests to ensure no regressions

### 8. Document the Issue and Fix

Create documentation that includes:
- What changed and when
- What the symptom was
- What the root cause was
- How the fix works
- How to verify the fix

## Example: The Detailed Error Output Issue

### Symptom
`pants_test` and `pants_lint` stopped returning detailed error output after a refactor.

### Investigation Steps

1. **Checked git history**: Found PR #3 (commit `52244b7`) introduced intent-based API
2. **Identified new layers**: `ToolExecutor` → `execute_with_error_handling` → `ErrorTranslator`
3. **Traced the code path**:
   - `server.py` calls `tool_executor.execute_pants_test()`
   - `ToolExecutor` calls `execute_with_error_handling()`
   - `execute_with_error_handling()` catches `PantsExecutionError`
   - Error handler extracts only `stderr` from exception
   - `ErrorTranslator` receives only `stderr`
4. **Found the data loss**: Detailed output in `stdout` was being ignored
5. **Applied fix**: Combined `stdout` and `stderr` before passing to translator
6. **Wrote test**: Verified `stdout` content appears in error messages
7. **Documented**: Created this guide and fix documentation

## Tools for Investigation

### Git Commands
- `git log` - View commit history
- `git show` - View commit details
- `git diff` - Compare versions
- `git blame` - See who changed each line

### Code Analysis
- `grep -r "pattern" src/` - Search for patterns in code
- `readCode` tool - View code structure
- `getDiagnostics` - Check for type/lint errors

### Testing
- `pytest -v` - Run tests with verbose output
- `pytest -k test_name` - Run specific test
- `pytest --pdb` - Drop into debugger on failure

## Prevention

To avoid similar issues in the future:

1. **Write comprehensive tests** - Especially for error cases
2. **Test with real failure scenarios** - Don't just test success paths
3. **Review data flow in refactors** - Ensure no information is lost
4. **Document assumptions** - Note what data is expected where
5. **Use type hints** - Catch data loss at type-check time
6. **Add integration tests** - Test the full path from MCP call to result

## Red Flags in Code Reviews

Watch for:
- Exception handlers that only preserve `str(e)` or `e.message`
- Functions that extract only one field from a multi-field object
- Error translators that discard the original error
- Formatters that truncate or filter output
- New abstraction layers without tests
- Changes to error handling without corresponding test updates
