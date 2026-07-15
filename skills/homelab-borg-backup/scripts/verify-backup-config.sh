#!/usr/bin/env sh
set -eu

config=${1:-backup.yaml}
agent-homelab-borg-backup --config "$config" validate
agent-homelab-borg-backup --config "$config" plan
