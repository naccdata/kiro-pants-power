# Pants DevContainer Power

A Kiro Power that provides MCP (Model Context Protocol) tools for managing development workflows using the Pants build system within devcontainers. This power eliminates friction by automatically wrapping Pants commands with devcontainer execution, ensuring all commands run in the proper containerized environment.

## Overview

The Pants DevContainer Power provides 13 MCP tools that handle the complexity of running Pants commands inside devcontainers. Instead of manually managing container lifecycle or remembering wrapper scripts, you can invoke Pants commands directly through the AI assistant, and the power handles all the container orchestration automatically.

### Key Features

- **Zero-friction execution**: Invoke Pants commands directly; the power handles container management
- **Automatic container lifecycle**: Ensures containers are running before executing commands
- **Workflow orchestration**: Run complete quality check workflows with a single command
- **Idempotent operations**: Container start operations are safe to call repeatedly
- **Target flexibility**: Support both full project operations (`::`) and specific target execution
- **Clear error messages**: Detailed troubleshooting guidance when operations fail
- **Real-time output**: Stream command output as it executes

## Prerequisites

### Required Software

1. **DevContainer CLI** - Required for container management
   ```bash
   npm install -g @devcontainers/cli
   ```
   For more information: https://containers.dev/supporting

2. **Docker** - Required for running containers
   - Docker Desktop (macOS/Windows)
   - Docker Engine (Linux)
   - Ensure Docker daemon is running before using this power

3. **Pants Build System** - Must be installed inside your devcontainer
   - Installation method depends on your project setup
   - See https://www.pantsbuild.org/docs/installation for installation methods
   - Common approaches:
     - Installation script in your repository
     - Package manager in Dockerfile
     - Pants' recommended installation method

4. **DevContainer Configuration** - Your repository must have:
   - `.devcontainer/` directory with `devcontainer.json`
   - Valid devcontainer configuration

### Python Requirements

- Python 3.12 or higher
- Dependencies managed via `pyproject.toml` and `uv.lock`

## Installation

1. Install the DevContainer CLI:
   ```bash
   npm install -g @devcontainers/cli
   ```

2. Ensure Docker is running:
   ```bash
   docker ps
   ```

