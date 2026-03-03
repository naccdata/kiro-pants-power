# Design Document: Pants DevContainer Power

## Overview

The Pants DevContainer Power is an MCP (Model Context Protocol) server that provides tools for managing the NACC Flywheel Extensions development workflow. It wraps Pants build system commands with automatic devcontainer execution, eliminating the need for developers to manually manage container lifecycle or remember wrapper scripts.

The power consolidates knowledge from multiple steering documents into executable tools that enforce best practices. It provides both individual command tools (pants_fix, pants_lint, etc.) and workflow orchestration tools (full_quality_check) that execute multiple commands in sequence.

### Key Design Goals

1. **Zero-friction execution**: Developers invoke Pants commands directly; the power handles container management
2. **Fail-fast feedback**: Commands stop on first error with clear diagnostic information
3. **Workflow automation**: Common command sequences (fix → lint → check → test) available as single operations
4. **Idempotent operations**: Container start operations are safe to call repeatedly
5. **Target flexibility**: Support both full monorepo operations (::) and specific target execution

## Architecture

### Component Structure

```
pants-devcontainer-power/
├── power.json              # MCP server manifest
├── README.md               # Installation and usage documentation
├── src/
│   └── server.py          # MCP server implementation
├── tests/
│   └── test_server.py     # Test suite
└── requirements.txt        # Python dependencies
```

### MCP Server Architecture

The power implements an MCP server that exposes tools through the Model Context Protocol. The server:

1. Receives tool invocation requests from the MCP client (Kiro)
2. Validates parameters and constructs shell commands
3. Ensures the devcontainer is running before executing commands
4. Executes commands via the bin/ wrapper scripts
5. Streams output back to the client
6. Returns structured results with exit codes and output

### Container Management Strategy

All Pants commands follow this execution pattern:

```
1. Check if devcontainer CLI is installed
2. Ensure container is running (via devcontainer up)
3. If container start fails, return error immediately
4. Execute command (via devcontainer exec)
5. Stream output to client
6. Return exit code and final output
```

The power embeds the devcontainer management logic directly using Python subprocess calls to the `devcontainer` CLI, rather than depending on external shell scripts. This makes the power self-contained and portable to any repository with a `.devcontainer/` configuration.

#### DevContainer CLI Integration

The power requires the `@devcontainers/cli` npm package to be installed globally:
```bash
npm install -g @devcontainers/cli
```

All devcontainer operations set these environment variables:
- `WORKSPACE_FOLDER`: Current working directory (repository root)
- `DOCKER_CLI_HINTS`: Set to "false" to suppress Docker hints

#### Pants Installation Requirement

The power assumes that Pants is installed inside the devcontainer. For the NACC repository, this is typically done by running:
```bash
devcontainer exec --workspace-folder . bash get-pants.sh
```

The power should detect if Pants is not installed and provide helpful error messages guiding users to install it.

This ensures commands never execute in the wrong environment and provides consistent error handling.

## Components and Interfaces

### MCP Tools

The power exposes the following MCP tools:

#### Core Pants Commands

**pants_fix**

- Description: Format code and auto-fix linting issues
- Parameters:
  - `target` (optional, string): Pants target specification (default: "::")
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec pants fix <target>`

**pants_lint**

- Description: Run linters on code
- Parameters:
  - `target` (optional, string): Pants target specification (default: "::")
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec pants lint <target>`

**pants_check**

- Description: Run type checking with mypy
- Parameters:
  - `target` (optional, string): Pants target specification (default: "::")
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec pants check <target>`

**pants_test**

- Description: Run tests
- Parameters:
  - `target` (optional, string): Pants target specification (default: "::")
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec pants test <target>`

**pants_package**

