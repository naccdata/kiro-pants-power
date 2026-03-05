"""Hypothesis test data generators for property-based testing.

This module provides custom Hypothesis strategies for generating test data
for all parsers and formatters in the enhanced Pants output capture system.
"""

from hypothesis import strategies as st

# ============================================================================
# JUnit XML Generators
# ============================================================================

@st.composite
def valid_junit_xml(draw: st.DrawFn) -> str:
    """Generate valid JUnit XML test report.

    Generates a complete JUnit XML document with random test suites,
    test cases, and results (pass/fail/skip).

    Returns:
        Valid JUnit XML string
    """
    import html

    # Character set for identifiers
    id_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='._-'
    )
    # Character set for text content
    text_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z')
    )

    # Generate test suite attributes
    suite_name = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
    test_count = draw(st.integers(min_value=0, max_value=20))

    # Generate test cases
    test_cases = []
    pass_count = 0
    fail_count = 0
    skip_count = 0
    total_time = 0.0

    for _ in range(test_count):
        test_name = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
        test_class = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
        file_chars = st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/._'
        )
        test_file = draw(st.text(min_size=1, max_size=50, alphabet=file_chars))
        test_file += '.py'
        test_time = draw(st.floats(min_value=0.0, max_value=10.0))
        total_time += test_time

        # Randomly choose test status
        status = draw(st.sampled_from(['pass', 'fail', 'skip']))

        if status == 'pass':
            pass_count += 1
            test_cases.append(
                f'    <testcase name="{html.escape(test_name)}" '
                f'classname="{html.escape(test_class)}" '
                f'file="{html.escape(test_file)}" time="{test_time:.3f}"/>'
            )
        elif status == 'fail':
            fail_count += 1
            failure_type = draw(st.sampled_from([
                'AssertionError', 'ValueError', 'TypeError', 'KeyError'
            ]))
            failure_message = draw(
                st.text(min_size=1, max_size=100, alphabet=text_chars)
            )
            stack_trace = draw(
                st.text(min_size=0, max_size=200, alphabet=text_chars)
            )
            test_cases.append(
                f'    <testcase name="{html.escape(test_name)}" '
                f'classname="{html.escape(test_class)}" '
                f'file="{html.escape(test_file)}" time="{test_time:.3f}">\n'
                f'      <failure type="{html.escape(failure_type)}" '
                f'message="{html.escape(failure_message)}">'
                f'{html.escape(stack_trace)}</failure>\n'
                f'    </testcase>'
            )
        else:  # skip
            skip_count += 1
            skip_message = draw(
                st.text(min_size=0, max_size=100, alphabet=text_chars)
            )
            test_cases.append(
                f'    <testcase name="{html.escape(test_name)}" '
                f'classname="{html.escape(test_class)}" '
                f'file="{html.escape(test_file)}" time="{test_time:.3f}">\n'
                f'      <skipped message="{html.escape(skip_message)}"/>\n'
                f'    </testcase>'
            )

    # Build the complete XML
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="{html.escape(suite_name)}" tests="{test_count}" \
failures="{fail_count}" skipped="{skip_count}" time="{total_time:.3f}">
{chr(10).join(test_cases)}
</testsuite>'''

    return xml


@st.composite
def invalid_junit_xml(draw: st.DrawFn) -> str:
    """Generate invalid JUnit XML for error handling tests.

    Returns:
        Invalid JUnit XML string (malformed, missing tags, etc.)
    """
    error_types = {
        'malformed_xml': '<testsuite><testcase name="test" unclosed>',
        'missing_root': (
            '<?xml version="1.0"?>\n'
            '<testcase name="test"/><testcase name="test2"/>'
        ),
        'incomplete_tags': '<testsuite><testcase name="test">',
        'invalid_attributes': (
            '<testsuite><testcase name="test" invalid-attr-no-value/>'
            '</testsuite>'
        ),
        'truncated': '<testsuite name="test" tests="5"><testcase name="t1"',
    }

    error_type = draw(st.sampled_from(list(error_types.keys())))
    return error_types[error_type]


# ============================================================================
# Coverage Report Generators
# ============================================================================

@st.composite
def valid_coverage_json(draw: st.DrawFn) -> str:
    """Generate valid JSON coverage report.

    Generates a coverage.py JSON format report with random file coverage data.

    Returns:
        Valid JSON coverage report string
    """
    import json

    # Generate overall coverage
    total_coverage = draw(st.floats(min_value=0.0, max_value=100.0))

    # Generate file coverage data
    num_files = draw(st.integers(min_value=0, max_value=10))
    files = {}

    id_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='/._'
    )

    for _ in range(num_files):
        file_path = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
        file_path += '.py'

        total_lines = draw(st.integers(min_value=1, max_value=100))
        covered_lines = draw(st.integers(min_value=0, max_value=total_lines))

        # Generate missing lines
        all_lines = list(range(1, total_lines + 1))
        missing_count = total_lines - covered_lines
        missing_lines = (
            draw(st.lists(
                st.sampled_from(all_lines),
                min_size=missing_count,
                max_size=missing_count,
                unique=True
            )) if missing_count > 0 else []
        )

        coverage_percent = (
            (covered_lines / total_lines * 100.0) if total_lines > 0 else 0.0
        )

        files[file_path] = {
            "summary": {
                "covered_lines": covered_lines,
                "num_statements": total_lines,
                "percent_covered": coverage_percent
            },
            "missing_lines": sorted(missing_lines)
        }

    report = {
        "totals": {
            "percent_covered": total_coverage
        },
        "files": files
    }

    return json.dumps(report, indent=2)


@st.composite
def valid_coverage_xml(draw: st.DrawFn) -> str:
    """Generate valid XML (Cobertura) coverage report.

    Generates a Cobertura XML format coverage report with random file
    coverage data.

    Returns:
        Valid XML coverage report string
    """
    # Generate overall coverage (line-rate is 0.0 to 1.0)
    line_rate = draw(st.floats(min_value=0.0, max_value=1.0))

    # Generate file coverage data
    num_files = draw(st.integers(min_value=0, max_value=10))
    classes = []

    id_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='/._'
    )

    for i in range(num_files):
        filename = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
        filename += '.py'

        class_line_rate = draw(st.floats(min_value=0.0, max_value=1.0))
        num_lines = draw(st.integers(min_value=1, max_value=50))

        # Generate line coverage
        lines = []
        for line_num in range(1, num_lines + 1):
            hits = draw(st.integers(min_value=0, max_value=10))
            lines.append(
                f'        <line number="{line_num}" hits="{hits}"/>'
            )

        classes.append(
            f'      <class name="Class{i}" filename="{filename}" '
            f'line-rate="{class_line_rate:.2f}">\n'
            f'        <lines>\n'
            f'{chr(10).join(lines)}\n'
            f'        </lines>\n'
            f'      </class>'
        )

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<coverage line-rate="{line_rate:.2f}" version="1.0">
  <packages>
    <package name="src" line-rate="{line_rate:.2f}">
      <classes>
{chr(10).join(classes)}
      </classes>
    </package>
  </packages>
</coverage>'''

    return xml


