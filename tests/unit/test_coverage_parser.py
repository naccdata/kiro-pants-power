"""Unit tests for CoverageReportParser."""

import json
from pathlib import Path

import pytest

from src.models import CoverageData
from src.parsers.coverage_parser import CoverageReportParser


class TestCoverageReportParser:
    """Test suite for CoverageReportParser class."""

    @pytest.fixture
    def parser(self) -> CoverageReportParser:
        """Create a CoverageReportParser instance."""
        return CoverageReportParser()

    @pytest.fixture
    def sample_json_coverage(self, tmp_path: Path) -> Path:
        """Create a sample JSON coverage report."""
        coverage_data = {
            "totals": {
                "percent_covered": 85.5
            },
            "files": {
                "src/module1.py": {
                    "summary": {
                        "covered_lines": 45,
                        "num_statements": 50
                    },
                    "missing_lines": [10, 11, 12, 25, 30]
                },
                "src/module2.py": {
                    "summary": {
                        "covered_lines": 100,
                        "num_statements": 100
                    },
                    "missing_lines": []
                }
            }
        }

        json_file = tmp_path / "coverage.json"
        with open(json_file, 'w') as f:
            json.dump(coverage_data, f)

        return json_file

    @pytest.fixture
    def sample_xml_coverage(self, tmp_path: Path) -> Path:
        """Create a sample XML (Cobertura) coverage report."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.855" branch-rate="0.8" version="1.0">
    <packages>
        <package name="src" line-rate="0.9" branch-rate="0.85">
            <classes>
                <class name="module1" filename="src/module1.py" line-rate="0.9">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                        <line number="3" hits="0"/>
                        <line number="4" hits="0"/>
                        <line number="5" hits="1"/>
                    </lines>
                </class>
                <class name="module2" filename="src/module2.py" line-rate="1.0">
                    <lines>
                        <line number="1" hits="5"/>
                        <line number="2" hits="3"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
        xml_file = tmp_path / "coverage.xml"
        xml_file.write_text(xml_content)

        return xml_file

    def test_parse_json_coverage_basic(
        self, parser: CoverageReportParser, sample_json_coverage: Path
    ) -> None:
        """Test parsing a basic JSON coverage report."""
        result = parser.parse_json_coverage(str(sample_json_coverage))

        assert isinstance(result, CoverageData)
        assert result.total_coverage == 85.5
        assert result.report_path == str(sample_json_coverage)
        assert len(result.file_coverage) == 2

    def test_parse_json_coverage_file_metrics(
        self, parser: CoverageReportParser, sample_json_coverage: Path
    ) -> None:
        """Test that JSON parser extracts correct per-file metrics."""
        result = parser.parse_json_coverage(str(sample_json_coverage))

        # Check module1
        module1 = result.file_coverage["src/module1.py"]
        assert module1.file_path == "src/module1.py"
        assert module1.covered_lines == 45
        assert module1.total_lines == 50
        assert module1.coverage_percent == 90.0

        # Check module2
        module2 = result.file_coverage["src/module2.py"]
        assert module2.file_path == "src/module2.py"
        assert module2.covered_lines == 100
        assert module2.total_lines == 100
        assert module2.coverage_percent == 100.0

    def test_parse_json_coverage_uncovered_ranges(
        self, parser: CoverageReportParser, sample_json_coverage: Path
    ) -> None:
        """Test that JSON parser extracts uncovered line ranges correctly."""
        result = parser.parse_json_coverage(str(sample_json_coverage))

        # Check module1 uncovered ranges
        # Missing lines: [10, 11, 12, 25, 30] should create 3 ranges:
        # (10,12), (25,25), (30,30)
        module1 = result.file_coverage["src/module1.py"]
        assert len(module1.uncovered_ranges) == 3
        assert (10, 12) in module1.uncovered_ranges
        assert (25, 25) in module1.uncovered_ranges
        assert (30, 30) in module1.uncovered_ranges

        # Check module2 has no uncovered ranges
        module2 = result.file_coverage["src/module2.py"]
        assert len(module2.uncovered_ranges) == 0

    def test_parse_xml_coverage_basic(
        self, parser: CoverageReportParser, sample_xml_coverage: Path
    ) -> None:
        """Test parsing a basic XML coverage report."""
        result = parser.parse_xml_coverage(str(sample_xml_coverage))

        assert isinstance(result, CoverageData)
        assert result.total_coverage == 85.5
        assert result.report_path == str(sample_xml_coverage)
        assert len(result.file_coverage) == 2

    def test_parse_xml_coverage_file_metrics(
        self, parser: CoverageReportParser, sample_xml_coverage: Path
    ) -> None:
        """Test that XML parser extracts correct per-file metrics."""
        result = parser.parse_xml_coverage(str(sample_xml_coverage))

        # Check module1
        module1 = result.file_coverage["src/module1.py"]
        assert module1.file_path == "src/module1.py"
        assert module1.total_lines == 5
        assert module1.covered_lines == 3
        assert module1.coverage_percent == 90.0

        # Check module2
        module2 = result.file_coverage["src/module2.py"]
        assert module2.file_path == "src/module2.py"
        assert module2.total_lines == 2
        assert module2.covered_lines == 2
        assert module2.coverage_percent == 100.0

    def test_parse_xml_coverage_uncovered_ranges(
        self, parser: CoverageReportParser, sample_xml_coverage: Path
    ) -> None:
        """Test that XML parser extracts uncovered line ranges correctly."""
        result = parser.parse_xml_coverage(str(sample_xml_coverage))

        # Check module1 uncovered ranges
        module1 = result.file_coverage["src/module1.py"]
        assert len(module1.uncovered_ranges) == 1
        assert (3, 4) in module1.uncovered_ranges

        # Check module2 has no uncovered ranges
        module2 = result.file_coverage["src/module2.py"]
        assert len(module2.uncovered_ranges) == 0

    def test_parse_coverage_auto_detect_json(
        self, parser: CoverageReportParser, sample_json_coverage: Path
    ) -> None:
        """Test that parse_coverage auto-detects JSON format."""
        result = parser.parse_coverage(str(sample_json_coverage))

        assert isinstance(result, CoverageData)
        assert result.total_coverage == 85.5

    def test_parse_coverage_auto_detect_xml(
        self, parser: CoverageReportParser, sample_xml_coverage: Path
    ) -> None:
        """Test that parse_coverage auto-detects XML format."""
        result = parser.parse_coverage(str(sample_xml_coverage))

        assert isinstance(result, CoverageData)
        assert result.total_coverage == 85.5

    def test_parse_coverage_file_not_found(self, parser: CoverageReportParser) -> None:
        """Test that parsing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse_coverage("/nonexistent/coverage.json")

    def test_parse_json_coverage_file_not_found(self, parser: CoverageReportParser) -> None:
        """Test that parsing non-existent JSON file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse_json_coverage("/nonexistent/coverage.json")

    def test_parse_xml_coverage_file_not_found(self, parser: CoverageReportParser) -> None:
        """Test that parsing non-existent XML file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse_xml_coverage("/nonexistent/coverage.xml")

    def test_parse_json_coverage_malformed(
        self, parser: CoverageReportParser, tmp_path: Path
    ) -> None:
        """Test that parsing malformed JSON raises JSONDecodeError."""
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text("{ invalid json")

        with pytest.raises(json.JSONDecodeError):
            parser.parse_json_coverage(str(malformed_file))

    def test_parse_xml_coverage_malformed(
        self, parser: CoverageReportParser, tmp_path: Path
    ) -> None:
        """Test that parsing malformed XML raises ParseError."""
        malformed_file = tmp_path / "malformed.xml"
        malformed_file.write_text("<coverage><unclosed>")

        # Use a more specific exception type instead of blind Exception
        from xml.etree.ElementTree import ParseError
        with pytest.raises(ParseError):
            parser.parse_xml_coverage(str(malformed_file))

    def test_parse_json_coverage_zero_coverage(
        self, parser: CoverageReportParser, tmp_path: Path
    ) -> None:
        """Test parsing JSON report with 0% coverage."""
        coverage_data = {
            "totals": {
                "percent_covered": 0.0
            },
            "files": {
                "src/uncovered.py": {
                    "summary": {
                        "covered_lines": 0,
                        "num_statements": 50
                    },
                    "missing_lines": list(range(1, 51))
                }
            }
        }

        json_file = tmp_path / "zero_coverage.json"
        with open(json_file, 'w') as f:
            json.dump(coverage_data, f)

        result = parser.parse_json_coverage(str(json_file))

        assert result.total_coverage == 0.0
        uncovered = result.file_coverage["src/uncovered.py"]
        assert uncovered.coverage_percent == 0.0
        assert uncovered.covered_lines == 0
        assert uncovered.total_lines == 50

    def test_parse_json_coverage_empty_files(
        self, parser: CoverageReportParser, tmp_path: Path
    ) -> None:
        """Test parsing JSON report with no files."""
        coverage_data = {
            "totals": {
                "percent_covered": 0.0
            },
            "files": {}
        }

        json_file = tmp_path / "empty_files.json"
        with open(json_file, 'w') as f:
            json.dump(coverage_data, f)

        result = parser.parse_json_coverage(str(json_file))

        assert result.total_coverage == 0.0
        assert len(result.file_coverage) == 0

    def test_parse_coverage_unknown_format(
        self, parser: CoverageReportParser, tmp_path: Path
    ) -> None:
        """Test that unknown format raises ValueError."""
        unknown_file = tmp_path / "coverage.txt"
        unknown_file.write_text("some random text")

        with pytest.raises(
            ValueError, match="Could not determine coverage report format"
        ):
            parser.parse_coverage(str(unknown_file))

    def test_extract_uncovered_ranges_consecutive_lines(
        self, parser: CoverageReportParser, tmp_path: Path
    ) -> None:
        """Test that consecutive uncovered lines are merged into ranges."""
        coverage_data = {
            "totals": {
                "percent_covered": 50.0
            },
            "files": {
                "src/test.py": {
                    "summary": {
                        "covered_lines": 5,
                        "num_statements": 10
                    },
                    "missing_lines": [1, 2, 3, 7, 8, 10]
                }
            }
        }

        json_file = tmp_path / "ranges.json"
        with open(json_file, 'w') as f:
            json.dump(coverage_data, f)

        result = parser.parse_json_coverage(str(json_file))
        test_file = result.file_coverage["src/test.py"]

        # Should have 3 ranges: (1,3), (7,8), (10,10)
        assert len(test_file.uncovered_ranges) == 3
        assert (1, 3) in test_file.uncovered_ranges
        assert (7, 8) in test_file.uncovered_ranges
        assert (10, 10) in test_file.uncovered_ranges
