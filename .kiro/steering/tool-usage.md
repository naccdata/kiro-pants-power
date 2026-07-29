# Tool Usage Guidelines

## Shell Command Execution

When running shell commands, use the `cwd` parameter to set the working directory instead of prefixing commands with `cd`. The `cd` command is not supported in tool invocations and will fail.

**Correct:**

```
execute_bash(command="terraform init", cwd="/path/to/environment")
```

**Incorrect:**

```
execute_bash(command="cd /path/to/environment && terraform init")
```

This applies to all shell command execution — builds, Terraform, scripts, and any other CLI operations.
