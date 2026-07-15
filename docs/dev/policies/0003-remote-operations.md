# Policy | Remote operations

- Remote mutations require an inventory-declared node, SSH alias, deployment root, and requested apply operation.
- Inspect and validate before mutation. Render to staging, validate staging, preserve the current destination, promote atomically, then reload.
- Roll back to the preserved destination when reload fails.
- Never discover a convenient SSH target and assume it is authorized.
- Never use a shell command from untrusted service data. Deployment commands belong in operator-controlled inventory.
- Report the node, destination, validation command, reload result, backup path, and smoke-test evidence.
