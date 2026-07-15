# Topology and inputs

Choose combined/direct when the public gateway and application upstreams share one Linux host. Choose relay when a separate edge gateway terminates public TLS and forwards to a service-host Traefik instance.

Required inputs:

- public base domain and DNS ownership
- node roles and existing reachable addresses
- SSH aliases for remote nodes
- durable deployment roots
- public ports 80/443 availability
- stable application ports and their source config
- ACME contact address stored in ignored `.env`
- Authelia user database and three generated secret files when authentication is enabled

Existing Tailscale or WireGuard addresses can be used as relay addresses. This skill does not install or configure the mesh itself.
