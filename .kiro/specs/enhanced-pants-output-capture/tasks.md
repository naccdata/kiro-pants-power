# Implementation Plan: Enhanced Pants Output Capture

## CRITICAL EXECUTION RULE

**ALL Python commands MUST use `uv run` prefix**

When implementing tasks, ALL test execution and Python script commands MUST be prefixed with `uv run`:
- ✅ CORRECT: `uv run pytest tests/unit/test_models.py -v`
- ❌ WRONG: `pytest tests/unit/test_models.py -v`
- ✅ CORRECT: `uv run python src/server.py`
- ❌ WRONG: `python src/server.py`

This ensures consistent dependency resolution and environment isolation. Do NOT skip this prefix.

## Overview

This implementation refactors the kiro-pants-power output capture system to provide structured data extraction and enhanced error diagnostics. The implementation will add parsing capabilities for JUnit XML, coverage reports, MyPy output, pytest output, and Pants configuration files, while maintaining backward compatibility with existing code.

## Tasks

- [x] 1. Create core data models and types
  - Create new data model classes in src/models.py for all structured output types
  - Add TestResults, TestFailure, PytestResults, PytestFailure, AssertionFailure models
  - Add CoverageData, FileCoverage models
  - Add TypeCheckResults, TypeCheckError models
  - Add SandboxInfo, Configuration, ValidationError models
  - Add ParsedOutput, EnhancedCommandResult, WorkflowProgress, EnhancedWorkflowResult models
  - _Requirements: 1.6, 2.5, 3.5, 4.5, 10.6, 11.1_

- [ ]* 1.1 Write property test for data model completeness
  - Verify all required fields exist on each model class
  - _Requirements: 1.6, 2.5, 3.5_

- [x] 2. Implement OutputBuffer for output capture
  - Create src/output_buffer.py with OutputBuffer class
  - Implement append_line() to buffer stdout/stderr with stream tracking
  - Implement get_complete_output() to return separated stdout/stderr
  - Implement get_interleaved_output() to preserve chronological order
  - _Requirements: 8.2, 8.3_

- [ ]* 2.1 Write property test for output ordering preservation
  - **Property 16: Output Ordering Preservation**
  - **Validates: Requirements 8.2**

- [ ]* 2.2 Write property test for streaming buffer completeness
  - **Property 17: Streaming Buffer Completeness**
  - **Validates: Requirements 8.3**

- [x] 3. Implement JUnit XML parser
  - Create src/parsers/junit_parser.py with JUnitXMLParser class
  - Implement parse_single_report() to parse one JUnit XML file
  - Implement parse_reports() to parse all XML files in directory
  - Extract test case names, status, execution time, failure messages
  - Handle malformed XML gracefully with error logging
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 3.1 Write property test for JUnit XML parsing completeness
  - **Property 1: JUnit XML Parsing Completeness**
  - **Validates: Requirements 1.2, 1.3, 1.6**

- [ ]* 3.2 Write property test for JUnit XML aggregation correctness
  - **Property 2: JUnit XML Aggregation Correctness**
  - **Validates: Requirements 1.5**

- [ ]* 3.3 Write unit tests for JUnit XML parser edge cases
  - Test empty test suites, nested test cases, missing fields
  - _Requirements: 1.2, 1.3_

- [x] 4. Implement coverage report parser
  - Create src/parsers/coverage_parser.py with CoverageReportParser class
  - Implement parse_coverage() with auto-detection of JSON vs XML format
  - Implement parse_json_coverage() for JSON coverage reports
  - Implement parse_xml_coverage() for XML (Cobertura) coverage reports
  - Extract overall coverage percentage, per-file metrics, uncovered line ranges
  - Handle missing coverage data gracefully
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

- [ ]* 4.1 Write property test for coverage report parsing completeness
  - **Property 4: Coverage Report Parsing Completeness**
  - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**

