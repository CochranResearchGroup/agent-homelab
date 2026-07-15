# Supported versions

The v0.1 release line supports:

- Python 3.11 and newer
- Traefik 3.7.8
- Authelia 4.39.20
- Docker Compose v2
- OpenSSH client/server for remote deployment

Component images are intentionally pinned in renderer source. Upgrades require upstream release-note review, isolated rendering and validation, backup, one-node rollout, and smoke tests.
