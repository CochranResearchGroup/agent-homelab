# Changelog

## 0.2.0-rc.2

- Established operator-owned Docker Compose project directories as the recommended authority for agent-managed services.
- Kept Portainer as an optional recipe for visibility and manual diagnostics rather than a primary control plane.
- Added `agent-homelab recipe policy` so installed agents can inspect the operating recommendation.

## 0.2.0-rc.1

- Added a privacy-safe catalog for twelve Compose-managed homelab services.
- Added a guarded BorgBackup runner with per-stack repositories, named-volume export, retention, checks, and staging restores.
- Added service-catalog and Borg-backup agent skills plus a full first-homelab guide.

## 0.1.0-rc.1

- Added schema-versioned direct, combined, and bastion-relay inventories.
- Added deterministic Traefik and Authelia rendering.
- Added plan-first local and SSH deployment with validation, backup, rollback, and idempotence.
- Added safe node bootstrap, recovery bundles, drift maintenance, service management, and route verification.
- Added five installable agent skills.
- Added the optional generic OAuth relay, GOG/GWS adapter, credential health checks, and threat-model tests.
- Added privacy, Gitleaks, dependency, artifact, and container security gates.
