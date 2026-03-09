# Implementation Plan: Intent-Based API Layer for Pants Target Validation

## Overview

This implementation plan breaks down the intent-based API layer into manageable, testable tasks. The system provides a clear interface for AI agents to run Pants commands without understanding Pants target syntax. Implementation follows a 5-phase approach: core intent mapping, path validation, error translation, configuration/integration, and tool schema updates.

## Tasks

- [x] 1. Set up project structure and core data models
  - Create directory structure for the intent-based API layer
  - Define all data model classes (IntentContext, ResolvedIntent, MappingResult, ValidationResult, BuildFileResult, TranslatedError, TranslationRule, Configuration)
  - Set up testing framework with pytest and hypothesis
  - Create conftest.py with shared fixtures (mock_validator, temp_repo, default_config, sample_pants_errors)
  - _Requirements: All requirements (foundational)_

- [x] 2. Implement Intent_Mapper component
  - [x] 2.1 Create Intent_Mapper class with initialization
    - Implement __init__ method accepting Configuration and PathValidator
    - Implement resolve_defaults method for applying smart defaults
    - _Requirements: 8.1, 8.2, 8.3, 8.5_
  
  - [x] 2.2 Implement core scope-to-target mapping logic
    - Implement _map_scope_to_target method handling all scope types (all, directory, file)
    - Handle recursive flag for directory scope (:: vs :)
    - Handle root directory and empty path cases
    - _Requirements: 1.2, 1.3, 1.4, 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 2.3 Implement test filter handling
    - Implement _add_test_filter method to add -k option
    - Support pytest-style filter syntax (wildcards, boolean operators)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 2.4 Implement map_intent method
    - Integrate path validation, scope mapping, and test filter handling
    - Return MappingResult with target spec and additional options
    - Handle validation errors and intent errors
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 2.5 Write property tests for Intent_Mapper
    - **Property 1: Scope "all" maps to recursive target**
    - **Validates: Requirements 1.2, 3.1**
    - **Property 2: Directory scope with recursive maps correctly**
    - **Validates: Requirements 1.3, 3.2**
    - **Property 3: Directory scope without recursive maps correctly**
    - **Validates: Requirements 1.3, 3.3**
    - **Property 4: File scope maps to path directly**
    - **Validates: Requirements 1.4, 3.4**
    - **Property 9: Test filter adds -k option**
    - **Validates: Requirements 4.2, 4.3**
    - **Property 10: Test filter works with all scopes**
    - **Validates: Requirements 4.5**
  
  - [ ]* 2.6 Write unit tests for Intent_Mapper
    - Test specific examples (scope="all" → "::", directory with recursive, file paths)
    - Test edge cases (empty paths, root directory, special characters)
    - Test error conditions (file scope without path, invalid scope)
    - Test default value application
    - _Requirements: 1.2, 1.3, 1.4, 8.1, 8.2, 8.3, 8.5_

