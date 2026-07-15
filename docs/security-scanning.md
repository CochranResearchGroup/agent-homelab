# Security scanning policy

Release gates include:

- Gitleaks over the clean tree and Git history
- a private identity/topology denylist maintained outside the public repo
- scans of the wheel, source distribution, and agent-skill bundle
- `pip-audit` with no known runtime or development dependency vulnerabilities
- Trivy over the built OAuth relay container

Container publication is blocked by fixed HIGH or CRITICAL vulnerabilities. Unfixed findings are reported but do not automatically block a release candidate; maintainers must document any accepted risk. Secret findings always block publication.
