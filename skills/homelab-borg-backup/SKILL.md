---
name: homelab-borg-backup
description: Configures and operates guarded BorgBackup for Agent Homelab Compose stacks, including named-volume export, retention, integrity checks, and staging restores. Use when asked to set up Borg, back up homelab services, schedule backups, verify archives, restore a stack, or test disaster recovery.
license: Apache-2.0
---

# Homelab Borg Backup

Backups are plan-first and restores are staging-only. Never infer that an archive is recoverable from command success alone.

## Reference files

| File | Read when |
|---|---|
| [references/backup-and-restore-contract.md](references/backup-and-restore-contract.md) | Selecting consistency boundaries, scheduling backups, checking repositories, or restoring data |

## Workflow

Copy and track:

- [ ] Identify every stack's Compose authority, host paths, named volumes, and application-native backup needs.
- [ ] Keep the Borg repository outside all source trees and synchronization recursion paths.
- [ ] Copy `recipes/borg-backup/backup.example.yaml` into ignored operator state and replace synthetic paths.
- [ ] Store the passphrase only in a mode-`0600` environment file; export and protect the repository key separately.
- [ ] Run `scripts/verify-backup-config.sh <config>` and inspect every stop, export, archive, prune, compact, and start action.
- [ ] Initialize each repository with `init --apply` only after confirming its destination.
- [ ] Run one selected stack with `backup <stack> --apply` and verify the application restarted.
- [ ] List archives and run `check`; schedule periodic `--verify-data` checks outside the daily backup window.
- [ ] Plan a restore into a new empty directory, apply it, and validate the restored contents without touching live state.
- [ ] Document the recovery order for application-native exports, bind mounts, and named volumes.
- [ ] Enable the systemd timer only after the manual backup and staged restore pass.

## Validation loop

After each configuration change, repeat validate, plan, one-stack backup, archive listing, repository check, and staged restore. Confirm service health and ingress after the runner restarts the stack. Disable the timer and repair the recovery boundary when any gate fails.

## Gotchas

- A successful archive creation does not prove the passphrase and key are available to a fresh recovery host.
- Named-volume tar exports are restore inputs, not automatically rehydrated live volumes.
- Stopping a database reduces filesystem inconsistency but does not replace an application-supported logical export where the recipe requires one.
- Borg `--repair`, lock removal, live-path extraction, and direct Docker-volume overwrite are manual break-glass actions outside this skill.
- A backup destination on the same physical failure domain is not sufficient by itself.
- Nextcloud AIO has its own Borg lifecycle; avoid running two independent writers against the same AIO repository.

## Related skills

- Use `homelab-service-catalog` to determine each service's persistence and consistency contract.
- Use `homelab-maintenance` to monitor freshness and schedule integrity checks.
- Use `homelab-troubleshooter` if services fail to restart after a backup attempt.
