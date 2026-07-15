# Disaster recovery

Back up the ignored inventory, secret files, Authelia user database and SQLite storage, and ACME storage using an encrypted system outside this repository.

To recover:

1. restore inventory and secrets with restrictive permissions
2. install the same Agent Homelab version
3. validate and render without applying
4. inspect the plan for every node
5. restore Authelia and ACME state
6. apply one node at a time
7. verify authentication and application behavior

Every changed apply reports the backup path. Restore that tree if a new configuration fails after promotion.
