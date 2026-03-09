"""Unit tests for tool schemas."""

from src.intent.tool_schemas import (
    COMMON_INTENT_PARAMETERS,
    LEGACY_TARGET_PARAMETER,
    TEST_SPECIFIC_PARAMETERS,
    TOOL_DESCRIPTIONS,
    get_pants_check_schema,
    get_pants_fix_schema,
    get_pants_lint_schema,
    get_pants_package_schema,
    get_pants_test_schema,
)


class TestCommonParameters:
    """Tests for common intent parameters."""

    def test_common_parameters_include_scope(self):
        """Test that common parameters include scope."""
        assert "scope" in COMMON_INTENT_PARAMETERS
        assert COMMON_INTENT_PARAMETERS["scope"]["type"] == "string"
        assert "enum" in COMMON_INTENT_PARAMETERS["scope"]
        assert set(COMMON_INTENT_PARAMETERS["scope"]["enum"]) == {
            "all",
            "directory",
            "file",
        }

    def test_common_parameters_include_path(self):
        """Test that common parameters include path."""
        assert "path" in COMMON_INTENT_PARAMETERS
        assert COMMON_INTENT_PARAMETERS["path"]["type"] == "string"
        assert "description" in COMMON_INTENT_PARAMETERS["path"]

    def test_common_parameters_include_recursive(self):
        """Test that common parameters include recursive."""
        assert "recursive" in COMMON_INTENT_PARAMETERS
        assert COMMON_INTENT_PARAMETERS["recursive"]["type"] == "boolean"
        assert "description" in COMMON_INTENT_PARAMETERS["recursive"]


class TestTestSpecificParameters:
    """Tests for test-specific parameters."""

    def test_test_filter_parameter(self):
        """Test that test_filter parameter is defined."""
        assert "test_filter" in TEST_SPECIFIC_PARAMETERS
        assert TEST_SPECIFIC_PARAMETERS["test_filter"]["type"] == "string"
        assert "description" in TEST_SPECIFIC_PARAMETERS["test_filter"]


class TestLegacyParameter:
    """Tests for legacy target parameter."""

    def test_legacy_target_parameter(self):
        """Test that legacy target parameter is defined."""
        assert "target" in LEGACY_TARGET_PARAMETER
        assert LEGACY_TARGET_PARAMETER["target"]["type"] == "string"
        assert "DEPRECATED" in LEGACY_TARGET_PARAMETER["target"]["description"]


class TestToolSchemas:
    """Tests for tool schema functions."""

    def test_pants_test_schema_includes_all_parameters(self):
        """Test that pants_test schema includes all parameters."""
        schema = get_pants_test_schema()

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check common parameters
        assert "scope" in schema["properties"]
        assert "path" in schema["properties"]
        assert "recursive" in schema["properties"]

        # Check test-specific parameters
        assert "test_filter" in schema["properties"]

        # Check legacy parameter
        assert "target" in schema["properties"]

    def test_pants_lint_schema_includes_common_parameters(self):
        """Test that pants_lint schema includes common parameters."""
        schema = get_pants_lint_schema()

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check common parameters
        assert "scope" in schema["properties"]
        assert "path" in schema["properties"]
        assert "recursive" in schema["properties"]

        # Check legacy parameter
        assert "target" in schema["properties"]

        # Should not have test_filter
        assert "test_filter" not in schema["properties"]

    def test_pants_check_schema_includes_common_parameters(self):
        """Test that pants_check schema includes common parameters."""
        schema = get_pants_check_schema()

        assert schema["type"] == "object"
        assert "scope" in schema["properties"]
        assert "path" in schema["properties"]
        assert "recursive" in schema["properties"]
        assert "target" in schema["properties"]

    def test_pants_fix_schema_includes_common_parameters(self):
        """Test that pants_fix schema includes common parameters."""
        schema = get_pants_fix_schema()

        assert schema["type"] == "object"
        assert "scope" in schema["properties"]
        assert "path" in schema["properties"]
        assert "recursive" in schema["properties"]
        assert "target" in schema["properties"]

    def test_pants_package_schema_includes_common_parameters(self):
        """Test that pants_package schema includes common parameters."""
        schema = get_pants_package_schema()

        assert schema["type"] == "object"
        assert "scope" in schema["properties"]
        assert "path" in schema["properties"]
        assert "recursive" in schema["properties"]
        assert "target" in schema["properties"]


class TestToolDescriptions:
    """Tests for tool descriptions."""

    def test_all_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        expected_tools = [
            "pants_test",
            "pants_lint",
            "pants_check",
            "pants_fix",
            "pants_format",
            "pants_package",
        ]

        for tool in expected_tools:
            assert tool in TOOL_DESCRIPTIONS
            assert isinstance(TOOL_DESCRIPTIONS[tool], str)
            assert len(TOOL_DESCRIPTIONS[tool]) > 0

    def test_descriptions_mention_intent_based_parameters(self):
        """Test that descriptions mention intent-based parameters."""
        for _tool, description in TOOL_DESCRIPTIONS.items():
            assert "intent-based" in description.lower() or "scope" in description.lower()

    def test_descriptions_mention_legacy_parameter(self):
        """Test that descriptions mention legacy parameter."""
        for _tool, description in TOOL_DESCRIPTIONS.items():
            assert "legacy" in description.lower() or "target" in description.lower()
