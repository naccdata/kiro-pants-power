"""Coverage report parser for extracting code coverage metrics."""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from src.models import CoverageData, FileCoverage

logger = logging.getLogger(__name__)


class CoverageReportParser:
    """Parser for coverage reports in JSON or XML (Cobertura) format.

    Extracts overall coverage percentage, per-file coverage metrics,
    and uncovered line ranges from coverage reports.
    """

    def parse_coverage(self, report_path: str) -> CoverageData:
        """Parse coverage report (auto-detects format).

        Automatically detects whether the report is JSON or XML format
        and routes to the appropriate parser.

        Args:
            report_path: Path to the coverage report file

        Returns:
            CoverageData object with parsed coverage information

        Raises:
            FileNotFoundError: If the report file does not exist
            ValueError: If the format cannot be determined or is unsupported
        """
        path = Path(report_path)

        if not path.exists():
            logger.error(f"Coverage report file does not exist: {report_path}")
            raise FileNotFoundError(f"Coverage report not found: {report_path}")

        # Auto-detect format based on file extension and content
        if path.suffix.lower() == ".json":
            return self.parse_json_coverage(report_path)
        elif path.suffix.lower() == ".xml":
            return self.parse_xml_coverage(report_path)
        else:
            # Try to detect by content
            try:
                with open(report_path) as f:
                    first_char = f.read(1)
                    if first_char == '{':
                        return self.parse_json_coverage(report_path)
                    elif first_char == '<':
                        return self.parse_xml_coverage(report_path)
                    else:
                        raise ValueError(f"Unknown coverage report format: {report_path}")
            except Exception as e:
                logger.error(f"Failed to detect coverage report format: {e}")
                raise ValueError(
                    f"Could not determine coverage report format: {report_path}"
                ) from e

    def parse_json_coverage(self, json_path: str) -> CoverageData:
        """Parse JSON coverage report.

        Parses coverage.py JSON format reports, extracting overall coverage
        and per-file metrics.

        Args:
            json_path: Path to the JSON coverage report

        Returns:
            CoverageData object with parsed coverage information

        Raises:
            FileNotFoundError: If the JSON file does not exist
            json.JSONDecodeError: If the JSON is malformed
        """
        path = Path(json_path)

        if not path.exists():
            logger.error(f"JSON coverage file does not exist: {json_path}")
            raise FileNotFoundError(f"JSON coverage file not found: {json_path}")

        try:
            with open(json_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in {json_path}: {e}")
            raise

        # Extract overall coverage from totals
        totals = data.get("totals", {})
        total_coverage = totals.get("percent_covered", 0.0)

        # Extract per-file coverage
        file_coverage = {}
        files = data.get("files", {})

        for file_path, file_data in files.items():
            summary = file_data.get("summary", {})
            covered_lines = summary.get("covered_lines", 0)
            total_lines = summary.get("num_statements", 0)

            # Calculate coverage percentage for this file
            coverage_percent = covered_lines / total_lines * 100.0 if total_lines > 0 else 0.0

            # Extract uncovered line ranges
            uncovered_ranges = self._extract_uncovered_ranges_from_json(file_data)

            file_coverage[file_path] = FileCoverage(
                file_path=file_path,
                coverage_percent=coverage_percent,
                covered_lines=covered_lines,
                total_lines=total_lines,
                uncovered_ranges=uncovered_ranges
            )

        return CoverageData(
            total_coverage=total_coverage,
            file_coverage=file_coverage,
            report_path=json_path
        )

    def parse_xml_coverage(self, xml_path: str) -> CoverageData:
        """Parse XML (Cobertura) coverage report.

        Parses Cobertura XML format coverage reports, extracting overall
        coverage and per-file metrics.

        Args:
            xml_path: Path to the XML coverage report

        Returns:
            CoverageData object with parsed coverage information

        Raises:
            FileNotFoundError: If the XML file does not exist
            ET.ParseError: If the XML is malformed
        """
        path = Path(xml_path)

        if not path.exists():
            logger.error(f"XML coverage file does not exist: {xml_path}")
            raise FileNotFoundError(f"XML coverage file not found: {xml_path}")

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Malformed XML in {xml_path}: {e}")
            raise

        # Extract overall coverage from root element
        # Cobertura uses line-rate (0.0 to 1.0)
        line_rate = root.get("line-rate", "0.0")
        try:
            total_coverage = float(line_rate) * 100.0
        except ValueError:
            logger.warning(f"Invalid line-rate value: {line_rate}")
            total_coverage = 0.0

        # Extract per-file coverage
        file_coverage = {}

        # Navigate through packages -> classes -> files
        packages = root.findall(".//package")
        for package in packages:
            classes = package.findall(".//class")
            for cls in classes:
                filename = cls.get("filename")
                if not filename:
                    continue

                # Get line coverage rate for this class
                class_line_rate = cls.get("line-rate", "0.0")
                try:
                    coverage_percent = float(class_line_rate) * 100.0
                except ValueError:
                    coverage_percent = 0.0

                # Count lines
                lines = cls.findall(".//line")
                total_lines = len(lines)
                covered_lines = sum(1 for line in lines if line.get("hits", "0") != "0")

                # Extract uncovered line ranges
                uncovered_ranges = self._extract_uncovered_ranges_from_xml(cls)

                file_coverage[filename] = FileCoverage(
                    file_path=filename,
                    coverage_percent=coverage_percent,
                    covered_lines=covered_lines,
                    total_lines=total_lines,
                    uncovered_ranges=uncovered_ranges
                )

        return CoverageData(
            total_coverage=total_coverage,
            file_coverage=file_coverage,
            report_path=xml_path
        )

    def _extract_uncovered_ranges_from_json(self, file_data: dict) -> list[tuple[int, int]]:
        """Extract uncovered line ranges from JSON file data.

        Args:
            file_data: File data dictionary from JSON coverage report

        Returns:
            List of (start_line, end_line) tuples for uncovered ranges
        """
        uncovered_ranges: list[tuple[int, int]] = []

        # Get missing lines (uncovered)
        missing_lines = file_data.get("missing_lines", [])
        if not missing_lines:
            return uncovered_ranges

        # Convert individual lines to ranges
        missing_lines.sort()
        if not missing_lines:
            return uncovered_ranges

        range_start = missing_lines[0]
        range_end = missing_lines[0]

        for line in missing_lines[1:]:
            if line == range_end + 1:
                # Extend current range
                range_end = line
            else:
                # Save current range and start new one
                uncovered_ranges.append((range_start, range_end))
                range_start = line
                range_end = line

        # Add the last range
        uncovered_ranges.append((range_start, range_end))

        return uncovered_ranges

    def _extract_uncovered_ranges_from_xml(self, class_elem: ET.Element) -> list[tuple[int, int]]:
        """Extract uncovered line ranges from XML class element.

        Args:
            class_elem: XML element representing a class in Cobertura format

        Returns:
            List of (start_line, end_line) tuples for uncovered ranges
        """
        uncovered_ranges: list[tuple[int, int]] = []

        # Get all lines with hits == 0
        lines = class_elem.findall(".//line")
        uncovered_lines = []

        for line in lines:
            hits = line.get("hits", "0")
            line_number = line.get("number")
            if hits == "0" and line_number:
                try:
                    uncovered_lines.append(int(line_number))
                except ValueError:
                    continue

        if not uncovered_lines:
            return uncovered_ranges

        # Convert individual lines to ranges
        uncovered_lines.sort()
        range_start = uncovered_lines[0]
        range_end = uncovered_lines[0]

        for line_num in uncovered_lines[1:]:
            if line_num == range_end + 1:
                # Extend current range
                range_end = line_num
            else:
                # Save current range and start new one
                uncovered_ranges.append((range_start, range_end))
                range_start = line_num
                range_end = line_num

        # Add the last range
        uncovered_ranges.append((range_start, range_end))

        return uncovered_ranges
