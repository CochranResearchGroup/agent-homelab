# Backup and restore contract

Agent Homelab targets BorgBackup 1.4 syntax. Keep one repository per stack to bound checks, retention, and recovery permissions. The runtime config contains repository locations and source paths; the environment file contains the passphrase.

Daily flow:

1. validate Compose, source paths, named volumes, and repository access
2. stop the stack when configured
3. export named volumes into a private temporary directory
4. create an encrypted Borg archive from host paths and volume exports
5. prune the configured daily, weekly, and monthly windows
6. compact the repository
7. restart the stack even when archive creation fails
8. probe raw and ingress health

Run repository checks separately from backups so deep verification does not extend application downtime. Restore only to an empty staging directory. Review paths and contents, rebuild empty named volumes, import their tar exports, restore bind mounts, then start and validate the stack. Preserve the old live state until the recovered stack passes.