- Description: Build packages
- Parameters:
  - `target` (optional, string): Pants target specification (default: "::")
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec pants package <target>`

#### Container Lifecycle Commands

**container_start**

- Description: Start the devcontainer (idempotent)
- Parameters: None
- Returns: Command output and exit code
- Implementation: Executes `devcontainer up --workspace-folder <workspace>`

**container_stop**

- Description: Stop the devcontainer
- Parameters: None
- Returns: Command output and exit code
- Implementation: Executes `devcontainer exec hostname | xargs docker rm -f` to get container name and stop it

**container_rebuild**
- Description: Rebuild and restart the devcontainer
- Parameters: None
- Returns: Command output and exit code
- Implementation: Executes `devcontainer build --workspace-folder <workspace>` then `devcontainer up --workspace-folder <workspace>`

**container_exec**
- Description: Execute arbitrary command in container
- Parameters:
  - `command` (required, string): Shell command to execute
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec --workspace-folder <workspace> <command>`

**container_shell**
- Description: Provide instructions for opening interactive shell
- Parameters: None
- Returns: Instructions for running `devcontainer exec --workspace-folder <workspace> /bin/zsh -l`
- Implementation: Returns informational message with command to run (cannot open interactive shell via MCP)

#### Workflow Orchestration Commands

**full_quality_check**
- Description: Run complete quality check workflow (fix → lint → check → test)
- Parameters:
  - `target` (optional, string): Pants target specification (default: "::")
- Returns: Aggregated output from all steps, exit code
- Implementation: Executes pants_fix, pants_lint, pants_check, pants_test in sequence, stopping on first failure

**pants_workflow**
- Description: Execute custom workflow sequence
- Parameters:
  - `workflow` (required, string): Workflow name ("fix-lint", "check-test", "fix-lint-check")
- Returns: Aggregated output from all steps, exit code
- Implementation: Maps workflow name to command sequence and executes

#### Utility Commands

**pants_clear_cache**
- Description: Clear Pants cache to resolve filesystem issues
- Parameters: None
- Returns: Command output and exit code
- Implementation: Ensures container is running via `devcontainer up`, then executes `devcontainer exec rm -rf .pants.d/pids`

### Internal Interfaces

#### CommandExecutor

Responsible for executing shell commands and capturing output.

```python
class CommandExecutor:
    def execute(self, command: str, cwd: str = ".") -> CommandResult:
        """Execute shell command and return result."""
        pass
    
    def execute_with_streaming(self, command: str, cwd: str = ".") -> Iterator[str]:
        """Execute command and yield output lines as they arrive."""
        pass
```

#### ContainerManager

Manages devcontainer lifecycle operations.

```python
class ContainerManager:
    def ensure_running(self) -> bool:
        """Ensure container is running, start if needed. Returns True if successful."""
        pass
    
    def start(self) -> CommandResult:
        """Start the devcontainer."""
        pass
    
    def stop(self) -> CommandResult:
        """Stop the devcontainer."""
        pass
    
    def rebuild(self) -> CommandResult:
        """Rebuild and restart the devcontainer."""
        pass
    
    def exec(self, command: str) -> CommandResult:
        """Execute command in running container."""
        pass
```

#### PantsCommandBuilder

Constructs Pants commands with proper target specifications.

```python
class PantsCommandBuilder:
    def build_command(self, subcommand: str, target: str = "::") -> str:
        """Build Pants command string."""
        pass
    
    def validate_target(self, target: str) -> bool:
        """Validate target specification syntax."""
        pass
```

#### WorkflowOrchestrator

Executes multi-step workflows with proper error handling.

```python
class WorkflowOrchestrator:
    def execute_workflow(self, steps: List[str], target: str = "::") -> WorkflowResult:
        """Execute workflow steps in sequence, stopping on first failure."""
        pass
    
    def get_workflow_steps(self, workflow_name: str) -> List[str]:
        """Map workflow name to list of command steps."""
        pass
```

### Data Models

#### CommandResult

```python
@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    command: str
    success: bool
    
    @property
    def output(self) -> str:
        """Combined stdout and stderr."""
        return f"{self.stdout}\n{self.stderr}".strip()
```

