from __future__ import annotations

import json
import os
import secrets
import subprocess
import tarfile
import textwrap
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from . import __version__
from .model import Inventory, InventoryError

STATE_DIRECTORIES = ("authelia", "letsencrypt", "secrets")
SECRET_FILES = (
    "authelia-jwt-secret",
    "authelia-session-secret",
    "authelia-storage-key",
)


def bootstrap_plan(inventory: Inventory, node_name: str, acme_email: str | None = None) -> dict[str, Any]:
    if node_name not in inventory.nodes:
        raise InventoryError(f"Unknown node: {node_name}")
    node = inventory.nodes[node_name]
    deploy = node.get("deploy")
    if not deploy:
        raise InventoryError(f"nodes.{node_name}.deploy is required for bootstrap")
    if "edge_gateway" in node["roles"] and not acme_email:
        raise InventoryError("--acme-email or AGENT_HOMELAB_ACME_EMAIL is required for an edge gateway")
    return {
        "node": node_name,
        "mode": deploy.get("mode", "local"),
        "state_root": deploy.get("state_root", "/var/lib/agent-homelab"),
        "create_directories": list(STATE_DIRECTORIES),
        "create_secret_files_if_missing": list(SECRET_FILES) if "edge_gateway" in node["roles"] else [],
        "create_authelia_users_file_if_missing": "edge_gateway" in node["roles"],
        "create_acme_storage_if_missing": "edge_gateway" in node["roles"],
        "write_runtime_env": "edge_gateway" in node["roles"],
    }


def bootstrap_node(
    inventory: Inventory, node_name: str, *, acme_email: str | None = None, apply: bool = False
) -> dict[str, Any]:
    plan = bootstrap_plan(inventory, node_name, acme_email)
    if not apply:
        return {"status": "planned", "plan": plan}
    node = inventory.nodes[node_name]
    if plan["mode"] == "local":
        created = _bootstrap_local(Path(plan["state_root"]).expanduser(), node, acme_email)
    elif plan["mode"] == "ssh":
        alias = node["connect"]["ssh_alias"]
        created = _bootstrap_ssh(alias, plan["state_root"], node, acme_email)
    else:
        raise InventoryError(f"Unsupported bootstrap mode: {plan['mode']}")
    return {"status": "applied", "plan": plan, "created": created}


def _bootstrap_local(root: Path, node: dict[str, Any], acme_email: str | None) -> list[str]:
    created: list[str] = []
    for name in STATE_DIRECTORIES:
        path = root / name
        if not path.exists():
            path.mkdir(parents=True, mode=0o700)
            created.append(str(path))
    if "edge_gateway" not in node["roles"]:
        return created
    for name in SECRET_FILES:
        path = root / "secrets" / name
        if _exclusive_write(path, secrets.token_urlsafe(64) + "\n"):
            created.append(str(path))
    users = root / "authelia" / "users_database.yml"
    if _exclusive_write(users, "users: {}\n"):
        created.append(str(users))
    acme = root / "letsencrypt" / "acme.json"
    if _exclusive_write(acme, "{}\n"):
        created.append(str(acme))
    runtime_env = root / "env"
    env_text = f"TRAEFIK_CERTIFICATESRESOLVERS_LETSENCRYPT_ACME_EMAIL={acme_email}\n"
    if runtime_env.exists():
        current = runtime_env.read_text()
        if current != env_text:
            raise InventoryError(f"Refusing to overwrite existing runtime environment: {runtime_env}")
    elif _exclusive_write(runtime_env, env_text):
        created.append(str(runtime_env))
    return created


def _exclusive_write(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(descriptor, "w") as handle:
        handle.write(text)
    return True


def _bootstrap_ssh(
    alias: str, root: str, node: dict[str, Any], acme_email: str | None
) -> list[str]:
    script = textwrap.dedent(
        """
        import json
        import os
        import pathlib
        import secrets
        import sys

        root = pathlib.Path(sys.argv[1])
        edge = sys.argv[2] == "1"
        email = sys.argv[3]
        created = []

        for path in (root / "authelia", root / "letsencrypt", root / "secrets"):
            path.mkdir(parents=True, exist_ok=True, mode=0o700)

        def create(path, content):
            if path.exists():
                return
            path.write_text(content)
            os.chmod(path, 0o600)
            created.append(str(path))

        if edge:
            for name in ("authelia-jwt-secret", "authelia-session-secret", "authelia-storage-key"):
                create(root / "secrets" / name, secrets.token_urlsafe(64) + "\\n")
            create(root / "authelia" / "users_database.yml", "users: {}\\n")
            create(root / "letsencrypt" / "acme.json", "{}\\n")
            runtime_env = root / "env"
            expected = "TRAEFIK_CERTIFICATESRESOLVERS_LETSENCRYPT_ACME_EMAIL=" + email + "\\n"
            if runtime_env.exists() and runtime_env.read_text() != expected:
                raise RuntimeError("refusing to overwrite runtime env")
            create(runtime_env, expected)

        print(json.dumps(created))
        """
    )
    command = [
        "ssh",
        alias,
        "python3",
        "-c",
        script,
        root,
        "1" if "edge_gateway" in node["roles"] else "0",
        acme_email or "",
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def create_recovery_bundle(
    inventory: Inventory, output: str | Path, rendered_dir: str | Path | None = None
) -> dict[str, Any]:
    target = Path(output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "agent_homelab_version": __version__,
        "contains_secrets": False,
        "inventory": "homelab.yaml",
    }
    readme = (
        "This private recovery bundle contains inventory and optional generated configuration, but no secrets, "
        "Authelia state, OAuth state, or ACME data. Restore those from the operator's encrypted backup.\n"
    )
    with tarfile.open(target, "w:gz") as archive:
        archive.add(inventory.path, arcname="homelab.yaml")
        _tar_bytes(archive, "manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n")
        _tar_bytes(archive, "README.txt", readme.encode())
        if rendered_dir:
            rendered = Path(rendered_dir).resolve()
            if rendered.is_dir():
                archive.add(rendered, arcname="rendered")
    os.chmod(target, 0o600)
    return {"status": "created", "path": str(target), **manifest}


def _tar_bytes(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mode = 0o600
    archive.addfile(info, BytesIO(payload))
