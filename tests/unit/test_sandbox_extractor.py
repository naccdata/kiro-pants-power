"""Unit tests for SandboxPathExtractor."""

from src.models import SandboxInfo
from src.parsers.sandbox_extractor import SandboxPathExtractor


class TestSandboxPathExtractor:
    """Test suite for SandboxPathExtractor class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.extractor = SandboxPathExtractor()

    def test_extract_sandbox_line_with_timestamp(self) -> None:
        """Test extracting sandbox info from a line with timestamp."""
        line = (
            '21:26:13.55 [INFO] preserving local process execution dir '
            '`"/private/var/folders/hm/qjjq4w3n0fsb07kp5bxbn8rw0000gn/'
            'T/process-executionQgIOjb"` '
            'for "Run isort on 1 file."'
        )

        result = self.extractor.extract_sandbox_line(line)

        assert result is not None
        assert isinstance(result, SandboxInfo)
        assert result.sandbox_path == (
            "/private/var/folders/hm/qjjq4w3n0fsb07kp5bxbn8rw0000gn/"
            "T/process-executionQgIOjb"
        )
        assert result.process_description == "Run isort on 1 file."
        assert result.timestamp == "21:26:13.55"

    def test_extract_sandbox_line_without_timestamp(self) -> None:
        """Test extracting sandbox info from a line without timestamp."""
        line = (
            '[INFO] preserving local process execution dir '
            '"/tmp/pants-sandbox-abc123" '
            'for "Run pytest tests."'
        )

        result = self.extractor.extract_sandbox_line(line)

        assert result is not None
        assert result.sandbox_path == "/tmp/pants-sandbox-abc123"
        assert result.process_description == "Run pytest tests."
        assert result.timestamp is None

    def test_extract_sandbox_line_with_backticks(self) -> None:
        """Test extracting sandbox info when path is wrapped in backticks and quotes."""
        line = (
            '[INFO] preserving local process execution dir '
            '`"/home/user/.cache/pants/sandbox-xyz"` '
            'for "Type check with mypy."'
        )

        result = self.extractor.extract_sandbox_line(line)

        assert result is not None
        assert result.sandbox_path == "/home/user/.cache/pants/sandbox-xyz"
        assert result.process_description == "Type check with mypy."

    def test_extract_sandbox_line_with_quotes(self) -> None:
        """Test extracting sandbox info when path is wrapped in quotes."""
        line = (
            '[INFO] preserving local process execution dir '
            '"/opt/pants/sandbox-123" '
            'for "Run black formatter."'
        )

        result = self.extractor.extract_sandbox_line(line)

        assert result is not None
        assert result.sandbox_path == "/opt/pants/sandbox-123"
        assert result.process_description == "Run black formatter."

    def test_extract_sandbox_line_non_matching(self) -> None:
        """Test that non-matching lines return None."""
        lines = [
            "Some random log line",
            "[INFO] Starting pants build",
            "[ERROR] Build failed",
            "21:26:13.55 [INFO] Some other info message",
            "",
        ]

        for line in lines:
            result = self.extractor.extract_sandbox_line(line)
            assert result is None

    def test_extract_sandboxes_multiple(self) -> None:
        """Test extracting multiple sandbox paths from output."""
        output = """
21:26:13.55 [INFO] preserving local process execution dir `"/tmp/sandbox-1"` for "Process 1."
Some other log line
21:26:14.12 [INFO] preserving local process execution dir "/tmp/sandbox-2" for "Process 2."
[ERROR] Some error message
[INFO] preserving local process execution dir `"/tmp/sandbox-3"` for "Process 3."
"""

        result = self.extractor.extract_sandboxes(output)

        assert len(result) == 3
        assert result[0].sandbox_path == "/tmp/sandbox-1"
        assert result[0].process_description == "Process 1."
        assert result[0].timestamp == "21:26:13.55"

        assert result[1].sandbox_path == "/tmp/sandbox-2"
        assert result[1].process_description == "Process 2."
        assert result[1].timestamp == "21:26:14.12"

        assert result[2].sandbox_path == "/tmp/sandbox-3"
        assert result[2].process_description == "Process 3."
        assert result[2].timestamp is None

    def test_extract_sandboxes_empty_output(self) -> None:
        """Test extracting from empty output returns empty list."""
        result = self.extractor.extract_sandboxes("")
        assert result == []

    def test_extract_sandboxes_no_matches(self) -> None:
        """Test extracting from output with no sandbox messages."""
        output = """
