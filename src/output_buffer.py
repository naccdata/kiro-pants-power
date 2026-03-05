"""Output buffer for capturing and organizing command output streams."""

from dataclasses import dataclass


@dataclass
class OutputLine:
    """A single line of output with stream tracking."""

    line: str
    stream: str  # "stdout" or "stderr"


class OutputBuffer:
    """Buffer for capturing command output with stream separation and ordering preservation.

    This class captures output lines from both stdout and stderr during command execution,
    maintaining chronological order while also allowing separate access to each stream.

    Requirements:
    - 8.2: Preserve output ordering (stdout and stderr interleaved correctly)
    - 8.3: Buffer output for both real-time display and final parsing
    """

    def __init__(self) -> None:
        """Initialize an empty output buffer."""
        self._lines: list[OutputLine] = []

    def append_line(self, line: str, stream: str) -> None:
        """Append a line from stdout or stderr.

        Args:
            line: The output line to append
            stream: The stream identifier ("stdout" or "stderr")

        Raises:
            ValueError: If stream is not "stdout" or "stderr"
        """
        if stream not in ("stdout", "stderr"):
            raise ValueError(f"Invalid stream: {stream}. Must be 'stdout' or 'stderr'")

        self._lines.append(OutputLine(line=line, stream=stream))

    def get_complete_output(self) -> tuple[str, str]:
        """Return complete stdout and stderr as separate strings.

        Returns:
            A tuple of (stdout, stderr) where each is a string containing
            all lines from that stream joined with newlines.
        """
        stdout_lines = [line.line for line in self._lines if line.stream == "stdout"]
        stderr_lines = [line.line for line in self._lines if line.stream == "stderr"]

        return ("\n".join(stdout_lines), "\n".join(stderr_lines))

    def get_interleaved_output(self) -> str:
        """Return stdout and stderr in execution order.

        This preserves the chronological order in which output lines were produced,
        which is important for understanding the sequence of events during execution.

        Returns:
            A string containing all output lines in the order they were appended,
            joined with newlines.
        """
        return "\n".join(line.line for line in self._lines)
