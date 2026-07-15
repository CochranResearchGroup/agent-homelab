from __future__ import annotations

import tarfile
from pathlib import Path

import pytest
import yaml

from agent_homelab.bootstrap import bootstrap_node, create_recovery_bundle
from agent_homelab.model import Inventory, InventoryError
from agent_homelab.render import render_inventory

FIXTURES = Path(__file__).parent / "fixtures"


def inventory_for(tmp_path: Path) -> Inventory:
    data = yaml.safe_load((FIXTURES / "direct.yaml").read_text())
    data["nodes"]["homelab"]["deploy"] = {
        "mode": "local",
        "root": str(tmp_path / "installed"),
        "state_root": str(tmp_path / "state"),
    }
    path = tmp_path / "homelab.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return Inventory(path, data)


def test_bootstrap_is_plan_first_and_does_not_overwrite_state(tmp_path: Path) -> None:
    inventory = inventory_for(tmp_path)
    planned = bootstrap_node(inventory, "homelab", acme_email="operator@example.invalid")
    assert planned["status"] == "planned"
    assert not (tmp_path / "state").exists()
    applied = bootstrap_node(inventory, "homelab", acme_email="operator@example.invalid", apply=True)
    assert applied["status"] == "applied"
    secret = tmp_path / "state/secrets/authelia-session-secret"
    original = secret.read_text()
    bootstrap_node(inventory, "homelab", acme_email="operator@example.invalid", apply=True)
    assert secret.read_text() == original
    assert secret.stat().st_mode & 0o777 == 0o600
    with pytest.raises(InventoryError, match="Refusing to overwrite"):
        bootstrap_node(inventory, "homelab", acme_email="changed@example.invalid", apply=True)


def test_recovery_bundle_excludes_persistent_state(tmp_path: Path) -> None:
    inventory = inventory_for(tmp_path)
    bootstrap_node(inventory, "homelab", acme_email="operator@example.invalid", apply=True)
    rendered = tmp_path / "rendered"
    render_inventory(inventory, rendered)
    bundle = tmp_path / "recovery-agent-homelab.tar.gz"
    create_recovery_bundle(inventory, bundle, rendered)
    with tarfile.open(bundle) as archive:
        names = archive.getnames()
    assert "homelab.yaml" in names
    assert not any("secret" in name or "acme.json" in name or "users_database" in name for name in names)
