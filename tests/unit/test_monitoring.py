"""Unit tests for monitoring and observability."""

import logging

import pytest

from src.intent.data_models import IntentContext, ResolvedIntent, ValidationResult
from src.intent.monitoring import (
    Metrics,
    get_metrics,
    log_intent_mapping,
    log_validation_performance,
    reset_metrics,
)


class TestLogIntentMapping:
    """Tests for log_intent_mapping function."""

    def test_logs_intent_mapping_at_info_level(self, caplog):
        """Test that intent mapping is logged at INFO level."""
        original = IntentContext(
            scope="directory", path="src/tests", recursive=True, test_filter=None
        )
        resolved = ResolvedIntent(
            scope="directory",
            path="src/tests",
            recursive=True,
            test_filter=None,
            defaults_applied={},
        )

        with caplog.at_level(logging.INFO):
            log_intent_mapping(original, resolved, "src/tests::", 5.2)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "INFO"
        assert "Intent mapped to target" in caplog.records[0].message

    def test_logs_defaults_applied_at_debug_level(self, caplog):
        """Test that defaults applied are logged at DEBUG level."""
        original = IntentContext(scope=None, path=None, recursive=None, test_filter=None)
        resolved = ResolvedIntent(
            scope="all",
            path=None,
            recursive=True,
            test_filter=None,
            defaults_applied={"scope": "all", "recursive": True},
        )

        with caplog.at_level(logging.DEBUG):
            log_intent_mapping(original, resolved, "::", 3.1)

        # Should have INFO log + DEBUG log for defaults
        assert len(caplog.records) == 2
        debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
        assert len(debug_records) == 1
        assert "Applied defaults" in debug_records[0].message

    def test_includes_structured_data(self, caplog):
        """Test that structured data is included in log extra."""
        original = IntentContext(
            scope="file", path="test.py", recursive=False, test_filter="test_foo"
        )
        resolved = ResolvedIntent(
            scope="file",
            path="test.py",
            recursive=False,
            test_filter="test_foo",
            defaults_applied={},
        )

        with caplog.at_level(logging.INFO):
            log_intent_mapping(original, resolved, "test.py", 2.5)

        record = caplog.records[0]
        assert record.original_scope == "file"
        assert record.original_path == "test.py"
        assert record.target_spec == "test.py"
        assert record.elapsed_ms == 2.5


class TestLogValidationPerformance:
    """Tests for log_validation_performance function."""

    def test_logs_warning_when_exceeding_threshold(self, caplog):
        """Test that warning is logged when validation exceeds threshold."""
        result = ValidationResult(valid=True)

        with caplog.at_level(logging.WARNING):
            log_validation_performance("src/tests", "directory", 75.0, result, 50.0)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "exceeded threshold" in caplog.records[0].message
        assert "75.00ms > 50.0ms" in caplog.records[0].message

    def test_logs_debug_when_within_threshold(self, caplog):
        """Test that debug log is used when within threshold."""
        result = ValidationResult(valid=True)

        with caplog.at_level(logging.DEBUG):
            log_validation_performance("src/tests", "directory", 30.0, result, 50.0)

        debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
        assert len(debug_records) == 1
        assert "completed in 30.00ms" in debug_records[0].message

    def test_logs_error_for_validation_failure(self, caplog):
        """Test that error is logged for validation failures."""
        result = ValidationResult(
            valid=False,
            error="Path does not exist",
            suggestion="pants tailor",
        )

        with caplog.at_level(logging.ERROR):
            log_validation_performance("src/missing", "directory", 5.0, result, 50.0)

        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) == 1
        assert "Path validation failed" in error_records[0].message
        assert error_records[0].error == "Path does not exist"
        assert error_records[0].suggestion == "pants tailor"

    def test_includes_performance_data(self, caplog):
        """Test that performance data is included in log extra."""
        result = ValidationResult(valid=True)

        with caplog.at_level(logging.DEBUG):
            log_validation_performance("test.py", "file", 8.5, result, 10.0)

        record = caplog.records[0]
        assert record.path == "test.py"
        assert record.scope == "file"
        assert record.elapsed_ms == 8.5
        assert record.threshold_ms == 10.0
        assert record.valid is True


