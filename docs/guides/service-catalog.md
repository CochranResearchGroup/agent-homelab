# Service catalog

The public catalog in `recipes/services/catalog.yaml` captures reusable service patterns observed in a multi-stack edge gateway without copying its Compose files, domains, paths, accounts, or network details.

It currently covers code-server, GitLab, Immich, Joplin Server, n8n, Nextcloud AIO, Odoo, OpenSign, Paperless-ngx, Portainer CE, Syncthing, and WordPress.

Each recipe records:

- the official upstream deployment authority
- the internal upstream scheme, port, and health path
- canonical URL and secret-setting names
- durable state that must survive replacement
- the backup consistency owner
- ingress behavior and high-risk setup details

Complex applications evolve faster than this project. The catalog therefore points agents to official release-specific Compose sources instead of embedding a private or stale copy. Pin the selected upstream release in ignored operator state, validate it, and record the raw port in the Agent Homelab inventory.

Use the `homelab-service-catalog` skill for the full install-to-recovery workflow.
