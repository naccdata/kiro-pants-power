# Implementation Plan: Pants DevContainer Power

## Overview

This implementation plan creates an MCP server that provides 15 tools for managing development workflows that use Pants build system within devcontainers. The power wraps Pants build system commands with automatic devcontainer execution using the devcontainer CLI directly, eliminating manual container management overhead.

The implementation follows a bottom-up approach: core utilities first, then command execution, then MCP tools, then workflows, and finally testing and documentation.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: src/, tests/unit/, tests/property/, tests/integration/
  - Create power.json manifest with tool definitions
  - Create pyproject.toml with dependencies: mcp, hypothesis, pytest
  - Create uv.lock for reproducible builds
  - Create .config.kiro with spec metadata
  - _Requirements: 8.1, 8.4_

- [x] 2. Implement core data models
  - [x] 2.1 Create CommandResult dataclass
    - Implement CommandResult with exit_code, stdout, stderr, command, success fields
    - Implement output property combining stdout and stderr
    - _Requirements: 5.4, 7.3_
  
  - [x] 2.2 Create WorkflowResult dataclass
    - Implement WorkflowResult with steps_completed, failed_step, results, overall_success
    - Implement summary property for human-readable output
    - _Requirements: 3.2, 3.3_
  
  - [x] 2.3 Create error exception classes
    - Implement PowerError base exception
    - Implement ContainerError for container operation failures
    - Implement CommandExecutionError for command failures
    - Implement ValidationError for parameter validation failures
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 3. Implement CommandExecutor component
  - [ ] 3.1 Create CommandExecutor class with execute method
    - Implement subprocess execution with output capture
    - Return CommandResult with exit code and output
    - Handle subprocess exceptions and convert to CommandExecutionError
    - _Requirements: 7.3_
  
  - [ ]* 3.2 Write property test for CommandExecutor
    - **Property 9: Exit Code Reporting**
    - **Validates: Requirements 7.3**
  
  - [ ] 3.3 Implement execute_with_streaming method
    - Use subprocess.Popen with stdout/stderr pipes
    - Yield output lines as they arrive
    - Return final CommandResult after completion
    - _Requirements: 7.1, 7.2_
  
  - [ ]* 3.4 Write property test for output streaming
    - **Property 10: Output Streaming**
    - **Validates: Requirements 7.1, 7.2**