- [x] 3. Checkpoint - Ensure Intent_Mapper tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Path_Validator component
  - [x] 4.1 Create Path_Validator class with initialization
    - Implement __init__ method with Configuration and repo_root
    - Initialize BUILD file cache dictionary
    - Set up cache TTL configuration
    - _Requirements: 9.4_
  
  - [x] 4.2 Implement file and directory existence validation
    - Implement _file_exists and _directory_exists helper methods
    - Implement _validate_file method checking file existence
    - Implement _validate_directory method checking directory existence
    - Return appropriate ValidationResult with error messages
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 4.3 Implement BUILD file detection with caching
    - Implement check_build_file method with cache lookup
    - Implement _search_build_file method traversing parent directories
    - Search for BUILD, BUILD.pants, and BUILD.bazel files
    - Limit search to max_parent_directory_depth (default 5)
    - Cache results with timestamp for TTL-based invalidation
    - _Requirements: 2.4, 7.1, 7.4, 9.4_
  
  - [x] 4.4 Implement validate_path method
    - Handle scope="all" (no validation needed)
    - Validate file paths for scope="file"
    - Validate directory paths and BUILD files for scope="directory"
    - Return error with "pants tailor" suggestion when BUILD file missing
    - Accept paths with BUILD files in parent directories
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.2, 7.5_
  
  - [x] 4.5 Implement performance tracking and cache management
    - Add timing to validate_path_with_timing wrapper
    - Log performance warnings when validation exceeds thresholds
    - Implement clear_cache method for cache invalidation
    - Implement get_cache_stats for monitoring
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 4.6 Write property tests for Path_Validator
    - **Property 5: File validation detects existence**
    - **Validates: Requirements 2.1, 2.3**
    - **Property 6: Directory validation detects existence**
    - **Validates: Requirements 2.2, 2.3**
    - **Property 7: BUILD file detection searches parent directories**
    - **Validates: Requirements 2.4, 7.4**
    - **Property 8: Missing BUILD file suggests tailor**
    - **Validates: Requirements 2.5, 7.2**
    - **Property 16: Parent BUILD file validates path**
    - **Validates: Requirements 7.5**
    - **Property 21: BUILD file cache returns same result**
    - **Validates: Requirements 9.4**
  
  - [ ]* 4.7 Write unit tests for Path_Validator
    - Test file existence checking (existing and missing files)
    - Test directory existence checking (existing and missing directories)
    - Test BUILD file detection in current and parent directories
    - Test cache behavior (hits, misses, TTL expiration)
    - Test performance tracking and warnings
    - Test cache clearing and statistics
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.4, 7.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 5. Checkpoint - Ensure Path_Validator tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Error_Translator component
  - [x] 6.1 Create Error_Translator class with translation rules
    - Implement __init__ method with Configuration
    - Define TranslationRule data class with pattern, template, priority
    - Load DEFAULT_RULES for common Pants errors
    - Implement add_translation_rule method for custom rules
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 6.2 Implement pattern matching and rule application
    - Implement TranslationRule.matches method using regex
    - Implement TranslationRule.apply method with template formatting
    - Handle regex groups and intent context in templates
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 6.3 Implement translate_error method
    - Sort rules by priority (highest first)
    - Try each rule's pattern against Pants error
    - Apply first matching rule's template
    - Return generic message if no rule matches
    - Always preserve raw error in TranslatedError
    - Extract actionable suggestions (e.g., "pants tailor")
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 6.4 Write property tests for Error_Translator
    - **Property 11: Error translation for "No targets found"**
    - **Validates: Requirements 5.1**
    - **Property 12: Error translation for "Unknown target"**
    - **Validates: Requirements 5.2**
    - **Property 13: Error translation for "BUILD file not found"**
    - **Validates: Requirements 5.3**
    - **Property 14: Raw error preservation**
    - **Validates: Requirements 5.4**
    - **Property 15: Fallback translation for unknown errors**
    - **Validates: Requirements 5.5**
  
  - [ ]* 6.5 Write unit tests for Error_Translator
    - Test each default translation rule with specific examples
    - Test custom rule addition and priority ordering
    - Test fallback for unknown errors
    - Test raw error preservation in all cases
    - Test suggestion extraction
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Checkpoint - Ensure Error_Translator tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Configuration_Manager component
  - [x] 8.1 Create Configuration data class
    - Define all configuration fields with defaults
    - Implement from_file class method for YAML loading
    - Implement from_dict class method for dictionary loading
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 8.2 Create ConfigurationManager class
    - Implement __init__ with optional config file path
    - Implement _load_config method (file or defaults)
    - Implement get_config method
    - Implement update_config method for runtime changes
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 8.3 Implement configuration validation
    - Implement validate_configuration function checking all constraints
    - Validate cache TTL is non-negative
    - Validate max_parent_directory_depth is between 1 and 20
    - Validate timeout values are at least 1ms
    - Return list of validation errors
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 8.4 Add environment variable support
    - Support KIRO_PANTS_VALIDATE_PATHS environment variable
    - Support KIRO_PANTS_CHECK_BUILD_FILES environment variable
    - Support KIRO_PANTS_CACHE_TTL environment variable
    - Support KIRO_PANTS_TRANSLATE_ERRORS environment variable
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ]* 8.5 Write property tests for Configuration
    - **Property 22: Configuration disables path validation**
    - **Validates: Requirements 10.1, 10.4**
    - **Property 23: Configuration disables BUILD file checking**
    - **Validates: Requirements 10.2**
    - **Property 24: Configuration disables error translation**
    - **Validates: Requirements 10.3, 10.5**
  
  - [ ]* 8.6 Write unit tests for Configuration_Manager
    - Test configuration loading from file
    - Test configuration loading from dictionary
    - Test default configuration values
    - Test runtime configuration updates
    - Test environment variable overrides
    - Test configuration validation
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 9. Integrate all components and implement end-to-end flow
  - [x] 9.1 Implement map_intent_to_pants_command function
    - Integrate Intent_Mapper, Path_Validator, and Configuration
    - Implement complete flow: resolve intent → validate → map → add filter
    - Return target spec, additional options, and intent context
    - Handle ValidationError and IntentError exceptions
    - _Requirements: All requirements (integration)_
  
  - [x] 9.2 Implement execute_with_error_handling function
    - Wrap intent mapping and Pants execution
    - Catch and handle ValidationError, MappingError, PantsExecutionError
    - Use Error_Translator for Pants errors
    - Return standardized SuccessResponse or ErrorResponse
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 9.3 Add security measures
    - Implement sanitize_path function preventing directory traversal
    - Implement sanitize_test_filter function preventing command injection
    - Validate all user inputs before processing
    - _Requirements: All requirements (security)_
  
  - [ ]* 9.4 Write property tests for default resolution
    - **Property 17: Default scope is "all"**
    - **Validates: Requirements 8.1**
    - **Property 18: Default path for directory scope**
    - **Validates: Requirements 8.2**
    - **Property 19: Default recursive is true**
    - **Validates: Requirements 8.3**
    - **Property 20: File scope requires path**
    - **Validates: Requirements 8.5**
  
  - [ ]* 9.5 Write integration tests
    - Test end-to-end flow from intent to Pants command execution
    - Test error translation with real Pants errors
    - Test configuration changes affecting behavior
    - Test cache invalidation after pants tailor
    - Test all scope types with various path combinations
    - Test security measures (path traversal, command injection)
    - _Requirements: All requirements (integration)_

