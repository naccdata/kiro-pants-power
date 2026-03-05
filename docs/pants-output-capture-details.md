# Pants Output Capture - Documentation Details

This document contains detailed information extracted from Pants documentation about output formats, reporting mechanisms, and debugging features that can be leveraged to improve output capture for agent use.

## Source Documentation

- [Pants Test Goal Documentation](https://www.pantsbuild.org/2.29/docs/python/goals/test)
- [Pants Check Goal Documentation](https://www.pantsbuild.org/2.29/docs/python/goals/check)
- [Pants Troubleshooting - Keep Sandboxes](https://www.pantsbuild.org/dev/docs/using-pants/troubleshooting-common-issues#debug-tip-inspect-the-sandbox-with---keep-sandboxes)

---

## Test Goal (`pants test`) Output Capabilities

### Output Control Options

**`--test-output` flag** (or `[test].output` in pants.toml):
- `failed` (default): Only show output for failed tests
- `all`: Show output for all tests
- `never`: Suppress all test output

**Pytest verbosity control via args**:
- `-q`: Quiet mode (minimal output)
- `-v`: Verbose mode
- `-vv`: Very verbose mode
- `-s`: Always print stdout/stderr even for passing tests
- `--no-header`: Suppress Pytest version header
- `-r`: Print summary report at end (useful for finding failures in large batches)

**Configuration examples**:
```toml
# pants.toml
[test]
output = "all"  # or "failed" or "never"

[pytest]
args = ["--no-header", "-v"]
```

### Structured Output Formats

#### JUnit XML Reports

**Configuration**:
```toml
# pants.toml
[test]
report = true  # Enables JUnit XML generation
```

**Output location**: `dist/test/reports` (default)

**Features**:
- Machine-readable XML format
- Contains test results, timing, failure details
- Can be consumed by CI/CD dashboards
- One report per test batch/file

**Pytest customization**:
- `[pytest].junit_family` option controls XML format variant

#### Coverage Reports

**Activation**:
```bash
pants test --use-coverage <target>
```

Or permanently:
```toml
# pants.toml
[test]
use_coverage = true
```

**Report formats** (via `[coverage-py].report`):
- `console`: Terminal output (default)
- `html`: HTML report files
- `xml`: XML format (Cobertura-compatible)
- `json`: JSON format
- `raw`: SQLite database file

**Output directory**: Configurable via `[coverage-py].output_dir`

**Filtering**: `--coverage-py-filter` to limit to specific modules

**Global reporting**: `[coverage-py].global_report = true` includes all importable files, not just encountered ones

**Opening reports**: `--test-open-coverage` automatically opens HTML/XML/JSON reports

**Configuration requirements**:
```ini
# .coveragerc
[run]
relative_files = true  # Required for Pants
branch = true
```

### Test Execution Context

#### Parallelism and Batching

**Default behavior**:
- Each test file runs as separate process
- Fine-grained caching per file
- Parallel execution across files

**Batching** (via `batch_compatibility_tag`):
- Groups compatible tests into single pytest process
- Shares high-level fixtures across tests
- Single success/failure result per batch
- Batch size controlled by `[test].batch_size`

**pytest-xdist integration**:
```toml
# pants.toml
[pytest]
xdist_enabled = true
```
- Parallelizes tests within a file
- Automatic concurrency calculation
- Sets `PYTEST_XDIST_WORKER` and `PYTEST_XDIST_WORKER_COUNT` env vars

#### Environment Variables

**Execution slot identification**:
```toml
# pants.toml
[pytest]
execution_slot_var = "PANTS_EXECUTION_SLOT"
```
- Unique integer per concurrent pytest process
- Useful for avoiding resource collisions (DB names, file paths)
- Combine with `PYTEST_XDIST_WORKER` for full isolation

**Custom environment variables**:
```python
# BUILD file
python_tests(
    name="tests",
    extra_env_vars=["VAR1=value", "VAR2", "VAR_PREFIX_*"],
)
```

### Test Debugging Features

#### Interactive Debugging

**`--debug` flag**:
- Runs tests sequentially
- Allows interactive debuggers (pdb, ipdb)
- Breakpoints work normally
- Must use `-- -s` with ipdb for stdin

**`--debug-adapter` flag**:
- Enables DAP (Debug Adapter Protocol) support
- Works with VS Code, IntelliJ, PyCharm
- Server host/port logged by Pants

#### Timeouts

**Configuration**:
```python
# BUILD file
python_test(
    name="tests",
    source="tests.py",
    timeout=120,  # seconds
)
```

**Global settings**:
```toml
# pants.toml
[test]
timeout_default = 60
timeout_maximum = 600
```

**Disable temporarily**: `--no-test-timeouts`

#### Retries

**Configuration**:
```toml
# pants.toml
[test]
attempts_default = 3  # Retry failed tests
```

### Custom Pytest Options

**Via environment variable**:
```python
# BUILD file
python_tests(
    name="tests",
    extra_env_vars=[
        "PYTEST_ADDOPTS=-p myplugin --reuse-db",
    ],
)
```

**Warning**: Overriding Pants-controlled options (`--color`, `--junit-xml`, `--cov`, etc.) may break Pants functionality.

---

## Check Goal (`pants check`) Output Capabilities

### MyPy Report Generation

**Report types available**:
- Line count reports
- HTML reports
- XML reports
- Text reports
- Custom report formats

**Configuration**:
```toml
# pants.toml
[mypy]
args = ["--linecount-report=reports"]
```

**Output location**: `dist/check/mypy` (Pants copies all reports here)

**Important**: MyPy must write to `reports/` folder for Pants to preserve them

### MyPy Output Control

**Verbosity**: Controlled via MyPy config or `[mypy].args`

**Config file support**:
- Auto-discovered: `mypy.ini`, `.mypy.ini`, `setup.cfg`, `pyproject.toml`
- Custom location: `[mypy].config = "path/to/config"`

### Performance Considerations

**Caching** (MyPy 0.700+):
- Subsequent runs are extremely fast
- Requires not setting `python_version` in config
- Cache invalidation handled automatically by Pants

**Incremental checking**:
```bash
pants --changed-since=HEAD --changed-dependents=transitive check
```
- Only checks changed files and their dependents
- Significant performance improvement for large codebases

---

## Sandbox Debugging (`--keep-sandboxes`)

### Overview

Pants runs most processes in hermetic sandboxes (temporary directories) for:
- Safe caching
- Parallel execution
- Reproducible builds

### Keep Sandboxes Options

**`--keep-sandboxes=always`**:
- Preserves all process sandboxes
- Logs the path to each sandbox
- Keeps sandboxes after run completes

**`--keep-sandboxes=on_failure`**:
- Only preserves sandboxes of failing processes
- Useful for debugging without clutter

### Sandbox Contents

**Files included**:
- All input files for the process
- Generated files
- Dependency files

**`__run.sh` script**:
- Located in each sandbox directory
- Reproduces exact process execution
- Uses same argv and environment variables as Pants

### Example Output

```
21:26:13.55 [INFO] preserving local process execution dir 
`"/private/var/folders/hm/qjjq4w3n0fsb07kp5bxbn8rw0000gn/T/process-executionQgIOjb"` 
for "Run isort on 1 file."
```

### Use Cases

1. **Inspect sandbox contents**: Verify expected files are present
2. **Debug missing dependencies**: Check what files are available to the process
3. **Reproduce failures**: Run `__run.sh` to execute with exact same conditions
4. **Investigate hermetic issues**: Confirm environment isolation

---

## Additional Debugging Options

### Stack Traces and Logging

**`--print-stacktrace`**:
- Shows full stack traces on errors
- Default behavior suppresses traces

**`-ldebug`**:
- Increases logging level to debug
- Shows detailed execution information

**`--pex-verbosity=9`**:
- Debug .pex file building issues
- Maximum verbosity for PEX operations

**Combined usage**:
```bash
pants --print-stacktrace -ldebug test ::
```

### Cache Debugging

**Disable pantsd**: `--no-pantsd`
- Bypasses Pants daemon
- Useful for cache invalidation issues

**Disable local cache**: `--no-local-cache`
- Ignores persistent caches at `~/.cache/pants`
- Forces fresh execution

**Clear pantsd cache**:
```bash
rm -r .pants.d/pids/
```

---

## Implications for Output Capture Refactor

### Structured Data Opportunities

1. **JUnit XML**: Parse for structured test results (pass/fail, timing, error messages)
2. **Coverage JSON/XML**: Extract coverage metrics programmatically
3. **MyPy reports**: Parse for type checking issues and statistics
4. **Sandbox paths**: Extract from logs to inspect artifacts

### Enhanced Agent Feedback

1. **Test summaries**: Parse JUnit XML to provide concise pass/fail counts
2. **Failure details**: Extract specific test failures from reports
3. **Coverage metrics**: Report coverage percentages and uncovered lines
4. **Type errors**: Parse MyPy output for actionable type issues
5. **Execution context**: Provide sandbox paths for artifact inspection

### Configuration Recommendations

For optimal agent output capture:

```toml
# pants.toml
[test]
output = "failed"  # Reduce noise, focus on failures
report = true      # Enable JUnit XML
use_coverage = true  # Always capture coverage

[coverage-py]
report = ["json", "console"]  # Machine-readable + human-readable
global_report = true  # Include all files

[pytest]
args = ["--no-header", "-r"]  # Clean output + failure summary
execution_slot_var = "PANTS_EXECUTION_SLOT"  # Avoid collisions

[mypy]
args = ["--linecount-report=reports"]  # Generate reports
```

### Parsing Strategies

1. **Regex patterns**: Extract key information from console output
2. **XML/JSON parsing**: Use structured formats when available
3. **Log parsing**: Extract sandbox paths and execution details
4. **Exit codes**: Distinguish failure types (test failures vs. execution errors)
5. **Streaming**: Capture real-time progress for long-running operations

### Error Handling Improvements

1. **Sandbox inspection**: On failure, provide sandbox path for debugging
2. **Artifact preservation**: Keep reports and coverage data for analysis
3. **Contextual errors**: Include relevant output sections, not full dumps
4. **Actionable guidance**: Parse errors to suggest fixes (e.g., missing dependencies)

---

## Current Implementation Gaps

Based on code review of existing implementation:

1. **No structured output parsing**: Currently only captures raw stdout/stderr
2. **No report file handling**: JUnit XML, coverage reports not extracted
3. **No sandbox path extraction**: Missing opportunity for artifact inspection
4. **Limited error context**: Full output dumps instead of relevant excerpts
5. **No streaming progress**: Workflow orchestrator doesn't show real-time progress
6. **No coverage integration**: Coverage data not captured or reported
7. **No retry logic**: Test retries not configured or handled
8. **No batch optimization**: No use of batching or pytest-xdist features

---

## Recommended Enhancements

### High Priority

1. **Parse JUnit XML reports**: Extract structured test results
2. **Capture coverage metrics**: Parse JSON/XML coverage reports
3. **Extract sandbox paths**: Parse logs for `--keep-sandboxes` output
4. **Structured error messages**: Parse failures for specific error types

### Medium Priority

5. **Enable report generation**: Configure JUnit XML and coverage by default
6. **Streaming progress**: Show real-time output during long operations
7. **Artifact management**: Copy reports to accessible locations
8. **Failure summaries**: Provide concise failure counts and details

### Low Priority

9. **Batch optimization**: Configure batching for fixture-heavy tests
10. **Retry configuration**: Enable automatic retries for flaky tests
11. **MyPy report parsing**: Extract type checking statistics
12. **Performance metrics**: Track and report execution times
