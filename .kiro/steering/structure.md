---
inclusion: auto
description: Project structure, conventions, and component architecture
---

# Project Structure

## Root Directory

```
.
├── .devcontainer/         # DevContainer configuration (required)
├── .git/                  # Git version control
├── .kiro/                 # Kiro IDE configuration
│   ├── speccs/            # Spec files for feature development
│   │   └── pants-devcontainer-power/  # This power's spec
│   └── steering/          # AI assistant guidance documents
├── .venv/                 # Virtual environment (managed by uv, gitignored)
├── .gitignore             # Git ignore patterns (Python-focused)
├── README.md              # Project documentation
├── power.json             # MCP server manifest
├── pyproject.toml         # Project metadata and dependencies (uv/pip)
├── uv.lock                # Locked dependencies for reproducible builds
├── src/                   # Source code
│   └── server.py          # MCP server implementation
└── tests/                 # Test suite
    ├── unit/              # Unit tests
    ├── property/          # Property-based tests
    └── integration/       # Integration tests
```

## Power Structure

### Core Components

- **power.json**: MCP server manifest declaring all 15 tools
- **src/server.py**: Main MCP server implementation
- **pyproject.toml**: Project metadata and dependencies
- **uv.lock**: Locked dependencies for reproducible builds

### Component Architecture

The power is organized into these internal components:

- **CommandExecutor**: Executes shell commands and captures output
- **ContainerManager**: Manages devcontainer lifecycle operations
- **PantsCommandBuilder**: Constructs Pants commands with target specifications
- **WorkflowOrchestrator**: Executes multi-step workflows with error handling

### MCP Tools (15 total)

**Core Pants Commands (5)**:
- pants_fix: Format code and auto-fix linting issues
- pants_lint: Run linters
- pants_check: Type check with mypy
- pants_test: Run tests
- pants_package: Build packages

**Container Lifecycle (5)**:
- container_start: Start devcontainer (idempotent)
- container_stop: Stop devcontainer
- container_rebuild: Rebuild and restart devcontainer
- container_exec: Execute arbitrary command in container
- container_shell: Provide instructions for interactive shell

**Workflow Orchestration (2)**:
- full_quality_check: Run fix → lint → check → test sequence
- pants_workflow: Execute custom workflow (fix-lint, check-test, fix-lint-check)

**Utilities (1)**:
- pants_clear_cache: Clear Pants cache to resolve filesystem issues

## Conventions

### Python Code Organization

- Follow standard Python package structure
- Use `__pycache__/` for compiled bytecode (gitignored)
- Keep virtual environments in `.venv/`, `venv/`, or similar (gitignored)
- Use dataclasses for data models (CommandResult, WorkflowResult)
- Use type hints throughout

### Build Artifacts

- Build outputs go to `build/`, `dist/`, `target/` (gitignored)
- Pants cache in `.pants.d/` (cache clearing available via pants_clear_cache tool)

### Testing

- Test files use `test_*.py` naming convention
- Property tests tagged with `@pytest.mark.property`
- Unit tests in `tests/unit/`
- Property tests in `tests/property/`
- Integration tests in `tests/integration/`
- Coverage reports in `htmlcov/`, `.coverage` (gitignored)
- Pytest cache in `.pytest_cache/` (gitignored)
- Minimum 90% line coverage, 85% branch coverage

### Configuration Files

- **power.json**: MCP tool definitions and metadata
- **pyproject.toml**: Project metadata, dependencies, and tool configuration
- **uv.lock**: Locked dependency versions for reproducible builds
- **.devcontainer/**: DevContainer configuration (required for power to function)
- **BUILD files**: Pants target definitions (in target repository)
- **pants.toml**: Pants configuration (in target repository)

## Development Environment

- DevContainer configuration required for power functionality
- Environment variables in `.env` files (gitignored)
- Docker must be running for devcontainer operations
- DevContainer CLI must be installed globally via npm
- **uv** recommended for fast dependency management (10-100x faster than pip)

## Error Handling

The power handles four categories of errors:

1. **Container Lifecycle Errors**: Container cannot start, stop, or rebuild
2. **Command Execution Errors**: Pants commands or shell commands fail
3. **Validation Errors**: Invalid parameters or tool invocations
4. **System Errors**: Missing CLI, permission issues, filesystem problems

All errors include:
- Failed command string
- Command output (stdout and stderr)
- Troubleshooting guidance for common issues
