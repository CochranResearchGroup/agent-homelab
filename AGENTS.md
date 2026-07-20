# Agent Homelab

## Repository context

This public repository provides a declarative Python CLI and installable agent skills for Traefik and Authelia homelab ingress. A node may be a `service_host`, an `edge_gateway`, or both. Public routes may terminate directly on the service host or relay through a separate edge gateway.

Tracked source and synthetic fixtures are product code. `homelab.yaml`, `secrets/`, `rendered/`, installed node directories, OAuth state, ACME data, and runtime logs are operator state and must remain untracked.

## Policy Loading Contract

- `AGENTS.md` is a routing surface, not a one-time pointer.
- Re-read the relevant policy files under `docs/dev/policies/` at the start of any non-trivial turn.
- Re-read the relevant policy files when task scope changes mid-session.
- When behavior is ambiguous, prefer re-reading policy over improvising from stale assumptions.

## Required workflow

- Use one inventory as the authority; generated files are derived.
- Run `agent-homelab validate` before rendering or applying.
- Use `plan` or `apply --dry-run` before mutation.
- Validate staged configuration before promotion and preserve the previous installed tree as a rollback backup.
- Never place credentials or private topology in source, fixtures, issues, logs, or agent memory.
- Use only reserved example domains and documentation IP ranges in tracked files.

## Development commands

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/agent-homelab validate --inventory tests/fixtures/relay.yaml
.venv/bin/agent-homelab render --inventory tests/fixtures/relay.yaml --output rendered
scripts/validate-skills.py
scripts/scan-public.sh
```

Do not test apply against a real host unless the user explicitly puts that host and inventory in scope.

## Policy Re-read Triggers

- re-read planning-related policy before opening, revising, or closing a substantive plan
- re-read documentation-related policy before changing docs, contracts, or canonical authorities
- re-read validation and closeout policy before claiming work complete
- re-read branch, commit, and integration policy before starting a multi-file or multi-step implementation slice

## Policy Entry

This repo keeps its durable repo-local policy under `docs/dev/policies/`.

Read and follow:
- `docs/dev/policies/0001-policy-management.md`
- `docs/dev/policies/0002-product-runtime-boundary.md`
- `docs/dev/policies/0003-remote-operations.md`
- `docs/dev/policies/0004-privacy-and-release.md`
- `docs/dev/policies/0005-validation.md`
- `docs/dev/policies/0006-git-and-closeout.md`
- `docs/dev/policies/0007-policy-upgrade-management.md`
- `docs/dev/policies/0008-policy-adoption-feedback-loop.md`
- `docs/dev/policies/0009-notes-and-memories.md`
- `docs/dev/policies/0010-graph-backed-memory-usage.md`
- `docs/dev/policies/0011-codegraph-usage.md`
- `docs/dev/policies/0013-goal-execution-governance.md`
- `docs/dev/policies/0014-parallel-plan-design.md`
- `docs/dev/policies/0016-architecture-guardrails.md`
- `docs/dev/policies/0017-documentation-change-control.md`
- `docs/dev/policies/0018-git-worktree-hygiene.md`
- `docs/dev/policies/0019-branch-and-integration-strategy.md`
- `docs/dev/policies/0020-multi-agent-reconciliation.md`
- `docs/dev/policies/0021-subagent-workflow-optimization.md`
- `docs/dev/policies/0022-turn-closeout.md`
- `docs/dev/policies/0023-validation-and-handoff.md`
- `docs/dev/policies/0024-upstream-fork-maintenance.md`

## Scope

- `AGENTS.md` includes repo-local guidance plus the policy entry section.
- The durable policy body lives under `docs/dev/policies/`.
- Keep repo-specific commands, environment details, and operational caveats in this file or adjacent local docs.