- [ ]* 4.2 Write unit tests for coverage parser edge cases
  - Test 0% coverage, 100% coverage, empty reports, missing files
  - _Requirements: 2.2, 2.3, 2.6_

- [x] 5. Implement MyPy output parser
  - Create src/parsers/mypy_parser.py with MyPyOutputParser class
  - Implement parse_output() to extract type errors from console output
  - Implement extract_error_line() to parse individual MyPy error lines
  - Extract file path, line number, column, error code, error message
  - Aggregate errors by file
  - Preserve MyPy report file paths when available
  - _Requirements: 3.1, 3.2, 3.4, 3.6_

- [ ]* 5.1 Write property test for MyPy error extraction completeness
  - **Property 5: MyPy Error Extraction Completeness**
  - **Validates: Requirements 3.1, 3.2, 3.5**

- [ ]* 5.2 Write property test for MyPy error aggregation by file
  - **Property 6: MyPy Error Aggregation by File**
  - **Validates: Requirements 3.4**

- [ ]* 5.3 Write property test for MyPy report path preservation
  - **Property 7: MyPy Report Path Preservation**
  - **Validates: Requirements 3.6, 5.5**

- [x] 6. Implement sandbox path extractor
  - Create src/parsers/sandbox_extractor.py with SandboxPathExtractor class
  - Implement extract_sandboxes() to find all sandbox preservation messages
  - Implement extract_sandbox_line() to parse individual log lines
  - Extract sandbox path and process description
  - Handle both --keep-sandboxes=always and on_failure modes
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ]* 6.1 Write property test for sandbox path extraction completeness
  - **Property 8: Sandbox Path Extraction Completeness**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [x] 7. Implement pytest output parser
  - Create src/parsers/pytest_parser.py with PytestOutputParser class
  - Implement parse_output() to extract pytest failures
  - Implement extract_failure_summary() to parse FAILED test lines
  - Implement extract_assertion_details() to parse assertion failures
  - Extract test name, failure type, failure message, assertion details
  - Extract relevant stack trace frames (filter framework internals)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 7.1 Write property test for pytest failure extraction
  - **Property 21: Pytest Failure Extraction**
  - **Validates: Requirements 10.1, 10.2**

- [ ]* 7.2 Write property test for pytest assertion detail extraction
  - **Property 22: Pytest Assertion Detail Extraction**
  - **Validates: Requirements 10.3**

- [ ]* 7.3 Write property test for pytest failure type identification
  - **Property 24: Pytest Failure Type Identification**
  - **Validates: Requirements 10.5**

- [x] 8. Checkpoint - Ensure all parser tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement configuration parser and pretty printer
  - Create src/parsers/config_parser.py with ConfigurationParser class
  - Implement parse_config() to parse pants.toml files
  - Implement validate_config() to check against Pants schema
  - Create src/formatters/config_formatter.py with ConfigurationPrettyPrinter class
  - Implement format_config() to convert Configuration back to TOML
  - Implement preserve_comments() to maintain comments during formatting
  - Handle invalid TOML with descriptive error messages including line numbers
  - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6_

- [ ]* 9.1 Write property test for configuration parsing validity
  - **Property 26: Configuration Parsing Validity**
  - **Validates: Requirements 11.1**

- [ ]* 9.2 Write property test for configuration formatting validity
  - **Property 28: Configuration Formatting Validity**
  - **Validates: Requirements 11.3**

- [ ]* 9.3 Write property test for configuration round-trip preservation
  - **Property 29: Configuration Round-Trip Preservation**
  - **Validates: Requirements 11.4**

- [ ]* 9.4 Write property test for configuration comment preservation
  - **Property 30: Configuration Comment Preservation**
  - **Validates: Requirements 11.5**

- [ ]* 9.5 Write property test for configuration schema validation
  - **Property 31: Configuration Schema Validation**
  - **Validates: Requirements 11.6**

