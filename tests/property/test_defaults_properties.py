"""Property-based tests for default resolution (Properties 17-20).

Feature: pants-target-validation
"""

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.intent.configuration import Configuration
from src.intent.intent_mapper import IntentError, IntentMapper
from src.intent.path_validator import PathValidator


def create_mapper():
    """Create a mapper instance for testing."""
    config = Configuration()
    validator = PathValidator(config, Path.cwd())
    return IntentMapper(config, validator)


# Property 17: Default scope is "all"
# **Validates: Requirements 8.1**
@given(
    path=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    recursive=st.one_of(st.none(), st.booleans()),
    test_filter=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.property_test
def test_property_17_default_scope_is_all(path, recursive, test_filter):
    """Property 17: For any intent mapping call where scope is None,
    the resolved intent should have scope='all'.

    **Validates: Requirements 8.1**
    """
    mapper = create_mapper()

    # Resolve intent with scope=None
    resolved = mapper.resolve_defaults(
        scope=None,
        path=path,
        recursive=recursive,
        test_filter=test_filter,
    )

    # Assert scope defaults to "all"
    assert resolved.scope == "all"
    assert "scope" in resolved.defaults_applied
    assert resolved.defaults_applied["scope"] == "all"


# Property 18: Default path for directory scope
# **Validates: Requirements 8.2**
@given(
    recursive=st.one_of(st.none(), st.booleans()),
    test_filter=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.property_test
def test_property_18_default_path_for_directory_scope(recursive, test_filter):
    """Property 18: For any intent mapping call where scope is 'directory'
    and path is None, the resolved intent should default path to '.'
    (current directory).

    **Validates: Requirements 8.2**
    """
    mapper = create_mapper()

    # Resolve intent with scope="directory" and path=None
    resolved = mapper.resolve_defaults(
        scope="directory",
        path=None,
        recursive=recursive,
        test_filter=test_filter,
    )

    # Assert path defaults to "."
    assert resolved.path == "."
    assert "path" in resolved.defaults_applied
    assert resolved.defaults_applied["path"] == "."


# Property 19: Default recursive is true
# **Validates: Requirements 8.3**
@given(
    path=st.text(min_size=1, max_size=50),
    test_filter=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.property_test
def test_property_19_default_recursive_is_true(path, test_filter):
    """Property 19: For any intent mapping call where scope is 'directory'
    and recursive is None, the resolved intent should have recursive=true.

    **Validates: Requirements 8.3**
    """
    mapper = create_mapper()

    # Resolve intent with scope="directory" and recursive=None
    resolved = mapper.resolve_defaults(
        scope="directory",
        path=path,
        recursive=None,
        test_filter=test_filter,
    )

    # Assert recursive defaults to True
    assert resolved.recursive is True
    assert "recursive" in resolved.defaults_applied
    assert resolved.defaults_applied["recursive"] is True


# Property 20: File scope requires path
# **Validates: Requirements 8.5**
@given(
    recursive=st.one_of(st.none(), st.booleans()),
    test_filter=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.property_test
def test_property_20_file_scope_requires_path(recursive, test_filter):
    """Property 20: For any intent mapping call where scope is 'file'
    and path is None, the Intent_Mapper should raise an IntentError
    requiring a path parameter.

    **Validates: Requirements 8.5**
    """
    mapper = create_mapper()

    # Attempt to resolve intent with scope="file" and path=None
    with pytest.raises(IntentError) as exc_info:
        mapper.resolve_defaults(
            scope="file",
            path=None,
            recursive=recursive,
            test_filter=test_filter,
        )

    # Assert error message mentions path requirement
    assert "path" in str(exc_info.value).lower()
    assert "file" in str(exc_info.value).lower()
