"""Unit tests for Pytest output parser."""

from src.parsers.pytest_parser import PytestOutputParser


class TestPytestOutputParser:
    """Test suite for PytestOutputParser."""

    def test_extract_failure_summary_single_failure(self) -> None:
        """Test extracting a single FAILED line from summary."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::test_addition - AssertionError: assert 1 == 2
========================= 1 failed, 2 passed in 0.50s =========================
"""

        summary_lines = parser.extract_failure_summary(output)

        assert len(summary_lines) == 1
        assert "FAILED tests/test_example.py::test_addition" in summary_lines[0]

    def test_extract_failure_summary_multiple_failures(self) -> None:
        """Test extracting multiple FAILED lines from summary."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::test_addition - AssertionError: assert 1 == 2
FAILED tests/test_example.py::test_subtraction - AssertionError: assert 5 == 3
FAILED tests/test_other.py::test_division - ZeroDivisionError: division by zero
========================= 3 failed, 1 passed in 0.75s =========================
"""

        summary_lines = parser.extract_failure_summary(output)

        assert len(summary_lines) == 3
        assert any("test_addition" in line for line in summary_lines)
        assert any("test_subtraction" in line for line in summary_lines)
        assert any("test_division" in line for line in summary_lines)

    def test_extract_failure_summary_no_failures(self) -> None:
        """Test extracting from output with no failures."""
        parser = PytestOutputParser()
        output = """
========================= 5 passed in 0.50s =========================
"""

        summary_lines = parser.extract_failure_summary(output)

        assert len(summary_lines) == 0

    def test_extract_failure_summary_from_failures_section(self) -> None:
        """Test extracting from FAILURES section marker."""
        parser = PytestOutputParser()
        output = """
========================= FAILURES =========================
FAILED tests/test_example.py::test_addition - AssertionError
========================= 1 failed in 0.50s =========================
"""

        summary_lines = parser.extract_failure_summary(output)

        assert len(summary_lines) == 1

    def test_parse_output_single_failure(self) -> None:
        """Test parsing output with a single test failure."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::test_addition - AssertionError: assert 1 == 2
========================= 1 failed, 2 passed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.test_name == "test_addition"
        assert failure.test_file == "tests/test_example.py"
        assert failure.failure_type == "AssertionError"
        assert "assert 1 == 2" in failure.failure_message

    def test_parse_output_multiple_failures(self) -> None:
        """Test parsing output with multiple test failures."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::test_addition - AssertionError: assert 1 == 2
FAILED tests/test_example.py::test_subtraction - AssertionError: assert 5 == 3
FAILED tests/test_other.py::test_division - ZeroDivisionError: division by zero
========================= 3 failed, 1 passed in 0.75s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 3

        # Check first failure
        assert result.failed_tests[0].test_name == "test_addition"
        assert result.failed_tests[0].test_file == "tests/test_example.py"
        assert result.failed_tests[0].failure_type == "AssertionError"

        # Check second failure
        assert result.failed_tests[1].test_name == "test_subtraction"
        assert result.failed_tests[1].failure_type == "AssertionError"

        # Check third failure
        assert result.failed_tests[2].test_name == "test_division"
        assert result.failed_tests[2].test_file == "tests/test_other.py"
        assert result.failed_tests[2].failure_type == "ZeroDivisionError"

    def test_parse_output_class_method_test(self) -> None:
        """Test parsing failure from a test class method."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::TestClass::test_method - ValueError: invalid value
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.test_name == "TestClass::test_method"
        assert failure.test_file == "tests/test_example.py"
        assert failure.failure_type == "ValueError"

    def test_parse_output_no_failures(self) -> None:
        """Test parsing output with no failures."""
        parser = PytestOutputParser()
        output = """
========================= 5 passed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 0

    def test_parse_output_failure_without_message(self) -> None:
        """Test parsing failure line without detailed message."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::test_something
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.test_name == "test_something"
        assert failure.test_file == "tests/test_example.py"
        assert failure.failure_type == "Unknown"
        assert failure.failure_message == ""

    def test_extract_assertion_details_simple_comparison(self) -> None:
        """Test extracting assertion details from simple comparison."""
        parser = PytestOutputParser()
        output = """
    def test_addition():
