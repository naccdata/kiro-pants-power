# Property-Based Test Generators

This directory contains Hypothesis strategies (generators) for property-based testing of the kiro-pants-power system.

## Overview

Property-based testing uses randomly generated test data to verify that code properties hold across a wide range of inputs. The generators in this module create realistic test data for various components.

## Available Generators

### Output Format Generators

These generators create valid and invalid output from various tools:

- `valid_junit_xml()` - JUnit XML test reports
- `valid_coverage_json()` - JSON coverage reports
- `valid_coverage_xml()` - XML (Cobertura) coverage reports
- `valid_mypy_output()` - MyPy type checking output
- `valid_pytest_output()` - Pytest test failure output
- `valid_pants_config()` - Pants TOML configuration files

### Intent-Based API Domain Generators

These generators create test data for the intent-based API layer:

#### Path Generators

- `valid_file_paths()` - Realistic file paths (e.g., "src/app/main.py")
  - Generates paths with 0-5 directory levels
  - Includes common Python file extensions (.py, .pyi, _test.py)
  - Uses realistic naming conventions

- `valid_directory_paths()` - Realistic directory paths (e.g., "src/tests/unit")
  - Generates paths with 1-5 directory levels
  - Includes common directory names (src, tests, lib, etc.)
  - No trailing slashes

- `edge_case_paths()` - Edge case paths for error handling
  - Very long paths (>200 characters)
  - Paths with special characters
  - Relative paths with parent references (..)
  - Paths with spaces
  - Root, empty, and dot paths

#### Test Filter Generators

- `pytest_filter_patterns()` - Pytest-style test filter patterns
  - Simple patterns: "test_create"
  - Wildcard patterns: "test_create*", "*auth*"
  - Boolean operators: "test_create or test_update"
  - Complex expressions: "(test_create or test_update) and not test_slow"

#### Error Message Generators

- `pants_errors()` - Realistic Pants error messages
  - "No targets found" errors
  - "Unknown target" errors
  - "BUILD file not found" errors
  - Dependency resolution errors
  - Execution failures
  - Invalid target specifications

#### Context Generators

- `intent_contexts()` - Complete IntentContext dictionaries
  - Generates scope, path, recursive, and test_filter
  - Ensures path matches scope requirements
  - Includes optional test filters

#### Target Specification Generators

- `pants_target_specs()` - Valid Pants target specifications
  - Recursive all: "::"
  - Recursive path: "src/tests::"
  - Non-recursive: "src/tests:"
  - File paths: "src/app/main.py"
  - Explicit targets: "src/app:main"
  - Wildcard targets: "src/tests:test_*"

## Usage Examples

### Basic Usage

```python
from hypothesis import given
from tests.property.generators import valid_file_paths, pytest_filter_patterns

@given(path=valid_file_paths())
def test_path_validation(path: str):
    """Test that path validator handles all valid file paths."""
    result = validate_path(path, scope="file")
    assert result.valid or result.error is not None

@given(pattern=pytest_filter_patterns())
def test_filter_application(pattern: str):
    """Test that test filters are applied correctly."""
    options = apply_test_filter(pattern)
    assert "-k" in options
    assert pattern in options
```

### Composite Strategies

```python
from hypothesis import given
from tests.property.generators import intent_contexts

@given(context=intent_contexts())
def test_intent_mapping(context: dict):
    """Test intent mapping with all parameter combinations."""
    result = map_intent(**context)
    assert result.target_spec is not None
```

### Edge Case Testing

```python
from hypothesis import given
from tests.property.generators import edge_case_paths

@given(path=edge_case_paths())
def test_path_sanitization(path: str):
    """Test that path sanitization handles edge cases."""
    sanitized = sanitize_path(path)
    assert ".." not in sanitized
    assert not sanitized.startswith("/")
```

## Running Property Tests

Run all property tests:
```bash
pytest tests/property/ -v
```

Run with more examples (default is 100):
```bash
pytest tests/property/ -v --hypothesis-max-examples=1000
```

Run smoke tests to verify generators:
```bash
pytest tests/property/test_generators_smoke.py -v
```

## Adding New Generators

When adding new generators:

1. Add the generator function to `generators.py`
2. Use the `@st.composite` decorator
3. Add a smoke test to `test_generators_smoke.py`
4. Document the generator in this README
5. Update the imports in test files that use it

Example:

```python
from hypothesis import strategies as st

@st.composite
def my_new_generator(draw: st.DrawFn) -> str:
    """Generate my custom data type.
    
    Returns:
        Custom data string
    """
    # Implementation here
    pass
```

## Best Practices

1. **Keep generators focused** - Each generator should produce one type of data
2. **Use realistic data** - Generate data that resembles real-world inputs
3. **Include edge cases** - Create separate generators for edge cases
4. **Document constraints** - Clearly document what the generator produces
5. **Test generators** - Always add smoke tests for new generators
6. **Use composition** - Build complex generators from simpler ones
7. **Set reasonable bounds** - Limit sizes to keep tests fast

## References

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Hypothesis Strategies](https://hypothesis.readthedocs.io/en/latest/data.html)
