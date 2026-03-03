# Requirements Document

## Introduction

The Pants DevContainer Power is a Kiro Power that provides MCP (Model Context Protocol) tools for managing the NACC Flywheel Extensions development workflow. This power eliminates friction by automatically wrapping Pants build system commands with devcontainer execution, ensuring all commands run in the proper containerized environment. It consolidates knowledge from multiple steering documents (tech.md, devcontainer.md, structure.md, versioning.md, product.md) into executable tools that enforce best practices and reduce manual overhead.

## Glossary

- **Power**: A Kiro extension that provides MCP tools for specific workflows
- **MCP_Tool**: A Model Context Protocol tool that can be invoked by the AI assistant
- **Pants**: The build system used by the NACC monorepo (v2.27.0)
- **DevContainer**: A Docker-based development environment providing consistent tooling
- **Container_Wrapper**: The bin/exec-in-devcontainer.sh script that executes commands inside the container
- **Workflow**: A sequence of related commands executed in order (e.g., fix → lint → check → test)
- **Cache**: Pants internal state stored in .pants.d/ directory

## Requirements

### Requirement 1: Pants Command Execution

**User Story:** As a developer, I want to run Pants commands without manually wrapping them in devcontainer scripts, so that I can focus on development instead of environment management.

#### Acceptance Criteria

1. WHEN a developer invokes pants_fix, THE MCP_Tool SHALL ensure the container is running and execute "pants fix ::" inside the container
2. WHEN a developer invokes pants_lint, THE MCP_Tool SHALL ensure the container is running and execute "pants lint ::" inside the container
3. WHEN a developer invokes pants_check, THE MCP_Tool SHALL ensure the container is running and execute "pants check ::" inside the container
4. WHEN a developer invokes pants_test with no target specified, THE MCP_Tool SHALL ensure the container is running and execute "pants test ::" inside the container
5. WHEN a developer invokes pants_test with a target specified, THE MCP_Tool SHALL ensure the container is running and execute "pants test <target>" inside the container
6. WHEN a developer invokes pants_package with no target specified, THE MCP_Tool SHALL ensure the container is running and execute "pants package ::" inside the container
7. WHEN a developer invokes pants_package with a target specified, THE MCP_Tool SHALL ensure the container is running and execute "pants package <target>" inside the container

### Requirement 2: Container Lifecycle Management

**User Story:** As a developer, I want the power to automatically manage the devcontainer lifecycle, so that I never execute commands in the wrong environment.

#### Acceptance Criteria

1. WHEN any Pants command is invoked, THE Power SHALL execute "devcontainer up" before running the command
2. WHEN "devcontainer up" exits with a non-zero status, THE Power SHALL return an error message and not execute the Pants command
3. WHEN a developer invokes container_start, THE MCP_Tool SHALL execute "devcontainer up --workspace-folder <workspace>" and return the result
4. WHEN a developer invokes container_stop, THE MCP_Tool SHALL execute "devcontainer exec hostname | xargs docker rm -f" and return the result
5. WHEN a developer invokes container_rebuild, THE MCP_Tool SHALL execute "devcontainer build" followed by "devcontainer up"
6. WHEN a developer invokes container_exec with a command, THE MCP_Tool SHALL ensure the container is running and execute "devcontainer exec <command>"
7. WHEN a developer invokes container_shell, THE MCP_Tool SHALL inform the user to run "devcontainer exec --workspace-folder <workspace> /bin/zsh -l" manually

### Requirement 3: Workflow Orchestration

**User Story:** As a developer, I want to run complete quality check workflows with a single command, so that I can efficiently validate my changes before committing.

#### Acceptance Criteria

1. WHEN a developer invokes full_quality_check, THE MCP_Tool SHALL execute pants_fix, then pants_lint, then pants_check, then pants_test in sequence
2. WHEN any step in full_quality_check fails, THE MCP_Tool SHALL stop execution and report which step failed
3. WHEN all steps in full_quality_check succeed, THE MCP_Tool SHALL report success with a summary of all steps executed
4. WHEN a developer invokes pants_workflow with "fix-lint", THE MCP_Tool SHALL execute pants_fix followed by pants_lint
5. WHEN a developer invokes pants_workflow with "check-test", THE MCP_Tool SHALL execute pants_check followed by pants_test