3. Install the power in Kiro (follow Kiro's power installation process)

4. Verify Pants is installed in your devcontainer:
   ```bash
   devcontainer exec --workspace-folder . pants --version
   ```

## Tools Reference

### Pants Command Tools

#### pants_fix

Format code and auto-fix linting issues.

**Parameters:**
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Fix all code in the repository
> Use pants_fix

Fix code in a specific directory
> Use pants_fix with target "src/python::"

Fix a specific file
> Use pants_fix with target "src/python/myapp.py"
```

#### pants_lint

Run linters on code.

**Parameters:**
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Lint all code
> Use pants_lint

Lint specific directory
> Use pants_lint with target "src/python::"
```

#### pants_check

Run type checking with mypy.

**Parameters:**
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Type check all code
> Use pants_check

Type check specific directory
> Use pants_check with target "src/python::"
```

#### pants_test

Run tests.

**Parameters:**
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Run all tests
> Use pants_test

Run tests in specific directory
> Use pants_test with target "tests/unit::"

Run specific test file
> Use pants_test with target "tests/unit/test_myapp.py"
```

#### pants_package

Build packages.

**Parameters:**
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Package all targets
> Use pants_package

Package specific target
> Use pants_package with target "src/python:myapp"
```

### Container Lifecycle Tools

#### container_start

Start the devcontainer. This operation is idempotent - safe to call multiple times.

**Parameters:** None

**Examples:**
```
Start the container
> Use container_start
```

#### container_stop

Stop the devcontainer.

**Parameters:** None

**Examples:**
```
Stop the container
> Use container_stop
```

#### container_rebuild

Rebuild and restart the devcontainer. Useful when Dockerfile or devcontainer.json changes.

**Parameters:** None

**Examples:**
```
Rebuild the container
> Use container_rebuild
```

#### container_exec

Execute an arbitrary command in the container.

**Parameters:**
- `command` (required): Shell command to execute

**Examples:**
```
Check Python version
> Use container_exec with command "python --version"

List files
> Use container_exec with command "ls -la"

Run custom script
> Use container_exec with command "bash scripts/setup.sh"
```

#### container_shell

Get instructions for opening an interactive shell in the container.

**Parameters:** None

**Examples:**
```
Get shell instructions
> Use container_shell
```

**Note:** This tool returns instructions rather than opening a shell directly, since MCP tools cannot create interactive sessions.

### Workflow Orchestration Tools

#### full_quality_check

Run a complete quality check workflow: fix → lint → check → test. Stops on first failure.

**Parameters:**
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Run full quality check on entire repository
> Use full_quality_check

Run full quality check on specific directory
> Use full_quality_check with target "src/python::"
```

**Workflow Steps:**
1. `pants fix` - Format and auto-fix code
2. `pants lint` - Run linters
3. `pants check` - Run type checking
4. `pants test` - Run tests

If any step fails, the workflow stops and reports which step failed.

#### pants_workflow

Execute a custom workflow sequence.

**Parameters:**
- `workflow` (required): Workflow name - one of:
  - `fix-lint`: Run fix then lint
  - `check-test`: Run check then test
  - `fix-lint-check`: Run fix, lint, then check
- `target` (optional): Pants target specification (default: `::`)

**Examples:**
```
Run fix and lint workflow
> Use pants_workflow with workflow "fix-lint"

Run check and test workflow
> Use pants_workflow with workflow "check-test" and target "src/python::"

Run fix, lint, and check workflow
> Use pants_workflow with workflow "fix-lint-check"
```

### Utility Tools

#### pants_clear_cache

Clear Pants cache to resolve filesystem issues. Removes `.pants.d/pids` directory.

**Parameters:** None

**Examples:**
```
Clear Pants cache
> Use pants_clear_cache
```

**When to use:**
- Encountering flaky filesystem issues
- Pants reporting stale lock files
- After major configuration changes

## Common Workflows

### Pre-commit Quality Check

Before committing code, run a full quality check:

```
> Use full_quality_check
```

This runs fix → lint → check → test in sequence, ensuring your code meets all quality standards.

### Quick Lint and Format

Format code and check linting:

```
> Use pants_workflow with workflow "fix-lint"
```

### Type Check and Test

Verify types and run tests:

```
> Use pants_workflow with workflow "check-test"
```

### Working with Specific Targets

Run quality checks on a specific directory:

```
> Use full_quality_check with target "src/python/myapp::"
```

Test a specific file:

```
> Use pants_test with target "tests/unit/test_myapp.py"
```

### Troubleshooting Container Issues

If you encounter container problems:

1. Check container status:
   ```
   > Use container_exec with command "hostname"
   ```

2. Restart the container:
   ```
   > Use container_stop
   > Use container_start
   ```

3. Rebuild from scratch:
   ```
   > Use container_rebuild
   ```

4. Clear Pants cache:
   ```
   > Use pants_clear_cache
   ```

## Relationship to DevContainer CLI

This power wraps the `@devcontainers/cli` npm package to provide seamless integration with devcontainers. Under the hood, it uses these devcontainer CLI commands:

- `devcontainer up` - Start container (used automatically before Pants commands)
- `devcontainer exec` - Execute commands in container
- `devcontainer build` - Rebuild container image

The power sets these environment variables for all devcontainer operations:
- `WORKSPACE_FOLDER`: Current repository root
- `DOCKER_CLI_HINTS`: Set to "false" to suppress Docker hints

You can still use the devcontainer CLI directly for operations not covered by this power, such as:
- `devcontainer open` - Open repository in VS Code with devcontainer
- `devcontainer read-configuration` - Read devcontainer configuration

## Target Specifications

Pants uses target specifications to identify what code to operate on. This power supports all Pants target formats:

- `::` - All targets in the repository (default)
- `path/to/dir::` - All targets in directory and subdirectories
- `path/to/dir:target` - Specific target in directory
- `path/to/file.py` - Single file target
- `path/to/dir:` - All targets directly in directory (not recursive)

For more information on Pants targets: https://www.pantsbuild.org/docs/targets

## Error Handling

The power provides detailed error messages with troubleshooting guidance:

### Container Start Failures

If the container fails to start, you'll see:
- The failed command and exit code
- Container output (stdout and stderr)
- Troubleshooting steps:
  - Check if Docker Desktop is running
  - Verify Docker daemon accessibility
  - Check Docker permissions
  - Verify devcontainer CLI installation
  - Check for port conflicts or resource constraints

### Command Execution Failures

If a Pants command fails, you'll see:
- The full command that was executed
- Exit code
- Complete output (stdout and stderr)

### Missing Prerequisites

If prerequisites are missing, you'll see:
- Clear description of what's missing
- Installation instructions
- Links to relevant documentation

## Architecture

The power is organized into these components:

- **MCP Server** (`src/server.py`): Exposes tools via Model Context Protocol
- **Container Manager** (`src/container_manager.py`): Manages devcontainer lifecycle
- **Pants Commands** (`src/pants_commands.py`): Implements Pants command tools
- **Workflow Orchestrator** (`src/workflow_orchestrator.py`): Executes multi-step workflows
- **Command Executor** (`src/command_executor.py`): Executes shell commands with output capture
- **Models** (`src/models.py`): Data structures for results and errors
- **Formatters** (`src/formatters.py`): Formats output messages

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Run linter
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Type checking
uv run mypy src/ tests/
```

### Running All Quality Checks

```bash
uv run ruff check src/ tests/ && \
uv run mypy src/ tests/ && \
uv run pytest
```

## Troubleshooting

### "DevContainer CLI not found"

Install the devcontainer CLI:
```bash
npm install -g @devcontainers/cli
```

### "DevContainer configuration not found"

Ensure your repository has a `.devcontainer/` directory with `devcontainer.json`. Run the power from the repository root.

### "Pants not found in devcontainer"

Install Pants inside your devcontainer according to your project's setup. See https://www.pantsbuild.org/docs/installation

### "Cannot connect to Docker daemon"

Ensure Docker Desktop (or Docker Engine) is running:
```bash
docker ps
```

### Container won't start

1. Check Docker is running
2. Verify devcontainer.json is valid
3. Check for port conflicts
4. Try rebuilding: `> Use container_rebuild`

### Pants commands fail

1. Verify Pants is installed: `> Use container_exec with command "pants --version"`
2. Clear cache: `> Use pants_clear_cache`
3. Check Pants configuration in repository

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:
- All tests pass
- Code follows style guidelines (ruff, mypy)
- New features include tests and documentation
- Type annotations are complete

## Support

For issues related to:
- **This power**: Open an issue in the power repository
- **DevContainer CLI**: See https://containers.dev/supporting
- **Pants build system**: See https://www.pantsbuild.org/docs/getting-help
- **Docker**: See https://docs.docker.com/get-support/