#### WorkflowResult

```python
@dataclass
class WorkflowResult:
    steps_completed: List[str]
    failed_step: Optional[str]
    results: List[CommandResult]
    overall_success: bool
    
    @property
    def summary(self) -> str:
        """Human-readable summary of workflow execution."""
        pass
```

#### ToolInvocation

```python
@dataclass
class ToolInvocation:
    tool_name: str
    parameters: Dict[str, Any]
    
    def validate(self) -> bool:
        """Validate parameters against tool schema."""
        pass
```

## Data Models

### MCP Protocol Models

The power uses standard MCP protocol data structures:

- **Tool**: Defines tool name, description, and input schema
- **ToolCall**: Represents a tool invocation request
- **ToolResult**: Contains tool execution results

### Configuration Models

**PowerConfig**

```python
@dataclass
class PowerConfig:
    name: str = "pants-devcontainer-power"
    version: str = "0.1.0"
    description: str = "MCP tools for Pants build system with devcontainer integration"
    python_version: str = "3.12"
    repository_root: Path = Path(".")
    
    def validate(self) -> bool:
        """Validate that devcontainer CLI is installed and .devcontainer/ exists."""
        # Check for devcontainer CLI
        devcontainer_installed = shutil.which("devcontainer") is not None
        # Check for .devcontainer directory
        devcontainer_dir = self.repository_root / ".devcontainer"
        return devcontainer_installed and devcontainer_dir.exists()
```

### Error Models

**PowerError**

```python
class PowerError(Exception):
    """Base exception for power errors."""
    pass

class ContainerError(PowerError):
    """Container operation failed."""
    pass

class CommandExecutionError(PowerError):
    """Command execution failed."""
    pass

class ValidationError(PowerError):
    """Parameter validation failed."""
    pass
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Pants Command Execution Pattern

*For any* Pants subcommand (fix, lint, check, test, package), invoking the corresponding MCP tool should ensure the container is running via `devcontainer up` and then execute "pants <subcommand> <target>" inside the container via `devcontainer exec`.

**Validates: Requirements 1.1, 1.2, 1.3, 2.1**

### Property 2: Target Parameter Pass-Through

*For any* Pants command tool (pants_fix, pants_lint, pants_check, pants_test, pants_package) and any valid target specification, providing the target parameter should result in that exact target being passed to the Pants command.

**Validates: Requirements 1.5, 1.7, 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 3: Default Target Behavior

*For any* Pants command tool, when no target parameter is provided, the command should execute with "::" as the target specification.

**Validates: Requirements 1.4, 1.6, 6.6**

### Property 4: Container Start Failure Handling

*For any* Pants command, if the container start script (start-devcontainer.sh) exits with a non-zero status, the power should return an error message and not execute the Pants command.

**Validates: Requirements 2.2**

### Property 5: Arbitrary Command Execution

*For any* shell command string, invoking container_exec with that command should ensure the container is running and then execute "./bin/exec-in-devcontainer.sh <command>" with the command string properly escaped.

**Validates: Requirements 2.6**

### Property 6: Workflow Failure Handling

*For any* multi-step workflow (full_quality_check, pants_workflow), if any step fails (exits with non-zero status), the workflow should stop execution immediately and report which step failed without executing subsequent steps.

**Validates: Requirements 3.2**

### Property 7: Error Message Formatting

*For any* command that fails (container operation or Pants command), the error result should include both the failed command string and its output (stdout and stderr).

**Validates: Requirements 5.1, 5.2**

### Property 8: Success Message Formatting

*For any* command that succeeds, the result should include a success indicator and relevant output from the command.

**Validates: Requirements 5.4**

### Property 9: Exit Code Reporting

*For any* command execution (Pants command, container operation, or workflow), the result should include the final exit code from the command.

**Validates: Requirements 7.3**

### Property 10: Output Streaming

*For any* command execution, both stdout and stderr should be streamed to the client in real-time as the command produces output, rather than being buffered until completion.

**Validates: Requirements 7.1, 7.2**

### Property 11: Workflow Progress Indication

*For any* multi-step workflow, the output should indicate which step is currently executing before that step begins.

**Validates: Requirements 7.4**

### Property 12: Idempotent Container Start

*For any* state of the devcontainer (running or stopped), invoking container_start should result in a running container and return success, without restarting an already-running container.

**Validates: Requirements 9.1**

## Error Handling

### Error Categories

The power handles four categories of errors:

1. **Container Lifecycle Errors**: Container cannot start, stop, or rebuild
2. **Command Execution Errors**: Pants commands or shell commands fail
3. **Validation Errors**: Invalid parameters or tool invocations
4. **System Errors**: Missing scripts, permission issues, filesystem problems

### Error Handling Strategy

#### Container Lifecycle Errors

When container operations fail:

- Return ContainerError with the failed command and output
- Include troubleshooting guidance for common issues:
  - DevContainer CLI not installed (`npm install -g @devcontainers/cli`)
  - Docker daemon not running
  - Insufficient permissions
  - Port conflicts
  - Resource constraints
  - Missing or invalid `.devcontainer/` configuration

Example error message:
```
Container start failed: devcontainer up exited with code 1

