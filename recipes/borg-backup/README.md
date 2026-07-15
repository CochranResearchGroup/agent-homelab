# Borg backup service

This recipe installs a host-side, systemd-scheduled BorgBackup 1.4 workflow for Compose-managed stacks. Each stack receives its own encrypted Borg repository and retention lifecycle.

The runner stops a configured stack, exports named Docker volumes into a mode-`0700` temporary directory, archives configured bind-mounted paths and volume exports, prunes retention, compacts the repository, and starts the stack in a `finally` path. A backup failure therefore does not intentionally leave the application stopped. The systemd unit intentionally does not use `PrivateTmp` because the Docker daemon must see the temporary bind mount used for volume export.

## Setup

1. Install BorgBackup 1.4, Docker Engine, and Docker Compose from trusted distribution or upstream packages.
2. Copy `backup.example.yaml` to an operator-owned path outside Git and replace every synthetic path.
3. Create a mode-`0600` environment file containing `BORG_PASSPHRASE`. Back up that passphrase and the exported Borg repository key separately.
4. Validate and preview:

   ```bash
   agent-homelab-borg-backup --config backup.yaml validate
   agent-homelab-borg-backup --config backup.yaml plan
   agent-homelab-borg-backup --config backup.yaml init
   ```

5. Initialize only after reviewing every repository destination:

   ```bash
   agent-homelab-borg-backup --config backup.yaml init --apply
   ```

6. Run one backup manually, check it, and perform a staging restore before enabling the timer:

   ```bash
   agent-homelab-borg-backup --config backup.yaml backup documents --apply
   agent-homelab-borg-backup --config backup.yaml archives documents
   agent-homelab-borg-backup --config backup.yaml check documents --verify-data
   agent-homelab-borg-backup --config backup.yaml restore documents ARCHIVE --target ./restore-staging
   ```

The restore command is plan-only until `--apply` is supplied. It refuses targets that overlap the Compose directory or configured live source paths and never writes directly into Docker volumes.

## Consistency boundary

Stopped filesystem snapshots are not a replacement for application-native exports when a service requires them. GitLab, Odoo, WordPress, and similar stateful applications should keep their supported database/application export in the recovery plan. Nextcloud AIO should use its AIO-managed Borg workflow for AIO-owned state.

Do not include a backup repository inside one of its own source paths or inside a synchronized tree that recursively copies the repository back to the same host.
