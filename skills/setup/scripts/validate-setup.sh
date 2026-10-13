#!/bin/sh
# Read-only preflight for the Pants devcontainer environment.
# Checks that Docker and the devcontainers CLI are present and that the Docker
# daemon is responsive. Installs nothing and mutates no state.
# Exits non-zero with a one-line reason when a prerequisite is missing;
# exits 0 when all prerequisites are present.

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found on PATH; install Docker and ensure it is running" >&2
  exit 1
fi

if ! docker ps >/dev/null 2>&1; then
  echo "docker is installed but the daemon is not responding; start Docker" >&2
  exit 1
fi

if ! command -v devcontainer >/dev/null 2>&1; then
  echo "devcontainer CLI not found on PATH; install with: npm install -g @devcontainers/cli" >&2
  exit 1
fi

echo "OK: docker and devcontainer CLI are present and Docker is responding"
exit 0