Output:
Error: Cannot connect to Docker daemon. Is Docker running?

Troubleshooting:
1. Check if Docker Desktop is running
2. Verify Docker daemon is accessible: docker ps
3. Check Docker permissions: docker run hello-world
4. Ensure devcontainer CLI is installed: npm install -g @devcontainers/cli
```

#### Command Execution Errors

When Pants commands or shell commands fail:
- Return CommandExecutionError with full command and output
- Preserve exit code for programmatic handling
- Include both stdout and stderr in output

Example error message:
```
Command failed: pants test common/test/python::

Exit code: 1

Output:
[stderr] ERROR: Test failed: test_identifier_validation
[stderr] AssertionError: Expected 5, got 3
```

#### Validation Errors

When parameters are invalid:
- Return ValidationError with specific validation failure
- Provide examples of valid parameter values
- Reference documentation for complex parameters

Example error message:
```
Invalid target specification: "common/src/python"

Target must be a valid Pants target specification:
- "::" for all targets
- "path/to/dir::" for directory and subdirectories
- "path/to/dir:target" for specific target
- "path/to/file.py" for single file

See: https://www.pantsbuild.org/docs/targets
```

#### System Errors

When system-level issues occur:

- Return PowerError with diagnostic information
- Check for common issues (devcontainer CLI missing, wrong directory, missing .devcontainer/, Pants not installed)
- Provide recovery steps

Example error message:
```
DevContainer CLI not found

The devcontainer CLI is required to use this power.

Install it with: npm install -g @devcontainers/cli

For more information: https://containers.dev/supporting
```

Example error message for missing configuration:
```
DevContainer configuration not found

This power requires a .devcontainer/ directory with devcontainer.json.

Current directory: /home/user/projects/other-repo

Please run this power from a repository with devcontainer configuration.
```

Example error message for Pants not installed:
```
Pants not found in devcontainer

Pants must be installed inside the devcontainer before using this power.

For NACC repository, run:
  devcontainer exec --workspace-folder . bash get-pants.sh

