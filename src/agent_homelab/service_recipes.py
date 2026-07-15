from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml

from .model import InventoryError


def catalog_path() -> Path:
    override = os.environ.get("AGENT_HOMELAB_RECIPE_CATALOG")
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        [
            Path(__file__).resolve().parents[2] / "recipes/services/catalog.yaml",
            Path(sys.prefix) / "share/agent-homelab/recipes/services/catalog.yaml",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise InventoryError(
        "Service recipe catalog is not installed; reinstall Agent Homelab or set AGENT_HOMELAB_RECIPE_CATALOG"
    )


def load_recipes() -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load(catalog_path().read_text())
    if not isinstance(raw, dict) or raw.get("schema_version") != 1 or not isinstance(raw.get("recipes"), dict):
        raise InventoryError("Service recipe catalog is invalid")
    return raw["recipes"]


def get_recipe(name: str) -> dict[str, Any]:
    recipes = load_recipes()
    if name not in recipes:
        raise InventoryError(f"Unknown service recipe: {name}")
    return recipes[name]
