---
name: troubleshooting
description: Diagnose and fix Pants devcontainer problems — container won't start, Docker or devcontainer CLI missing, Pants not found, stale cache, or failing quality steps.
---

# Troubleshoot the Pants devcontainer

Every tool requires `workspace_folder`: the absolute path to the repository root
containing `.devcontainer/`. Pass it on every call.

## Step 1: Operating rules

- **Stop on infrastructure, MCP, or container errors.** When a container or
  tool-infrastructure error occurs, report it and stop. Do NOT fall back to
  running raw `pants` via `container_exec` when a dedicated tool exists — the
  dedicated tools are the supported path.
- **Do NOT retry an identical failure.** If a tool fails the same way twice,
  stop and report rather than re-running and hoping for a different result.
- **Code-level failures are normal development feedback.** Lint, type-check, and
  test failures mean fix the code — they are not tool failures. Read the output
  and address the code.
- **Fix all issues in a category before re-running**, not one at a time.

## Step 2: Container issues

- `devcontainer` CLI not found: install it with `npm install -g @devcontainers/cli`.
- Docker daemon unreachable: start Docker, then confirm with `docker ps`.
- Container not running: this power auto-starts it; otherwise call
  `container_start(workspace_folder="<repo root>")`.
- Container start failed: `container_rebuild(workspace_folder="<repo root>")` and
  check the `.devcontainer/` configuration.
- `.devcontainer/` not found: fix the `workspace_folder` path so it points at the
  repository root that contains `.devcontainer/`.

## Step 3: Pants issues

- Pants not installed ("pants not found"): install it INSIDE the container using
  the repository's own install method, for example:

  ```
  container_exec(workspace_folder="<repo root>", command="bash get-pants.sh")
  ```

  > EXAMPLE ONLY: `get-pants.sh` is a repo-specific script name, not part of this
  > power. If the repository has no install script, follow
  > https://www.pantsbuild.org/docs/installation.

  Then verify:

  ```
  container_exec(workspace_folder="<repo root>", command="pants --version")
  ```

- Lint or test failures: read the output, run `pants_fix`, and re-run the failing
  step scoped via the `targeting` skill.

## Step 4: Cache and stale-state issues

Symptoms include unexplained "file not found" errors or stale state after
refactors or file moves:

```
pants_clear_cache(workspace_folder="<repo root>")
```

Then retry. If the problem persists, `container_rebuild(workspace_folder="<repo root>")`.

## Step 5: Narrowing strategy for unstructured errors

When an error lacks actionable detail, narrow scope to isolate it: first separate
source runs from test runs, then narrow to individual files using the `targeting`
skill's `scope`/`path` parameters.

## Step 6: Targeting mistakes

- "path does not exist": the path must be relative to the repository root.
- "no BUILD file found": run `pants_tailor(workspace_folder="<repo root>")`.
- `test_filter` boolean operators must be lowercase: `and`, `or`, `not`.
