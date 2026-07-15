# Security policy

## Reporting

Use GitHub private vulnerability reporting for this repository. Do not open a public issue containing credentials, private topology, OAuth callback data, or exploit details.

## Deployment responsibility

Agent Homelab generates and deploys security-sensitive proxy and identity configuration. Operators must review plans, provide secrets outside Git, restrict SSH access, back up Authelia state, and test authentication before relying on a route.

## Supported versions

Security fixes target the latest prerelease or stable release. Older prereleases may be unsupported.

## Secret boundary

Inventories contain references, not values. Keep `.env`, `secrets/`, OAuth state, ACME state, rendered private configuration, and backups outside version control with restrictive filesystem permissions.
