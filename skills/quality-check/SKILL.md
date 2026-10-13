---
name: quality-check
description: Run the Pants quality workflow — fix, lint, type-check, and test code before committing — using the full check for a gate or targeted checks while working.
---

# Run the Pants quality workflow

Every tool requires `workspace_folder`: the absolute path to the repository root
containing `.devcontainer/`. Pass it on every call.

## Step 1: Always fix first

Whatever path you take, run `pants_fix` first to auto-fix formatting before
linting, type-checking, or testing:

```
pants_fix(workspace_folder="<repo root>")
```

## Step 2: Pre-commit / pre-PR gate (full check)

Before pushing, run the complete sequence:

```
full_quality_check(workspace_folder="<repo root>", target="::")
```

This runs fix → lint → check → test, stops on the first failure, and reports
which step failed. Never push with known failures in code you changed.
`full_quality_check` takes `target` only — do not pass `scope`/`path` to it.

## Step 3: Layered strategy while working

Do NOT run the full check after every subtask — that is wasteful. While working:

- Changed source files: `pants_fix` then `pants_check`, scoped to the file or
  its directory.
- Changed test files: `pants_fix` then `pants_test`, scoped to the file.
- Run the full `full_quality_check` only at wave/task boundaries or immediately
  before a push.

See the `targeting` skill for the `scope`/`path`/`recursive`/`test_filter`
parameters on the individual tools.

## Step 4: Pre-existing-failure rule

Failures in code you did NOT modify are noted but do NOT block. Fix only the
failures in code you changed. Do not expand scope to repair unrelated
pre-existing breakage.

## Step 5: Regenerate BUILD files after new source files

After creating new Python files, regenerate BUILD files so Pants picks them up:

```
pants_tailor(workspace_folder="<repo root>", target="::")
```

Batch this ONCE at the end of a task, not per file. `pants_tailor` takes
`target` only.

## Step 6: Partial workflows

When only part of the loop is needed, call the individual tools in order —
`pants_fix` → `pants_lint` → `pants_check` → `pants_test` — or use a named
workflow:

```
pants_workflow(workflow="fix-lint", workspace_folder="<repo root>")
```

Valid workflow names are `fix-lint`, `check-test`, and `fix-lint-check`. This
skill is the recommended entry point for the quality loop; `pants_workflow`
remains available for partial sequences and is equally valid. `pants_workflow`
takes `target` only.

## Step 7: Parallel non-Pants gate

Some monorepos have a second quality gate this power does NOT drive — for example
a TypeScript/JS gate run through the project's own tooling:

```
# EXAMPLE ONLY — a project-specific gate this power does not run:
npm run quality
```

Pants covers only the Pants-managed code. Remind the user to run BOTH gates
before opening a PR.

## Step 8: On failure

Read the failing step's output, run `pants_fix` to auto-resolve formatting, then
re-run the failing step. Code-level lint, type, and test failures are normal
development feedback — fix the code. See the `troubleshooting` skill for the
stop-on-infrastructure-error rule.
