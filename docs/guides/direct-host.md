# Direct-host setup

Use a node with both `service_host` and `edge_gateway` roles. The public router terminates TLS and forwards directly to the application upstream. Run `agent-homelab init --topology combined`, replace all example values, configure `.env` and secret files, then validate, render, plan, apply, and verify.

Port 80 must be reachable for the default ACME HTTP challenge. Port 443 serves public routes. Keep raw application ports restricted to the host.
