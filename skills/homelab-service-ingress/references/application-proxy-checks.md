# Application proxy checks

After the router responds, inspect:

- `Location`, `Link`, and canonical URL headers
- HTML, API docs, and asset URLs for raw host or port leakage
- secure, domain, path, and same-site cookie attributes
- CSRF and allowed-host configuration
- OAuth and webhook callback URLs
- forwarded host/protocol trust
- WebSocket origin behavior
- subpath base URL behavior when path routes are used

Treat a correct status code with incorrect generated URLs as an application failure, not a completed ingress setup.
