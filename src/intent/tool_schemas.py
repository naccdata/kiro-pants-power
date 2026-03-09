"""Tool schemas for intent-based Pants commands."""

from typing import Any

# Common intent-based parameters for all Pants commands
COMMON_INTENT_PARAMETERS: dict[str, Any] = {
    "scope": {
        "type": "string",
        "enum": ["all", "directory", "file"],
        "description": (
            "What to operate on: 'all' runs on all code recursively, "
            "'directory' runs on a specific directory, 'file' runs on a specific file"
        ),
    },
    "path": {
        "type": "string",
        "description": (
            "Path to directory or file (required for 'directory' and 'file' scopes). "
            "Examples: 'src/tests', 'src/tests/test_auth.py'"
        ),
    },
    "recursive": {
        "type": "boolean",
        "description": (
            "Include subdirectories when operating on a directory "
            "(only applies to 'directory' scope, default: true)"
        ),
    },
}

# Test-specific parameters
TEST_SPECIFIC_PARAMETERS: dict[str, Any] = {
    "test_filter": {
        "type": "string",
        "description": (
            "Run only tests matching this name pattern (uses pytest-style filtering). "
            "Examples: 'test_create', 'test_create or test_update', 'not test_slow'"
        ),
    }
}

# Backward compatibility parameter (deprecated)
LEGACY_TARGET_PARAMETER: dict[str, Any] = {
    "target": {
        "type": "string",
        "description": (
            "DEPRECATED: Use scope/path/recursive instead. "
            "Pants target specification (e.g., '::', 'src/tests::', 'src/test.py')"
        ),
    }
}


def get_pants_test_schema() -> dict[str, Any]:
    """Get the pants_test tool schema with intent-based parameters."""
    return {
        "type": "object",
        "properties": {
            **COMMON_INTENT_PARAMETERS,
            **TEST_SPECIFIC_PARAMETERS,
            **LEGACY_TARGET_PARAMETER,
        },
    }


def get_pants_lint_schema() -> dict[str, Any]:
    """Get the pants_lint tool schema with intent-based parameters."""
    return {
        "type": "object",
        "properties": {
            **COMMON_INTENT_PARAMETERS,
            **LEGACY_TARGET_PARAMETER,
        },
    }


def get_pants_check_schema() -> dict[str, Any]:
    """Get the pants_check tool schema with intent-based parameters."""
    return {
        "type": "object",
        "properties": {
            **COMMON_INTENT_PARAMETERS,
            **LEGACY_TARGET_PARAMETER,
        },
    }


def get_pants_fix_schema() -> dict[str, Any]:
    """Get the pants_fix tool schema with intent-based parameters."""
    return {
        "type": "object",
        "properties": {
            **COMMON_INTENT_PARAMETERS,
            **LEGACY_TARGET_PARAMETER,
        },
    }


def get_pants_format_schema() -> dict[str, Any]:
    """Get the pants_format tool schema with intent-based parameters."""
    return {
        "type": "object",
        "properties": {
            **COMMON_INTENT_PARAMETERS,
            **LEGACY_TARGET_PARAMETER,
        },
    }


def get_pants_package_schema() -> dict[str, Any]:
    """Get the pants_package tool schema with intent-based parameters."""
    return {
        "type": "object",
        "properties": {
            **COMMON_INTENT_PARAMETERS,
            **LEGACY_TARGET_PARAMETER,
        },
    }


# Tool descriptions
TOOL_DESCRIPTIONS = {
    "pants_test": (
        "Run tests using Pants build system. Use intent-based parameters "
        "(scope/path/recursive/test_filter) for a simpler interface, or the legacy "
        "'target' parameter for direct Pants target specifications."
    ),
    "pants_lint": (
        "Run linters on code using Pants build system. Use intent-based parameters "
        "(scope/path/recursive) for a simpler interface, or the legacy 'target' "
        "parameter for direct Pants target specifications."
    ),
    "pants_check": (
        "Run type checking with mypy using Pants build system. Use intent-based "
        "parameters (scope/path/recursive) for a simpler interface, or the legacy "
        "'target' parameter for direct Pants target specifications."
    ),
    "pants_fix": (
        "Format code and auto-fix linting issues using Pants build system. Use "
        "intent-based parameters (scope/path/recursive) for a simpler interface, "
        "or the legacy 'target' parameter for direct Pants target specifications."
    ),
    "pants_format": (
        "Format code using Pants build system. Use intent-based parameters "
        "(scope/path/recursive) for a simpler interface, or the legacy 'target' "
        "parameter for direct Pants target specifications."
    ),
    "pants_package": (
        "Build packages using Pants build system. Use intent-based parameters "
        "(scope/path/recursive) for a simpler interface, or the legacy 'target' "
        "parameter for direct Pants target specifications."
    ),
}


# Example usage for documentation
PANTS_TEST_EXAMPLES = [
    {
        "description": "Run all tests in the repository",
        "parameters": {"scope": "all"},
    },
    {
        "description": "Run all tests in a directory and its subdirectories",
        "parameters": {"scope": "directory", "path": "src/tests", "recursive": True},
    },
    {
        "description": "Run tests in a single directory (not subdirectories)",
        "parameters": {"scope": "directory", "path": "src/tests", "recursive": False},
    },
    {
        "description": "Run tests in a specific file",
        "parameters": {"scope": "file", "path": "src/tests/test_auth.py"},
    },
    {
        "description": "Run specific test functions in all tests",
        "parameters": {"scope": "all", "test_filter": "test_create"},
    },
    {
        "description": "Run specific test in a directory",
        "parameters": {
            "scope": "directory",
            "path": "src/tests",
            "test_filter": "test_authentication",
        },
    },
    {
        "description": "Legacy: Run tests using Pants target syntax",
        "parameters": {"target": "src/tests::"},
    },
]

PANTS_LINT_EXAMPLES = [
    {
        "description": "Lint all code in the repository",
        "parameters": {"scope": "all"},
    },
    {
        "description": "Lint code in a directory and its subdirectories",
        "parameters": {"scope": "directory", "path": "src/app", "recursive": True},
    },
    {
        "description": "Lint a specific file",
        "parameters": {"scope": "file", "path": "src/app/main.py"},
    },
    {
        "description": "Legacy: Lint using Pants target syntax",
        "parameters": {"target": "src/app::"},
    },
]
