#!/usr/bin/env sh
set -eu

config="${1:-oauth-relay.yaml}"
exec agent-homelab-oauth-relay --config "$config" --help
