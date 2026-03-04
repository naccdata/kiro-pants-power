---
name: "pants-devcontainer-power"
displayName: "Pants DevContainer"
description: "Automated Pants build system commands with devcontainer integration for NACC Flywheel Extensions development workflow"
keywords: ["pants", "build", "devcontainer", "workflow", "monorepo", "nacc"]
author: "NACC Team"
---

# Pants DevContainer

## Overview

The Pants DevContainer power eliminates friction in the NACC Flywheel Extensions development workflow by automatically wrapping Pants build system commands with devcontainer execution. Instead of manually managing container lifecycle or remembering wrapper scripts, you can invoke Pants commands directly - the power handles all container management automatically.

This power provides MCP tools organized into four categories:
- **Pants Commands**: fix, lint, check, test, package
- **Container Lifecycle**: start, stop, rebuild, exec, shell
- **Workflow Orchestration**: full_quality_check, pants_workflow
- **Utilities**: clear_cache

All commands ensure the devcontainer is running before execution, providing consistent environment management and clear error messages when issues occur.

## Onboarding

### Prerequisites

Before using this power, you need:

1. **Docker Desktop** - Running and accessible
   - macOS: Download from https://www.docker.com/products/docker-desktop
   - Linux: Install Docker Engine
   - Verify: `docker ps` should run without errors

2. **DevContainer CLI** - Installed globally via npm
   ```bash
   npm install -g @devcontainers/cli
   ```
   - Verify: `devcontainer --version` should show version info

3. **Repository with DevContainer Configuration**
   - Must have `.devcontainer/` directory with `devcontainer.json`
   - NACC Flywheel Extensions repository includes this configuration

4. **Pants Installation** (inside devcontainer)
   - For NACC repository, run after container starts:
   ```bash
   devcontainer exec --workspace-folder . bash get-pants.sh
   ```

### Installation

This power is installed as an MCP server in Kiro:

1. Add the power to your Kiro configuration
2. The power will validate prerequisites on startup
3. If devcontainer CLI is missing, you'll see installation instructions
4. If `.devcontainer/` directory is missing, you'll be prompted to use a compatible repository

### Verification

Test that everything is set up correctly:

```bash
# Start the container (should succeed)
# Use the container_start tool

# Verify Pants is installed
# Use the container_exec tool with command: "pants --version"

# Expected output: Pants version 2.27.0 or similar
```

## Common Workflows

### Workflow 1: Quick Code Quality Check

**Goal:** Format code and check for linting issues before committing

**Steps:**
1. Use `pants_fix` tool with target parameter (or omit for all targets)
2. Use `pants_lint` tool to verify no linting issues remain

**Example:**
```
# Fix all code
pants_fix()

# Or fix specific directory
pants_fix(target="common/src/python::")

# Then verify linting
pants_lint()
```

**Common Errors:**
- Error: "Container not running"
  - Cause: DevContainer hasn't been started
  - Solution: Power automatically starts container, but if this fails, check Docker is running

### Workflow 2: Full Quality Check Before Commit

**Goal:** Run complete validation (fix → lint → check → test) with a single command

**Steps:**
1. Use `full_quality_check` tool
2. Power executes all steps in sequence
3. Stops on first failure with clear indication of which step failed

**Example:**
```
# Run full quality check on all targets
full_quality_check()

# Or on specific directory
full_quality_check(target="common/src/python::")
```

**Output:**
```
Step 1/4: Running pants fix...
✓ Fix completed successfully

Step 2/4: Running pants lint...
✓ Lint completed successfully

Step 3/4: Running pants check...
✓ Type checking completed successfully

Step 4/4: Running pants test...
✓ All tests passed

Full quality check completed successfully!
```

**Common Errors:**
- Error: "Step failed: pants_lint"
  - Cause: Linting issues found in code
  - Solution: Review lint output, fix issues, run again

### Workflow 3: Run Tests on Specific Target

**Goal:** Test a specific module or directory without running all tests

**Steps:**
1. Identify the Pants target (directory path or specific target)
2. Use `pants_test` tool with target parameter

**Example:**
```
# Test specific directory
pants_test(target="common/test/python::")

# Test single file
pants_test(target="common/test/python/test_identifier.py")

# Test specific target
pants_test(target="common/test/python:test_identifier")
```

**Explanation:**
- `::` suffix means "this directory and all subdirectories"
- Without `::`, targets a specific file or target
- Default (no target) runs all tests in repository

### Workflow 4: Build Packages

**Goal:** Build distributable packages for deployment

**Steps:**
1. Ensure code quality checks pass
2. Use `pants_package` tool to build packages

**Example:**
```
# Build all packages
pants_package()

# Build specific package
pants_package(target="apps/gear-identifier::")
```

### Workflow 5: Container Management

**Goal:** Manually control devcontainer lifecycle

**Steps:**
1. Use container lifecycle tools as needed
2. Most commands auto-start container, but manual control available