- [ ] 4. Implement ContainerManager component
  - [ ] 4.1 Create ContainerManager class with devcontainer CLI integration
    - Implement _check_devcontainer_cli method to verify CLI is installed
    - Implement _get_workspace_folder method to get repository root
    - Set WORKSPACE_FOLDER and DOCKER_CLI_HINTS environment variables
    - _Requirements: 2.1, 8.5_
  
  - [ ] 4.2 Implement ensure_running method
    - Execute "devcontainer up --workspace-folder <workspace>"
    - Return True if successful, False otherwise
    - Handle errors and provide troubleshooting guidance
    - _Requirements: 2.1, 2.2, 5.3_
  
  - [ ]* 4.3 Write property test for idempotent container start
    - **Property 12: Idempotent Container Start**
    - **Validates: Requirements 9.1**
  
  - [ ] 4.4 Implement start method
    - Call ensure_running and return CommandResult
    - _Requirements: 2.3_
  
  - [ ] 4.5 Implement stop method
    - Execute "devcontainer exec hostname | xargs docker rm -f"
    - Return CommandResult
    - _Requirements: 2.4_
  
  - [ ] 4.6 Implement rebuild method
    - Execute "devcontainer build --workspace-folder <workspace>"
    - Then execute "devcontainer up --workspace-folder <workspace>"
    - Return CommandResult
    - _Requirements: 2.5, 9.3_
  
  - [ ] 4.7 Implement exec method
    - Call ensure_running first
    - Execute "devcontainer exec --workspace-folder <workspace> <command>"
    - Return CommandResult
    - _Requirements: 2.6_
  
  - [ ]* 4.8 Write unit tests for ContainerManager error handling
    - Test devcontainer CLI not found
    - Test .devcontainer/ directory missing
    - Test container start failure
    - Test Docker daemon not running
    - _Requirements: 5.3_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement PantsCommandBuilder component
  - [ ] 6.1 Create PantsCommandBuilder class
    - Implement build_command method to construct "pants <subcommand> <target>"
    - Default target to "::" if not provided
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [ ]* 6.2 Write property test for target pass-through
    - **Property 2: Target Parameter Pass-Through**
    - **Validates: Requirements 1.5, 1.7, 6.1, 6.2, 6.3, 6.4, 6.5**
  
  - [ ]* 6.3 Write property test for default target behavior
    - **Property 3: Default Target Behavior**
    - **Validates: Requirements 1.4, 1.6, 6.6**
  
  - [ ] 6.2 Implement validate_target method
    - Validate target specification syntax
    - Return True for valid targets, False otherwise
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 6.5 Write unit tests for PantsCommandBuilder
    - Test command construction for each subcommand
    - Test default target behavior
    - Test custom target specifications
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] 7. Implement core Pants command tools
  - [ ] 7.1 Implement pants_fix tool
    - Use ContainerManager.ensure_running
    - Use PantsCommandBuilder.build_command("fix", target)
    - Execute via ContainerManager.exec
    - Return CommandResult
    - _Requirements: 1.1, 6.4_
  
  - [ ]* 7.2 Write property test for Pants command execution pattern
    - **Property 1: Pants Command Execution Pattern**
    - **Validates: Requirements 1.1, 1.2, 1.3, 2.1**
  
  - [ ] 7.3 Implement pants_lint tool
    - Use ContainerManager.ensure_running
    - Use PantsCommandBuilder.build_command("lint", target)
    - Execute via ContainerManager.exec
    - Return CommandResult
    - _Requirements: 1.2, 6.3_
  
  - [ ] 7.4 Implement pants_check tool
    - Use ContainerManager.ensure_running
    - Use PantsCommandBuilder.build_command("check", target)
    - Execute via ContainerManager.exec
    - Return CommandResult
    - _Requirements: 1.3, 6.5_
  
  - [ ] 7.5 Implement pants_test tool
    - Use ContainerManager.ensure_running
    - Use PantsCommandBuilder.build_command("test", target)
    - Execute via ContainerManager.exec
    - Return CommandResult
    - _Requirements: 1.4, 1.5, 6.1_
  
  - [ ] 7.6 Implement pants_package tool
    - Use ContainerManager.ensure_running
    - Use PantsCommandBuilder.build_command("package", target)
    - Execute via ContainerManager.exec
    - Return CommandResult
    - _Requirements: 1.6, 1.7, 6.2_
  
  - [ ]* 7.7 Write unit tests for Pants command tools
    - Test each tool with default target
    - Test each tool with custom target
    - Test container start failure handling
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] 8. Implement container lifecycle tools
  - [ ] 8.1 Implement container_start tool
    - Call ContainerManager.start
    - Return CommandResult
    - _Requirements: 2.3, 9.1_
  
  - [ ] 8.2 Implement container_stop tool
    - Call ContainerManager.stop
    - Return CommandResult
    - _Requirements: 2.4_
  
  - [ ] 8.3 Implement container_rebuild tool
    - Call ContainerManager.rebuild
    - Return CommandResult
    - _Requirements: 2.5_
  
  - [ ] 8.4 Implement container_exec tool
    - Validate command parameter
    - Call ContainerManager.exec with command
    - Return CommandResult
    - _Requirements: 2.6_
  
  - [ ]* 8.5 Write property test for arbitrary command execution
    - **Property 5: Arbitrary Command Execution**
    - **Validates: Requirements 2.6**
  
  - [ ] 8.6 Implement container_shell tool
    - Return informational message with command to run manually
    - Include "devcontainer exec --workspace-folder <workspace> /bin/zsh -l"
    - _Requirements: 2.7_
  
  - [ ]* 8.7 Write unit tests for container lifecycle tools
    - Test each tool with successful execution
    - Test error handling for each tool
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement WorkflowOrchestrator component
  - [ ] 10.1 Create WorkflowOrchestrator class
    - Implement get_workflow_steps method to map workflow names to command lists
    - Support "fix-lint", "check-test", "fix-lint-check" workflows
    - _Requirements: 3.4, 3.5_
  
  - [ ] 10.2 Implement execute_workflow method
    - Execute steps in sequence using appropriate tool functions
    - Stop on first failure and record failed step
    - Stream progress indication before each step
    - Return WorkflowResult with all step results
    - _Requirements: 3.1, 3.2, 7.4_
  
  - [ ]* 10.3 Write property test for workflow failure handling
    - **Property 6: Workflow Failure Handling**
    - **Validates: Requirements 3.2**
  
  - [ ]* 10.4 Write property test for workflow progress indication
    - **Property 11: Workflow Progress Indication**
    - **Validates: Requirements 7.4**
  
  - [ ]* 10.5 Write unit tests for WorkflowOrchestrator
    - Test successful workflow execution
    - Test workflow stopping on failure at each step
    - Test workflow progress messages
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 11. Implement workflow tools
  - [ ] 11.1 Implement full_quality_check tool
    - Use WorkflowOrchestrator with ["fix", "lint", "check", "test"] steps
    - Pass target parameter to all steps
    - Return WorkflowResult
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 11.2 Implement pants_workflow tool
    - Validate workflow parameter against supported workflows
    - Use WorkflowOrchestrator.get_workflow_steps
    - Execute workflow with WorkflowOrchestrator.execute_workflow
    - Return WorkflowResult
    - _Requirements: 3.4, 3.5_
  
  - [ ]* 11.3 Write unit tests for workflow tools
    - Test full_quality_check with all steps succeeding
    - Test full_quality_check stopping at each possible failure point
    - Test pants_workflow with each supported workflow
    - Test pants_workflow with invalid workflow name
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 12. Implement utility tools
  - [ ] 12.1 Implement pants_clear_cache tool
    - Use ContainerManager.ensure_running
    - Execute "rm -rf .pants.d/pids" via ContainerManager.exec
    - Handle missing directory gracefully (success without error)
    - Return CommandResult
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 12.2 Write unit tests for pants_clear_cache
    - Test successful cache clearing
    - Test graceful handling of missing cache directory
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 13. Implement error handling and formatting
  - [ ] 13.1 Implement error message formatting
    - Create format_error function for ContainerError
    - Create format_error function for CommandExecutionError
    - Create format_error function for ValidationError
    - Include command, output, and troubleshooting guidance
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 13.2 Write property test for error message formatting
    - **Property 7: Error Message Formatting**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ] 13.3 Implement success message formatting
    - Create format_success function for CommandResult
    - Handle empty output gracefully
    - _Requirements: 5.4, 5.5_
  
  - [ ]* 13.4 Write property test for success message formatting
    - **Property 8: Success Message Formatting**
    - **Validates: Requirements 5.4**
  
  - [ ]* 13.5 Write unit tests for error and success formatting
    - Test each error type with various failure scenarios
    - Test success formatting with output and without output
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Implement MCP server
  - [ ] 15.1 Create MCP server class
    - Initialize with PowerConfig
    - Validate devcontainer CLI and .devcontainer/ directory on startup
    - Provide helpful error messages if prerequisites missing
    - _Requirements: 8.5_
  
  - [ ] 15.2 Register all MCP tools
    - Register 5 Pants command tools (fix, lint, check, test, package)
    - Register 5 container lifecycle tools (start, stop, rebuild, exec, shell)
    - Register 2 workflow tools (full_quality_check, pants_workflow)
    - Register 1 utility tool (pants_clear_cache)
    - Each tool includes description and parameter schema
    - _Requirements: 8.1, 10.1_
  
  - [ ] 15.3 Implement tool invocation handler
    - Validate tool name and parameters
    - Route to appropriate tool function
    - Catch exceptions and convert to MCP error responses
    - Return MCP tool result with formatted output
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 15.4 Write integration tests for MCP server
    - Test server initialization
    - Test tool registration
    - Test tool invocation for each tool
    - Test error handling and response formatting
    - _Requirements: 8.1, 8.2, 8.5_

