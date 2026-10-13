---
name: targeting
description: Scope Pants commands to a directory, file, or test name using scope, path, recursive, and test_filter instead of raw Pants target syntax.
---

# Scope Pants commands with intent parameters

Every tool requires `workspace_folder`: the absolute path to the repository root
containing `.devcontainer/`. Pass it on every call.

## Step 1: The intent parameters

On `pants_fix`, `pants_lint`, `pants_check`, `pants_test`, and `pants_package`:

- `scope`: `all`, `directory`, or `file`.
- `path`: required for `directory` and `file` scopes; relative to the repo root.
- `recursive`: directory scope only, default `true` — include subdirectories.
- `test_filter`: pytest-style name filter, `pants_test` only.

## Step 2: Which tools take which parameter (CRITICAL)

The intent parameters (`scope`/`path`/`recursive`/`test_filter`) apply ONLY to
`pants_fix`, `pants_lint`, `pants_check`, `pants_test`, and `pants_package`.

The remaining tools — `full_quality_check`, `pants_workflow`, and `pants_tailor`
— take the legacy `target` only. Do NOT pass `scope`/`path` to them.

## Step 3: `target` is deprecated on the intent-aware tools

Prefer the intent parameters on the five intent-aware tools. Keep `target` only
when reproducing a legacy raw-syntax call, or when calling the three target-only
tools above.

## Step 4: Concrete examples

```
pants_test(workspace_folder="<repo root>", scope="directory", path="<test-dir>", recursive=true)
pants_test(workspace_folder="<repo root>", scope="all", test_filter="test_auth")
pants_check(workspace_folder="<repo root>", scope="file", path="<path/to/module>")
```

Keep any real directory name as a labeled example, not a baked-in default.

## Step 5: Source-root model

Pants monorepos typically declare source roots like `src/*` for sources and
`test/*` (or `tests`) for tests. Scope to the directory you changed; use
`scope="all"` only for cross-cutting changes.

## Step 6: Test-directory naming gotcha

Test directories may need a distinct name or suffix from their source package to
avoid Python namespace collisions that confuse type-checking and test
collection. Treat this as a principle; show real suffixes only as labeled
examples (for example, a `_test` suffix on a package directory).

## Step 7: Mapping reference

For the raw Pants target → intent-parameter mapping, consult
`references/target-mapping.md`.
