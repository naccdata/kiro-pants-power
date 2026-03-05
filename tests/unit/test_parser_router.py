"""Unit tests for ParserRouter."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from src.models import (
    CommandResult,
    CoverageData,
    PytestResults,
    SandboxInfo,
    TestResults,
    TypeCheckResults,
)
from src.parsers.parser_router import ParserRouter


class TestParserRouter:
    """Test suite for ParserRouter class."""

    @pytest.fixture
    def mock_parsers(self):
        """Create mock parser instances."""
        return {
            'junit': MagicMock(),
            'coverage': MagicMock(),
            'mypy': MagicMock(),
            'pytest': MagicMock(),
            'sandbox': MagicMock()
        }

    @pytest.fixture
    def router(self, mock_parsers):
        """Create ParserRouter with mock parsers."""
        return ParserRouter(
            junit_parser=mock_parsers['junit'],
            coverage_parser=mock_parsers['coverage'],
            mypy_parser=mock_parsers['mypy'],
            pytest_parser=mock_parsers['pytest'],
            sandbox_extractor=mock_parsers['sandbox']
        )

    @pytest.fixture
    def command_result(self):
        """Create a sample CommandResult."""
        return CommandResult(
            exit_code=0,
            stdout="Test output",
            stderr="",
            command="pants test ::",
            success=True
        )

    def test_get_parsers_for_test_command(self, router):
        """Test parser selection for test commands."""
        parsers = router.get_parsers_for_command("pants test ::")
        assert 'junit' in parsers
        assert 'coverage' in parsers
        assert 'pytest' in parsers

    def test_get_parsers_for_check_command(self, router):
        """Test parser selection for check commands."""
        parsers = router.get_parsers_for_command("pants check ::")
        assert 'mypy' in parsers
        assert 'junit' not in parsers

    def test_get_parsers_for_mypy_command(self, router):
        """Test parser selection for explicit mypy commands."""
        parsers = router.get_parsers_for_command("pants mypy src/")
        assert 'mypy' in parsers

    def test_get_parsers_for_lint_command(self, router):
        """Test parser selection for lint commands."""
        parsers = router.get_parsers_for_command("pants lint ::")
        assert 'pytest' in parsers

    def test_parse_command_output_extracts_sandboxes(
        self, router, mock_parsers, command_result
    ):
        """Test that sandbox extraction always runs."""
        mock_sandboxes = [
            SandboxInfo(
                sandbox_path="/tmp/sandbox1",
                process_description="test process",
                timestamp="12:34:56"
            )
        ]
        mock_parsers['sandbox'].extract_sandboxes.return_value = mock_sandboxes

        result = router.parse_command_output("pants test ::", command_result)

        mock_parsers['sandbox'].extract_sandboxes.assert_called_once()
        assert result.sandboxes == mock_sandboxes

    def test_parse_test_command_invokes_junit_parser(
        self, router, mock_parsers, command_result
    ):
        """Test that test commands invoke JUnit parser."""
        mock_test_results = TestResults(
            total_count=10,
            pass_count=8,
            fail_count=2,
            skip_count=0,
            failures=[],
            execution_time=1.5
        )
        mock_parsers['junit'].parse_reports.return_value = mock_test_results
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        mock_parsers['junit'].parse_reports.assert_called_once_with("/tmp/reports")
        assert result.test_results == mock_test_results

    def test_parse_test_command_invokes_pytest_parser(
        self, router, mock_parsers, command_result
    ):
        """Test that test commands invoke pytest parser."""
        mock_pytest_results = PytestResults(failed_tests=[])
        mock_parsers['pytest'].parse_output.return_value = mock_pytest_results
        mock_parsers['sandbox'].extract_sandboxes.return_value = []
        mock_parsers['junit'].parse_reports.return_value = TestResults(
            total_count=0, pass_count=0, fail_count=0,
            skip_count=0, failures=[], execution_time=0.0
        )

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        mock_parsers['pytest'].parse_output.assert_called_once()

    def test_parse_check_command_invokes_mypy_parser(
        self, router, mock_parsers, command_result
    ):
        """Test that check commands invoke MyPy parser."""
        mock_type_results = TypeCheckResults(
            error_count=3,
            errors_by_file={},
            report_paths=[]
        )
        mock_parsers['mypy'].parse_output.return_value = mock_type_results
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output("pants check ::", command_result)

        mock_parsers['mypy'].parse_output.assert_called_once()
        assert result.type_check_results == mock_type_results

    def test_parse_command_handles_junit_parsing_error(
        self, router, mock_parsers, command_result
    ):
        """Test graceful handling of JUnit parsing errors."""
        mock_parsers['junit'].parse_reports.side_effect = Exception("Parse error")
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        assert result.test_results is None
        assert len(result.parsing_errors) > 0
        assert "JUnit XML" in result.parsing_errors[0]

    def test_parse_command_handles_coverage_parsing_error(
        self, router, mock_parsers, command_result
    ):
        """Test graceful handling of coverage parsing errors."""
        mock_parsers['junit'].parse_reports.return_value = TestResults(
            total_count=0, pass_count=0, fail_count=0,
            skip_count=0, failures=[], execution_time=0.0
        )
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        # Mock _find_and_parse_coverage to raise an exception
        router._find_and_parse_coverage = Mock(side_effect=Exception("Parse error"))

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        assert result.coverage_data is None
        assert len(result.parsing_errors) > 0
        assert "coverage" in result.parsing_errors[0]

    def test_parse_command_handles_mypy_parsing_error(
        self, router, mock_parsers, command_result
    ):
        """Test graceful handling of MyPy parsing errors."""
        mock_parsers['mypy'].parse_output.side_effect = Exception("Parse error")
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output("pants check ::", command_result)

        assert result.type_check_results is None
        assert len(result.parsing_errors) > 0
        assert "MyPy" in result.parsing_errors[0]

    def test_parse_command_handles_pytest_parsing_error(
        self, router, mock_parsers, command_result
    ):
        """Test graceful handling of pytest parsing errors."""
        mock_parsers['pytest'].parse_output.side_effect = Exception("Parse error")
        mock_parsers['sandbox'].extract_sandboxes.return_value = []
        mock_parsers['junit'].parse_reports.return_value = TestResults(
            total_count=0, pass_count=0, fail_count=0,
            skip_count=0, failures=[], execution_time=0.0
        )

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        assert result.pytest_results is None
        assert len(result.parsing_errors) > 0
        assert "pytest" in result.parsing_errors[0]

    def test_parse_command_handles_sandbox_extraction_error(
        self, router, mock_parsers, command_result
    ):
        """Test graceful handling of sandbox extraction errors."""
        mock_parsers['sandbox'].extract_sandboxes.side_effect = Exception(
            "Extraction error"
        )

        result = router.parse_command_output("pants test ::", command_result)

        assert result.sandboxes == []
        assert len(result.parsing_errors) > 0
        assert "sandbox" in result.parsing_errors[0]

    def test_parse_command_without_report_dir(
        self, router, mock_parsers, command_result
    ):
        """Test parsing when no report directory is provided."""
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output("pants test ::", command_result)

        # JUnit and coverage parsers should not be called without report_dir
        mock_parsers['junit'].parse_reports.assert_not_called()
        assert result.test_results is None
        assert result.coverage_data is None

    def test_find_and_parse_coverage_with_standard_json(self, router, mock_parsers):
        """Test finding and parsing standard coverage.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a coverage.json file
            coverage_file = Path(tmpdir) / "coverage.json"
            coverage_file.write_text('{"totals": {"percent_covered": 85.5}}')

            mock_coverage_data = CoverageData(
                total_coverage=85.5,
                file_coverage={},
                report_path=str(coverage_file)
            )
            mock_parsers['coverage'].parse_coverage.return_value = mock_coverage_data

            result = router._find_and_parse_coverage(tmpdir)

            assert result == mock_coverage_data
            mock_parsers['coverage'].parse_coverage.assert_called_once()

    def test_find_and_parse_coverage_with_standard_xml(self, router, mock_parsers):
        """Test finding and parsing standard coverage.xml file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a coverage.xml file
            coverage_file = Path(tmpdir) / "coverage.xml"
            coverage_file.write_text('<coverage line-rate="0.855"></coverage>')

            mock_coverage_data = CoverageData(
                total_coverage=85.5,
                file_coverage={},
                report_path=str(coverage_file)
            )
            mock_parsers['coverage'].parse_coverage.return_value = mock_coverage_data

            result = router._find_and_parse_coverage(tmpdir)

            assert result == mock_coverage_data

    def test_find_and_parse_coverage_with_nonexistent_dir(self, router):
        """Test handling of nonexistent report directory."""
        result = router._find_and_parse_coverage("/nonexistent/directory")
        assert result is None

    def test_find_and_parse_coverage_with_no_reports(self, router):
        """Test handling when no coverage reports are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = router._find_and_parse_coverage(tmpdir)
            assert result is None

    def test_find_and_parse_coverage_handles_parse_errors(
        self, router, mock_parsers
    ):
        """Test handling of coverage parsing errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid coverage file
            coverage_file = Path(tmpdir) / "coverage.json"
            coverage_file.write_text('invalid json')

            mock_parsers['coverage'].parse_coverage.side_effect = Exception(
                "Parse error"
            )

            result = router._find_and_parse_coverage(tmpdir)

            # Should return None and not raise exception
            assert result is None

    def test_parse_command_skips_empty_test_results(
        self, router, mock_parsers, command_result
    ):
        """Test that empty test results are not included in output."""
        mock_parsers['junit'].parse_reports.return_value = TestResults(
            total_count=0,
            pass_count=0,
            fail_count=0,
            skip_count=0,
            failures=[],
            execution_time=0.0
        )
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        assert result.test_results is None

    def test_parse_command_skips_empty_type_results(
        self, router, mock_parsers, command_result
    ):
        """Test that empty type check results are not included in output."""
        mock_parsers['mypy'].parse_output.return_value = TypeCheckResults(
            error_count=0,
            errors_by_file={},
            report_paths=[]
        )
        mock_parsers['sandbox'].extract_sandboxes.return_value = []

        result = router.parse_command_output("pants check ::", command_result)

        assert result.type_check_results is None

    def test_parse_command_skips_empty_pytest_results(
        self, router, mock_parsers, command_result
    ):
        """Test that empty pytest results are not included in output."""
        mock_parsers['pytest'].parse_output.return_value = PytestResults(
            failed_tests=[]
        )
        mock_parsers['sandbox'].extract_sandboxes.return_value = []
        mock_parsers['junit'].parse_reports.return_value = TestResults(
            total_count=0, pass_count=0, fail_count=0,
            skip_count=0, failures=[], execution_time=0.0
        )

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        assert result.pytest_results is None

    def test_multiple_parsing_errors_accumulated(
        self, router, mock_parsers, command_result
    ):
        """Test that multiple parsing errors are accumulated."""
        mock_parsers['junit'].parse_reports.side_effect = Exception("JUnit error")
        mock_parsers['pytest'].parse_output.side_effect = Exception("Pytest error")
        mock_parsers['sandbox'].extract_sandboxes.side_effect = Exception(
            "Sandbox error"
        )

        result = router.parse_command_output(
            "pants test ::",
            command_result,
            report_dir="/tmp/reports"
        )

        assert len(result.parsing_errors) == 3
        assert any("JUnit" in err for err in result.parsing_errors)
        assert any("pytest" in err for err in result.parsing_errors)
        assert any("sandbox" in err for err in result.parsing_errors)
