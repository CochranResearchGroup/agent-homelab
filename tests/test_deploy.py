from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest
import yaml

from agent_homelab.deploy import apply_plan, build_plan
from agent_homelab.model import Inventory, InventoryError
from agent_homelab.render import render_inventory

FIXTURES = Path(__file__).parent / "fixtures"


def local_inventory(tmp_path: Path, *, reload_command: list[str] | None = None) -> Inventory:
    data = yaml.safe_load((FIXTURES / "direct.yaml").read_text())
    data["nodes"]["homelab"]["deploy"] = {"mode": "local", "root": str(tmp_path / "installed")}
    if reload_command:
        data["nodes"]["homelab"]["deploy"]["reload_command"] = reload_command
    source = tmp_path / "inventory.yaml"
    source.write_text(yaml.safe_dump(data, sort_keys=False))
    return Inventory(source, data)


def test_apply_is_atomic_and_second_apply_is_unchanged(tmp_path: Path) -> None:
    inventory = local_inventory(tmp_path)
    rendered = tmp_path / "rendered"
    render_inventory(inventory, rendered)
    plan = build_plan(inventory, rendered, "homelab")
    result = apply_plan(inventory, plan)
    assert result["status"] == "applied"
    second = build_plan(inventory, rendered, "homelab")
    assert second.changed is False
    assert apply_plan(inventory, second)["status"] == "unchanged"


def test_invalid_stage_does_not_replace_installed_tree(tmp_path: Path) -> None:
    inventory = local_inventory(tmp_path)
    rendered = tmp_path / "rendered"
    render_inventory(inventory, rendered)
    apply_plan(inventory, build_plan(inventory, rendered, "homelab"))
    marker = tmp_path / "installed/marker.txt"
    marker.write_text("known-good")
    (rendered / "nodes/homelab/traefik/dynamic/services.yaml").write_text("http: [invalid")
    plan = build_plan(inventory, rendered, "homelab")
    with pytest.raises(InventoryError, match="Generated YAML is invalid"):
        apply_plan(inventory, plan)
    assert marker.read_text() == "known-good"


def test_reload_failure_restores_previous_tree(tmp_path: Path) -> None:
    inventory = local_inventory(tmp_path)
    rendered = tmp_path / "rendered"
    render_inventory(inventory, rendered)
    apply_plan(inventory, build_plan(inventory, rendered, "homelab"))
    marker = tmp_path / "installed/marker.txt"
    marker.write_text("known-good")
    failing = local_inventory(tmp_path, reload_command=["false"])
    changed = copy.deepcopy(failing.data)
    changed["services"]["hello"]["upstream"]["port"] = 8081
    changed["services"]["hello"]["upstream"]["port_source"] = "compose.yaml ports 8081:8081"
    failing = Inventory(failing.path, changed)
    render_inventory(failing, rendered)
    with pytest.raises(subprocess.CalledProcessError):
        apply_plan(failing, build_plan(failing, rendered, "homelab"))
    assert marker.read_text() == "known-good"
