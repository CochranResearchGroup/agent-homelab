---
name: homelab-oauth-relay
description: Installs and validates Agent Homelab's optional headless OAuth callback relay and credential-health checks. Use when asked to relay OAuth callbacks, reauthorize a CLI remotely, configure GOG/GWS authorization, or monitor expiring credentials.
license: Apache-2.0
---

# Homelab OAuth Relay

Treat provider adapters as trusted local code and callback data as credential material.

## Reference files

| File | Read when |
|---|---|
| [references/provider-adapter-contract.md](references/provider-adapter-contract.md) | Implementing or reviewing an OAuth provider adapter |

## Workflow

Copy and track:

- [ ] Read `recipes/oauth-relay/THREAT_MODEL.md`.
- [ ] Copy example config into an ignored operator directory.
- [ ] Configure the HTTPS public base URL, loopback bind, exact authorization host allowlist, adapter commands, and synthetic tenant aliases.
- [ ] Keep client material and real accounts in ignored adapter config or environment references.
- [ ] Test the adapter start and finish paths without logging callback data.
- [ ] Run state mismatch, expiry, replay, callback host/path, redirect allowlist, and redaction tests.
- [ ] Install the user service with restrictive filesystem access.
- [ ] Publish the relay through authenticated ingress; do not bind it publicly by default.
- [ ] Configure credential-health commands and a notifier if desired.
- [ ] Verify a complete authorization and one repeated-callback rejection.

## Validation loop

Any unexplained callback, state, redirect, or log behavior is a security failure. Disable public routing while fixing it.

## Gotchas

- Authelia on the start route does not replace OAuth state validation.
- `state_mode: adapter` trusts the adapter to generate strong state; weak state is rejected.
- Query strings can contain authorization codes and must never appear in logs or error responses.
- Callback host comparison is exact; proxy configuration must preserve the intended public Host header.
- Credential health checks should report names and exit codes, never credential output.

## Related skills

- Use `homelab-service-ingress` to publish the relay route.
- Use `homelab-troubleshooter` for edge/auth/callback failures.
