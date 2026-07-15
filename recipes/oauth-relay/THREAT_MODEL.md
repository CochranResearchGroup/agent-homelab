# OAuth relay threat model

## Protected assets

- OAuth authorization codes and refresh credentials
- provider tenant selection
- callback integrity
- adapter command environment

## Trust boundaries

- Traefik and the optional authentication gate terminate public access.
- The relay binds to loopback by default.
- Provider adapters are trusted local executables and receive callback data through environment variables.
- The state file is local, mode `0600`, and stores only state hashes.

## Required controls

- State values are cryptographically random, short-lived, provider/tenant-bound, and consumed once.
- Returned provider authorization URLs must preserve state, use HTTPS, and match an exact host allowlist.
- Callback requests must match the configured public host and exact callback path.
- Request logging strips query strings; adapter failures never return subprocess output to clients.
- Configuration contains command paths and tenant aliases, not client secrets or credentials.
- The relay start route should be placed behind Authelia or an equivalent gate when publicly reachable.

## Explicit non-goals

- The relay does not implement provider token exchange itself.
- The relay does not make an unsafe provider adapter safe.
- The relay does not replace TLS or ingress authentication.
