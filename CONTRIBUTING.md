# Contributing

1. Use only synthetic domains, identities, and documentation IP addresses in changes and tests.
2. Add tests for behavior and safety invariants.
3. Run `make check` before opening a pull request.
4. Explain operator impact and rollback behavior for deployment changes.
5. Never include live inventory, generated private config, credentials, screenshots, or logs.

Changes to inventory schema require a versioning and migration note. Changes to deployment or OAuth behavior require threat-focused tests.