- [x] 10. Implement enhanced error formatter
  - Create src/formatters/enhanced_error_formatter.py with EnhancedErrorFormatter class
  - Implement format_test_failures() to format test failure summaries
  - Implement format_type_errors() to format type checking error summaries
  - Implement format_coverage_summary() to format coverage metrics
  - Implement format_error_summary() to create complete error diagnostics
  - Include error type categorization (test failure, type error, execution error)
  - Limit error detail output to most relevant information (configurable N errors per category)
  - Include sandbox paths when available
  - _Requirements: 1.4, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ]* 10.1 Write property test for test failure formatting completeness
  - **Property 9: Test Failure Formatting Completeness**
  - **Validates: Requirements 1.4, 6.3**

- [ ]* 10.2 Write property test for type error formatting completeness
  - **Property 10: Type Error Formatting Completeness**
  - **Validates: Requirements 3.3, 6.4**

- [ ]* 10.3 Write property test for sandbox path inclusion in error output
  - **Property 11: Sandbox Path Inclusion in Error Output**
  - **Validates: Requirements 4.4, 6.6**

- [ ]* 10.4 Write property test for error summary structure
  - **Property 12: Error Summary Structure**
  - **Validates: Requirements 6.1, 6.2**

- [ ]* 10.5 Write property test for error detail limiting
  - **Property 13: Error Detail Limiting**
  - **Validates: Requirements 6.5**

- [ ]* 10.6 Write property test for pytest failure formatting completeness
  - **Property 25: Pytest Failure Formatting Completeness**
  - **Validates: Requirements 10.6**

- [x] 11. Implement parser router
  - Create src/parsers/parser_router.py with ParserRouter class
  - Implement parse_command_output() to coordinate all parsers
  - Implement get_parsers_for_command() to determine which parsers to use
  - Route test commands to JUnit, coverage, and pytest parsers
  - Route check commands to MyPy parser
  - Route all commands to sandbox extractor
  - Handle parsing errors gracefully with fallback to raw output
  - Log parsing errors and include in ParsedOutput.parsing_errors
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ]* 11.1 Write property test for report file detection
  - **Property 3: Report File Detection**
  - **Validates: Requirements 1.1, 2.1**

- [ ]* 11.2 Write property test for parsing error graceful handling
  - **Property 14: Parsing Error Graceful Handling**
  - **Validates: Requirements 7.1, 7.3, 7.4, 7.5**

- [ ]* 11.3 Write property test for parsing error transparency
  - **Property 15: Parsing Error Transparency**
  - **Validates: Requirements 7.6**

- [ ]* 11.4 Write unit tests for parser router coordination
  - Test parser selection logic, error aggregation, fallback behavior
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 12. Checkpoint - Ensure all parsing and formatting tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Enhance PantsCommands with parsing integration
  - Modify src/pants_commands.py to integrate parsing capabilities
  - Add parser_router and formatter as optional dependencies to __init__
  - Update pants_test() to configure --test-report and --use-coverage flags
  - Update pants_test() to parse JUnit XML and coverage reports after execution
  - Update pants_check() to parse MyPy errors after execution
  - Update all command methods to extract sandbox paths
  - Return EnhancedCommandResult with parsed_output and formatted_summary
  - Maintain backward compatibility with existing CommandResult interface
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 8.5_

- [ ]* 13.1 Write property test for post-execution parsing
  - **Property 18: Post-Execution Parsing**
  - **Validates: Requirements 8.5**

- [ ]* 13.2 Write property test for coverage flag configuration
  - **Property 32: Coverage Flag Configuration**
  - **Validates: Requirements 5.2**

- [ ]* 13.3 Write integration tests for enhanced pants commands
  - Test complete pipeline: execution → parsing → formatting
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 14. Enhance WorkflowOrchestrator with progress tracking
  - Modify src/workflow_orchestrator.py to add progress tracking
  - Add progress_callback parameter to execute_workflow()
  - Track completion status of each workflow step
  - Report step completion with timing information
  - Create workflow summary showing completed steps and failure point
  - Include enhanced diagnostics for failed steps
  - Return EnhancedWorkflowResult with step_timings and workflow_summary
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ]* 14.1 Write property test for workflow step tracking
  - **Property 19: Workflow Step Tracking**
  - **Validates: Requirements 9.1, 9.2, 9.3**