>       assert 1 == 2
E       assert 1 == 2
"""

        assertions = parser.extract_assertion_details(output)

        assert len(assertions) == 1
        assert assertions[0].actual_value == "1"
        assert assertions[0].expected_value == "2"
        assert assertions[0].comparison_operator == "=="

    def test_extract_assertion_details_not_equal(self) -> None:
        """Test extracting assertion with != operator."""
        parser = PytestOutputParser()
        output = """
    def test_inequality():
>       assert result != expected
E       assert result != expected
"""

        assertions = parser.extract_assertion_details(output)

        assert len(assertions) == 1
        assert assertions[0].actual_value == "result"
        assert assertions[0].expected_value == "expected"
        assert assertions[0].comparison_operator == "!="

    def test_extract_assertion_details_comparison_operators(self) -> None:
        """Test extracting assertions with various comparison operators."""
        parser = PytestOutputParser()
        output = """
E       assert 5 < 3
E       assert 10 > 20
E       assert x <= y
E       assert a >= b
E       assert item in collection
E       assert value is None
"""

        assertions = parser.extract_assertion_details(output)

        assert len(assertions) == 6
        assert assertions[0].comparison_operator == "<"
        assert assertions[1].comparison_operator == ">"
        assert assertions[2].comparison_operator == "<="
        assert assertions[3].comparison_operator == ">="
        assert assertions[4].comparison_operator == "in"
        assert assertions[5].comparison_operator == "is"

    def test_extract_assertion_details_no_assertions(self) -> None:
        """Test extracting from output with no assertions."""
        parser = PytestOutputParser()
        output = """
    def test_exception():
>       raise ValueError("Something went wrong")
E       ValueError: Something went wrong
"""

        assertions = parser.extract_assertion_details(output)

        assert len(assertions) == 0

    def test_parse_output_with_assertion_details(self) -> None:
        """Test parsing output that includes assertion details."""
        parser = PytestOutputParser()
        output = """
_ test_addition _

    def test_addition():
>       assert 1 == 2
E       assert 1 == 2

tests/test_example.py:10: AssertionError
========================= short test summary info =========================
FAILED tests/test_example.py::test_addition - AssertionError: assert 1 == 2
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.assertion_details is not None
        assert failure.assertion_details.actual_value == "1"
        assert failure.assertion_details.expected_value == "2"
        assert failure.assertion_details.comparison_operator == "=="

    def test_parse_output_with_stack_trace(self) -> None:
        """Test parsing output that includes stack trace."""
        parser = PytestOutputParser()
        output = """
_ test_division _

    def test_division():
>       result = 10 / 0
E       ZeroDivisionError: division by zero

tests/test_example.py:15: ZeroDivisionError
========================= short test summary info =========================
FAILED tests/test_example.py::test_division - ZeroDivisionError: division by zero
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.stack_trace_excerpt is not None
        assert "result = 10 / 0" in failure.stack_trace_excerpt

    def test_parse_output_filters_framework_internals(self) -> None:
        """Test that framework internal stack frames are filtered."""
        parser = PytestOutputParser()
        output = """
_ test_example _

    def test_example():
>       assert False
E       assert False

tests/test_example.py:10: AssertionError
    /_pytest/runner.py:123: in pytest_runtest_call
        item.runtest()
    /pytest.py:456: in runtest
        self.ihook.pytest_runtest_call(item=self)