- [ ] 16. Create power.json manifest
  - [ ] 16.1 Define power metadata
    - Set name: "pants-devcontainer-power"
    - Set version: "0.1.0"
    - Set description
    - Set keywords: ["pants", "build", "devcontainer", "workflow", "monorepo"]
    - Set runtime: "python3.11+"
    - _Requirements: 8.1, 8.3, 8.4_
  
  - [ ] 16.2 Define all 15 MCP tools in manifest
    - Define each tool with name, description, and input schema
    - Include parameter types and descriptions
    - Mark optional parameters
    - _Requirements: 8.1, 10.1_

- [ ] 17. Create documentation
  - [ ] 17.1 Create README.md
    - Write overview and key features
    - Document installation steps (npm install -g @devcontainers/cli)
    - Document Pants installation requirement
    - Provide usage examples for common workflows
    - Document all 15 tools with examples
    - Explain relationship to devcontainer CLI
    - _Requirements: 8.2, 10.2, 10.3, 10.4, 10.5_
  
  - [ ] 17.2 Add inline documentation
    - Add docstrings to all classes and methods
    - Include parameter descriptions and return types
    - Add usage examples in docstrings
    - _Requirements: 10.1_

- [ ] 18. Final integration and validation
  - [ ] 18.1 Run full test suite
    - Run all unit tests
    - Run all property tests (minimum 100 iterations each)
    - Run integration tests
    - Verify 90% line coverage and 85% branch coverage
    - _Requirements: All_
  
  - [ ]* 18.2 Validate all correctness properties
    - Verify Property 1: Pants Command Execution Pattern
    - Verify Property 2: Target Parameter Pass-Through
    - Verify Property 3: Default Target Behavior
    - Verify Property 4: Container Start Failure Handling
    - Verify Property 5: Arbitrary Command Execution
    - Verify Property 6: Workflow Failure Handling
    - Verify Property 7: Error Message Formatting
    - Verify Property 8: Success Message Formatting
    - Verify Property 9: Exit Code Reporting
    - Verify Property 10: Output Streaming
    - Verify Property 11: Workflow Progress Indication
    - Verify Property 12: Idempotent Container Start
  
  - [ ] 18.3 Manual testing with actual devcontainer
    - Test power in a repository with real devcontainer
    - Verify all tools work with actual Pants commands
    - Test error scenarios (container not running, CLI not found, etc.)
    - Verify output formatting and streaming
    - _Requirements: All_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and additional unit tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with Hypothesis
- Unit tests validate specific examples, edge cases, and error conditions
- The implementation follows a bottom-up approach: utilities → commands → tools → workflows → integration
- All 12 correctness properties from the design document have corresponding property test tasks
