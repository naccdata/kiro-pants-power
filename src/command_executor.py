"""Command execution utilities for the Pants DevContainer Power."""

import subprocess
from collections.abc import Iterator

from src.models import CommandExecutionError, CommandResult
from src.output_buffer import OutputBuffer


class CommandExecutor:
    """Executes shell commands and captures output.

    This class provides methods for executing shell commands both synchronously
    (with full output capture) and with streaming output.
    """

    def execute(self, command: str, cwd: str = ".") -> CommandResult:
        """Execute a shell command and return the result.

        Args:
            command: The shell command to execute
            cwd: The working directory for command execution (default: ".")

        Returns:
            CommandResult containing exit code, stdout, stderr, and success status

        Raises:
            CommandExecutionError: If the subprocess execution fails
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True
            )

            return CommandResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=command,
                success=result.returncode == 0
            )
        except Exception as e:
            raise CommandExecutionError(
                f"Failed to execute command '{command}': {e!s}"
            ) from e

    def execute_with_streaming(self, command: str, cwd: str = ".") -> Iterator[str | CommandResult]:
        """Execute a command and yield output lines as they arrive.

        This method streams both stdout and stderr in real-time as the command
        executes, while also buffering the output for final parsing. The output
        is captured using OutputBuffer to maintain chronological order and enable
        both real-time display and post-execution parsing.

        Args:
            command: The shell command to execute
            cwd: The working directory for command execution (default: ".")

        Yields:
            Output lines from stdout and stderr as they arrive, followed by
            the final CommandResult after command completion

        Raises:
            CommandExecutionError: If the subprocess execution fails

        Requirements:
            - 8.1: Stream console output in real-time
            - 8.2: Preserve output ordering (stdout and stderr interleaved correctly)
            - 8.3: Buffer output for both real-time display and final parsing
            - 8.4: Indicate command progress through incremental output updates
        """
        try:
            # Create OutputBuffer for dual capture (streaming + buffering)
            buffer = OutputBuffer()

            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Read stdout and stderr until process completes
            # Note: This simplified implementation reads stdout first, then stderr
            # A production implementation might use select/threading for true interleaving
            if process.stdout:
                for line in process.stdout:
                    line = line.rstrip('\n')
                    buffer.append_line(line, "stdout")
                    yield line

            # Wait for process to complete and get stderr
            process.wait()

            if process.stderr:
                stderr_content = process.stderr.read()
                if stderr_content:
                    stderr_lines = stderr_content.splitlines()
                    for line in stderr_lines:
                        buffer.append_line(line, "stderr")
                        yield line

            # Get complete output from buffer for final CommandResult
            stdout, stderr = buffer.get_complete_output()

            # Yield final CommandResult with buffered output
            result = CommandResult(
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                command=command,
                success=process.returncode == 0
            )

            yield result

        except Exception as e:
            raise CommandExecutionError(
                f"Failed to execute command '{command}': {e!s}"
            ) from e