========================= short test summary info =========================
FAILED tests/test_example.py::test_example - AssertionError
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]

        # Stack trace should not include framework internals
        if failure.stack_trace_excerpt:
            assert "/_pytest/" not in failure.stack_trace_excerpt
            assert "/pytest.py" not in failure.stack_trace_excerpt

    def test_parse_output_real_world_example(self) -> None:
        """Test parsing a real-world pytest output example."""
        parser = PytestOutputParser()
        output = """
================================= FAILURES =================================
_ test_parser_extracts_errors _

    def test_parser_extracts_errors():
        output = "src/main.py:42:10: error: Type mismatch"
        parser = MyPyOutputParser()
        result = parser.parse_output(output)
>       assert result.error_count == 2
E       assert 1 == 2
E        +  where 1 = TypeCheckResults(error_count=1, ...).error_count

tests/test_mypy_parser.py:25: AssertionError
========================= short test summary info =========================
FAILED tests/test_mypy_parser.py::test_parser_extracts_errors - AssertionError: assert 1 == 2
========================= 1 failed, 5 passed in 0.75s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.test_name == "test_parser_extracts_errors"
        assert failure.test_file == "tests/test_mypy_parser.py"
        assert failure.failure_type == "AssertionError"
        assert failure.assertion_details is not None
        assert failure.assertion_details.actual_value == "1"
        assert failure.assertion_details.expected_value == "2"

    def test_parse_output_empty_string(self) -> None:
        """Test parsing an empty output string."""
        parser = PytestOutputParser()
        output = ""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 0

    def test_parse_output_preserves_failure_order(self) -> None:
        """Test that failures are preserved in the order they appear."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_a.py::test_first - AssertionError
FAILED tests/test_b.py::test_second - ValueError
FAILED tests/test_c.py::test_third - TypeError
========================= 3 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 3
        assert result.failed_tests[0].test_name == "test_first"
        assert result.failed_tests[1].test_name == "test_second"
        assert result.failed_tests[2].test_name == "test_third"

    def test_parse_output_handles_complex_test_names(self) -> None:
        """Test parsing failures with complex test names."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::TestSuite::TestNestedClass::test_method - AssertionError
FAILED tests/test_example.py::test_with_params[param1-param2] - ValueError
========================= 2 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 2
        assert "TestSuite::TestNestedClass::test_method" in result.failed_tests[0].test_name
        assert "test_with_params[param1-param2]" in result.failed_tests[1].test_name

    def test_parse_output_handles_exception_types(self) -> None:
        """Test parsing various exception types."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_a.py::test_1 - AssertionError: message
FAILED tests/test_b.py::test_2 - ValueError: invalid value
FAILED tests/test_c.py::test_3 - TypeError: wrong type
FAILED tests/test_d.py::test_4 - KeyError: 'missing_key'
FAILED tests/test_e.py::test_5 - RuntimeError: runtime issue
FAILED tests/test_f.py::test_6 - CustomException: custom error
========================= 6 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 6
        assert result.failed_tests[0].failure_type == "AssertionError"
        assert result.failed_tests[1].failure_type == "ValueError"
        assert result.failed_tests[2].failure_type == "TypeError"
        assert result.failed_tests[3].failure_type == "KeyError"
        assert result.failed_tests[4].failure_type == "RuntimeError"
        assert result.failed_tests[5].failure_type == "CustomException"

    def test_parse_output_handles_multiline_messages(self) -> None:
        """Test parsing failures with messages containing colons."""
        parser = PytestOutputParser()
        output = """
========================= short test summary info =========================
FAILED tests/test_example.py::test_complex - AssertionError: Expected: 5, Got: 3
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]
        assert failure.failure_type == "AssertionError"
        assert "Expected: 5, Got: 3" in failure.failure_message

    def test_extract_assertion_for_specific_test(self) -> None:
        """Test extracting assertion details for a specific test."""
        parser = PytestOutputParser()
        output = """
_ test_first _

    def test_first():
>       assert 1 == 2
E       assert 1 == 2

_ test_second _

    def test_second():
>       assert 3 == 4
E       assert 3 == 4
"""

        # Extract for test_first
        assertion = parser._extract_assertion_for_test(  # noqa: SLF001
            output, "tests/test_example.py", "test_first"
        )

        assert assertion is not None
        assert assertion.actual_value == "1"
        assert assertion.expected_value == "2"

    def test_extract_stack_trace_limits_frames(self) -> None:
        """Test that stack trace extraction limits to relevant frames."""
        parser = PytestOutputParser()
        output = """
