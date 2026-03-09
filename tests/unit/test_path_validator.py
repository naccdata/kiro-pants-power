"""Unit tests for PathValidator."""


from src.intent.path_validator import PathValidator


def test_validate_file_exists(real_validator):
    """Test validation succeeds for existing file."""
    result = real_validator.validate_path("src/tests/test_example.py", "file")
    assert result.valid is True
    assert result.error is None


def test_validate_file_not_exists(real_validator):
    """Test validation fails for non-existent file."""
    result = real_validator.validate_path("src/tests/missing.py", "file")
    assert result.valid is False
    assert "does not exist" in result.error


def test_validate_directory_exists(real_validator):
    """Test validation succeeds for existing directory with BUILD file."""
    result = real_validator.validate_path("src/tests", "directory")
    assert result.valid is True
    assert result.error is None


def test_validate_directory_not_exists(real_validator):
    """Test validation fails for non-existent directory."""
    result = real_validator.validate_path("src/missing", "directory")
    assert result.valid is False
    assert "does not exist" in result.error


def test_validate_directory_no_build_file(default_config, temp_repo):
    """Test validation fails for directory without BUILD file."""
    # Create directory without BUILD file
    no_build_dir = temp_repo / "src" / "no_build"
    no_build_dir.mkdir()

    validator = PathValidator(config=default_config, repo_root=temp_repo)
    result = validator.validate_path("src/no_build", "directory")

    assert result.valid is False
    assert "No BUILD file found" in result.error
    assert result.suggestion == "pants tailor"


def test_validate_scope_all_always_valid(real_validator):
    """Test scope='all' always validates successfully."""
    result = real_validator.validate_path("any/path", "all")
    assert result.valid is True


def test_check_build_file_found(real_validator):
    """Test BUILD file detection when file exists."""
    result = real_validator.check_build_file("src/tests")
    assert result.found is True
    assert result.location is not None


def test_check_build_file_not_found(default_config, temp_repo):
    """Test BUILD file detection when file doesn't exist."""
    # Create directory without BUILD file
    no_build_dir = temp_repo / "src" / "no_build"
    no_build_dir.mkdir()

    validator = PathValidator(config=default_config, repo_root=temp_repo)
    result = validator.check_build_file("src/no_build")

    assert result.found is False
    assert result.location is None


def test_check_build_file_parent_directory(default_config, temp_repo):
    """Test BUILD file detection searches parent directories."""
    # Create nested directory without BUILD file
    nested_dir = temp_repo / "src" / "tests" / "nested"
    nested_dir.mkdir()

    validator = PathValidator(config=default_config, repo_root=temp_repo)
    result = validator.check_build_file("src/tests/nested")

    # Should find BUILD file in parent directory
    assert result.found is True


def test_build_file_cache(real_validator):
    """Test BUILD file detection uses cache."""
    # First call
    result1 = real_validator.check_build_file("src/tests")

    # Second call should use cache
    result2 = real_validator.check_build_file("src/tests")

    assert result1.found == result2.found
    assert result1.location == result2.location


def test_clear_cache(real_validator):
    """Test cache can be cleared."""
    # Populate cache
    real_validator.check_build_file("src/tests")

    # Clear cache
    real_validator.clear_cache()

    # Cache should be empty (we can't directly test this, but it shouldn't error)
    result = real_validator.check_build_file("src/tests")
    assert result.found is True


def test_validation_disabled(default_config, temp_repo):
    """Test validation can be disabled via configuration."""
    config = default_config
    config.enable_path_validation = False

    validator = PathValidator(config=config, repo_root=temp_repo)
    result = validator.validate_path("nonexistent/path", "file")

    # Should pass even though path doesn't exist
    assert result.valid is True


def test_build_file_checking_disabled(default_config, temp_repo):
    """Test BUILD file checking can be disabled."""
    # Create directory without BUILD file
    no_build_dir = temp_repo / "src" / "no_build"
    no_build_dir.mkdir()

    config = default_config
    config.enable_build_file_checking = False

    validator = PathValidator(config=config, repo_root=temp_repo)
    result = validator.validate_path("src/no_build", "directory")

    # Should pass even though no BUILD file exists
    assert result.valid is True
