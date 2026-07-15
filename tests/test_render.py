from __future__ import annotations

import json
from pathlib import Path

import yaml

from agent_homelab.model import load_inventory
from agent_homelab.render import render_inventory, tree_digest

FIXTURES = Path(__file__).parent / "fixtures"


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def test_direct_render_targets_local_upstream(tmp_path: Path) -> None:
    inventory = load_inventory(FIXTURES / "direct.yaml")
    render_inventory(inventory, tmp_path / "rendered")
    dynamic = read_yaml(tmp_path / "rendered/nodes/homelab/traefik/dynamic/services.yaml")
    assert dynamic["http"]["services"]["hello-edge"]["loadBalancer"]["servers"][0]["url"] == (
        "http://host.docker.internal:8080"
    )
    assert dynamic["http"]["routers"]["hello-public"]["tls"]["certResolver"] == "letsencrypt"
    assert dynamic["http"]["routers"]["agent-homelab-health"]["service"] == "ping@internal"


def test_relay_render_targets_origin_and_pairs_authelia_rule(tmp_path: Path) -> None:
    inventory = load_inventory(FIXTURES / "relay.yaml")
    render_inventory(inventory, tmp_path / "rendered")
    edge = read_yaml(tmp_path / "rendered/nodes/gateway/traefik/dynamic/services.yaml")
    origin = read_yaml(tmp_path / "rendered/nodes/app-host/traefik/dynamic/services.yaml")
    auth = read_yaml(tmp_path / "rendered/nodes/gateway/authelia/configuration.yml")
    assert edge["http"]["services"]["photos-edge"]["loadBalancer"]["servers"][0]["url"] == "http://192.0.2.10:80"
    assert edge["http"]["routers"]["photos-public"]["middlewares"] == ["authelia-forward-auth"]
    assert origin["http"]["routers"]["photos-origin"]["rule"] == "Host(`photos.example.net`)"
    assert origin["http"]["routers"]["photos-viewer-origin"]["priority"] == 100
    assert origin["http"]["routers"]["photos-viewer-origin"]["middlewares"] == ["photos-viewer-auth"]
    assert origin["http"]["middlewares"]["photos-viewer-auth"]["forwardAuth"]["authResponseHeaders"] == [
        "Remote-User"
    ]
    assert auth["access_control"]["rules"] == [{"domain": "photos.example.net", "policy": "one_factor"}]


def test_render_is_deterministic_and_manifest_matches_tree(tmp_path: Path) -> None:
    inventory = load_inventory(FIXTURES / "relay.yaml")
    first = tmp_path / "first"
    second = tmp_path / "second"
    manifest_one = render_inventory(inventory, first)
    manifest_two = render_inventory(inventory, second)
    assert manifest_one == manifest_two
    assert tree_digest(first / "nodes/gateway") == tree_digest(second / "nodes/gateway")
    on_disk = json.loads((first / "manifest.json").read_text())
    assert on_disk == manifest_one