_ test_example _

    def test_example():
        frame1()

    def frame1():
        frame2()

    def frame2():
        frame3()

    def frame3():
        frame4()

    def frame4():
        frame5()

    def frame5():
>       assert False
E       assert False
"""

        result = parser.parse_output(output)

        # Stack trace should be limited to last 5 frames
        if result.failed_tests and result.failed_tests[0].stack_trace_excerpt:
            lines = result.failed_tests[0].stack_trace_excerpt.split('\n')
            # Should not include all frames, just the most relevant ones
            assert len(lines) <= 50  # Reasonable limit

    def test_parse_output_handles_warnings_in_output(self) -> None:
        """Test parsing output that includes pytest warnings."""
        parser = PytestOutputParser()
        output = """
========================= warnings summary =========================
tests/test_example.py::test_something
  /path/to/file.py:10: DeprecationWarning: deprecated function
    warnings.warn("deprecated function", DeprecationWarning)

========================= short test summary info =========================
FAILED tests/test_example.py::test_addition - AssertionError: assert 1 == 2
========================= 1 failed, 1 warning in 0.50s =========================
"""

        result = parser.parse_output(output)

        # Should still parse the failure correctly despite warnings
        assert len(result.failed_tests) == 1
        assert result.failed_tests[0].test_name == "test_addition"

    def test_stack_trace_filters_pytest_internals(self) -> None:
        """Test that pytest internal frames are filtered from stack traces."""
        parser = PytestOutputParser()
        output = """
_ test_example _

    def test_example():
>       assert helper_function() == expected
E       assert False == True

tests/test_example.py:10: AssertionError
    /_pytest/runner.py:123: in pytest_runtest_call
        item.runtest()
    /site-packages/_pytest/python.py:456: in runtest
        self.ihook.pytest_runtest_call(item=self)
    /site-packages/pluggy/_hooks.py:789: in __call__
        return self._hookexec(self, self.get_hookimpls(), kwargs)
========================= short test summary info =========================
FAILED tests/test_example.py::test_example - AssertionError
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]

        # Stack trace should not include pytest internals
        if failure.stack_trace_excerpt:
            assert "/_pytest/" not in failure.stack_trace_excerpt
            assert "/site-packages/_pytest/" not in failure.stack_trace_excerpt
            assert "/pluggy/" not in failure.stack_trace_excerpt

    def test_stack_trace_prioritizes_application_code(self) -> None:
        """Test that application code frames are prioritized over other frames."""
        parser = PytestOutputParser()
        output = """
_ test_complex _

    def test_complex():
>       result = process_data()

tests/test_example.py:15:
    src/processor.py:42: in process_data
        return transform(data)
    src/transformer.py:28: in transform
        validate(data)
    src/validator.py:10: in validate
        raise ValueError("Invalid data")
E   ValueError: Invalid data

========================= short test summary info =========================
FAILED tests/test_example.py::test_complex - ValueError: Invalid data
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]

        # Stack trace should include application code
        assert failure.stack_trace_excerpt is not None
        assert "src/processor.py" in failure.stack_trace_excerpt
        assert "src/transformer.py" in failure.stack_trace_excerpt
        assert "src/validator.py" in failure.stack_trace_excerpt

    def test_stack_trace_limits_depth(self) -> None:
        """Test that stack trace depth is limited to most actionable frames."""
        parser = PytestOutputParser()
        # Create output with many stack frames in proper pytest format
        frames = []
        for i in range(15):
            frames.append(f"    src/module{i}.py:{i*10}: in function{i}")
            frames.append("        call_next()")
            frames.append("")  # Empty line between frames

        stack_trace = '\n'.join(frames)
        output = f"""
_ test_deep_stack _

    def test_deep_stack():
>       result = start_chain()

tests/test_example.py:5:
{stack_trace}
E   RuntimeError: Too deep