class TestMetrics:
    """Tests for Metrics class."""

    def test_initial_state(self):
        """Test that metrics start at zero."""
        metrics = Metrics()

        assert metrics.total_validations == 0
        assert metrics.successful_validations == 0
        assert metrics.failed_validations == 0
        assert metrics.total_validation_time_ms == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.total_mappings == 0
        assert metrics.total_mapping_time_ms == 0.0

    def test_record_validation_success(self):
        """Test recording successful validation."""
        metrics = Metrics()

        metrics.record_validation(10.5, success=True)

        assert metrics.total_validations == 1
        assert metrics.successful_validations == 1
        assert metrics.failed_validations == 0
        assert metrics.total_validation_time_ms == 10.5
        assert len(metrics.validation_times) == 1

    def test_record_validation_failure(self):
        """Test recording failed validation."""
        metrics = Metrics()

        metrics.record_validation(5.2, success=False)

        assert metrics.total_validations == 1
        assert metrics.successful_validations == 0
        assert metrics.failed_validations == 1
        assert metrics.total_validation_time_ms == 5.2

    def test_record_multiple_validations(self):
        """Test recording multiple validations."""
        metrics = Metrics()

        metrics.record_validation(10.0, success=True)
        metrics.record_validation(15.0, success=False)
        metrics.record_validation(12.0, success=True)

        assert metrics.total_validations == 3
        assert metrics.successful_validations == 2
        assert metrics.failed_validations == 1
        assert metrics.total_validation_time_ms == 37.0

    def test_record_cache_hit(self):
        """Test recording cache hit."""
        metrics = Metrics()

        metrics.record_cache_hit()
        metrics.record_cache_hit()

        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 0

    def test_record_cache_miss(self):
        """Test recording cache miss."""
        metrics = Metrics()

        metrics.record_cache_miss()
        metrics.record_cache_miss()
        metrics.record_cache_miss()

        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 3

    def test_record_mapping(self):
        """Test recording intent mapping."""
        metrics = Metrics()

        metrics.record_mapping(3.5)
        metrics.record_mapping(4.2)

        assert metrics.total_mappings == 2
        assert metrics.total_mapping_time_ms == 7.7
        assert len(metrics.mapping_times) == 2

    def test_get_cache_hit_rate_with_operations(self):
        """Test cache hit rate calculation with operations."""
        metrics = Metrics()

        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 75.0  # 3 hits out of 4 total

    def test_get_cache_hit_rate_no_operations(self):
        """Test cache hit rate returns 0 with no operations."""
        metrics = Metrics()

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 0.0

    def test_get_cache_hit_rate_all_hits(self):
        """Test cache hit rate with all hits."""
        metrics = Metrics()

        metrics.record_cache_hit()
        metrics.record_cache_hit()

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 100.0

    def test_get_cache_hit_rate_all_misses(self):
        """Test cache hit rate with all misses."""
        metrics = Metrics()

        metrics.record_cache_miss()
        metrics.record_cache_miss()

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 0.0

    def test_get_average_validation_time(self):
        """Test average validation time calculation."""
        metrics = Metrics()

        metrics.record_validation(10.0, success=True)
        metrics.record_validation(20.0, success=True)
        metrics.record_validation(30.0, success=False)

        avg_time = metrics.get_average_validation_time()
        assert avg_time == 20.0  # (10 + 20 + 30) / 3

    def test_get_average_validation_time_no_validations(self):
        """Test average validation time returns 0 with no validations."""
        metrics = Metrics()

        avg_time = metrics.get_average_validation_time()
        assert avg_time == 0.0

    def test_get_average_mapping_time(self):
        """Test average mapping time calculation."""
        metrics = Metrics()

        metrics.record_mapping(5.0)
        metrics.record_mapping(10.0)
        metrics.record_mapping(15.0)

        avg_time = metrics.get_average_mapping_time()
        assert avg_time == 10.0  # (5 + 10 + 15) / 3

    def test_get_average_mapping_time_no_mappings(self):
        """Test average mapping time returns 0 with no mappings."""
        metrics = Metrics()

        avg_time = metrics.get_average_mapping_time()
        assert avg_time == 0.0

    def test_to_dict(self):
        """Test metrics export to dictionary."""
        metrics = Metrics()

        metrics.record_validation(10.0, success=True)
        metrics.record_validation(20.0, success=False)
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        metrics.record_mapping(5.0)

        result = metrics.to_dict()

        assert result["validation"]["total"] == 2
        assert result["validation"]["successful"] == 1
        assert result["validation"]["failed"] == 1
        assert result["validation"]["total_time_ms"] == 30.0
        assert result["validation"]["average_time_ms"] == 15.0

        assert result["cache"]["hits"] == 2
        assert result["cache"]["misses"] == 1
        assert result["cache"]["hit_rate_percent"] == pytest.approx(66.666, rel=0.01)

        assert result["mapping"]["total"] == 1
        assert result["mapping"]["total_time_ms"] == 5.0
        assert result["mapping"]["average_time_ms"] == 5.0

    def test_to_dict_empty_metrics(self):
        """Test metrics export with no data."""
        metrics = Metrics()

        result = metrics.to_dict()

        assert result["validation"]["total"] == 0
        assert result["validation"]["average_time_ms"] == 0.0
        assert result["cache"]["hit_rate_percent"] == 0.0
        assert result["mapping"]["average_time_ms"] == 0.0

    def test_reset(self):
        """Test metrics reset."""
        metrics = Metrics()

        # Add some data
        metrics.record_validation(10.0, success=True)
        metrics.record_cache_hit()
        metrics.record_mapping(5.0)

        # Reset
        metrics.reset()

        # Verify all metrics are back to zero
        assert metrics.total_validations == 0
        assert metrics.successful_validations == 0
        assert metrics.failed_validations == 0
        assert metrics.total_validation_time_ms == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.total_mappings == 0
        assert metrics.total_mapping_time_ms == 0.0
        assert len(metrics.validation_times) == 0
        assert len(metrics.mapping_times) == 0


class TestGlobalMetrics:
    """Tests for global metrics functions."""

    def test_get_metrics_creates_instance(self):
        """Test that get_metrics creates global instance."""
        # Reset first to ensure clean state
        reset_metrics()

        metrics = get_metrics()

        assert metrics is not None
        assert isinstance(metrics, Metrics)

    def test_get_metrics_returns_same_instance(self):
        """Test that get_metrics returns same instance."""
        reset_metrics()

        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    def test_reset_metrics_clears_data(self):
        """Test that reset_metrics clears all data."""
        metrics = get_metrics()
        metrics.record_validation(10.0, success=True)
        metrics.record_cache_hit()

        reset_metrics()

        metrics = get_metrics()
        assert metrics.total_validations == 0
        assert metrics.cache_hits == 0

    def test_global_metrics_persists_across_calls(self):
        """Test that global metrics persists data."""
        reset_metrics()

        metrics1 = get_metrics()
        metrics1.record_validation(10.0, success=True)

        metrics2 = get_metrics()
        assert metrics2.total_validations == 1
