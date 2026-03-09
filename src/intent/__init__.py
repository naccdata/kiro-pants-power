"""Intent-based API layer for Pants target validation.

This module provides a clear, intent-driven interface for Pants operations,
abstracting away the complexity of Pants target syntax.
"""

from src.intent.configuration import Configuration, ConfigurationManager
from src.intent.data_models import (
    BuildFileResult,
    IntentContext,
    MappingResult,
    ResolvedIntent,
    TranslatedError,
    TranslationRule,
    ValidationResult,
)
from src.intent.error_translator import ErrorTranslator
from src.intent.integration import (
    ErrorResponse,
    MappingError,
    PantsExecutionError,
    SuccessResponse,
    execute_with_error_handling,
    map_intent_to_pants_command,
    sanitize_path,
    sanitize_test_filter,
)
from src.intent.intent_mapper import IntentMapper
from src.intent.monitoring import (
    Metrics,
    get_metrics,
    log_intent_mapping,
    log_validation_performance,
    reset_metrics,
)
from src.intent.path_validator import PathValidator
from src.intent.tool_executor import ToolExecutor
from src.intent.tool_schemas import (
    TOOL_DESCRIPTIONS,
    get_pants_check_schema,
    get_pants_fix_schema,
    get_pants_lint_schema,
    get_pants_package_schema,
    get_pants_test_schema,
)

__all__ = [
    "TOOL_DESCRIPTIONS",
    "BuildFileResult",
    "Configuration",
    "ConfigurationManager",
    "ErrorResponse",
    "ErrorTranslator",
    "IntentContext",
    "IntentMapper",
    "MappingError",
    "MappingResult",
    "Metrics",
    "PantsExecutionError",
    "PathValidator",
    "ResolvedIntent",
    "SuccessResponse",
    "ToolExecutor",
    "TranslatedError",
    "TranslationRule",
    "ValidationResult",
    "execute_with_error_handling",
    "get_metrics",
    "get_pants_check_schema",
    "get_pants_fix_schema",
    "get_pants_lint_schema",
    "get_pants_package_schema",
    "get_pants_test_schema",
    "log_intent_mapping",
    "log_validation_performance",
    "map_intent_to_pants_command",
    "reset_metrics",
    "sanitize_path",
    "sanitize_test_filter",
]
