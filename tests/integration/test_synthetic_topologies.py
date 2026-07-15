from __future__ import annotations

from pathlib import Path

import yaml

from agent_homelab.model import load_inventory
from agent_homelab.render import render_inventory

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_every_synthetic_topology_renders_parseable_yaml(tmp_path: Path) -> None:
    for fixture in sorted(FIXTURES.glob("*.yaml")):
        target = tmp_path / fixture.stem
        render_inventory(load_inventory(fixture), target)
        outputs = list(target.rglob("*.yaml")) + list(target.rglob("*.yml"))
        assert outputs
        for output in outputs:
            assert yaml.safe_load(output.read_text()) is not None
