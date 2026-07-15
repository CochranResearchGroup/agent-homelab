# Disaster recovery

Back up the ignored inventory, secret files, Authelia user database and SQLite storage, ACME storage, and every service recipe persistence input using an encrypted system outside this repository. See [Borg backups](borg-backups.md) for the included host-side runner.

To recover:

1. restore inventory and secrets with restrictive permissions
2. install the same Agent Homelab version
3. validate and render without applying
4. inspect the plan for every node
5. restore Authelia and ACME state
6. apply one node at a time
7. verify authentication and application behavior
8. restore one service into staging and verify its application-native data before replacing live state

Every changed apply reports the backup path. Restore that tree if a new configuration fails after promotion.
