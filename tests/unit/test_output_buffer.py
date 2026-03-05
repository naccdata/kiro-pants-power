"""Unit tests for OutputBuffer."""

import pytest

from src.output_buffer import OutputBuffer


class TestOutputBuffer:
    """Test suite for OutputBuffer class."""

    def test_append_line_stdout(self) -> None:
        """Test appending stdout lines."""
        buffer = OutputBuffer()
        buffer.append_line("line 1", "stdout")
        buffer.append_line("line 2", "stdout")

        stdout, stderr = buffer.get_complete_output()
        assert stdout == "line 1\nline 2"
        assert stderr == ""

    def test_append_line_stderr(self) -> None:
        """Test appending stderr lines."""
        buffer = OutputBuffer()
        buffer.append_line("error 1", "stderr")
        buffer.append_line("error 2", "stderr")

        stdout, stderr = buffer.get_complete_output()
        assert stdout == ""
        assert stderr == "error 1\nerror 2"

    def test_append_line_mixed_streams(self) -> None:
        """Test appending lines from both streams."""
        buffer = OutputBuffer()
        buffer.append_line("stdout 1", "stdout")
        buffer.append_line("stderr 1", "stderr")
        buffer.append_line("stdout 2", "stdout")
        buffer.append_line("stderr 2", "stderr")

        stdout, stderr = buffer.get_complete_output()
        assert stdout == "stdout 1\nstdout 2"
        assert stderr == "stderr 1\nstderr 2"

    def test_get_interleaved_output_preserves_order(self) -> None:
        """Test that interleaved output preserves chronological order."""
        buffer = OutputBuffer()
        buffer.append_line("line 1", "stdout")
        buffer.append_line("line 2", "stderr")
        buffer.append_line("line 3", "stdout")
        buffer.append_line("line 4", "stderr")

        interleaved = buffer.get_interleaved_output()
        assert interleaved == "line 1\nline 2\nline 3\nline 4"

    def test_invalid_stream_raises_error(self) -> None:
        """Test that invalid stream identifier raises ValueError."""
        buffer = OutputBuffer()
        with pytest.raises(ValueError, match="Invalid stream"):
            buffer.append_line("line", "invalid")

    def test_empty_buffer(self) -> None:
        """Test behavior with empty buffer."""
        buffer = OutputBuffer()

        stdout, stderr = buffer.get_complete_output()
        assert stdout == ""
        assert stderr == ""

        interleaved = buffer.get_interleaved_output()
        assert interleaved == ""

    def test_single_line(self) -> None:
        """Test buffer with single line."""
        buffer = OutputBuffer()
        buffer.append_line("single line", "stdout")

        stdout, stderr = buffer.get_complete_output()
        assert stdout == "single line"
        assert stderr == ""

        interleaved = buffer.get_interleaved_output()
        assert interleaved == "single line"
