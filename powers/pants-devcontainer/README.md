# Pants DevContainer Power

This directory contains the Kiro Power documentation for the Pants DevContainer MCP server.

## Files Created

### POWER.md
Complete user-facing documentation including:
- Overview of the power and its 15 tools
- Onboarding section with prerequisites and installation
- 6 common workflows with examples
- Complete MCP tools reference
- Troubleshooting guide for container, Pants, and workflow issues
- Best practices for using the power
- Configuration details

### mcp.json
MCP server configuration for Kiro:
- Server name: `pants-devcontainer`
- Command: `python -m src.server`
- Working directory: Workspace folder
- Python path configuration

## Next Steps

### 1. Complete Implementation (Tasks 1-15)
Follow your spec to build the MCP server implementation in `src/server.py`

### 2. Test the Power Locally

Once implementation is complete:

1. **Install the power in Kiro:**
   - Open Kiro Powers panel (use configure action)
   - Click "Add Custom Power"
   - Select "Local Directory"
   - Enter path: `{workspace}/powers/pants-devcontainer`
   - Click "Add"

2. **Test discovery:**
   - Type "pants" in Kiro chat
   - Power should activate automatically

3. **Test tools:**
   - Try: "Run pants fix on all targets"
   - Try: "Run full quality check"
   - Try: "Start the devcontainer"

4. **Verify documentation:**
   - Ask: "How do I run tests on a specific directory?"
   - Ask: "What should I do if the container won't start?"
   - Check that responses reference the POWER.md content

### 3. Iterate on Documentation

Based on testing:
- Add missing troubleshooting scenarios
- Clarify confusing workflows
- Add more examples if needed
- Update tool descriptions based on actual behavior

### 4. Update mcp.json if Needed

If your implementation structure differs:
- Update `command` and `args` to match your entry point
- Add any required environment variables
- Adjust `cwd` if needed

## Documentation Structure

The POWER.md follows the recommended structure for Guided MCP Powers:

1. **Frontmatter** - Metadata (name, displayName, description, keywords, author)
2. **Overview** - What the power does and why it's useful
3. **Onboarding** - Prerequisites, installation, verification
4. **Common Workflows** - 6 real-world usage scenarios with examples
5. **MCP Tools Reference** - Complete documentation of all 15 tools
6. **Troubleshooting** - Solutions for container, Pants, and workflow issues
7. **Best Practices** - Guidelines for effective usage
8. **Configuration** - Environment variables and target specifications

## Power Metadata

- **Name:** pants-devcontainer
- **Display Name:** Pants DevContainer
- **Keywords:** pants, build, devcontainer, workflow, monorepo, nacc
- **Author:** NACC Team
- **Type:** Guided MCP Power (includes MCP server)

## Tools Documented

### Pants Commands (5)
- pants_fix - Format code and auto-fix linting issues
- pants_lint - Run linters on code
- pants_check - Run type checking with mypy
- pants_test - Run tests with pytest
- pants_package - Build distributable packages

### Container Lifecycle (5)
- container_start - Start the devcontainer
- container_stop - Stop the devcontainer
- container_rebuild - Rebuild and restart the devcontainer
- container_exec - Execute arbitrary command in container
- container_shell - Get instructions for interactive shell

### Workflow Orchestration (2)
- full_quality_check - Run complete quality check (fix → lint → check → test)
- pants_workflow - Execute custom workflow sequence

### Utilities (1)
- pants_clear_cache - Clear Pants cache to resolve filesystem issues

## Alignment with Spec

This documentation aligns with your spec tasks:

- **Task 16:** Power metadata and tool definitions (covered in POWER.md frontmatter)
- **Task 17.1:** README with overview, installation, usage examples (covered in POWER.md)
- **Task 17.2:** Tool documentation with examples (covered in MCP Tools Reference section)

The POWER.md serves as the comprehensive user guide that your spec's Task 17 requires.
