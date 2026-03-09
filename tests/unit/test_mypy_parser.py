"""Unit tests for MyPy output parser."""

from src.parsers.mypy_parser import MyPyOutputParser


class TestMyPyOutputParser:
    """Test suite for MyPyOutputParser."""

    def test_extract_error_line_with_column(self) -> None:
        """Test extracting a MyPy error line with column number."""
        parser = MyPyOutputParser()
        line = (
            'src/main.py:42:10: error: Argument 1 has incompatible type '
            '"str"; expected "int"  [arg-type]'
        )

        error = parser.extract_error_line(line)

        assert error is not None
        assert error.file_path == "src/main.py"
        assert error.line_number == 42
        assert error.column == 10
        assert error.error_code == "arg-type"
        assert 'Argument 1 has incompatible type "str"; expected "int"' in error.error_message

    def test_extract_error_line_without_column(self) -> None:
        """Test extracting a MyPy error line without column number."""
        parser = MyPyOutputParser()
        line = (
            'src/utils.py:15: error: Function is missing a return type '
            'annotation  [no-untyped-def]'
        )

        error = parser.extract_error_line(line)

        assert error is not None
        assert error.file_path == "src/utils.py"
        assert error.line_number == 15
        assert error.column is None
        assert error.error_code == "no-untyped-def"
        assert "Function is missing a return type annotation" in error.error_message

    def test_extract_error_line_without_error_code(self) -> None:
        """Test extracting a MyPy error line without error code."""
        parser = MyPyOutputParser()
        line = 'src/models.py:100:5: error: Name "undefined_var" is not defined'

        error = parser.extract_error_line(line)

        assert error is not None
        assert error.file_path == "src/models.py"
        assert error.line_number == 100
        assert error.column == 5
        assert error.error_code == "unknown"
        assert 'Name "undefined_var" is not defined' in error.error_message

    def test_extract_error_line_ignores_notes(self) -> None:
        """Test that note lines are ignored (not errors)."""
        parser = MyPyOutputParser()
        line = 'src/main.py:42:10: note: Consider using Optional[int] instead'

        error = parser.extract_error_line(line)

        assert error is None

    def test_extract_error_line_ignores_warnings(self) -> None:
        """Test that warning lines are ignored (not errors)."""
        parser = MyPyOutputParser()
        line = 'src/main.py:42:10: warning: Unused variable "x"'

        error = parser.extract_error_line(line)

        assert error is None

    def test_extract_error_line_non_error_line(self) -> None:
        """Test that non-error lines return None."""
        parser = MyPyOutputParser()
        lines = [
            "Success: no issues found in 5 source files",
            "Found 3 errors in 2 files (checked 10 source files)",
            "",
            "Some random output",
        ]

        for line in lines:
            error = parser.extract_error_line(line)
            assert error is None

    def test_parse_output_single_error(self) -> None:
        """Test parsing output with a single error."""
        parser = MyPyOutputParser()
        output = """
src/main.py:42:10: error: Argument 1 has incompatible type "str"; expected "int"  [arg-type]
Found 1 error in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        assert result.error_count == 1
        assert len(result.errors_by_file) == 1
        assert "src/main.py" in result.errors_by_file
        assert len(result.errors_by_file["src/main.py"]) == 1

        error = result.errors_by_file["src/main.py"][0]
        assert error.line_number == 42
        assert error.column == 10
        assert error.error_code == "arg-type"

    def test_parse_output_multiple_errors_single_file(self) -> None:
        """Test parsing output with multiple errors in one file."""
        parser = MyPyOutputParser()
        output = """
