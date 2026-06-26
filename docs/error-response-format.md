## How Pants Command Errors Are Returned

When you call any Pants tool (`pants_test`, `pants_lint`, `pants_check`, `pants_fix`, `pants_package`), the result comes back as plain text in the MCP tool response. There are two categories of responses: success and failure.

### Successful commands

A successful response starts with a formatted summary if structured output was parsed, or falls back to:

```
Command completed successfully: <command>

<stdout + stderr output>
```

For test commands, a successful response may still include coverage metrics and sandbox paths.

### Failed commands

Failures are returned as formatted text with structured sections depending on what failed. The power parses raw Pants output into actionable summaries rather than dumping the full console log.

#### Test failures (`pants_test`)

```
Test Results: <N> failed, <N> passed, <N> skipped out of <N> total

Failed Tests:
  - <test_name>
    File: <file_path>
    Class: <class_name>  (if applicable)
    Type: <exception_type>
    Message: <failure_message>
    Stack trace: <first few lines>
```

Pytest-specific assertion details may also appear:

```
Pytest Failures: <N> tests failed

  - <test_name>
    File: <file_path>
    Expected: <value>
    Actual: <value>
    Operator: ==
```

#### Type checking failures (`pants_check`)

```
Type Checking: <N> errors found

Errors by file:
  <file_path>: <N> errors
    - Line <N>, Column <N>: [<error_code>] <message>
    - Line <N>: [<error_code>] <message>
```

#### Coverage metrics (included with test results)

```
Coverage: <percent>%
Report: <path>

Per-file coverage:
  <file_path>: <percent>% (<covered>/<total> lines)
    Uncovered lines: 45-52, 67-70
```

#### Sandbox paths (included on failure when `--keep-sandboxes=on_failure`)

```
Preserved Sandboxes:
  - <sandbox_path>
    Process: <description>
```

These paths point to temporary directories inside the container where you can inspect the exact inputs and run script (`__run.sh`) that Pants used.

#### Intent-based error translation

When using intent parameters (`scope`, `path`, `recursive`) instead of raw `target`, common Pants errors are translated into user-friendly messages:

| Pants error pattern | Translated message |
|---|---|
| "No targets found" | "No tests found in {scope} {path}" |
| "BUILD file not found" | "Directory not configured for Pants. Run 'pants tailor' to set up BUILD files" |
| "No such file or directory" | "Path does not exist: {path}" |

The translated error may include a `suggestion` field (e.g., `"pants tailor"`) indicating a remediation command.

#### Fallback behavior

If structured parsing fails or no parsers match the command type, the response falls back to:

```
Command execution failed: <command>

Exit code: <N>

Output:
<raw stdout + stderr>
```

### What to do with errors

- **Test failures**: Look at the file path and test name to locate the failing code. Use assertion details (expected vs. actual) to understand the mismatch.
- **Type errors**: Fix in order by file. The error code (e.g., `arg-type`, `return-value`) tells you the category of type issue.
- **Missing BUILD files**: Run `pants_tailor` to auto-generate them.
- **Sandbox paths**: Use `container_exec` to inspect sandbox contents or re-run `__run.sh` for reproduction.
- **Coverage gaps**: Check uncovered line ranges to identify untested code paths.