For other repositories, see: https://www.pantsbuild.org/docs/installation
```

### Graceful Degradation

The power handles missing or incomplete environments gracefully:

1. **Missing cache directory**: pants_clear_cache succeeds without error if .pants.d/pids doesn't exist
2. **Empty command output**: Returns success confirmation when command produces no output
3. **Interactive shell request**: container_shell provides instructions instead of attempting to open shell via MCP

### Error Recovery

The power provides automatic recovery for transient issues:

1. **Container not running**: Automatically starts container before executing commands
2. **Stale cache**: pants_clear_cache tool available to clear problematic cache state
3. **Container rebuild**: container_rebuild tool available to rebuild from clean state

## Testing Strategy

### Dual Testing Approach

The testing strategy uses both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, error conditions, and integration points
- **Property tests**: Verify universal properties across all inputs using randomized testing

### Unit Testing Focus

Unit tests should cover:

1. **Specific tool invocations**: Test each MCP tool with known inputs and expected outputs
2. **Error scenarios**: Test specific error conditions (container start failure, command not found, etc.)
3. **Edge cases**: Test empty output, missing cache directory, already-running container
4. **Workflow sequences**: Test specific workflow definitions (full_quality_check, fix-lint, check-test)
5. **Integration points**: Test interaction with bin/ scripts and MCP protocol

Example unit tests:
- `test_pants_fix_with_default_target`: Verify pants_fix with no target uses "::"
- `test_container_start_when_already_running`: Verify idempotent behavior
- `test_full_quality_check_stops_on_lint_failure`: Verify workflow stops at failing step
- `test_pants_clear_cache_with_missing_directory`: Verify graceful handling of missing cache

### Property-Based Testing Focus

Property tests should verify universal behaviors across randomized inputs:

1. **Target pass-through**: Generate random valid target specifications and verify they're passed correctly
2. **Command construction**: Generate random Pants subcommands and verify correct command strings
3. **Error message format**: Generate random command failures and verify error format consistency
4. **Output streaming**: Verify output appears incrementally for commands of varying lengths
5. **Workflow failure handling**: Generate failures at random workflow steps and verify proper stopping

### Property-Based Testing Configuration

- **Library**: Use Hypothesis for Python property-based testing
- **Iterations**: Minimum 100 iterations per property test
- **Tagging**: Each property test must reference its design document property

Tag format:
```python
@pytest.mark.property
@pytest.mark.feature("pants-devcontainer-power")
def test_property_2_target_passthrough(pants_command, target):
    """
    Feature: pants-devcontainer-power, Property 2: Target Parameter Pass-Through
    
    For any Pants command tool and any valid target specification,
    providing the target parameter should result in that exact target
    being passed to the Pants command.
    """
    # Test implementation
```

### Test Doubles and Mocking

To enable fast, reliable testing without requiring actual container execution:

1. **Mock devcontainer CLI**: Replace subprocess calls with test doubles that return controlled output
2. **Mock MCP protocol**: Use test harness to simulate MCP client requests
3. **Mock filesystem**: Use temporary directories for cache operations
4. **Controllable failures**: Test doubles can simulate various failure modes (CLI not found, container start failure, etc.)

### Test Organization

```
tests/
├── unit/
│   ├── test_pants_commands.py      # Individual Pants command tools
│   ├── test_container_lifecycle.py # Container management tools
│   ├── test_workflows.py           # Workflow orchestration
│   ├── test_error_handling.py      # Error scenarios
│   └── test_edge_cases.py          # Edge cases and special conditions
├── property/
│   ├── test_target_passthrough.py  # Property 2
│   ├── test_error_formatting.py    # Property 7, 8
│   ├── test_workflow_failures.py   # Property 6
│   └── test_output_streaming.py    # Property 10
└── integration/
    ├── test_mcp_protocol.py        # MCP protocol integration
    └── test_script_execution.py    # Actual script execution (optional, slow)
```

### Coverage Goals

- **Line coverage**: Minimum 90% for core logic
- **Branch coverage**: Minimum 85% for error handling paths
- **Property coverage**: All 12 correctness properties must have corresponding property tests
- **Tool coverage**: All MCP tools must have unit tests

### Continuous Testing

Tests should run:
- On every commit (via pre-commit hook or CI)
- Before merging pull requests
- On schedule (nightly) for integration tests
- After dependency updates

### Test Data

Use realistic test data:

- Valid Pants target specifications from actual NACC repository
- Real error messages from Pants and Docker
- Actual devcontainer CLI output formats
- Representative workflow sequences

