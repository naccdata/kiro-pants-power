# kiro-pants-power
Kiro Power for Pants build system with devcontainer support

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python dependency management.

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed

### Quick Start

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
```

### Why uv?

- 10-100x faster than pip
- Built-in lock file support for reproducible builds
- Automatic virtual environment management
- Aligns with MCP ecosystem tooling (many MCP servers use `uvx`)
