# Policy | Privacy and release

- Tracked content must use reserved domains, `.invalid` addresses, and documentation IP ranges.
- Do not track names, account addresses, usernames, real domains, hostnames, public or private deployment addresses, tenant names, tokens, passwords, key material, cookies, ACME data, or private logs.
- Build public source from an allowlist or clean tree; never publish private Git history.
- Before release, scan source and history with Gitleaks, run the private-pattern gate, inspect built packages and containers, and run dependency/container vulnerability checks.
- Create or update the public remote only after local validation passes.
- Publish prereleases for compatibility-significant early versions and verify visibility, default branch, commit, tag, and release metadata after publication.
