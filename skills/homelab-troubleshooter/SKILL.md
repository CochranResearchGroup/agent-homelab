---
name: homelab-troubleshooter
description: Diagnoses Agent Homelab failures across DNS, TLS, edge Traefik, Authelia, relay reachability, service-host Traefik, and application proxy behavior. Use when a route returns 302, 403, 404, 502, has certificate errors, or behaves incorrectly behind ingress.
license: Apache-2.0
---

# Homelab Troubleshooter

Start read-only and identify the first failing layer.

## Reference files

| File | Read when |
|---|---|
| [references/status-map.md](references/status-map.md) | Mapping HTTP/TLS symptoms to the next probe |

## Workflow

Copy and track:

- [ ] Record the exact URL, expected auth behavior, observed status, headers, and time.
- [ ] Validate inventory and inspect the desired node plan.
- [ ] Resolve DNS and inspect the served certificate.
- [ ] Probe edge Traefik locally with the public Host header.
- [ ] For protected routes, probe Authelia health and rule presence.
- [ ] In relay mode, test gateway-to-origin address reachability.
- [ ] Probe service-host Traefik with local and public Host headers.
- [ ] Probe the raw upstream.
- [ ] Inspect application URLs, cookies, callbacks, assets, and WebSockets.
- [ ] Repair the narrow durable authority, rerender, dry-run, apply, and repeat the failed probe.

## Output contract

Report the failing layer, evidence, durable authority, bounded repair, validation, and anything still unverified.

## Validation loop

After a repair, rerun the exact failed probe and every downstream layer. A changed status without the expected authentication or application behavior is not resolution.

## Gotchas

- Redirects to `auth.<domain>` are expected for unauthenticated protected routes.
- `403` often means Authelia is reachable but policy does not allow the hostname.
- `404` usually points to a missing router or wrong Host rule.
- `502` usually points to edge-to-origin or origin-to-upstream reachability.
- A successful raw upstream does not prove edge, TLS, auth, or application proxy correctness.
- Do not mutate containers before identifying the durable inventory or installed config authority.

## Related skills

- Use `homelab-service-ingress` for the durable service repair.
- Use `homelab-maintenance` when the incident reveals broader drift.
