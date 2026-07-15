# Bastion relay

Use one `service_host` and one `edge_gateway`. The service host exposes only its Traefik ingress to the gateway over an existing LAN or Tailscale/WireGuard address. The gateway terminates TLS and preserves the public `Host` header.

Validate in layers:

1. raw upstream on the service host
2. origin Traefik with the public Host header
3. gateway-to-origin reachability
4. public TLS router
5. Authelia redirect when protected
6. application links, redirects, cookies, callbacks, assets, and WebSockets

A `502` usually means the edge router loaded but cannot reach the origin. A `404` usually means the expected router did not load or the hostname is wrong.
