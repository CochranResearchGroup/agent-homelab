#!/usr/bin/env sh
set -eu

inventory="${1:-homelab.yaml}"
agent-homelab validate --inventory "$inventory"
exec agent-homelab maintenance --inventory "$inventory"