### Requirement 4: Cache Management

**User Story:** As a developer, I want to clear the Pants cache when encountering flaky filesystem issues, so that I can resolve build problems without manual intervention.

#### Acceptance Criteria

1. WHEN a developer invokes pants_clear_cache, THE MCP_Tool SHALL ensure the container is running and execute "rm -rf .pants.d/pids" inside the container
2. WHEN pants_clear_cache completes successfully, THE MCP_Tool SHALL report that the cache was cleared
3. IF the cache directory does not exist, THEN THE MCP_Tool SHALL report success without error

### Requirement 5: Error Handling and Feedback

**User Story:** As a developer, I want clear error messages when commands fail, so that I can quickly understand and resolve issues.

#### Acceptance Criteria

1. WHEN a container operation fails, THE Power SHALL return an error message that includes the failed command and its output
2. WHEN a Pants command fails, THE Power SHALL return the command output including error details
3. WHEN the container is not running and cannot be started, THE Power SHALL provide instructions for manual troubleshooting
4. WHEN a command succeeds, THE Power SHALL return a concise success message with relevant output
5. IF a command produces no output, THEN THE Power SHALL return a confirmation that the command completed successfully

### Requirement 6: Target Specification

**User Story:** As a developer, I want to run Pants commands on specific targets, so that I can work efficiently with subsets of the monorepo.

#### Acceptance Criteria

1. WHEN a developer provides a target parameter to pants_test, THE MCP_Tool SHALL pass the target to the Pants test command
2. WHEN a developer provides a target parameter to pants_package, THE MCP_Tool SHALL pass the target to the Pants package command
3. WHEN a developer provides a target parameter to pants_lint, THE MCP_Tool SHALL pass the target to the Pants lint command
4. WHEN a developer provides a target parameter to pants_fix, THE MCP_Tool SHALL pass the target to the Pants fix command
5. WHEN a developer provides a target parameter to pants_check, THE MCP_Tool SHALL pass the target to the Pants check command
6. WHEN no target is specified for any Pants command, THE MCP_Tool SHALL default to "::" (all targets)

### Requirement 7: Command Output Streaming

**User Story:** As a developer, I want to see command output as it executes, so that I can monitor progress for long-running operations.

#### Acceptance Criteria

1. WHEN a Pants command is executing, THE Power SHALL stream stdout to the developer in real-time
2. WHEN a Pants command is executing, THE Power SHALL stream stderr to the developer in real-time
3. WHEN a command completes, THE Power SHALL provide the final exit code
4. WHEN a workflow is executing, THE Power SHALL indicate which step is currently running

### Requirement 8: Power Configuration

**User Story:** As a developer, I want the power to be easily installable and configurable, so that I can start using it with minimal setup.

#### Acceptance Criteria

1. THE Power SHALL include a power.json manifest file that declares all MCP tools
2. THE Power SHALL include a README.md file with installation and usage instructions
3. THE Power SHALL include keywords: "pants", "build", "devcontainer", "workflow", "monorepo", "nacc"
4. THE Power SHALL specify Python 3.12 as the required runtime environment
5. THE Power SHALL require the devcontainer CLI to be installed (`npm install -g @devcontainers/cli`)

### Requirement 9: Idempotent Container Operations

**User Story:** As a developer, I want container start operations to be safe to call multiple times, so that I don't have to track container state manually.

#### Acceptance Criteria

1. WHEN container_start is invoked and the container is already running, THE MCP_Tool SHALL return success without restarting the container
2. WHEN any Pants command checks if the container is running, THE Power SHALL use the idempotent "devcontainer up" command
3. WHEN container_rebuild is invoked, THE Power SHALL stop the container if running before rebuilding

### Requirement 10: Documentation and Discoverability

**User Story:** As a developer, I want clear documentation for each tool, so that I can understand what each command does and when to use it.

#### Acceptance Criteria

1. THE Power SHALL provide a description for each MCP tool in the power.json manifest
2. THE Power SHALL include usage examples in the README.md for common workflows
3. THE Power SHALL document the relationship between power tools and the underlying devcontainer CLI
4. THE Power SHALL explain when to use individual commands versus workflow orchestration
5. THE Power SHALL document the cache clearing capability and when it should be used
