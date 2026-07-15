from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .model import Inventory, InventoryError
from .render import tree_digest


@dataclass(frozen=True)
class DeploymentPlan:
    node: str
    mode: str
    source: str
    destination: str
    current_digest: str | None
    desired_digest: str
    changed: bool
    validate_command: list[str]
    reload_command: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_plan(inventory: Inventory, rendered_dir: str | Path, node_name: str) -> DeploymentPlan:
    if node_name not in inventory.nodes:
        raise InventoryError(f"Unknown node: {node_name}")
    node = inventory.nodes[node_name]
    deploy = node.get("deploy")
    if not deploy:
        raise InventoryError(f"nodes.{node_name}.deploy is required for plan/apply")
    source = Path(rendered_dir).resolve() / "nodes" / node_name
    if not source.is_dir():
        raise InventoryError(f"Rendered node directory is missing: {source}")
    mode = deploy.get("mode", "local")
    destination = deploy["root"]
    current_digest = _current_digest(node, destination, mode)
    desired_digest = tree_digest(source)
    return DeploymentPlan(
        node=node_name,
        mode=mode,
        source=str(source),
        destination=destination,
        current_digest=current_digest,
        desired_digest=desired_digest,
        changed=current_digest != desired_digest,
        validate_command=list(deploy.get("validate_command", [])),
        reload_command=list(deploy.get("reload_command", [])),
    )


def apply_plan(inventory: Inventory, plan: DeploymentPlan, *, dry_run: bool = False) -> dict[str, Any]:
    if dry_run or not plan.changed:
        return {"status": "planned" if dry_run else "unchanged", "plan": plan.to_dict(), "reloaded": False}
    if plan.mode == "local":
        return _apply_local(plan)
    if plan.mode == "ssh":
        return _apply_ssh(inventory, plan)
    raise InventoryError(f"Unsupported deployment mode: {plan.mode}")


def _apply_local(plan: DeploymentPlan) -> dict[str, Any]:
    source = Path(plan.source)
    destination = Path(plan.destination).expanduser().resolve()
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stage = parent / f".{destination.name}.stage-{os.getpid()}"
    backup = parent / f".{destination.name}.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(source, stage)
    _validate_tree(stage, plan.validate_command)
    had_destination = destination.exists()
    try:
        if had_destination:
            destination.rename(backup)
        stage.rename(destination)
        if plan.reload_command:
            subprocess.run(plan.reload_command, cwd=destination, check=True)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        if backup.exists():
            backup.rename(destination)
        raise
    return {
        "status": "applied",
        "plan": plan.to_dict(),
        "backup": str(backup) if had_destination else None,
        "reloaded": bool(plan.reload_command),
    }


def _apply_ssh(inventory: Inventory, plan: DeploymentPlan) -> dict[str, Any]:
    node = inventory.nodes[plan.node]
    alias = node["connect"]["ssh_alias"]
    destination = plan.destination
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    remote_stage = f"{destination}.stage-{stamp}"
    remote_backup = f"{destination}.backup-{stamp}"

    with tempfile.TemporaryDirectory() as temp_dir:
        archive = Path(temp_dir) / "node.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(plan.source, arcname=".")
        subprocess.run(["ssh", alias, "mkdir", "-p", remote_stage], check=True)
        subprocess.run(["scp", str(archive), f"{alias}:{remote_stage}/node.tar.gz"], check=True)
        subprocess.run(
            ["ssh", alias, f"cd {shlex.quote(remote_stage)} && tar -xzf node.tar.gz && rm node.tar.gz"], check=True
        )

    _validate_remote(alias, remote_stage, plan.validate_command)
    promote = (
        "set -eu; had_destination=0; "
        f"if [ -e {shlex.quote(destination)} ]; then "
        f"mv {shlex.quote(destination)} {shlex.quote(remote_backup)}; had_destination=1; fi; "
        f"if ! mv {shlex.quote(remote_stage)} {shlex.quote(destination)}; then "
        f"if [ \"$had_destination\" -eq 1 ] && [ -e {shlex.quote(remote_backup)} ]; then "
        f"mv {shlex.quote(remote_backup)} {shlex.quote(destination)}; fi; exit 1; fi"
    )
    subprocess.run(["ssh", alias, promote], check=True)
    try:
        if plan.reload_command:
            command = "cd " + shlex.quote(destination) + " && " + shlex.join(plan.reload_command)
            subprocess.run(["ssh", alias, command], check=True)
    except Exception:
        rollback = (
            "set -eu; "
            f"rm -rf {shlex.quote(destination)}; "
            f"if [ -e {shlex.quote(remote_backup)} ]; then "
            f"mv {shlex.quote(remote_backup)} {shlex.quote(destination)}; fi"
        )
        subprocess.run(["ssh", alias, rollback], check=False)
        raise
    return {
        "status": "applied",
        "plan": plan.to_dict(),
        "backup": remote_backup,
        "reloaded": bool(plan.reload_command),
    }


def _validate_tree(root: Path, command: list[str]) -> None:
    for yaml_path in root.rglob("*.y*ml"):
        try:
            yaml.safe_load(yaml_path.read_text())
        except yaml.YAMLError as exc:
            raise InventoryError(f"Generated YAML is invalid: {yaml_path}: {exc}") from exc
    if command:
        subprocess.run(command, cwd=root, check=True)


def _validate_remote(alias: str, root: str, command: list[str]) -> None:
    if not command:
        return
    remote_command = "cd " + shlex.quote(root) + " && " + shlex.join(command)
    subprocess.run(["ssh", alias, remote_command], check=True)


def _current_digest(node: dict[str, Any], destination: str, mode: str) -> str | None:
    if mode == "local":
        path = Path(destination).expanduser()
        return tree_digest(path) if path.is_dir() else None
    alias = node.get("connect", {}).get("ssh_alias")
    if not alias:
        return None
    script = (
        "import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); h=hashlib.sha256(); "
        "files=sorted(x for x in p.rglob('*') if x.is_file()); "
        "[(h.update(x.relative_to(p).as_posix().encode()),h.update(b'\\0'),"
        "h.update(x.read_bytes()),h.update(b'\\0')) for x in files]; "
        "print(h.hexdigest())"
    )
    result = subprocess.run(
        ["ssh", alias, "python3", "-c", script, destination], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def format_plan(plan: DeploymentPlan) -> str:
    return json.dumps(plan.to_dict(), indent=2, sort_keys=True)
