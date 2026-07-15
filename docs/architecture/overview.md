# Architecture

The inventory is the only durable routing authority. Rendering creates a node tree for each declared machine.

## Roles

- `service_host` owns stable application upstreams and the origin Traefik route.
- `edge_gateway` owns public TLS and optional Authelia.
- A combined node owns both roles.

For relay topology, edge Traefik forwards the public hostname to service-host Traefik. The origin router preserves host-based and path-based dispatch while avoiding public exposure of every application port.

## Apply lifecycle

`validate -> render -> plan -> stage -> validate stage -> backup -> promote -> reload -> verify`

An invalid stage never replaces the installed tree. A failed reload restores the backup. A second apply with the same tree reports `unchanged` and does not reload.

## Authorities

- Inventory: desired topology and deployment commands
- Rendered tree: disposable desired artifacts
- Installed tree: current node runtime input
- State root: ignored Authelia users/database, secrets, ACME storage, and runtime environment
- Containers: runtime state, never the sole durable authority
