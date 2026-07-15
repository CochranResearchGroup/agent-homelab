# Agent Homelab

## Repository context

This public repository provides a declarative Python CLI and installable agent skills for Traefik and Authelia homelab ingress. A node may be a `service_host`, an `edge_gateway`, or both. Public routes may terminate directly on the service host or relay through a separate edge gateway.

Tracked source and synthetic fixtures are product code. `homelab.yaml`, `secrets/`, `rendered/`, installed node directories, OAuth state, ACME data, and runtime logs are operator state and must remain untracked.

## Policy loading contract

Re-read the relevant files under `docs/dev/policies/` at the start of non-trivial work and whenever scope changes:

- `0001-policy-management.md`
- `0002-product-runtime-boundary.md`
- `0003-remote-operations.md`
- `0004-privacy-and-release.md`
- `0005-validation.md`
- `0006-git-and-closeout.md`

Re-read `0003` and `0005` before changing deployment behavior. Re-read `0004` and `0005` before any public push or release. Re-read `0005` and `0006` before claiming completion.

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