**Example:**
```
# Start container explicitly
container_start()

# Execute arbitrary command in container
container_exec(command="ls -la")

# Rebuild container from scratch (when dependencies change)
container_rebuild()

# Stop container when done
container_stop()

# Get instructions for interactive shell
container_shell()
```

### Workflow 6: Troubleshooting Cache Issues

**Goal:** Clear Pants cache when encountering flaky filesystem issues

**Steps:**
1. Use `pants_clear_cache` tool
2. Re-run the failing command

**Example:**
```
# Clear Pants cache
pants_clear_cache()

# Then retry the command that was failing
pants_test()
```

**When to use:**
- Seeing "File not found" errors that don't make sense
- Pants reporting stale state
- After major refactoring or file moves
- When Pants seems confused about file locations

## MCP Tools Reference

### Pants Command Tools

#### pants_fix
**Purpose:** Format code and auto-fix linting issues

**Parameters:**
- `target` (optional, string): Pants target specification
  - Default: `"::"` (all targets)
  - Examples: `"common/src/python::"`, `"apps/gear-identifier:gear"`

**Returns:** Command output and exit code

**Example:**
```
pants_fix()
pants_fix(target="common/src/python::")
```

#### pants_lint
**Purpose:** Run linters on code (ruff, black, isort)

**Parameters:**
- `target` (optional, string): Pants target specification (default: `"::"`)

**Returns:** Command output and exit code

**Example:**
```
pants_lint()
pants_lint(target="common/test/python::")
```

#### pants_check
**Purpose:** Run type checking with mypy

**Parameters:**
- `target` (optional, string): Pants target specification (default: `"::"`)

**Returns:** Command output and exit code

**Example:**
```
pants_check()
pants_check(target="common/src/python::")
```

#### pants_test
**Purpose:** Run tests with pytest

**Parameters:**
- `target` (optional, string): Pants target specification (default: `"::"`)

**Returns:** Command output and exit code

**Example:**
```
pants_test()
pants_test(target="common/test/python::test_identifier")
```

#### pants_package
**Purpose:** Build distributable packages

**Parameters:**
- `target` (optional, string): Pants target specification (default: `"::"`)

**Returns:** Command output and exit code

**Example:**
```
pants_package()
pants_package(target="apps/gear-identifier::")
```

### Container Lifecycle Tools

#### container_start
**Purpose:** Start the devcontainer (idempotent - safe to call multiple times)

**Parameters:** None

**Returns:** Command output and exit code

**Example:**
```
container_start()
```

**Note:** Most commands auto-start the container, so explicit start is rarely needed.

#### container_stop
**Purpose:** Stop the devcontainer

**Parameters:** None

**Returns:** Command output and exit code

**Example:**
```
container_stop()
```

#### container_rebuild
**Purpose:** Rebuild and restart the devcontainer (use when dependencies change)

**Parameters:** None

**Returns:** Command output and exit code

**Example:**
```
container_rebuild()
```

**When to use:**
- After updating `.devcontainer/devcontainer.json`
- After changing Docker image or Dockerfile
- When container environment seems corrupted

#### container_exec
**Purpose:** Execute arbitrary shell command in container

**Parameters:**
- `command` (required, string): Shell command to execute

**Returns:** Command output and exit code

**Example:**
```
container_exec(command="ls -la")
container_exec(command="python --version")
container_exec(command="pants --version")
```

#### container_shell
**Purpose:** Get instructions for opening interactive shell

**Parameters:** None

**Returns:** Instructions with command to run manually

**Example:**
```
container_shell()
```

**Output:**
```
To open an interactive shell in the devcontainer, run this command in your terminal:

devcontainer exec --workspace-folder . /bin/zsh -l

Note: Interactive shells cannot be opened via MCP protocol.
```

### Workflow Orchestration Tools

#### full_quality_check
**Purpose:** Run complete quality check workflow (fix → lint → check → test)

**Parameters:**
- `target` (optional, string): Pants target specification (default: `"::"`)

**Returns:** Aggregated output from all steps, overall success/failure

**Behavior:**
- Executes steps in sequence
- Stops on first failure
- Reports which step failed
- Shows progress indication for each step

**Example:**
```
full_quality_check()
full_quality_check(target="common/src/python::")
```

#### pants_workflow
**Purpose:** Execute custom workflow sequence

**Parameters:**
- `workflow` (required, string): Workflow name
  - `"fix-lint"`: Run fix then lint
  - `"check-test"`: Run check then test
  - `"fix-lint-check"`: Run fix, lint, then check

**Returns:** Aggregated output from all steps, overall success/failure

**Example:**
```
pants_workflow(workflow="fix-lint")
pants_workflow(workflow="check-test")
```

### Utility Tools

#### pants_clear_cache
**Purpose:** Clear Pants cache to resolve filesystem issues

**Parameters:** None

**Returns:** Command output and exit code

**Example:**
```
pants_clear_cache()
```

**Note:** Gracefully handles missing cache directory (reports success without error).