- [x] 10. Checkpoint - Ensure integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement monitoring and observability
  - [x] 11.1 Add structured logging
    - Implement log_intent_mapping function
    - Implement log_validation_performance function
    - Add logging at DEBUG, INFO, WARNING, and ERROR levels
    - _Requirements: 9.5_
  
  - [x] 11.2 Implement metrics collection
    - Create Metrics data class tracking key metrics
    - Implement record_validation, record_cache_hit, record_cache_miss methods
    - Implement get_cache_hit_rate and to_dict methods
    - Add global metrics instance and accessor functions
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 11.3 Write unit tests for monitoring
    - Test logging output for various scenarios
    - Test metrics collection and calculation
    - Test cache hit rate calculation
    - Test metrics export to dictionary
    - _Requirements: 9.5_

- [x] 12. Update tool schemas for all Pants commands
  - [x] 12.1 Create pants_test tool schema
    - Define scope, path, recursive, test_filter parameters
    - Write intent-based descriptions avoiding Pants internals
    - Add comprehensive examples for all scope types
    - _Requirements: 1.1, 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 12.2 Create unified schema for other Pants commands
    - Apply same intent-based parameters to pants_lint
    - Apply same intent-based parameters to pants_check
    - Apply same intent-based parameters to pants_fix
    - Apply same intent-based parameters to pants_format
    - Apply same intent-based parameters to pants_package
    - Remove command-specific parameters not applicable (e.g., test_filter for lint)
    - _Requirements: 1.1, 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 12.3 Add backward compatibility for legacy syntax
    - Support deprecated 'target' parameter with deprecation warning
    - Implement _execute_legacy_mode function
    - Implement _execute_intent_mode function
    - Document migration path from raw Pants syntax
    - _Requirements: All requirements (backward compatibility)_
  
  - [ ]* 12.4 Write unit tests for tool schemas
    - Test schema validation for all parameters
    - Test backward compatibility with legacy syntax
    - Test deprecation warnings
    - Test all example scenarios from schemas
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 13. Create custom hypothesis strategies for domain types
  - Create valid_file_paths strategy generating realistic file paths
  - Create valid_directory_paths strategy generating realistic directory paths
  - Create test_filter_patterns strategy generating pytest-style patterns
  - Create pants_errors strategy generating realistic Pants error messages
  - _Requirements: All requirements (testing infrastructure)_

- [x] 14. Final checkpoint and optimization
  - [x] 14.1 Run complete test suite
    - Run all unit tests with coverage reporting
    - Run all property tests with statistics
    - Run all integration tests
    - Verify coverage > 90%
    - _Requirements: All requirements_
  
  - [x] 14.2 Performance optimization
    - Profile validation performance
    - Optimize cache lookup and storage
    - Verify all performance targets met (< 10ms file check, < 50ms BUILD check)
    - Add performance tests for regression prevention
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 14.3 Documentation and examples
    - Write usage examples for all scope types
    - Document configuration options
    - Create migration guide from raw Pants syntax
    - Add troubleshooting guide
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, verify coverage goals met, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (24 properties total)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Implementation uses Python as specified in the design document
- All property tests must run with minimum 100 iterations
- Performance targets: file check < 10ms, directory check < 10ms, BUILD check < 50ms, overall validation < 100ms
- Security measures prevent path traversal and command injection attacks
