# Agent Homelab

## Repo Context

- Describe the product area, architecture boundaries, and canonical planning surfaces here.

## Repo-Specific Guidance

- Add the exact build, test, deploy, and service-boundary rules this repo expects.

## Policy Loading Contract

- `AGENTS.md` is a routing surface, not a one-time pointer.
- Re-read the relevant policy files under `docs/dev/policies/` at the start of any non-trivial turn.
- Re-read the relevant policy files when task scope changes mid-session.
- When behavior is ambiguous, prefer re-reading policy over improvising from stale assumptions.

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
- `docs/dev/policies/0025-planning-discipline.md`
- `docs/dev/policies/0027-subagent-runtime-governance.md`
- `docs/dev/policies/0029-active-lane-coordination.md`
- `docs/dev/policies/0031-code-testing-discipline.md`

## Scope

- `AGENTS.md` includes repo-local guidance plus the policy entry section.
- The durable policy body lives under `docs/dev/policies/`.
- Keep repo-specific commands, environment details, and operational caveats in this file or adjacent local docs.