## Troubleshooting

### Container Issues

#### Problem: "DevContainer CLI not found"
**Cause:** DevContainer CLI not installed or not in PATH

**Solution:**
1. Install DevContainer CLI:
   ```bash
   npm install -g @devcontainers/cli
   ```
2. Verify installation:
   ```bash
   devcontainer --version
   ```
3. Restart Kiro

#### Problem: "Cannot connect to Docker daemon"
**Cause:** Docker Desktop not running or Docker daemon not accessible

**Solution:**
1. Start Docker Desktop
2. Verify Docker is running:
   ```bash
   docker ps
   ```
3. Check Docker permissions:
   ```bash
   docker run hello-world
   ```
4. Retry the command

#### Problem: "Container start failed"
**Cause:** Various issues with container startup

**Solution:**
1. Check Docker Desktop is running
2. Review error output for specific issue
3. Try rebuilding container:
   ```
   container_rebuild()
   ```
4. Check `.devcontainer/devcontainer.json` for configuration errors
5. Verify sufficient disk space and memory

#### Problem: ".devcontainer/ directory not found"
**Cause:** Running power in repository without devcontainer configuration

**Solution:**
1. Verify you're in the correct repository
2. Check for `.devcontainer/` directory:
   ```bash
   ls -la .devcontainer/
   ```
3. If missing, this repository doesn't support devcontainer development
4. Switch to NACC Flywheel Extensions repository

### Pants Issues

#### Problem: "Pants not found in devcontainer"
**Cause:** Pants not installed inside the devcontainer

**Solution:**
1. For NACC repository, install Pants:
   ```bash
   devcontainer exec --workspace-folder . bash get-pants.sh
   ```
2. For other repositories, see: https://www.pantsbuild.org/docs/installation
3. Verify installation:
   ```
   container_exec(command="pants --version")
   ```

#### Problem: "Test failed" or "Lint failed"
**Cause:** Code quality issues in the codebase

**Solution:**
1. Review the error output carefully
2. Fix the reported issues in your code
3. Run `pants_fix` to auto-fix formatting issues
4. Re-run the failing command
5. Use target parameter to focus on specific areas:
   ```
   pants_test(target="path/to/failing/test::")
   ```

#### Problem: "File not found" or stale state errors
**Cause:** Pants cache is stale or corrupted

**Solution:**
1. Clear Pants cache:
   ```
   pants_clear_cache()
   ```
2. Retry the command
3. If issue persists, rebuild container:
   ```
   container_rebuild()
   ```

### Workflow Issues

#### Problem: "Workflow stopped at step X"
**Cause:** Step X failed, workflow stops on first failure

**Solution:**
1. Review the error output for step X
2. Fix the issues reported by that step
3. Re-run the workflow
4. Or run individual steps to isolate the problem:
   ```
   pants_fix()
   pants_lint()
   pants_check()
   pants_test()
   ```

#### Problem: "Invalid workflow name"
**Cause:** Provided workflow name not recognized

**Solution:**
1. Use one of the supported workflow names:
   - `"fix-lint"`
   - `"check-test"`
   - `"fix-lint-check"`
2. Or use `full_quality_check()` for complete workflow
3. Or run individual commands in sequence

## Best Practices

- **Use workflows for pre-commit checks**: Run `full_quality_check()` before committing to catch issues early
- **Target specific areas during development**: Use target parameter to focus on code you're actively changing
- **Let the power manage containers**: Don't manually start/stop containers unless troubleshooting
- **Clear cache when seeing weird errors**: Pants cache can become stale, `pants_clear_cache()` often resolves issues
- **Rebuild container after dependency changes**: When `.devcontainer/` config changes, use `container_rebuild()`
- **Use `pants_fix` liberally**: Auto-formatting saves time and prevents lint failures
- **Run tests frequently**: Use `pants_test(target="...")` to test specific modules during development

## Configuration

### Environment Variables

The power automatically sets these environment variables for devcontainer operations:
- `WORKSPACE_FOLDER`: Current working directory (repository root)
- `DOCKER_CLI_HINTS`: Set to "false" to suppress Docker hints

### Pants Target Specifications

Understanding Pants target syntax:
- `"::"` - All targets in repository (default)
- `"path/to/dir::"` - Directory and all subdirectories
- `"path/to/dir:target"` - Specific target in directory
- `"path/to/file.py"` - Single file

For more details: https://www.pantsbuild.org/docs/targets

### Workflow Definitions

Available workflow sequences:
- `"fix-lint"`: Format code, then check linting
- `"check-test"`: Type check, then run tests
- `"fix-lint-check"`: Format, lint, then type check
- `full_quality_check`: All steps (fix → lint → check → test)

---

**Package:** `pants-devcontainer-power`
**Runtime:** Python 3.12
**DevContainer CLI:** Required (`npm install -g @devcontainers/cli`)
**Pants Version:** 2.27.0 (inside devcontainer)