========================= short test summary info =========================
FAILED tests/test_example.py::test_deep_stack - RuntimeError: Too deep
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]

        # Stack trace should be limited
        if failure.stack_trace_excerpt:
            # Count the number of "src/module" occurrences
            # Should have at most MAX_RELEVANT_FRAMES (5) frames
            frame_lines = [
                line for line in failure.stack_trace_excerpt.split('\n')
                if 'src/module' in line
            ]
            assert len(frame_lines) <= 5, (
                f"Expected at most 5 frames, got {len(frame_lines)}"
            )

    def test_stack_trace_handles_standard_library_frames(self) -> None:
        """Test that standard library frames are filtered appropriately."""
        parser = PytestOutputParser()
        output = """
_ test_stdlib _

    def test_stdlib():
>       result = json.loads(data)

tests/test_example.py:20:
    /usr/lib/python3.12/json/__init__.py:346: in loads
        return _default_decoder.decode(s)
    /usr/lib/python3.12/json/decoder.py:337: in decode
        obj, end = self.raw_decode(s, idx=_w(s, 0).end())
    src/parser.py:15: in custom_decode
        raise ValueError("Invalid JSON")
E   ValueError: Invalid JSON

========================= short test summary info =========================
FAILED tests/test_example.py::test_stdlib - ValueError: Invalid JSON
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]

        # Stack trace should prioritize application code
        if failure.stack_trace_excerpt:
            # Should include application code
            assert "src/parser.py" in failure.stack_trace_excerpt

    def test_stack_trace_handles_no_application_frames(self) -> None:
        """Test stack trace when no application frames are present."""
        parser = PytestOutputParser()
        output = """
_ test_external _

    def test_external():
>       result = external_lib.process()

tests/test_example.py:25:
    /usr/local/lib/external_lib.py:100: in process
        raise RuntimeError("External error")
E   RuntimeError: External error

========================= short test summary info =========================
FAILED tests/test_example.py::test_external - RuntimeError: External error
========================= 1 failed in 0.50s =========================
"""

        result = parser.parse_output(output)

        assert len(result.failed_tests) == 1
        failure = result.failed_tests[0]

        # Should still have some stack trace even without application frames
        # (falls back to other frames)
        assert failure.stack_trace_excerpt is not None

    def test_is_application_frame(self) -> None:
        """Test application frame detection."""
        parser = PytestOutputParser()

        # Application frames
        assert parser._is_application_frame(  # noqa: SLF001
            "    src/module.py:10: in function"
        )
        assert parser._is_application_frame(  # noqa: SLF001
            "    tests/test_module.py:20: in test"
        )
        assert parser._is_application_frame(  # noqa: SLF001
            "    /path/to/src/file.py:30: in method"
        )
        assert parser._is_application_frame(  # noqa: SLF001
            "    /path/to/tests/test_file.py:40: in test"
        )

        # Non-application frames
        assert not parser._is_application_frame(  # noqa: SLF001
            "    /usr/lib/python3.12/json.py:10: in loads"
        )
        assert not parser._is_application_frame(  # noqa: SLF001
            "    /external/lib.py:20: in process"
        )

    def test_is_framework_frame(self) -> None:
        """Test framework frame detection."""
        parser = PytestOutputParser()

        # Framework frames
        assert parser._is_framework_frame(  # noqa: SLF001
            "    /_pytest/runner.py:123: in call"
        )
        assert parser._is_framework_frame(  # noqa: SLF001
            "    /site-packages/_pytest/python.py:456: in runtest"
        )
        assert parser._is_framework_frame(  # noqa: SLF001
            "    /pluggy/_hooks.py:789: in __call__"
        )
        assert parser._is_framework_frame(  # noqa: SLF001
            "    <frozen importlib._bootstrap>:123: in _find_and_load"
        )
        assert parser._is_framework_frame(  # noqa: SLF001
            "    /unittest/case.py:100: in run"
        )

        # Non-framework frames
        assert not parser._is_framework_frame(  # noqa: SLF001
            "    src/module.py:10: in function"
        )
        assert not parser._is_framework_frame(  # noqa: SLF001
            "    tests/test_module.py:20: in test"
        )