[INFO] Starting build
[INFO] Running tests
[ERROR] Test failed
Build completed
"""

        result = self.extractor.extract_sandboxes(output)
        assert result == []

    def test_extract_sandboxes_single(self) -> None:
        """Test extracting a single sandbox path."""
        output = (
            '[INFO] preserving local process execution dir '
            '"/var/tmp/pants-sandbox" for "Run unit tests."'
        )

        result = self.extractor.extract_sandboxes(output)

        assert len(result) == 1
        assert result[0].sandbox_path == "/var/tmp/pants-sandbox"
        assert result[0].process_description == "Run unit tests."

    def test_extract_sandbox_line_complex_path(self) -> None:
        """Test extracting sandbox with complex path containing spaces and special chars."""
        line = (
            '[INFO] preserving local process execution dir '
            '"/tmp/my sandbox/with spaces/process-execution-123" '
            'for "Complex process description."'
        )

        result = self.extractor.extract_sandbox_line(line)

        assert result is not None
        assert result.sandbox_path == "/tmp/my sandbox/with spaces/process-execution-123"
        assert result.process_description == "Complex process description."

    def test_extract_sandbox_line_complex_description(self) -> None:
        """Test extracting sandbox with complex process description."""
        line = (
            '[INFO] preserving local process execution dir '
            '"/tmp/sandbox" '
            'for "Run pytest on 15 files with coverage enabled."'
        )

        result = self.extractor.extract_sandbox_line(line)

        assert result is not None
        assert result.sandbox_path == "/tmp/sandbox"
        assert result.process_description == "Run pytest on 15 files with coverage enabled."

    def test_extract_sandboxes_preserves_order(self) -> None:
        """Test that sandbox extraction preserves the order from output."""
        output = """
[INFO] preserving local process execution dir "/tmp/first" for "First process."
[INFO] preserving local process execution dir "/tmp/second" for "Second process."
[INFO] preserving local process execution dir "/tmp/third" for "Third process."
"""

        result = self.extractor.extract_sandboxes(output)

        assert len(result) == 3
        assert result[0].sandbox_path == "/tmp/first"
        assert result[1].sandbox_path == "/tmp/second"
        assert result[2].sandbox_path == "/tmp/third"

    def test_extract_sandbox_line_with_extra_whitespace(self) -> None:
        """Test extracting sandbox info with extra whitespace in the line."""
        line = (
            '  21:26:13.55   [INFO]   preserving   local   process   execution   dir   '
            '"/tmp/sandbox"   for   "Process description."  '
        )

        result = self.extractor.extract_sandbox_line(line)

        # The regex should still match despite extra whitespace
        assert result is not None
        assert result.sandbox_path == "/tmp/sandbox"
        assert result.process_description == "Process description."

    def test_extract_sandboxes_mixed_output(self) -> None:
        """Test extracting sandboxes from output mixed with other log levels."""
        output = """
[DEBUG] Debug message
21:26:13.55 [INFO] preserving local process execution dir "/tmp/sandbox-1" for "Process 1."
[WARN] Warning message
[ERROR] Error message
[INFO] preserving local process execution dir "/tmp/sandbox-2" for "Process 2."
[INFO] Some other info message
"""

        result = self.extractor.extract_sandboxes(output)

        assert len(result) == 2
        assert result[0].sandbox_path == "/tmp/sandbox-1"
        assert result[1].sandbox_path == "/tmp/sandbox-2"
