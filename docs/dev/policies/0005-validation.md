# Policy | Validation

- Match evidence to the touched surface; a render check cannot prove remote runtime behavior.
- Inventory changes require schema and semantic validation.
- Renderer changes require direct, combined, relay, path-route, and Authelia golden behavior plus idempotence checks.
- Deployment changes require dry-run, unchanged second apply, invalid-stage rejection, backup, and rollback tests.
- OAuth relay changes require state mismatch, expiry, replay, callback host/path, redirect allowlist, adapter failure, and log-redaction tests.
- Skills require frontmatter, line-count, reference-link, script-help, and clean-install checks.
- Releases require tests, lint, build, package inspection, secret/privacy scans, dependency audit, and container scan evidence.
