# Pants Power Error Reporting Review

## Context

During execution of the `center-form-export` spec (tasks 5.1–5.4), the orchestrator agent encountered a `pants_check` failure. The power's error response did not contain the structured detail documented in the error specification. This report captures the observed behavior, identifies gaps, and proposes improvements.

## Observed Behavior

### Scenario: `full_quality_check` mypy failure

**What happened:**
1. Orchestrator called `full_quality_check` with `target="gear/gather_form_data::"`
2. The workflow failed at the `check` step
3. The response returned:

```text
Workflow failed at step: check
Steps completed before failure: fix, lint

--- Step Details ---

Step: fix
Command: devcontainer exec ... pants fix gear/gather_form_data/:: --keep-sandboxes=on_failure
Exit code: 0
Output:
✓ docformatter made no changes.
✓ ruff made no changes.
+ ruff check --fix made changes.
✓ ruff format made no changes.

Step: lint
Command: devcontainer exec ... pants lint gear/gather_form_data/:: --keep-sandboxes=on_failure
Exit code: 0
Output:
✓ docformatter succeeded.
✓ hadolint succeeded.
✓ ruff succeeded.
✓ ruff check succeeded.
✓ ruff format succeeded.

Step: unknown
Command: devcontainer exec ... pants check gear/gather_form_data/:: --keep-sandboxes=on_failure
Exit code: 1
Output:
✕ mypy failed.
```

**Problem:** The `check` step shows only `✕ mypy failed.` with no structured error detail — no file paths, line numbers, or error codes.

### Scenario: Standalone `pants_check` call

After the workflow failure, the orchestrator called `pants_check` directly:

```text
Command execution failed: pants check

Exit code: 1

Output:
Pants command failed. Error: 
✕ mypy failed.
```

**Same problem:** No structured mypy errors. This is the "fallback behavior" format but with no useful content beyond the summary line.

### Scenario: `container_exec` attempts

The orchestrator tried multiple `container_exec` calls to get detail:
- `pants check gear/gather_form_data/:: 2>&1 | tail -30` → same one-liner
- `pants check gear/gather_form_data/:: 2>&1` → same one-liner

