#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_CONSISTENCY = {"stop", "application-native", "application-native-plus-stop"}
ALLOWED_AUTH = {"optional", "recommended", "avoid-double-auth"}


def validate_catalog(path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text()) or {}
    problems: list[str] = []
    if data.get("schema_version") != 1:
        problems.append("schema_version must be 1")
    recipes = data.get("recipes")
    if not isinstance(recipes, dict) or not recipes:
        return [*problems, "recipes must be a non-empty mapping"]
    for recipe_id, recipe in sorted(recipes.items()):
        prefix = f"recipes.{recipe_id}"
        if not ID_RE.fullmatch(recipe_id):
            problems.append(f"{prefix}: invalid recipe id")
        required = (
            "title",
            "category",
            "install",
            "upstream",
            "configuration",
            "persistence",
            "backup",
            "ingress",
            "gotchas",
        )
        for key in required:
            if key not in recipe:
                problems.append(f"{prefix}: missing {key}")
        install = recipe.get("install", {})
        documentation = install.get("documentation", "")
        parsed = urlsplit(documentation)
        if parsed.scheme != "https" or not parsed.hostname:
            problems.append(f"{prefix}.install.documentation: must be an HTTPS URL")
        upstream = recipe.get("upstream", {})
        if upstream.get("scheme") not in {"http", "https"}:
            problems.append(f"{prefix}.upstream.scheme: unsupported scheme")
        port = upstream.get("port")
        if not isinstance(port, int) or not 1 <= port <= 65535:
            problems.append(f"{prefix}.upstream.port: invalid port")
        if recipe.get("backup", {}).get("consistency") not in ALLOWED_CONSISTENCY:
            problems.append(f"{prefix}.backup.consistency: unsupported value")
        if recipe.get("ingress", {}).get("authelia") not in ALLOWED_AUTH:
            problems.append(f"{prefix}.ingress.authelia: unsupported value")
        if not recipe.get("persistence"):
            problems.append(f"{prefix}.persistence: must identify durable state")
        if not recipe.get("gotchas"):
            problems.append(f"{prefix}.gotchas: must not be empty")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    path = root / "recipes/services/catalog.yaml"
    problems = validate_catalog(path)
    if problems:
        print("Recipe validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    count = len(yaml.safe_load(path.read_text())["recipes"])
    print(f"Recipe validation passed: {count} services")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