src/utils.py:10:5: error: Incompatible return value type  [return-value]
src/utils.py:15:10: error: Argument 1 has incompatible type  [arg-type]
src/utils.py:20: error: Function is missing a return type annotation  [no-untyped-def]
Found 3 errors in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        assert result.error_count == 3
        assert len(result.errors_by_file) == 1
        assert "src/utils.py" in result.errors_by_file
        assert len(result.errors_by_file["src/utils.py"]) == 3

        errors = result.errors_by_file["src/utils.py"]
        assert errors[0].line_number == 10
        assert errors[1].line_number == 15
        assert errors[2].line_number == 20

    def test_parse_output_multiple_errors_multiple_files(self) -> None:
        """Test parsing output with errors in multiple files."""
        parser = MyPyOutputParser()
        output = """
src/main.py:42:10: error: Argument 1 has incompatible type "str"; expected "int"  [arg-type]
src/main.py:50:5: error: Incompatible return value type  [return-value]
src/utils.py:15:10: error: Function is missing a return type annotation  [no-untyped-def]
tests/test_main.py:100:20: error: Name "undefined_var" is not defined  [name-defined]
Found 4 errors in 3 files (checked 10 source files)
"""

        result = parser.parse_output(output)

        assert result.error_count == 4
        assert len(result.errors_by_file) == 3
        assert "src/main.py" in result.errors_by_file
        assert "src/utils.py" in result.errors_by_file
        assert "tests/test_main.py" in result.errors_by_file

        assert len(result.errors_by_file["src/main.py"]) == 2
        assert len(result.errors_by_file["src/utils.py"]) == 1
        assert len(result.errors_by_file["tests/test_main.py"]) == 1

    def test_parse_output_no_errors(self) -> None:
        """Test parsing output with no errors."""
        parser = MyPyOutputParser()
        output = """
Success: no issues found in 5 source files
"""

        result = parser.parse_output(output)

        assert result.error_count == 0
        assert len(result.errors_by_file) == 0
        assert len(result.report_paths) == 0

    def test_parse_output_with_notes_and_warnings(self) -> None:
        """Test parsing output that includes notes and warnings (should be ignored)."""
        parser = MyPyOutputParser()
        output = """
src/main.py:42:10: error: Argument 1 has incompatible type "str"; expected "int"  [arg-type]
src/main.py:42:10: note: Consider using Optional[int] instead
src/main.py:50:5: warning: Unused variable "x"
Found 1 error in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        # Only the error should be counted, not notes or warnings
        assert result.error_count == 1
        assert len(result.errors_by_file) == 1
        assert len(result.errors_by_file["src/main.py"]) == 1

    def test_parse_output_extracts_report_paths(self) -> None:
        """Test extracting MyPy report file paths from output."""
        parser = MyPyOutputParser()
        output = """
src/main.py:42:10: error: Argument 1 has incompatible type "str"; expected "int"  [arg-type]
Writing HTML report to mypy-html/
Found 1 error in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        assert result.error_count == 1
        assert len(result.report_paths) == 1
        assert "mypy-html/" in result.report_paths

    def test_parse_output_extracts_multiple_report_paths(self) -> None:
        """Test extracting multiple report paths."""
        parser = MyPyOutputParser()
        output = """
src/main.py:42:10: error: Argument 1 has incompatible type "str"; expected "int"  [arg-type]
Writing HTML report to mypy-html/
Generating XML report in mypy-reports/coverage.xml
Created report at "output/mypy-report.txt"
Found 1 error in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        assert result.error_count == 1
        assert len(result.report_paths) == 3
        assert "mypy-html/" in result.report_paths
        assert "mypy-reports/coverage.xml" in result.report_paths
        assert "output/mypy-report.txt" in result.report_paths

    def test_parse_output_empty_string(self) -> None:
        """Test parsing an empty output string."""
        parser = MyPyOutputParser()
        output = ""

        result = parser.parse_output(output)

        assert result.error_count == 0
        assert len(result.errors_by_file) == 0
        assert len(result.report_paths) == 0

    def test_parse_output_with_file_paths_containing_colons(self) -> None:
        """Test parsing errors from files with paths containing colons."""
        parser = MyPyOutputParser()
        # Note: This is a tricky case - Windows paths like C:\path\file.py
        # The regex should handle the first colon as part of the path
        output = """
