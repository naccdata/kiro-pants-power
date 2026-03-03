---
inclusion: auto
---

# Technology Stack

## Build System

- **Pants v2.27.0**: Modern build system for Python monorepos and multi-language projects
- **DevContainer CLI**: Development container management via `@devcontainers/cli` npm package
- **Docker**: Container runtime for devcontainer execution

## Language & Runtime

- **Python 3.12**: Primary language and required runtime for the power
- **MCP (Model Context Protocol)**: Protocol for exposing tools to AI assistants

## Development Tools

- **Type Checking**: mypy (via `pants check`)
- **Linting**: Ruff and other linters (via `pants lint`)
- **Formatting**: Auto-formatting (via `pants fix`)
- **Testing**: pytest with Hypothesis for property-based testing
- **Coverage**: coverage.py for test coverage reporting

## Package Management

- **uv**: Fast Python package manager and resolver (recommended, 10-100x faster than pip)
- **pyproject.toml**: Modern Python project configuration (PEP 621)
- **uv.lock**: Locked dependency versions for reproducible builds
- **pip**: Alternative package installer (still supported via pyproject.toml)

## Prerequisites

Before using this power, ensure:

1. **DevContainer CLI installed**:
   ```bash
   npm install -g @devcontainers/cli
   ```

2. **Docker running**: Docker Desktop or Docker daemon must be active

3. **Pants installed in devcontainer**: For NACC repository:
   ```bash
   devcontainer exec --workspace-folder . bash get-pants.sh
   ```

4. **uv installed (recommended for development)**:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or via Homebrew
   brew install uv
   
   # Or via pip
   pip install uv
   ```

## Development Workflow

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_models.py -v

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Run the MCP server
uv run python src/server.py
```

### Using pip (Alternative)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run tests
pytest
```

## Common Pants Commands

The power wraps these Pants commands with automatic devcontainer execution:

```bash
# Format code and auto-fix linting issues
pants fix ::

# Run linters
pants lint ::

# Type check with mypy
pants check ::

# Run tests
pants test ::

# Build packages
pants package ::

# Clear Pants cache (for filesystem issues)
rm -rf .pants.d/pids
```

## Workflow Commands

The power provides workflow orchestration for common sequences:

```bash
# Full quality check: fix → lint → check → test
# (Available as single MCP tool: full_quality_check)

# Partial workflows:
# - fix-lint: Format and lint
# - check-test: Type check and test
# - fix-lint-check: Format, lint, and type check
```

## Container Management

All commands automatically ensure the devcontainer is running via:

```bash
# Start container (idempotent)
devcontainer up --workspace-folder <workspace>

# Execute command in container
devcontainer exec --workspace-folder <workspace> <command>

# Stop container
devcontainer exec hostname | xargs docker rm -f

# Rebuild container
devcontainer build --workspace-folder <workspace>
```

## Environment Variables

The power sets these environment variables for devcontainer operations:

- `WORKSPACE_FOLDER`: Repository root directory
- `DOCKER_CLI_HINTS`: Set to "false" to suppress Docker hints
