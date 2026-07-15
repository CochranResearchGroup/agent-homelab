from __future__ import annotations

import importlib.util
from pathlib import Path


def load_validator():
    path = Path(__file__).parents[1] / "scripts/validate-recipes.py"
    spec = importlib.util.spec_from_file_location("validate_recipes", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_service_catalog_is_valid() -> None:
    root = Path(__file__).parents[1]
    validator = load_validator()
    assert validator.validate_catalog(root / "recipes/services/catalog.yaml") == []
