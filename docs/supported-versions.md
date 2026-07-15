# Supported versions

The v0.2 release line supports:

- Python 3.11 and newer
- Traefik 3.7.8
- Authelia 4.39.20
- Docker Compose v2
- OpenSSH client/server for remote deployment
- BorgBackup 1.4.x for the optional stack backup service
- BusyBox 1.37.0 for named-volume export unless the operator pins another reviewed image

Component images are intentionally pinned in renderer source. Upgrades require upstream release-note review, isolated rendering and validation, backup, one-node rollout, and smoke tests.
