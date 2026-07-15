---
name: homelab-maintenance
description: Maintains Agent Homelab Traefik and Authelia nodes with drift inspection, backup, guarded apply, health verification, and rollback. Use when asked to check homelab health, reconcile configuration, upgrade ingress, verify certificates, or perform routine maintenance.
license: Apache-2.0
---

# Homelab Maintenance

Maintenance is read-only until a reviewed drift plan identifies a durable change.

## Reference files

| File | Read when |
|---|---|
| [references/maintenance-evidence.md](references/maintenance-evidence.md) | Reporting drift, upgrade, backup, or recovery evidence |

## Workflow

Copy and track:

- [ ] Check Git and inventory state; keep runtime data out of the repo.
- [ ] Run `scripts/check.sh` for validation and node drift.
- [ ] Inspect container health, certificates, Authelia storage, backup freshness, and route probes.
- [ ] Classify drift as desired inventory change, stale generated output, installed-state drift, or runtime-only failure.
- [ ] For upgrades, read upstream release notes and change one component version at a time.
- [ ] Render, validate, plan, and dry-run the bounded change.
- [ ] Confirm a usable backup and explicit rollback command.
- [ ] Apply one node at a time and verify before continuing.
- [ ] Record exact versions, files, backup paths, reloads, probes, and remaining risk.

## Validation loop

Do not proceed to the next node during an upgrade until current routes and authentication behavior pass. Roll back before widening scope when a regression appears.

## Gotchas

- Running containers can be healthy while installed config has drifted from inventory.
- A second identical apply should be `unchanged`; an unexpected diff means rendering or runtime state is nondeterministic.
- Back up Authelia database and secret files, not only generated YAML.
- Certificate expiry checks do not prove the backend or authentication route works.
- Never edit only the running container and call the repair durable.

## Related skills

- Use `homelab-troubleshooter` to localize failures found by maintenance.
- Use `homelab-service-ingress` for service-specific inventory changes.
