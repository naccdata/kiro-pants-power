---
name: setup
description: Set up and verify the Pants devcontainer environment — check Docker and the devcontainers CLI, start the container, install Pants using the repo's install method, and confirm it runs.
---

# Set up the Pants devcontainer environment

Every tool in this power requires `workspace_folder`: the absolute path to the
repository root that contains the `.devcontainer/` directory. Pass it on every
call.

## Step 1: Validate prerequisites

Confirm the host has what the devcontainer needs:

- Docker is running: `docker ps` should succeed.
- The devcontainers CLI is installed: `devcontainer --version`.
- The repository has a `.devcontainer/` directory at its root.

Optionally run this skill's preflight to check Docker and the CLI in one shot:

```sh
scripts/validate-setup.sh
```

It is read-only — it checks presence and exits non-zero with a one-line reason
when something is missing. It installs nothing.

## Step 2: Start the container

```
container_start(workspace_folder="<repo root>")
```

This tool is idempotent and auto-starts the container. If the container is
already running, the call is a no-op, so re-running it as a manual fallback is
safe.

## Step 3: Confirm Pants is available

```
container_exec(workspace_folder="<repo root>", command="pants --version")
```

Do NOT assume or assert a specific Pants version — it comes from the
devcontainer. Report whatever `pants --version` prints.

## Step 4: Install Pants if it is missing

If step 3 reports "pants not found", install Pants INSIDE the container using
the repository's own install method. Installation always happens in the
container, never on the host.

Many repositories ship an install script. Run it in the container, for example:

```
container_exec(workspace_folder="<repo root>", command="bash get-pants.sh")
```

> EXAMPLE ONLY: `get-pants.sh` is a repo-specific script name. It is not part of
> this power and is not guaranteed to exist in any repository. Use the repo's own
> install method. If the repository has no install script, follow the official
> instructions at https://www.pantsbuild.org/docs/installation.

After installing, add the install directory to `PATH` and re-verify:

```
container_exec(workspace_folder="<repo root>", command="pants --version")
```

## Concepts to keep in mind

### Two-environment model

A host `.venv` (if present) exists ONLY for IDE analysis — autocomplete and type
hints in your editor. ALL execution — fix, lint, check, test, package — happens
inside the container via Pants and this power's tools. Never run Pants on the
host.

### Image assumption

The devcontainer image ships Python preinstalled (the standard devcontainers
Python image). Pants itself is added inside the container via the repository's
own install method — an install script if the repo ships one, otherwise the
pantsbuild.org install docs. Do not hardcode an image name or a specific
install-script name.

### Shell behavior

`container_shell` opens an interactive `/bin/zsh -l`, which is correct for the
standard devcontainers Python image (it ships zsh). If a consumer's image lacks
zsh, bash is the safe fallback. Non-interactive `container_exec` runs the image's
default shell regardless, and you should not assume a `.zshrc` exists in every
image.
