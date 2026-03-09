"""Monitoring and observability for intent-based API layer."""

import logging
from dataclasses import dataclass, field
from typing import Any

from .data_models import IntentContext, ResolvedIntent, ValidationResult

# Configure logger
logger = logging.getLogger(__name__)


def log_intent_mapping(
    original_intent: IntentContext,
    resolved_intent: ResolvedIntent,
    target_spec: str,
    elapsed_ms: float,
) -> None:
    """
    Log intent mapping operation with structured data.

    Args:
        original_intent: Original intent parameters from user
        resolved_intent: Intent after applying defaults
        target_spec: Resulting Pants target specification
        elapsed_ms: Time taken for mapping operation
    """
    logger.info(
        "Intent mapped to target",
        extra={
            "original_scope": original_intent.scope,
            "original_path": original_intent.path,
            "original_recursive": original_intent.recursive,
            "original_test_filter": original_intent.test_filter,
            "resolved_scope": resolved_intent.scope,
            "resolved_path": resolved_intent.path,
            "resolved_recursive": resolved_intent.recursive,
            "defaults_applied": resolved_intent.defaults_applied,
            "target_spec": target_spec,
            "elapsed_ms": elapsed_ms,
        },
    )

    # Log defaults applied at DEBUG level
    if resolved_intent.defaults_applied:
        logger.debug(
            f"Applied defaults: {resolved_intent.defaults_applied}",
            extra={"defaults": resolved_intent.defaults_applied},
        )


def log_validation_performance(
    path: str,
    scope: str,
    elapsed_ms: float,
    result: ValidationResult,
    threshold_ms: float,
) -> None:
    """
    Log path validation performance with warnings for slow operations.

    Args:
        path: Path being validated
        scope: Scope type (all, directory, file)
        elapsed_ms: Time taken for validation
        result: Validation result
        threshold_ms: Performance threshold in milliseconds
    """
    log_data = {
        "path": path,
        "scope": scope,
        "elapsed_ms": elapsed_ms,
        "valid": result.valid,
        "threshold_ms": threshold_ms,
    }

    if elapsed_ms > threshold_ms:
        logger.warning(
            f"Path validation exceeded threshold: {elapsed_ms:.2f}ms > "
            f"{threshold_ms}ms for {scope} '{path}'",
            extra=log_data,
        )
    else:
        logger.debug(
            f"Path validation completed in {elapsed_ms:.2f}ms for {scope} '{path}'",
            extra=log_data,
        )

    # Log validation errors at ERROR level
    if not result.valid:
        logger.error(
            f"Path validation failed: {result.error}",
            extra={
                **log_data,
                "error": result.error,
                "suggestion": result.suggestion,
            },
        )


@dataclass
class Metrics:
    """Metrics tracking for intent-based API operations."""

    # Validation metrics
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    total_validation_time_ms: float = 0.0

    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0

    # Intent mapping metrics
    total_mappings: int = 0
    total_mapping_time_ms: float = 0.0

    # Performance tracking
    validation_times: list[float] = field(default_factory=list)
    mapping_times: list[float] = field(default_factory=list)

    def record_validation(self, elapsed_ms: float, success: bool) -> None:
        """
        Record a validation operation.

        Args:
            elapsed_ms: Time taken for validation
            success: Whether validation succeeded
        """
        self.total_validations += 1
        self.total_validation_time_ms += elapsed_ms
        self.validation_times.append(elapsed_ms)

        if success:
            self.successful_validations += 1
        else:
            self.failed_validations += 1

        logger.debug(
            f"Recorded validation: {elapsed_ms:.2f}ms, success={success}",
            extra={
                "elapsed_ms": elapsed_ms,
                "success": success,
                "total_validations": self.total_validations,
            },
        )

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1
        logger.debug(
            f"Cache hit recorded (total: {self.cache_hits})",
            extra={"cache_hits": self.cache_hits},
        )

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1
        logger.debug(
            f"Cache miss recorded (total: {self.cache_misses})",
            extra={"cache_misses": self.cache_misses},
        )

    def record_mapping(self, elapsed_ms: float) -> None:
        """
        Record an intent mapping operation.

        Args:
            elapsed_ms: Time taken for mapping
        """
        self.total_mappings += 1
        self.total_mapping_time_ms += elapsed_ms
        self.mapping_times.append(elapsed_ms)

        logger.debug(
            f"Recorded mapping: {elapsed_ms:.2f}ms",
            extra={
                "elapsed_ms": elapsed_ms,
                "total_mappings": self.total_mappings,
            },
        )

    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Cache hit rate as a percentage (0-100), or 0.0 if no cache operations
        """
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return (self.cache_hits / total_cache_ops) * 100.0

    def get_average_validation_time(self) -> float:
        """
        Get average validation time in milliseconds.

        Returns:
            Average validation time, or 0.0 if no validations
        """
        if self.total_validations == 0:
            return 0.0
        return self.total_validation_time_ms / self.total_validations

    def get_average_mapping_time(self) -> float:
        """
        Get average mapping time in milliseconds.

        Returns:
            Average mapping time, or 0.0 if no mappings
        """
        if self.total_mappings == 0:
            return 0.0
        return self.total_mapping_time_ms / self.total_mappings

    def to_dict(self) -> dict[str, Any]:
        """
        Export metrics as dictionary.

        Returns:
            Dictionary containing all metrics
        """
        return {
            "validation": {
                "total": self.total_validations,
                "successful": self.successful_validations,
                "failed": self.failed_validations,
                "total_time_ms": self.total_validation_time_ms,
                "average_time_ms": self.get_average_validation_time(),
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate_percent": self.get_cache_hit_rate(),
            },
            "mapping": {
                "total": self.total_mappings,
                "total_time_ms": self.total_mapping_time_ms,
                "average_time_ms": self.get_average_mapping_time(),
            },
        }

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.total_validation_time_ms = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_mappings = 0
        self.total_mapping_time_ms = 0.0
        self.validation_times.clear()
        self.mapping_times.clear()

        logger.info("Metrics reset")


# Global metrics instance
_global_metrics: Metrics | None = None


def get_metrics() -> Metrics:
    """
    Get the global metrics instance.

    Returns:
        Global Metrics instance
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = Metrics()
    return _global_metrics


def reset_metrics() -> None:
    """Reset the global metrics instance."""
    global _global_metrics
    if _global_metrics is not None:
        _global_metrics.reset()
    else:
        _global_metrics = Metrics()
