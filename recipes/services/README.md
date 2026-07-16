# Service recipe catalog

`catalog.yaml` is an agent-oriented map from a service name to its upstream deployment authority, ingress contract, persistent state, backup consistency level, and high-risk setup details.

The catalog recommends one operator-owned Docker Compose project directory per service. Use that directory as the deployment authority for agent operations, upgrades, backup mapping, and recovery. Portainer remains an optional recipe for visibility and manual diagnostics, not the primary control plane.

The catalog deliberately does not copy private Compose files or freeze complex upstream stacks. For services whose maintainers publish a release-specific Compose bundle, fetch that bundle from the listed official source, pin the selected release in operator-owned runtime state, and record the resulting upstream port with `agent-homelab service upsert`.

Use the catalog in this order:

1. Select a recipe and read its official deployment source.
2. Create a private stack directory and runtime secret files.
3. Pin images or the upstream release; do not deploy floating tags unattended.
4. Start the raw service and validate its documented health path.
5. Add it to the Agent Homelab inventory and validate ingress behavior.
6. Register every listed persistence input with the Borg backup configuration.
7. Run a backup, integrity check, and staged restore before considering the service complete.

`application-native-plus-stop` means the service's supported export or database-dump mechanism remains part of the recovery design even when a stopped filesystem snapshot is also taken. `application-native` means the application's own backup workflow is authoritative.
