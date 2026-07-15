from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

EPHEMERAL_PORT_MIN = 32768
EPHEMERAL_PORT_MAX = 60999
IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
INLINE_SECRET_KEYS = {
    "api_key",
    "client_secret",
    "cookie",
    "jwt_secret",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "session_secret",
    "token",
}


class InventoryError(ValueError):
    """Raised when an inventory cannot safely drive rendering or deployment."""


@dataclass(frozen=True)
class Inventory:
    path: Path
    data: dict[str, Any]

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        return self.data["nodes"]

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return self.data["services"]


def schema() -> dict[str, Any]:
    return json.loads(files("agent_homelab").joinpath("homelab.schema.json").read_text())


def load_inventory(path: str | Path) -> Inventory:
    source = Path(path).expanduser().resolve()
    try:
        payload = yaml.safe_load(source.read_text())
    except FileNotFoundError as exc:
        raise InventoryError(f"Inventory does not exist: {source}") from exc
    except yaml.YAMLError as exc:
        raise InventoryError(f"Inventory is not valid YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise InventoryError("Inventory root must be a mapping")
    validate_inventory(payload)
    return Inventory(path=source, data=payload)


def validate_inventory(data: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema(), format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))
    problems = [f"{_path(error.absolute_path)}: {error.message}" for error in schema_errors]
    problems.extend(_semantic_errors(data) if not schema_errors else [])
    if problems:
        raise InventoryError("Inventory validation failed:\n- " + "\n- ".join(problems))


def _path(parts: Iterable[Any]) -> str:
    text = ".".join(str(part) for part in parts)
    return text or "<root>"


def _semantic_errors(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    nodes = data["nodes"]
    services = data["services"]

    for node_name, node in nodes.items():
        if not IDENTIFIER_RE.fullmatch(node_name):
            problems.append(f"nodes.{node_name}: node identifiers must use lowercase letters, digits, and hyphens")
        deploy = node.get("deploy", {})
        if deploy.get("mode") == "ssh" and not node.get("connect", {}).get("ssh_alias"):
            problems.append(f"nodes.{node_name}.connect.ssh_alias: required for SSH deployment")

    for service_name, service in services.items():
        if not IDENTIFIER_RE.fullmatch(service_name):
            problems.append(
                f"services.{service_name}: service identifiers must use lowercase letters, digits, and hyphens"
            )
        _check_upstream(service["upstream"], f"services.{service_name}.upstream", nodes, problems)

        local = service.get("local", {})
        if local.get("enabled") and not local.get("hostname"):
            problems.append(f"services.{service_name}.local.hostname: required when local ingress is enabled")

        public = service.get("public", {})
        if public.get("enabled"):
            if not public.get("hostname"):
                problems.append(f"services.{service_name}.public.hostname: required when public ingress is enabled")
            edge_name = public.get("edge_node")
            if not edge_name:
                problems.append(f"services.{service_name}.public.edge_node: required when public ingress is enabled")
            elif edge_name not in nodes:
                problems.append(f"services.{service_name}.public.edge_node: unknown node {edge_name!r}")
            elif "edge_gateway" not in nodes[edge_name]["roles"]:
                problems.append(f"services.{service_name}.public.edge_node: {edge_name!r} is not an edge_gateway")

        route_names: set[str] = set()
        defined_middlewares = set(service.get("forward_auth", {}))
        for index, route in enumerate(service.get("path_routes", [])):
            route_path = f"services.{service_name}.path_routes.{index}"
            if route["name"] in route_names:
                problems.append(f"{route_path}.name: duplicate path route name {route['name']!r}")
            route_names.add(route["name"])
            _check_upstream(route["upstream"], f"{route_path}.upstream", nodes, problems)
            for middleware in route.get("middlewares", []):
                if middleware not in defined_middlewares:
                    problems.append(f"{route_path}.middlewares: undefined service forward-auth {middleware!r}")

    problems.extend(_inline_secret_errors(data))
    return problems


def _check_upstream(
    upstream: dict[str, Any], path: str, nodes: dict[str, dict[str, Any]], problems: list[str]
) -> None:
    node_name = upstream["node"]
    if node_name not in nodes:
        problems.append(f"{path}.node: unknown node {node_name!r}")
    elif "service_host" not in nodes[node_name]["roles"]:
        problems.append(f"{path}.node: {node_name!r} is not a service_host")
    port = upstream["port"]
    if EPHEMERAL_PORT_MIN <= port <= EPHEMERAL_PORT_MAX and not upstream.get("allow_ephemeral_port", False):
        problems.append(
            f"{path}.port: {port} is in the usual ephemeral range; pin it explicitly and set allow_ephemeral_port"
        )
    if not upstream.get("port_source", "").strip():
        problems.append(f"{path}.port_source: must identify the durable runtime port authority")


def _inline_secret_errors(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    problems: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in INLINE_SECRET_KEYS and not normalized.endswith("_ref"):
                problems.append(
                    f"{_path((*path, str(key)))}: inline secret fields are forbidden; use a secret reference"
                )
            problems.extend(_inline_secret_errors(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_inline_secret_errors(child, (*path, str(index))))
    return problems


def topology_for(service: dict[str, Any]) -> str | None:
    public = service.get("public", {})
    if not public.get("enabled"):
        return None
    return "direct" if public["edge_node"] == service["upstream"]["node"] else "relay"
