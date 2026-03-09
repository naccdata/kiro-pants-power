# Requirements Document

## Introduction

This document specifies requirements for an intent-based API layer for kiro-pants-power. Instead of exposing Pants target syntax to AI agents, the system provides a clear, intent-driven interface where agents specify what they want to test using simple scopes and paths. The system internally maps these intents to appropriate Pants target specifications, validates paths, and provides helpful error messages. This approach hides the complexity of Pants target syntax while maintaining full testing power.

## Glossary

- **Intent_Mapper**: Component that translates user intents (scope + path) into Pants target specifications
- **Path_Validator**: Component that verifies file and directory paths exist and contain testable code
- **Error_Translator**: Component that converts Pants error messages into intent-based guidance
- **Test_Scope**: High-level description of what to test (all, directory, file, function)
- **Pants_Command**: Any of the core Pants operations (fix, lint, check, test, package, tailor)
- **BUILD_File**: Pants configuration file defining targets in a directory
- **Agent**: AI system using the kiro-pants-power tools to execute Pants commands
- **Tool_Schema**: JSON schema describing tool parameters and usage for AI agents
- **Test_Filter**: Pattern to select specific test functions within a scope

## Requirements

### Requirement 1: Intent-Based Test Scope API

**User Story:** As an Agent, I want to specify what to test using clear intent parameters, so that I can focus on my testing goals without learning Pants target syntax.

#### Acceptance Criteria

1. THE Tool_Schema SHALL provide a "scope" parameter accepting values: "all", "directory", "file"
2. WHEN scope is "all", THE Intent_Mapper SHALL map the intent to Pants target "::" (all tests recursively)
3. WHEN scope is "directory", THE Intent_Mapper SHALL require a "path" parameter and map to "path::" or "path:" based on recursive flag
4. WHEN scope is "file", THE Intent_Mapper SHALL require a "path" parameter and map to the file path directly
5. THE Tool_Schema SHALL provide a "recursive" boolean parameter (default true) for directory scope to control subdirectory inclusion

### Requirement 2: Path Validation

**User Story:** As an Agent, I want paths validated before execution, so that I receive clear feedback when paths don't exist or aren't testable.

#### Acceptance Criteria

1. WHEN a file path is provided, THE Path_Validator SHALL verify the file exists in the repository
2. WHEN a directory path is provided, THE Path_Validator SHALL verify the directory exists in the repository
3. WHEN a path does not exist, THE Path_Validator SHALL return an error message stating "Path does not exist: {path}"
4. WHEN a directory path is provided, THE Path_Validator SHALL check if a BUILD_File exists in that directory or parent directories
5. WHERE no BUILD_File exists for a directory, THE Path_Validator SHALL suggest running "pants tailor" to generate BUILD files

### Requirement 3: Intent-to-Target Mapping

**User Story:** As a developer, I want user intents automatically translated to correct Pants target syntax, so that the complexity of Pants addressing is hidden from agents.

#### Acceptance Criteria

1. THE Intent_Mapper SHALL translate scope "all" to Pants target "::"
2. WHEN scope is "directory" with recursive true, THE Intent_Mapper SHALL translate to "{path}::"
3. WHEN scope is "directory" with recursive false, THE Intent_Mapper SHALL translate to "{path}:"
4. WHEN scope is "file", THE Intent_Mapper SHALL translate to the file path as-is (Pants shorthand for generated targets)
5. THE Intent_Mapper SHALL handle root directory paths by translating empty path with scope "all" to "::"

### Requirement 4: Test Function Filtering

**User Story:** As an Agent, I want to filter tests by function name, so that I can run specific tests within a broader scope.

#### Acceptance Criteria

1. THE Tool_Schema SHALL provide a "test_filter" parameter accepting a test name pattern
2. WHEN test_filter is provided, THE Intent_Mapper SHALL add the "-k {pattern}" option to the Pants command
3. THE Intent_Mapper SHALL support Pants native filter syntax including wildcards and boolean operators
4. THE Tool_Schema SHALL document that test_filter uses pytest-style filtering syntax
5. WHEN test_filter is combined with any scope, THE Intent_Mapper SHALL apply the filter to the resolved target specification

### Requirement 5: Enhanced Error Translation

