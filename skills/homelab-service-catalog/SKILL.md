---
name: homelab-service-catalog
description: Deploys privacy-safe application stacks from the Agent Homelab service recipe catalog and connects them to ingress and backup. Use when asked to install Paperless-ngx, Immich, Nextcloud AIO, GitLab, Joplin Server, n8n, Odoo, OpenSign, code-server, Portainer, Syncthing, WordPress, or another catalog service.
license: Apache-2.0
---

# Homelab Service Catalog

Use the recipe as an operational contract, then obtain complex Compose definitions from the named upstream authority. Do not copy a private deployment or silently improvise a stale stack.

## Reference files

| File | Read when |
|---|---|
| [references/service-lifecycle.md](references/service-lifecycle.md) | Planning storage, secrets, ingress, backup, or completion evidence for a catalog service |

## Workflow

Copy and track:

- [ ] Run `scripts/show-recipe.py <recipe>` and read the recipe's official deployment source.
- [ ] Confirm the host role, resource budget, persistent-storage root, and raw upstream port.
- [ ] Fetch the upstream release or Compose definition into an ignored operator-owned stack directory.
- [ ] Pin the selected release or image versions and save only secret references in durable configuration.
- [ ] Map every recipe persistence item to a bind mount, named volume, or application-native backup.
- [ ] Validate Compose before startup, then start the raw service and probe its documented health path.
- [ ] Set every canonical URL, callback, proxy, websocket, and forwarded-header option listed by the recipe.
- [ ] Register the pinned upstream with `agent-homelab service upsert`, render, plan, and apply ingress.
- [ ] Add the service to the Borg configuration unless its recipe requires an application-native backup owner.
- [ ] Run route, application, backup, integrity-check, and staged-restore validation.
- [ ] Record versions, source URLs, state paths by logical name, probes, and remaining manual steps without logging secret values.

## Validation loop

Treat raw service health, ingress reachability, application proxy correctness, and recovery as four separate gates. If one fails, fix that layer and repeat all downstream gates. A service is not complete until a staged restore demonstrates that the listed persistence boundary is usable.

## Gotchas

- `latest` in an upstream example is not an unattended upgrade policy; pin the reviewed release in runtime state.
- Nextcloud AIO owns sibling containers and its backup lifecycle. Do not replace AIO backup with a mastercontainer-only archive.
- Portainer and code-server are administrative access surfaces; external authentication does not reduce Docker socket or shell privileges.
- Immich database files need local storage even when the photo library uses another storage tier.
- n8n recovery requires its encryption key as well as database and application data.
- GitLab, Odoo, and WordPress need application/database exports coordinated with filesystem state.
- Syncthing replication is not a versioned backup and must not recursively synchronize a Borg repository into its own source tree.

## Related skills

- Use `homelab-service-ingress` to render and verify the selected route.
- Use `homelab-borg-backup` to add and test the recovery boundary.
- Use `homelab-troubleshooter` when a raw service works but ingress behavior fails.
