#!/usr/bin/env sh
set -eu

if [ "$#" -lt 8 ]; then
  echo "usage: $0 INVENTORY NAME NODE PORT PORT_SOURCE LOCAL_HOST PUBLIC_HOST EDGE_NODE [AUTH_POLICY]" >&2
  exit 2
fi

inventory=$1
name=$2
node=$3
port=$4
port_source=$5
local_host=$6
public_host=$7
edge_node=$8
auth_policy=${9:-one_factor}

exec agent-homelab service upsert "$name" \
  --inventory "$inventory" \
  --upstream-node "$node" \
  --port "$port" \
  --port-source "$port_source" \
  --local-hostname "$local_host" \
  --public-hostname "$public_host" \
  --edge-node "$edge_node" \
  --auth-policy "$auth_policy"