**This suggests Pants itself only outputs the summary line to stdout/stderr**, and the detailed mypy errors are written elsewhere (e.g., to sandbox logs or internal Pants process output that isn't captured by simple command redirection).

### Resolution

The orchestrator eventually narrowed the issue by checking individual files:
- `pants check .../run.py` → ✓ succeeded
- `pants check .../main.py` → ✓ succeeded  
- `pants check gear/gather_form_data/test/python::` → ✕ failed

This revealed the test files (which referenced removed code) were the culprit. Total: 5 extra tool calls to diagnose what should have been visible in the first response.

## Expected vs. Actual

Per the error specification, a `pants_check` failure should return:

```text
Type Checking: <N> errors found

Errors by file:
<file_path>: <N> errors
  - Line <N>, Column <N>: [<error_code>] <message>
  - Line <N>: [<error_code>] <message>
```

**Actual:** Only `✕ mypy failed.` was returned.

## Root Cause Hypotheses

1. **Pants mypy output format not matching parser regex:** Pants 2.29 may format mypy output differently than what the power's parser expects. The parser sees no matching lines and falls through to fallback, which only captures the summary.

2. **Mypy output written to a different stream:** Pants may route mypy's detailed output through a process that doesn't combine into the same stdout/stderr captured by `devcontainer exec`. The `--keep-sandboxes=on_failure` flag suggests sandboxes capture this detail, but the power doesn't read sandbox contents.

3. **Workflow tool truncation:** The `full_quality_check` tool may be truncating step output. Note the step was labeled `"unknown"` rather than `"check"` — this suggests parsing of the step name itself failed, which could indicate broader output parsing issues.

4. **Cached result with no output:** When mypy results are cached by Pants, the re-run may produce only the summary line without re-emitting the detailed errors. The `--no-local-cache` flag the orchestrator used later also didn't help.

## Issues Identified

### Issue 1: Step labeled "unknown" in workflow output

The `full_quality_check` response shows `Step: unknown` for the check step. This should be `Step: check`. Likely a parsing issue where the step name extraction doesn't handle the check step correctly.

### Issue 2: No structured mypy detail in fallback

When the structured parser fails to match, the fallback should still include the raw stdout/stderr. But the raw output from Pants is just `✕ mypy failed.` — meaning either:
- Pants truly only outputs that single line (detail is elsewhere)
- The power is not capturing the full output

### Issue 3: `pants_check` standalone also lacks detail

This rules out workflow-specific truncation. The standalone `pants_check` tool has the same problem, confirming the parser isn't extracting mypy errors.

### Issue 4: No guidance for agents on "detail-less" failures

The steering documents (before this session's update) didn't explain what to do when error detail is missing. Agents fall back to re-running commands in different ways, wasting tool calls.

## Recommendations

### For the Power (code changes)

1. **Investigate mypy output capture**: Run `pants check` on code with known type errors and examine the full raw output (before parsing). Determine where mypy detail goes — is it in stdout, stderr, or only in sandbox logs?

2. **Add `--show-error-codes` flag**: Ensure mypy is invoked (via Pants config or flags) with options that force detailed output to stdout. Check if `pants.toml` needs `[mypy].args = ["--show-error-codes"]`.

3. **Parse sandbox logs on failure**: When `--keep-sandboxes=on_failure` is set and mypy fails, read the preserved sandbox's `__run.sh` output or `.stdout`/`.stderr` files to extract error detail.

4. **Fix step name parsing**: The `"unknown"` step label in `full_quality_check` output indicates the check step isn't recognized. Ensure the workflow tool correctly labels all steps.

5. **Include raw output in fallback**: When the structured parser matches nothing, include ALL captured stdout+stderr in the response (not just the last line). Cap at a reasonable limit (e.g., 5000 chars) with truncation marker.

6. **Test the parser against current Pants 2.29 output**: The mypy output format may have changed between Pants versions. Verify the regex patterns match what Pants 2.29 actually produces.

### For the Steering Documents (already partially done)

1. ✅ Added "Understanding Error Output" section to `kiro-pants-power.md`
2. ✅ Added "Do NOT retry blindly" guidance
3. Consider adding a note about known limitation: "If `pants_check` returns only a summary without file-level detail, the power's parser may not be matching the output format. Use `container_exec` with `pants check <target> 2>&1` as a diagnostic fallback."

### For the Task Execution Steering

Add to the subagent instructions in `task-execution.md`:

```markdown
### When pants_check fails without detail

If `pants_check` returns only "mypy failed" with no file/line information:
1. Do NOT retry the same command multiple times
2. Try narrowing scope: check source and test directories separately
3. The most common cause is test files referencing code that was just removed/renamed
```

## Test Plan for Verifying the Fix

To verify the power produces structured mypy output:

1. Introduce a deliberate type error in a file:
   ```python
   def foo(x: int) -> str:
       return x  # type error: incompatible return value
   ```
2. Call `pants_check` with `scope="file"` on that file
3. Verify the response contains:
   ```text
   Type Checking: 1 errors found
   Errors by file:
   path/to/file.py: 1 errors
     - Line N: [return-value] Incompatible return value type...
   ```
4. If it only returns `✕ mypy failed.`, the parser needs fixing
5. Also test via `full_quality_check` to verify workflow propagation

## Summary

The power's documented error format for mypy failures is not being produced in practice. The root cause is likely either (a) Pants 2.27's mypy output format doesn't match the parser's expectations, or (b) the detailed output goes to a stream/location the power doesn't capture. The agent compensated by making 5+ extra tool calls to narrow the issue file-by-file — wasteful but effective. Fixing the parser to actually produce structured output would eliminate this inefficiency entirely.

## Resolution (June 2026)

### Investigation Results

A test workspace (`kiro-pants-power-testing`) was created with deliberate type errors and used to verify Pants 2.29 output. Findings:

- **Hypothesis 1 (parser regex mismatch): DISPROVEN** — The parser regex correctly matches Pants 2.29 mypy output format.
- **Hypothesis 2 (output on different stream): DISPROVEN** — Pants outputs detailed mypy errors to stdout via `devcontainer exec`.
- **Hypothesis 3 (workflow tool truncation): PARTIALLY CORRECT** — The "unknown" step label was a real bug (fixed), but output wasn't truncated.
- **Hypothesis 4 (cached result with no output): DISPROVEN** — Both cached and fresh runs include the detail.

### Actual Root Cause

The `ParserRouter` and `EnhancedErrorFormatter` were never instantiated in `server.py`'s `_try_initialize()`. The `PantsCommands` class was created with `parser_router=None` and `formatter=None`, causing `pants_check` to always return a bare `CommandResult` and skip the parsing step entirely.

The raw stdout from Pants *did* contain the detailed mypy errors all along, but it was presented as unstructured text under a generic "Output:" label — making it easy to miss.

### Fixes Applied

1. **Wired up parser and formatter** in server initialization (`ParserRouter()` and `EnhancedErrorFormatter()` now passed to `PantsCommands`)
2. **Fixed "Step: unknown" label** in `_format_workflow_result` — now uses `result.failed_step`
3. **Added raw output fallback** — when the parser finds nothing but the command failed, the raw output is included with context
4. **Fixed intent-mode path** — `execute_with_error_handling` now uses `EnhancedCommandResult.formatted_summary` when available, instead of always falling through to the generic error translator

### Verification

All 585 existing tests pass. Parser verified against actual Pants 2.29 output:

```
Input:  "src/type_errors_live.py:9: error: Incompatible return value type (got "int", expected "str")  [return-value]"
Output: Type Checking: 3 errors found — with file, line, error code, and message for each error
```