**User Story:** As an Agent, I want Pants errors translated to intent-based language, so that I understand what went wrong in terms of my original request.

#### Acceptance Criteria

1. WHEN Pants returns "No targets found", THE Error_Translator SHALL return "No tests found in {scope} {path}"
2. WHEN Pants returns "Unknown target", THE Error_Translator SHALL return "Path contains no testable code: {path}"
3. WHEN Pants returns "BUILD file not found", THE Error_Translator SHALL return "Directory not configured for Pants. Run 'pants tailor' to set up BUILD files"
4. THE Error_Translator SHALL preserve the original Pants error in a "raw_error" field for debugging
5. WHEN an error cannot be translated, THE Error_Translator SHALL return a generic message with the original error included

### Requirement 6: Intent-Based Tool Documentation

**User Story:** As an Agent, I want tool documentation focused on testing intents, so that I can understand what I can accomplish without learning Pants internals.

#### Acceptance Criteria

1. THE Tool_Schema SHALL describe the "scope" parameter as "What to test: all tests, tests in a directory, or a specific file"
2. THE Tool_Schema SHALL provide examples using intent-based language: "Test everything", "Test a directory", "Test one file"
3. THE Tool_Schema SHALL explain the "recursive" parameter as "Include subdirectories when testing a directory"
4. THE Tool_Schema SHALL document the "test_filter" parameter as "Run only tests matching this name pattern"
5. THE Tool_Schema SHALL avoid mentioning Pants target syntax, BUILD files, or target generators in primary documentation

### Requirement 7: BUILD File Detection and Guidance

**User Story:** As an Agent, I want helpful guidance when BUILD files are missing, so that I can set up the repository correctly.

#### Acceptance Criteria

1. WHEN a directory path is provided without a BUILD_File, THE Path_Validator SHALL detect the missing BUILD_File
2. THE Path_Validator SHALL return an error message: "No BUILD file found for {path}. Run 'pants tailor' to generate BUILD files"
3. WHERE the repository root has no BUILD files, THE Path_Validator SHALL suggest running "pants tailor" at the repository root
4. THE Path_Validator SHALL check parent directories for BUILD files to determine if the path is within a Pants-managed area
5. WHEN BUILD files exist in parent directories, THE Path_Validator SHALL accept the path as valid

### Requirement 8: Smart Default Behavior

**User Story:** As an Agent, I want sensible defaults when I don't specify all parameters, so that I can run tests quickly with minimal configuration.

#### Acceptance Criteria

1. WHEN no scope is provided, THE Intent_Mapper SHALL default to scope "all"
2. WHEN scope is "directory" without a path, THE Intent_Mapper SHALL default to the current working directory
3. WHEN scope is "directory" without recursive flag, THE Intent_Mapper SHALL default recursive to true
4. THE Intent_Mapper SHALL log the resolved intent (scope, path, recursive, filter) for transparency
5. WHEN scope is "file" without a path, THE Intent_Mapper SHALL return an error requiring a path parameter

### Requirement 9: Path Resolution Performance

**User Story:** As an Agent, I want path validation to be fast, so that it doesn't significantly slow down test execution.

#### Acceptance Criteria

1. THE Path_Validator SHALL complete file existence checks within 10ms for any single path
2. THE Path_Validator SHALL complete directory existence checks within 10ms for any single path
3. THE Path_Validator SHALL complete BUILD_File detection within 50ms by checking up to 5 parent directories
4. WHERE BUILD_File detection requires filesystem traversal, THE Path_Validator SHALL cache results for 60 seconds
5. WHEN validation takes longer than 100ms, THE Path_Validator SHALL log a performance warning

### Requirement 10: Configuration Options

**User Story:** As a developer, I want to configure intent-based API behavior, so that I can customize the system for my workflow.

#### Acceptance Criteria

1. THE Intent_Mapper SHALL support a configuration option to enable/disable path validation
2. THE Intent_Mapper SHALL support a configuration option to enable/disable BUILD_File checking
3. THE Intent_Mapper SHALL support a configuration option to enable/disable error translation
4. WHERE path validation is disabled, THE Intent_Mapper SHALL pass paths directly to Pants without checking
5. WHERE error translation is disabled, THE Error_Translator SHALL return original Pants errors unchanged
