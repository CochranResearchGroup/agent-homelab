# First homelab: ingress, services, and recovery

This sequence brings up a direct host or a service host relayed through an edge gateway without placing runtime identity or secrets in Git.

## 1. Prepare hosts

Install Linux, Docker Engine with Compose v2, Python 3.11 or newer, OpenSSH for relay deployments, and BorgBackup 1.4 on every host that owns backup sources. Confirm DNS points only at the intended edge gateway and that relay links use an operator-approved private transport.

## 2. Create ingress inventory

```bash
agent-homelab init homelab.yaml --topology relay
agent-homelab doctor --inventory homelab.yaml
```

Replace all documentation addresses and domains in the ignored inventory. Set node deployment roots, SSH aliases, state roots, validation commands, and reload commands. Validate before rendering.

## 3. Bootstrap edge and service hosts

```bash
agent-homelab validate --inventory homelab.yaml
agent-homelab bootstrap --inventory homelab.yaml --node gateway --acme-email operator@example.invalid
agent-homelab bootstrap --inventory homelab.yaml --node gateway --acme-email operator@example.invalid --apply
agent-homelab render --inventory homelab.yaml --output rendered
agent-homelab plan --inventory homelab.yaml --rendered rendered --node gateway
```

Repeat for each service host. Apply one node at a time and verify the built-in health route before continuing.

## 4. Add services

Choose an entry from `recipes/services/catalog.yaml` and follow the `homelab-service-catalog` skill. Fetch the current official Compose source, pin it in private runtime state, configure its persistent storage and secrets, then validate the raw service before adding ingress.

```bash
agent-homelab service upsert documents \
  --inventory homelab.yaml \
  --upstream-node app-host \
  --port 8000 \
  --port-source 'compose.yaml published port' \
  --local-hostname documents.localhost \
  --public-hostname documents.example.net \
  --edge-node gateway \
  --auth-policy one_factor
```

Render, plan, apply, and verify both unauthenticated behavior and application behavior after login. Administrative services should default to Authelia protection or remain private-only.

## 5. Establish recovery before adding more services

Copy the Borg example into ignored operator state. Map every catalog persistence input, initialize per-stack repositories, run one manual backup, run an integrity check, and restore to a fresh staging directory. Keep repository keys and passphrases in a separate recovery location.

Only enable the timer after the staged restore passes. Then repeat the service and recovery workflow one stack at a time.

## 6. Operate

Use `homelab-maintenance` for drift, certificate, backup-freshness, and upgrade checks. Upgrade one application or infrastructure component at a time after a verified backup. Use `homelab-troubleshooter` to localize failures across DNS, TLS, edge routing, Authelia, relay reachability, origin routing, and application behavior.