- [ ]* 14.2 Write property test for workflow summary completeness
  - **Property 20: Workflow Summary Completeness**
  - **Validates: Requirements 9.4, 9.5, 9.6**

- [ ]* 14.3 Write integration tests for enhanced workflow orchestrator
  - Test multi-step workflows with progress callbacks
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 15. Update command executor for streaming with buffering
  - Modify src/command_executor.py to integrate OutputBuffer
  - Update execute_with_streaming() to use OutputBuffer for dual capture
  - Ensure streaming output is preserved for final parsing
  - Maintain existing streaming behavior for backward compatibility
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 15.1 Write unit tests for command executor streaming
  - Test streaming mode with output buffering
  - _Requirements: 8.1, 8.3_

- [x] 16. Create Hypothesis test data generators
  - Create tests/property/generators.py with custom Hypothesis strategies
  - Implement valid_junit_xml() strategy for generating JUnit XML
  - Implement valid_coverage_json() and valid_coverage_xml() strategies
  - Implement valid_mypy_output() strategy for MyPy error output
  - Implement valid_pytest_output() strategy for pytest output
  - Implement valid_pants_config() strategy for TOML configuration
  - Implement invalid variants for error handling tests
  - _Requirements: All property tests_

- [x] 17. Checkpoint - Ensure all integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Add pytest stack trace filtering
  - Update src/parsers/pytest_parser.py to filter stack traces
  - Implement logic to exclude framework internals from stack traces
  - Keep only relevant application code frames
  - Limit stack trace depth to most actionable information
  - _Requirements: 10.4_

- [ ]* 18.1 Write property test for pytest stack trace filtering
  - **Property 23: Pytest Stack Trace Filtering**
  - **Validates: Requirements 10.4**

- [x] 19. Update existing formatters for compatibility
  - Review src/formatters.py for compatibility with enhanced error formatter
  - Ensure existing format_command_execution_error() works with EnhancedCommandResult
  - Add fallback logic to use enhanced formatting when available
  - Maintain backward compatibility with existing error formatting
  - _Requirements: 6.1, 6.2_

- [x] 20. Add configuration for parser behavior
  - Add parser configuration options to PowerConfig in src/server.py
  - Add report_output_dir configuration for report file locations
  - Add max_errors_per_category for error detail limiting
  - Add enable_verbose_parsing for detailed parsing error output
  - Add keep_sandboxes configuration option
  - _Requirements: 5.1, 5.2, 5.3, 5.6, 6.5, 7.6_

- [x] 21. Create test fixtures for integration tests
  - Create tests/fixtures/sample_junit_reports/ with example JUnit XML files
  - Create tests/fixtures/sample_coverage_reports/ with JSON and XML coverage reports
  - Create tests/fixtures/sample_mypy_output/ with example MyPy error output
  - Create tests/fixtures/sample_pants_logs/ with sandbox preservation messages
  - Create tests/fixtures/sample_configs/ with valid and invalid pants.toml files
  - Create tests/fixtures/sample_pytest_output/ with pytest failure output
  - _Requirements: All integration tests_

- [x] 22. Final checkpoint - Run full test suite
  - Run all unit tests, property tests, and integration tests
  - Verify > 90% line coverage
  - Verify all 32 correctness properties pass
  - Ensure backward compatibility with existing code
  - Ask the user if questions arise.

## Notes

- **CRITICAL**: ALL Python commands MUST use `uv run` prefix (e.g., `uv run pytest`, NOT `pytest`)
- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (32 total)
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end functionality
- Backward compatibility is maintained throughout the refactor
- All parsers implement graceful error handling with fallback to raw output