@st.composite
def invalid_coverage_json(draw: st.DrawFn) -> str:
    """Generate invalid JSON coverage report for error handling tests.

    Returns:
        Invalid JSON coverage report string
    """
    error_types = {
        'malformed_json': '{"totals": {"percent_covered": 50.0}, "files": {',
        'missing_totals': '{"files": {}}',
        'invalid_structure': '{"totals": "not_an_object"}',
        'truncated': '{"totals": {"percent_cov',
    }

    error_type = draw(st.sampled_from(list(error_types.keys())))
    return error_types[error_type]


# ============================================================================
# MyPy Output Generators
# ============================================================================

@st.composite
def valid_mypy_output(draw: st.DrawFn) -> str:
    """Generate valid MyPy error output.

    Generates MyPy console output with random type checking errors.

    Returns:
        Valid MyPy output string
    """
    num_errors = draw(st.integers(min_value=0, max_value=20))
    error_lines = []

    id_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='/._'
    )

    for _ in range(num_errors):
        file_path = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
        file_path += '.py'
        line_number = draw(st.integers(min_value=1, max_value=1000))
        column = draw(st.integers(min_value=1, max_value=100))
        error_code = draw(st.sampled_from([
            'arg-type', 'return-value', 'assignment', 'call-arg',
            'attr-defined', 'name-defined', 'import', 'type-arg'
        ]))
        error_message = draw(st.text(min_size=10, max_size=100))

        error_lines.append(
            f'{file_path}:{line_number}:{column}: error: '
            f'{error_message}  [{error_code}]'
        )

    # Add summary line
    if num_errors > 0:
        unique_files = {line.split(":")[0] for line in error_lines}
        num_files = len(unique_files)
        error_lines.append(
            f'Found {num_errors} error{"s" if num_errors != 1 else ""} in '
            f'{num_files} file{"s" if num_files != 1 else ""}'
        )

    return '\n'.join(error_lines)


@st.composite
def valid_mypy_output_with_reports(draw: st.DrawFn) -> str:
    """Generate valid MyPy output with report file paths.

    Returns:
        MyPy output string including report generation messages
    """
    base_output = draw(valid_mypy_output())
    id_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='/._-'
    )
    report_path = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))

    report_type = draw(st.sampled_from(['HTML', 'XML']))
    report_line = f'Writing {report_type} report to {report_path}/'

    return f'{base_output}\n{report_line}'


