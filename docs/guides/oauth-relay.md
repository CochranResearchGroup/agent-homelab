# OAuth relay

The optional relay supports headless and CLI OAuth flows through local command adapters. It binds to loopback by default and should be exposed only through authenticated ingress.

Copy the recipe examples to an ignored operator directory, configure exact provider authorization hosts, tenant aliases, and adapter commands, then run:

```bash
agent-homelab-oauth-relay --config oauth-relay.yaml
```

Adapters receive provider, tenant, redirect URI, state, and callback URL through environment variables. They must never print tokens or callback payloads. `state_mode: relay` requires the adapter to preserve relay-generated state. `state_mode: adapter` supports tools that generate their own strong state; the relay still binds it to one provider and tenant, expires it, and consumes it once.

The included GOG/GWS adapter is configuration-driven. Account addresses, client aliases, config directories, and credentials stay in ignored operator files.
