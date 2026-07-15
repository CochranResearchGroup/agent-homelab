#!/usr/bin/env sh
set -eu

topology="${1:-combined}"
inventory="${2:-homelab.yaml}"
agent-homelab init "$inventory" --topology "$topology"
exec agent-homelab doctor --inventory "$inventory"