@st.composite
def invalid_mypy_output(draw: st.DrawFn) -> str:
    """Generate invalid MyPy output for error handling tests.

    Returns:
        Invalid or malformed MyPy output string
    """
    error_types = {
        'missing_line_number': 'src/main.py: error: Something went wrong',
        'missing_error_code': 'src/main.py:42:10: error: Type error occurred',
        'invalid_format': 'This is not a valid mypy error line at all',
        'empty': '',
    }

    error_type = draw(st.sampled_from(list(error_types.keys())))
    return error_types[error_type]


# ============================================================================
# Pytest Output Generators
# ============================================================================

@st.composite
def valid_pytest_output(draw: st.DrawFn) -> str:
    """Generate valid pytest failure output.

    Generates pytest console output with test failures, including
    short test summary and detailed failure information.

    Returns:
        Valid pytest output string
    """
    num_failures = draw(st.integers(min_value=1, max_value=10))
    output_lines = []

    id_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='/._'
    )

    # Add header
    output_lines.append('=' * 70)
    output_lines.append('FAILURES')
    output_lines.append('=' * 70)

    # Generate detailed failure sections
    for _ in range(num_failures):
        test_file = draw(st.text(min_size=1, max_size=50, alphabet=id_chars))
        test_file += '.py'
        test_name = draw(st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='_'
            )
        ))

        output_lines.append(f'_ {test_name} _')
        output_lines.append('')

        # Add stack trace
        output_lines.append(f'    {test_file}:42: in {test_name}')

        # Add assertion failure
        failure_type = draw(st.sampled_from([
            'AssertionError', 'ValueError', 'TypeError', 'KeyError'
        ]))

        if failure_type == 'AssertionError':
            left_value = draw(st.integers(min_value=0, max_value=100))
            right_value = draw(st.integers(min_value=0, max_value=100))
            operator = draw(st.sampled_from(
                ['==', '!=', '<', '>', '<=', '>=']
            ))
            output_lines.append(
                f'E       assert {left_value} {operator} {right_value}'
            )
        else:
            error_message = draw(st.text(min_size=10, max_size=100))
            output_lines.append(f'E       {failure_type}: {error_message}')

        output_lines.append('')

    # Add short test summary
    output_lines.append('=' * 70)
    output_lines.append('short test summary info')
    output_lines.append('=' * 70)

    for i in range(num_failures):
        test_file = f'tests/test_file{i}.py'
        test_name = f'test_function_{i}'
        failure_type = draw(st.sampled_from([
            'AssertionError', 'ValueError', 'TypeError'
        ]))
        output_lines.append(
            f'FAILED {test_file}::{test_name} - {failure_type}'
        )

    output_lines.append('=' * 70)

    return '\n'.join(output_lines)


@st.composite
def invalid_pytest_output(draw: st.DrawFn) -> str:
    """Generate invalid pytest output for error handling tests.

    Returns:
        Invalid or incomplete pytest output string
    """
    error_types = {
        'missing_summary': (
            '=' * 70 + '\nFAILURES\n' + '=' * 70 +
            '\n_ test_something _\nE   AssertionError'
        ),
        'malformed_failed_line': 'FAILED this is not a valid format',
        'incomplete': '=' * 70 + '\nFAILURES\n',
        'empty': '',
    }

    error_type = draw(st.sampled_from(list(error_types.keys())))
    return error_types[error_type]


# ============================================================================
# Pants Configuration (TOML) Generators
# ============================================================================

@st.composite
def valid_pants_config(draw: st.DrawFn) -> str:
    """Generate valid Pants configuration (TOML).

    Generates a valid pants.toml configuration file with random sections
    and options.

    Returns:
        Valid TOML configuration string
    """
    config_lines = []

    # Add GLOBAL section
    config_lines.append('[GLOBAL]')
    version_chars = st.characters(
        whitelist_categories=['Nd'],
        whitelist_characters='.'
    )
    pants_version = draw(st.text(min_size=5, max_size=10, alphabet=version_chars))
    config_lines.append(f'pants_version = "{pants_version}"')

    # Add backend packages
    num_backends = draw(st.integers(min_value=1, max_value=5))
    backends = [
        'pants.backend.python',
        'pants.backend.python.lint.black',
        'pants.backend.python.lint.flake8',
        'pants.backend.python.typecheck.mypy',
        'pants.backend.shell'
    ]
    selected_backends = draw(st.lists(
        st.sampled_from(backends),
        min_size=num_backends,
        max_size=num_backends,
        unique=True
    ))
    config_lines.append('backend_packages = [')
    for backend in selected_backends:
        config_lines.append(f'  "{backend}",')
    config_lines.append(']')
    config_lines.append('')

    # Add optional sections
    if draw(st.booleans()):
        config_lines.append('[python]')
        interpreter_constraints = draw(st.sampled_from([
            '[">=3.8,<3.13"]',
            '[">=3.9"]',
            '["==3.11.*"]'
        ]))
        config_lines.append(f'interpreter_constraints = {interpreter_constraints}')
        config_lines.append('')

    if draw(st.booleans()):
        config_lines.append('[pytest]')
        config_lines.append('args = ["-v"]')
        config_lines.append('')

    if draw(st.booleans()):
        config_lines.append('[test]')
        config_lines.append('output = "failed"')
        config_lines.append('')

    return '\n'.join(config_lines)


