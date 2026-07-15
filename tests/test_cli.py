from __future__ import annotations

from pathlib import Path

import yaml

from agent_homelab.cli import main


def test_init_validate_render_and_service_upsert(tmp_path: Path) -> None:
    inventory = tmp_path / "homelab.yaml"
    rendered = tmp_path / "rendered"
    assert main(["init", str(inventory), "--topology", "relay"]) == 0
    assert main(["validate", "--inventory", str(inventory)]) == 0
    assert (
        main(
            [
                "service",
                "upsert",
                "wiki",
                "--inventory",
                str(inventory),
                "--upstream-node",
                "app-host",
                "--port",
                "3000",
                "--port-source",
                "compose.yaml ports 3000:3000",
                "--local-hostname",
                "wiki.localhost",
                "--public-hostname",
                "wiki.example.net",
                "--edge-node",
                "gateway",
                "--auth-policy",
                "one_factor",
            ]
        )
        == 0
    )
    assert main(["render", "--inventory", str(inventory), "--output", str(rendered)]) == 0
    data = yaml.safe_load(inventory.read_text())
    assert data["services"]["wiki"]["public"]["auth"]["policy"] == "one_factor"


def test_init_refuses_overwrite(tmp_path: Path) -> None:
    inventory = tmp_path / "homelab.yaml"
    assert main(["init", str(inventory)]) == 0
    assert main(["init", str(inventory)]) == 2


def test_recipe_catalog_commands(capsys) -> None:
    assert main(["recipe", "list"]) == 0
    assert "paperless-ngx" in capsys.readouterr().out
    assert main(["recipe", "show", "immich"]) == 0
    assert '"port": 2283' in capsys.readouterr().out
    assert main(["recipe", "show", "missing-recipe"]) == 2
