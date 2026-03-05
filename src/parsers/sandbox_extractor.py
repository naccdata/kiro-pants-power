"""Sandbox path extractor for parsing Pants log output."""

import logging
import re

from src.models import SandboxInfo

logger = logging.getLogger(__name__)


class SandboxPathExtractor:
    """Extractor for sandbox directory paths from Pants log output.

    Parses Pants log messages to extract sandbox preservation notices,
    including the full sandbox path and process description. Handles both
    --keep-sandboxes=always and on_failure modes.
    """

    # Regex pattern to match sandbox preservation messages
    # Handles multiple formats:
    # - `"/path/to/sandbox"` (backtick + quotes)
    # - "/path/to/sandbox" (just quotes)
    # - `/path/to/sandbox` (just backticks)
    # The pattern looks for the path between delimiters, handling nested quotes
    SANDBOX_PATTERN = re.compile(
        r'\[INFO\]\s+preserving\s+local\s+process\s+execution\s+dir\s+'
        r'`?"([^"]+)"`?\s+'  # Match path inside quotes, with optional surrounding backticks
        r'for\s+"([^"]+)"'
    )

    # Alternative pattern for timestamp-prefixed messages
    # Example: 21:26:13.55 [INFO] preserving local process execution dir ...
    TIMESTAMP_PATTERN = re.compile(
        r'^\d{2}:\d{2}:\d{2}\.\d{2}\s+'
    )

    def extract_sandboxes(self, output: str) -> list[SandboxInfo]:
        """Extract all sandbox paths from Pants output.

        Parses the complete Pants log output to find all sandbox preservation
        messages and extracts the sandbox path and process description from each.

        Args:
            output: Complete Pants command output (stdout/stderr combined)

        Returns:
            List of SandboxInfo objects, one for each preserved sandbox found
        """
        sandboxes = []

        # Process output line by line
        for line in output.splitlines():
            sandbox_info = self.extract_sandbox_line(line)
            if sandbox_info:
                sandboxes.append(sandbox_info)

        if sandboxes:
            logger.info(f"Extracted {len(sandboxes)} sandbox path(s) from output")
        else:
            logger.debug("No sandbox preservation messages found in output")

        return sandboxes

    def extract_sandbox_line(self, line: str) -> SandboxInfo | None:
        """Parse a single sandbox preservation log line.

        Extracts sandbox path and process description from a single log line
        if it matches the sandbox preservation message format.

        Args:
            line: Single line from Pants log output

        Returns:
            SandboxInfo object if the line contains a sandbox preservation message,
            None otherwise
        """
        # Try to match the sandbox pattern
        match = self.SANDBOX_PATTERN.search(line)

        if not match:
            return None

        sandbox_path = match.group(1)
        process_description = match.group(2)

        # Extract timestamp if present
        timestamp = None
        timestamp_match = self.TIMESTAMP_PATTERN.match(line)
        if timestamp_match:
            timestamp = timestamp_match.group(0).strip()

        logger.debug(
            f"Extracted sandbox: path={sandbox_path}, "
            f"process={process_description}, timestamp={timestamp}"
        )

        return SandboxInfo(
            sandbox_path=sandbox_path,
            process_description=process_description,
            timestamp=timestamp
        )
