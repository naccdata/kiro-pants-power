# Raw Pants target → MCP intent parameters

Use this table to translate a raw Pants target specification into the intent
parameters accepted by `pants_fix`, `pants_lint`, `pants_check`, `pants_test`,
and `pants_package`. Every call also requires `workspace_folder` (the absolute
path to the repo root containing `.devcontainer/`).

| Raw Pants target | MCP intent parameters |
| --- | --- |
| `::` | `scope="all"` |
| `src/tests::` | `scope="directory", path="src/tests", recursive=true` |
| `src/tests:` | `scope="directory", path="src/tests", recursive=false` |
| `src/test.py` | `scope="file", path="src/test.py"` |
| `:: -k test_auth` | `scope="all", test_filter="test_auth"` |

Example in MCP-call form:

```
pants_test(workspace_folder="<repo root>", scope="directory", path="src/tests", recursive=true)
```

## Notes

- `path` is relative to the repository root.
- A directory needs a BUILD file. If none exists, run `pants_tailor` to generate
  one before scoping a command to that directory.
- The intent parameters (`scope`/`path`/`recursive`/`test_filter`) apply ONLY to
  `pants_fix`, `pants_lint`, `pants_check`, `pants_test`, and `pants_package`.
  `full_quality_check`, `pants_workflow`, and `pants_tailor` take the legacy
  `target` only.
- Source-root model: Pants monorepos typically declare `src/*` for sources and
  `test/*` (or `tests`) for tests. Scope to the directory you changed; use
  `scope="all"` only for cross-cutting changes. Test directories may need a
  distinct name or suffix from their source package to avoid Python namespace
  collisions that confuse type-checking and test collection.
