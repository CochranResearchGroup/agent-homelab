# Status map

| Symptom | Likely layer | Next probe |
|---|---|---|
| DNS failure | DNS | authoritative and client resolution |
| TLS name/expiry error | edge TLS | certificate and SNI on port 443 |
| `302` to auth host | expected protected route | authenticate, then probe backend |
| `403` | Authelia policy | matching access-control rule and identity policy |
| `404` | Traefik router | loaded dynamic config, Host rule, entrypoint |
| `502` | relay/upstream | gateway-to-origin, then origin-to-app |
| `200` without auth | missing middleware | public router middleware and Authelia rule |
| Broken assets/callbacks | application | forwarded headers and canonical/base URL config |