@st.composite
def invalid_pants_config(draw: st.DrawFn) -> str:
    """Generate invalid Pants configuration for error handling tests.

    Returns:
        Invalid TOML configuration string
    """
    error_types = {
        'malformed_toml': '[GLOBAL]\npants_version = "2.0.0\n',
        'unclosed_bracket': (
            '[GLOBAL]\nbackend_packages = [\n  "pants.backend.python"'
        ),
        'invalid_syntax': '[GLOBAL]\npants_version == "2.0.0"',
        'duplicate_section': (
            '[GLOBAL]\npants_version = "2.0.0"\n'
            '[GLOBAL]\npants_version = "2.1.0"'
        ),
    }

    error_type = draw(st.sampled_from(list(error_types.keys())))
    return error_types[error_type]


# ============================================================================
# Composite Generators for Complex Scenarios
# ============================================================================

@st.composite
def junit_xml_with_all_statuses(draw: st.DrawFn) -> str:
    """Generate JUnit XML with at least one pass, fail, and skip.

    Returns:
        JUnit XML string with mixed test statuses
    """
    # Ensure we have at least one of each status
    test_cases = []

    # Add one passing test
    test_cases.append(
        '    <testcase name="test_pass" classname="TestClass" '
        'file="test.py" time="0.001"/>'
    )

    # Add one failing test
    test_cases.append(
        '    <testcase name="test_fail" classname="TestClass" '
        'file="test.py" time="0.002">\n'
        '      <failure type="AssertionError" message="Test failed">Stack trace</failure>\n'
        '    </testcase>'
    )

    # Add one skipped test
    test_cases.append(
        '    <testcase name="test_skip" classname="TestClass" '
        'file="test.py" time="0.000">\n'
        '      <skipped message="Skipped"/>\n'
        '    </testcase>'
    )

    # Add additional random tests
    num_additional = draw(st.integers(min_value=0, max_value=10))
    for i in range(num_additional):
        status = draw(st.sampled_from(['pass', 'fail', 'skip']))
        if status == 'pass':
            test_cases.append(
                f'    <testcase name="test_{i}" classname="TestClass" '
                f'file="test.py" time="0.001"/>'
            )
        elif status == 'fail':
            test_cases.append(
                f'    <testcase name="test_{i}" classname="TestClass" '
                f'file="test.py" time="0.001">\n'
                f'      <failure type="AssertionError" message="Failed">Trace</failure>\n'
                f'    </testcase>'
            )
        else:
            test_cases.append(
                f'    <testcase name="test_{i}" classname="TestClass" '
                f'file="test.py" time="0.001">\n'
                f'      <skipped message="Skipped"/>\n'
                f'    </testcase>'
            )

    total = len(test_cases)
    failures = sum(1 for tc in test_cases if '<failure' in tc)
    skipped = sum(1 for tc in test_cases if '<skipped' in tc)

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="TestSuite" tests="{total}" failures="{failures}" skipped="{skipped}" time="0.010">
{chr(10).join(test_cases)}
</testsuite>'''

    return xml


@st.composite
def mypy_output_multiple_files(draw: st.DrawFn) -> str:
    """Generate MyPy output with errors in multiple files.

    Returns:
        MyPy output string with errors across multiple files
    """
    num_files = draw(st.integers(min_value=2, max_value=5))
    error_lines = []

    for i in range(num_files):
        file_path = f'src/module{i}.py'
        num_errors_in_file = draw(st.integers(min_value=1, max_value=5))

        for _ in range(num_errors_in_file):
            line_number = draw(st.integers(min_value=1, max_value=100))
            column = draw(st.integers(min_value=1, max_value=80))
            error_code = draw(st.sampled_from(['arg-type', 'return-value', 'assignment']))
            error_message = draw(st.text(min_size=10, max_size=50))

            error_lines.append(
                f'{file_path}:{line_number}:{column}: error: {error_message}  [{error_code}]'
            )

    total_errors = len(error_lines)
    error_lines.append(f'Found {total_errors} errors in {num_files} files')

    return '\n'.join(error_lines)
