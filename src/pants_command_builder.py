"""Pants command construction and validation utilities."""

import re
from typing import Optional

from src.models import ValidationError


class PantsCommandBuilder:
    """Constructs and validates Pants build system commands.
    
    This class provides methods for building Pants commands with proper
    target specifications and validating target syntax.
    """
    
    # Valid target patterns:
    # - "::" for all targets
    # - "path/to/dir::" for directory and subdirectories
    # - "path/to/dir:target" for specific target
    # - "path/to/file.py" for single file
    # - "path/to/dir" for directory (implicit)
    TARGET_PATTERN = re.compile(
        r'^('
        r'::|'  # All targets
        r'[a-zA-Z0-9_\-./]+::[a-zA-Z0-9_\-*]*|'  # Directory with :: (e.g., "src::" or "src::*")
        r'[a-zA-Z0-9_\-./]+:[a-zA-Z0-9_\-*]+|'  # Specific target (e.g., "src:target")
        r'[a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+|'  # File with extension (e.g., "file.py")
        r'[a-zA-Z0-9_\-./]+'  # Directory or path (e.g., "src/dir")
        r')$'
    )
    
    def build_command(self, subcommand: str, target: Optional[str] = None) -> str:
        """Build a Pants command string.
        
        Constructs a command in the format "pants <subcommand> <target>".
        If no target is provided, defaults to "::" (all targets).
        
        Args:
            subcommand: The Pants subcommand (e.g., "fix", "lint", "check", "test", "package")
            target: The target specification (default: "::")
            
        Returns:
            Complete Pants command string
            
        Examples:
            >>> builder = PantsCommandBuilder()
            >>> builder.build_command("test")
            'pants test ::'
            >>> builder.build_command("test", "src/python::")
            'pants test src/python::'
            >>> builder.build_command("lint", "src/python/myapp.py")
            'pants lint src/python/myapp.py'
        """
        # Default to "::" if no target provided
        if target is None or target == "":
            target = "::"
        
        return f"pants {subcommand} {target}"
    
    def validate_target(self, target: str) -> bool:
        """Validate a Pants target specification.
        
        Checks if the target specification follows valid Pants syntax:
        - "::" for all targets
        - "path/to/dir::" for directory and subdirectories
        - "path/to/dir:target" for specific target
        - "path/to/file.py" for single file
        - "path/to/dir" for directory
        
        Args:
            target: The target specification to validate
            
        Returns:
            True if the target is valid, False otherwise
            
        Examples:
            >>> builder = PantsCommandBuilder()
            >>> builder.validate_target("::")
            True
            >>> builder.validate_target("src/python::")
            True
            >>> builder.validate_target("src/python:myapp")
            True
            >>> builder.validate_target("src/python/myapp.py")
            True
            >>> builder.validate_target("invalid target!")
            False
        """
        if not target:
            return False
        
        return bool(self.TARGET_PATTERN.match(target))
