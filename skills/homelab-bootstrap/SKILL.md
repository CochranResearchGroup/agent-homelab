---
name: homelab-bootstrap
description: Bootstraps Agent Homelab with Traefik and optional Authelia for combined, direct, or bastion-relay Linux topologies. Use when asked to "set up my homelab", install Traefik, install Authelia, create the first inventory, or prepare a new service host or edge gateway.
license: Apache-2.0
---

# Homelab Bootstrap

Use discovery, plan, apply, and verification as separate gates.

## Reference files

| File | Read when |
|---|---|
| [references/topology-and-inputs.md](references/topology-and-inputs.md) | Selecting topology or gathering required operator inputs |

## Workflow

Copy and track:

- [ ] Inspect OS, Docker Compose, SSH, occupied ports, DNS, and node reachability without mutation.
- [ ] Select combined/direct or relay topology from the actual node layout.
- [ ] Create `homelab.yaml` with `scripts/bootstrap.sh`; keep it untracked.
- [ ] Replace every reserved example with operator-provided values and secret references.
- [ ] Run `agent-homelab doctor` and `agent-homelab validate`.
- [ ] Render to a staging directory and review every node manifest.
- [ ] Create ignored `.env` and secret files with mode `0600`.
- [ ] Run `plan` and `apply --dry-run` for one node at a time.
- [ ] Apply only after destination, validation, reload, backup, and rollback behavior are understood.
- [ ] Verify the health route, TLS, authentication, and one example service.

Do not infer DNS credentials, SSH targets, real domains, account addresses, or secret values. Missing secret material is an operator input, not a reason to write placeholders into a live config.

## Validation loop

When any gate fails, fix the durable inventory or template input, rerender, and repeat from validation. Do not patch generated files as the durable fix.

## Gotchas

- A container restart policy does not prove Docker is running after host boot.
- The default ACME HTTP challenge requires public port 80 reachability.
- A relay gateway should reach service-host Traefik, not every raw application port.
- Authelia middleware without an access-control rule commonly returns `403`.
- Never add `homelab.yaml`, `.env`, `secrets/`, ACME state, or rendered private config to Git.

## Related skills

- Use `homelab-service-ingress` after the base topology is healthy.
- Use `homelab-troubleshooter` when a bootstrap verification gate fails.