C:\\Users\\dev\\project\\src\\main.py:42:10: error: Argument 1 has incompatible type  [arg-type]
Found 1 error in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        # This should still parse correctly
        assert result.error_count == 1
        assert len(result.errors_by_file) == 1

    def test_parse_output_aggregates_errors_by_file(self) -> None:
        """Test that errors are correctly aggregated by file path."""
        parser = MyPyOutputParser()
        output = """
src/main.py:10:5: error: Error 1  [error-code-1]
src/utils.py:20:10: error: Error 2  [error-code-2]
src/main.py:30:15: error: Error 3  [error-code-3]
src/main.py:40:20: error: Error 4  [error-code-4]
src/utils.py:50:25: error: Error 5  [error-code-5]
Found 5 errors in 2 files (checked 10 source files)
"""

        result = parser.parse_output(output)

        assert result.error_count == 5
        assert len(result.errors_by_file) == 2

        # Check src/main.py has 3 errors
        assert len(result.errors_by_file["src/main.py"]) == 3
        main_errors = result.errors_by_file["src/main.py"]
        assert main_errors[0].line_number == 10
        assert main_errors[1].line_number == 30
        assert main_errors[2].line_number == 40

        # Check src/utils.py has 2 errors
        assert len(result.errors_by_file["src/utils.py"]) == 2
        utils_errors = result.errors_by_file["src/utils.py"]
        assert utils_errors[0].line_number == 20
        assert utils_errors[1].line_number == 50

    def test_parse_output_preserves_error_order(self) -> None:
        """Test that errors are preserved in the order they appear in output."""
        parser = MyPyOutputParser()
        output = """
src/main.py:100:5: error: Error at line 100  [error-1]
src/main.py:50:10: error: Error at line 50  [error-2]
src/main.py:75:15: error: Error at line 75  [error-3]
Found 3 errors in 1 file (checked 5 source files)
"""

        result = parser.parse_output(output)

        errors = result.errors_by_file["src/main.py"]
        # Errors should be in the order they appeared in output
        assert errors[0].line_number == 100
        assert errors[1].line_number == 50
        assert errors[2].line_number == 75

    def test_extract_error_line_with_complex_message(self) -> None:
        """Test extracting error with complex multi-part message."""
        parser = MyPyOutputParser()
        line = (
            'src/main.py:42:10: error: Argument 1 to "func" has '
            'incompatible type "str"; expected "int"  [arg-type]'
        )

        error = parser.extract_error_line(line)

        assert error is not None
        assert error.file_path == "src/main.py"
        assert error.line_number == 42
        assert error.column == 10
        assert error.error_code == "arg-type"
        assert (
            'Argument 1 to "func" has incompatible type "str"; '
            'expected "int"' in error.error_message
        )

    def test_parse_output_real_world_example(self) -> None:
        """Test parsing a real-world MyPy output example."""
        parser = MyPyOutputParser()
        output = """
src/parsers/mypy_parser.py:45:16: error: Incompatible return value type (got "None", expected "TypeCheckError")  [return-value]
src/parsers/mypy_parser.py:52:16: error: Incompatible return value type (got "None", expected "TypeCheckError")  [return-value]
src/models.py:150:5: error: Missing return statement  [return]
tests/test_parser.py:10:20: error: Argument 1 to "parse_output" has incompatible type "int"; expected "str"  [arg-type]
tests/test_parser.py:15: error: Function is missing a return type annotation  [no-untyped-def]
Writing HTML report to .mypy_cache/html/
Found 5 errors in 3 files (checked 15 source files)
"""  # noqa: E501

        result = parser.parse_output(output)

        assert result.error_count == 5
        assert len(result.errors_by_file) == 3
        assert (
            len(result.errors_by_file["src/parsers/mypy_parser.py"]) == 2
        )
        assert len(result.errors_by_file["src/models.py"]) == 1
        assert len(result.errors_by_file["tests/test_parser.py"]) == 2
        assert len(result.report_paths) == 1
        assert ".mypy_cache/html/" in result.report_paths
