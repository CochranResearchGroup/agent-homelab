# Borg backups

Agent Homelab provides `agent-homelab-borg-backup`, a host-side BorgBackup 1.4 runner for Compose stacks. It uses one encrypted repository per stack, exports named Docker volumes while the stack is stopped, applies daily/weekly/monthly retention, compacts repositories, and restores only to staging directories.

Start with `recipes/borg-backup/backup.example.yaml` and keep the real configuration outside Git. The runner expects the passphrase through the configured environment-variable name and never accepts an inline passphrase field.

## Bring-up sequence

```bash
agent-homelab-borg-backup --config backup.yaml validate
agent-homelab-borg-backup --config backup.yaml plan
agent-homelab-borg-backup --config backup.yaml init --apply
agent-homelab-borg-backup --config backup.yaml backup --apply
agent-homelab-borg-backup --config backup.yaml archives documents
agent-homelab-borg-backup --config backup.yaml check documents --verify-data
agent-homelab-borg-backup --config backup.yaml restore documents ARCHIVE --target ./restore-staging
```

Review the restore plan, then add `--apply`. The destination must be empty and cannot overlap the Compose directory or configured live source paths.

Install the example systemd service and timer only after a manual backup, repository check, and staged restore pass. Put the real paths in `%h/.config/agent-homelab/backup.yaml`, the passphrase in `%h/.config/agent-homelab/borg.env`, restrict both files, and confirm the unit's `PATH` contains the installed CLI. Then use `systemctl --user enable --now agent-homelab-borg-backup.timer`. A system service should use root-owned paths and an explicitly reviewed service account instead.

Application-native backup requirements in the service catalog remain authoritative. Nextcloud AIO should use its own Borg workflow for AIO-managed state.
