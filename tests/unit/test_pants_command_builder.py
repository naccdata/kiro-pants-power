"""Unit tests for PantsCommandBuilder."""

import pytest

from src.pants_command_builder import PantsCommandBuilder


class TestPantsCommandBuilder:
    """Test suite for PantsCommandBuilder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.builder = PantsCommandBuilder()
    
    # Tests for build_command method
    
    def test_build_command_with_default_target(self):
        """Test that build_command defaults to :: when no target provided."""
        result = self.builder.build_command("test")
        assert result == "pants test ::"
    
    def test_build_command_with_none_target(self):
        """Test that build_command handles None target."""
        result = self.builder.build_command("lint", None)
        assert result == "pants lint ::"
    
    def test_build_command_with_empty_target(self):
        """Test that build_command handles empty string target."""
        result = self.builder.build_command("check", "")
        assert result == "pants check ::"
    
    def test_build_command_with_all_targets(self):
        """Test build_command with :: target."""
        result = self.builder.build_command("fix", "::")
        assert result == "pants fix ::"
    
    def test_build_command_with_directory_target(self):
        """Test build_command with directory:: target."""
        result = self.builder.build_command("test", "src/python::")
        assert result == "pants test src/python::"
    
    def test_build_command_with_specific_target(self):
        """Test build_command with specific target."""
        result = self.builder.build_command("package", "src/python:myapp")
        assert result == "pants package src/python:myapp"
    
    def test_build_command_with_file_target(self):
        """Test build_command with file target."""
        result = self.builder.build_command("lint", "src/python/myapp.py")
        assert result == "pants lint src/python/myapp.py"
    
    def test_build_command_with_path_target(self):
        """Test build_command with path target."""
        result = self.builder.build_command("check", "src/python")
        assert result == "pants check src/python"
    
    def test_build_command_for_fix_subcommand(self):
        """Test build_command for fix subcommand."""
        result = self.builder.build_command("fix", "common/src::")
        assert result == "pants fix common/src::"
    
    def test_build_command_for_lint_subcommand(self):
        """Test build_command for lint subcommand."""
        result = self.builder.build_command("lint", "common/test::")
        assert result == "pants lint common/test::"
    
    def test_build_command_for_check_subcommand(self):
        """Test build_command for check subcommand."""
        result = self.builder.build_command("check", "src::")
        assert result == "pants check src::"
    
    def test_build_command_for_test_subcommand(self):
        """Test build_command for test subcommand."""
        result = self.builder.build_command("test", "tests::")
        assert result == "pants test tests::"
    
    def test_build_command_for_package_subcommand(self):
        """Test build_command for package subcommand."""
        result = self.builder.build_command("package", "src:app")
        assert result == "pants package src:app"
    
    # Tests for validate_target method
    
    def test_validate_target_all_targets(self):
        """Test validation of :: target."""
        assert self.builder.validate_target("::") is True
    
    def test_validate_target_directory_with_double_colon(self):
        """Test validation of directory:: target."""
        assert self.builder.validate_target("src/python::") is True
        assert self.builder.validate_target("common/src::") is True
        assert self.builder.validate_target("tests::") is True
    
    def test_validate_target_specific_target(self):
        """Test validation of directory:target format."""
        assert self.builder.validate_target("src/python:myapp") is True
        assert self.builder.validate_target("common:lib") is True
        assert self.builder.validate_target("src:target-name") is True
    
    def test_validate_target_file_with_extension(self):
        """Test validation of file.ext format."""
        assert self.builder.validate_target("src/python/myapp.py") is True
        assert self.builder.validate_target("common/test/test_file.py") is True
        assert self.builder.validate_target("BUILD.txt") is True
    
    def test_validate_target_directory_path(self):
        """Test validation of directory path format."""
        assert self.builder.validate_target("src/python") is True
        assert self.builder.validate_target("common") is True
        assert self.builder.validate_target("src/python/myapp") is True
    
    def test_validate_target_with_underscores(self):
        """Test validation of targets with underscores."""
        assert self.builder.validate_target("src_dir/my_app::") is True
        assert self.builder.validate_target("src:my_target") is True
    
    def test_validate_target_with_hyphens(self):
        """Test validation of targets with hyphens."""
        assert self.builder.validate_target("src-dir/my-app::") is True
        assert self.builder.validate_target("src:my-target") is True
    
    def test_validate_target_with_wildcards(self):
        """Test validation of targets with wildcards."""
        assert self.builder.validate_target("src/python::*") is True
        assert self.builder.validate_target("src:*") is True
    
    def test_validate_target_empty_string(self):
        """Test validation of empty string."""
        assert self.builder.validate_target("") is False
    
    def test_validate_target_with_spaces(self):
        """Test validation rejects targets with spaces."""
        assert self.builder.validate_target("src python::") is False
        assert self.builder.validate_target("src: target") is False
    
    def test_validate_target_with_special_chars(self):
        """Test validation rejects targets with invalid special characters."""
        assert self.builder.validate_target("src@python::") is False
        assert self.builder.validate_target("src#python") is False
        assert self.builder.validate_target("src!target") is False
    
    def test_validate_target_malformed_colon(self):
        """Test validation rejects malformed colon syntax."""
        assert self.builder.validate_target("src:::") is False
        assert self.builder.validate_target(":src") is False
        assert self.builder.validate_target("src:") is False  # Missing target name after colon
    
    def test_validate_target_complex_paths(self):
        """Test validation of complex nested paths."""
        assert self.builder.validate_target("common/src/python/myapp::") is True
        assert self.builder.validate_target("a/b/c/d/e.py") is True
        assert self.builder.validate_target("deep/nested/path:target") is True
