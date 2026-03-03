---
inclusion: auto
---

# Product Overview

The Pants DevContainer Power is a Kiro Power that provides MCP (Model Context Protocol) tools for managing the NACC Flywheel Extensions development workflow.

## Purpose

This power eliminates friction by automatically wrapping Pants build system commands with devcontainer execution, ensuring all commands run in the proper containerized environment. It consolidates knowledge from multiple steering documents into executable tools that enforce best practices and reduce manual overhead.

## Key Features

- Zero-friction execution: Developers invoke Pants commands directly; the power handles container management
- Fail-fast feedback: Commands stop on first error with clear diagnostic information
- Workflow automation: Common command sequences (fix → lint → check → test) available as single operations
- Idempotent operations: Container start operations are safe to call repeatedly
- Target flexibility: Support both full monorepo operations (::) and specific target execution

## Target Users

Developers working on the NACC Flywheel Extensions monorepo who need to run Pants build commands within a devcontainer environment without manual container management overhead.
