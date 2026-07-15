#!/usr/bin/env sh
set -eu

inventory="${1:-homelab.yaml}"
exec agent-homelab maintenance --inventory "$inventory"
