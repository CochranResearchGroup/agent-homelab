from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .model import InventoryError

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
ENV_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
ARCHIVE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class Retention:
    daily: int
    weekly: int
    monthly: int


@dataclass(frozen=True)
class Stack:
    name: str
    compose_file: Path
    paths: tuple[Path, ...]
    docker_volumes: tuple[str, ...]
    stop_for_backup: bool


@dataclass(frozen=True)
class BorgConfig:
    source: Path
    repository_template: str
    passphrase_env: str
    compression: str
    volume_export_image: str
    retention: Retention
    stacks: dict[str, Stack]

    def repository_for(self, stack: str) -> str:
        return self.repository_template.format(stack=stack)


def load_config(path: str | Path) -> BorgConfig:
    source = Path(path).expanduser().resolve()
    raw = yaml.safe_load(source.read_text())
    if not isinstance(raw, dict):
        raise InventoryError("Borg configuration root must be a mapping")
    if raw.get("schema_version") != 1:
        raise InventoryError("Borg configuration schema_version must be 1")
    _reject_inline_secrets(raw)
    allowed_root = {
        "schema_version",
        "repository_template",
        "passphrase_env",
        "compression",
        "volume_export_image",
        "retention",
        "stacks",
    }
    _reject_unknown_keys(raw, allowed_root, "Borg configuration")
    repository_template = _required_text(raw, "repository_template")
    repository_without_stack = repository_template.replace("{stack}", "")
    if (
        repository_template.count("{stack}") != 1
        or any(char.isspace() for char in repository_template)
        or repository_template.startswith("-")
        or "{" in repository_without_stack
        or "}" in repository_without_stack
    ):
        raise InventoryError("repository_template must contain {stack} exactly once")
    if not repository_template.startswith(("/", "ssh://")):
        raise InventoryError("repository_template must be an absolute local path or ssh:// URL")
    passphrase_env = raw.get("passphrase_env", "BORG_PASSPHRASE")
    if not isinstance(passphrase_env, str) or not ENV_RE.fullmatch(passphrase_env):
        raise InventoryError("passphrase_env must be an uppercase environment variable name")
    compression = raw.get("compression", "zstd,3")
    if not isinstance(compression, str) or not re.fullmatch(r"[a-z0-9,+-]+", compression):
        raise InventoryError("compression contains unsupported characters")
    volume_export_image = raw.get("volume_export_image", "busybox:1.37.0")
    if not isinstance(volume_export_image, str) or any(char.isspace() for char in volume_export_image):
        raise InventoryError("volume_export_image must be one image reference")
    retention_raw = raw.get("retention", {})
    if not isinstance(retention_raw, dict):
        raise InventoryError("retention must be a mapping")
    _reject_unknown_keys(retention_raw, {"daily", "weekly", "monthly"}, "retention")
    retention = Retention(
        daily=_positive_int(retention_raw, "daily", 7),
        weekly=_positive_int(retention_raw, "weekly", 4),
        monthly=_positive_int(retention_raw, "monthly", 6),
    )
    stacks_raw = raw.get("stacks")
    if not isinstance(stacks_raw, dict) or not stacks_raw:
        raise InventoryError("stacks must be a non-empty mapping")
    stacks: dict[str, Stack] = {}
    for name, stack_raw in sorted(stacks_raw.items()):
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise InventoryError(f"Invalid stack name: {name}")
        if not isinstance(stack_raw, dict):
            raise InventoryError(f"stacks.{name} must be a mapping")
        _reject_unknown_keys(
            stack_raw,
            {"compose_file", "paths", "docker_volumes", "stop_for_backup"},
            f"stacks.{name}",
        )
        compose_file = Path(_required_text(stack_raw, "compose_file")).expanduser()
        if not compose_file.is_absolute():
            raise InventoryError(f"stacks.{name}.compose_file must be absolute")
        paths = tuple(Path(item).expanduser() for item in _string_list(stack_raw, "paths"))
        if any(not item.is_absolute() for item in paths):
            raise InventoryError(f"stacks.{name}.paths must contain only absolute paths")
        docker_volumes = tuple(_string_list(stack_raw, "docker_volumes"))
        if any(not NAME_RE.fullmatch(item) for item in docker_volumes):
            raise InventoryError(f"stacks.{name}.docker_volumes contains an invalid volume name")
        if not paths and not docker_volumes:
            raise InventoryError(f"stacks.{name} must define paths or docker_volumes")
        stop_for_backup = stack_raw.get("stop_for_backup", True)
        if not isinstance(stop_for_backup, bool):
            raise InventoryError(f"stacks.{name}.stop_for_backup must be true or false")
        stacks[name] = Stack(name, compose_file, paths, docker_volumes, stop_for_backup)
    config = BorgConfig(
        source=source,
        repository_template=repository_template,
        passphrase_env=passphrase_env,
        compression=compression,
        volume_export_image=volume_export_image,
        retention=retention,
        stacks=stacks,
    )
    _validate_repository_boundaries(config)
    return config


def plan_backup(config: BorgConfig, selected: list[str] | None = None) -> dict[str, Any]:
    stacks = _select_stacks(config, selected)
    return {
        "status": "planned",
        "config": str(config.source),
        "stacks": [
            {
                "name": stack.name,
                "repository": config.repository_for(stack.name),
                "compose_file": str(stack.compose_file),
                "stop_for_backup": stack.stop_for_backup,
                "paths": [str(path) for path in stack.paths],
                "docker_volumes": list(stack.docker_volumes),
                "actions": (
                    (["stop stack"] if stack.stop_for_backup else [])
                    + ["export named volumes", "create Borg archive", "prune retention", "compact repository"]
                    + (["start stack"] if stack.stop_for_backup else [])
                ),
            }
            for stack in stacks
        ],
    }


def initialize_repositories(
    config: BorgConfig, selected: list[str] | None = None, *, apply: bool = False, runner: Runner | None = None
) -> dict[str, Any]:
    stacks = _select_stacks(config, selected)
    commands = [["borg", "init", "--encryption=repokey-blake2", config.repository_for(stack.name)] for stack in stacks]
    if not apply:
        return {"status": "planned", "commands": commands}
    _require_tools("borg")
    env = _borg_env(config)
    invoke = runner or _run
    for command in commands:
        invoke(command, env=env, check=True, text=True)
    return {"status": "initialized", "repositories": [config.repository_for(stack.name) for stack in stacks]}


def run_backup(
    config: BorgConfig, selected: list[str] | None = None, *, apply: bool = False, runner: Runner | None = None
) -> dict[str, Any]:
    if not apply:
        return plan_backup(config, selected)
    _require_tools("borg", "docker")
    env = _borg_env(config)
    invoke = runner or _run
    results = []
    for stack in _select_stacks(config, selected):
        results.append(_backup_stack(config, stack, env, invoke))
    return {"status": "complete", "stacks": results}


def _backup_stack(config: BorgConfig, stack: Stack, env: dict[str, str], runner: Runner) -> dict[str, Any]:
    compose = [
        "docker",
        "compose",
        "--project-directory",
        str(stack.compose_file.parent),
        "-f",
        str(stack.compose_file),
    ]
    if not stack.compose_file.is_file():
        raise InventoryError(f"Compose file does not exist: {stack.compose_file}")
    missing_paths = [str(path) for path in stack.paths if not path.exists()]
    if missing_paths:
        raise InventoryError(f"Backup paths do not exist: {', '.join(missing_paths)}")
    runner([*compose, "config", "--quiet"], check=True, text=True)
    for volume in stack.docker_volumes:
        runner(["docker", "volume", "inspect", volume], check=True, capture_output=True, text=True)
    runner(
        ["borg", "info", config.repository_for(stack.name)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    stopped = False
    with tempfile.TemporaryDirectory(prefix=f"agent-homelab-{stack.name}-") as temp_dir:
        staging = Path(temp_dir)
        volume_staging = staging / "docker-volumes"
        volume_staging.mkdir(mode=0o700)
        archive_inputs = [str(path) for path in stack.paths]
        try:
            if stack.stop_for_backup:
                stopped = True
                runner([*compose, "stop"], check=True, text=True)
            for volume in stack.docker_volumes:
                target = volume_staging / f"{volume}.tar"
                runner(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--mount",
                        f"type=volume,src={volume},dst=/source,readonly",
                        "--mount",
                        f"type=bind,src={volume_staging},dst=/backup",
                        config.volume_export_image,
                        "tar",
                        "-C",
                        "/source",
                        "-cpf",
                        f"/backup/{target.name}",
                        ".",
                    ],
                    check=True,
                    text=True,
                )
                archive_inputs.append(f"{staging}/./docker-volumes/{target.name}")
            archive = f"{stack.name}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
            repository = config.repository_for(stack.name)
            runner(
                [
                    "borg",
                    "create",
                    "--stats",
                    "--compression",
                    config.compression,
                    f"{repository}::{archive}",
                    *archive_inputs,
                ],
                env=env,
                check=True,
                text=True,
            )
            runner(
                [
                    "borg",
                    "prune",
                    "--list",
                    "--keep-daily",
                    str(config.retention.daily),
                    "--keep-weekly",
                    str(config.retention.weekly),
                    "--keep-monthly",
                    str(config.retention.monthly),
                    repository,
                ],
                env=env,
                check=True,
                text=True,
            )
            runner(["borg", "compact", repository], env=env, check=True, text=True)
        finally:
            if stopped:
                runner([*compose, "up", "-d"], check=True, text=True)
    return {"name": stack.name, "status": "backed-up", "repository": config.repository_for(stack.name)}


def list_archives(config: BorgConfig, stack_name: str, *, runner: Runner | None = None) -> list[str]:
    stack = _select_stacks(config, [stack_name])[0]
    _require_tools("borg")
    result = (runner or _run)(
        ["borg", "list", "--short", config.repository_for(stack.name)],
        env=_borg_env(config),
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def check_repository(
    config: BorgConfig, stack_name: str, *, verify_data: bool = False, runner: Runner | None = None
) -> dict[str, Any]:
    stack = _select_stacks(config, [stack_name])[0]
    _require_tools("borg")
    command = ["borg", "check"]
    if verify_data:
        command.append("--verify-data")
    command.append(config.repository_for(stack.name))
    (runner or _run)(command, env=_borg_env(config), check=True, text=True)
    return {"status": "healthy", "stack": stack.name, "verify_data": verify_data}


def restore_archive(
    config: BorgConfig,
    stack_name: str,
    archive: str,
    target: str | Path,
    *,
    apply: bool = False,
    runner: Runner | None = None,
) -> dict[str, Any]:
    stack = _select_stacks(config, [stack_name])[0]
    if not ARCHIVE_RE.fullmatch(archive):
        raise InventoryError("archive contains unsupported characters")
    destination = Path(target).expanduser().resolve()
    _validate_restore_target(stack, destination)
    command = ["borg", "extract", f"{config.repository_for(stack.name)}::{archive}"]
    if not apply:
        return {"status": "planned", "stack": stack.name, "target": str(destination), "command": command}
    _require_tools("borg")
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise InventoryError("restore target must be empty")
    (runner or _run)(command, cwd=destination, env=_borg_env(config), check=True, text=True)
    return {"status": "restored-to-staging", "stack": stack.name, "target": str(destination)}


def _validate_restore_target(stack: Stack, target: Path) -> None:
    protected = [stack.compose_file.parent.resolve(), *(path.resolve() for path in stack.paths)]
    for source in protected:
        if target == source or target.is_relative_to(source) or source.is_relative_to(target):
            raise InventoryError(f"restore target overlaps live stack state: {source}")


def _validate_repository_boundaries(config: BorgConfig) -> None:
    for stack in config.stacks.values():
        repository = config.repository_for(stack.name)
        if not repository.startswith("/"):
            continue
        repository_path = Path(repository).resolve()
        for source in stack.paths:
            source_path = source.resolve()
            if repository_path == source_path or repository_path.is_relative_to(source_path):
                raise InventoryError(f"Repository for {stack.name} must not be inside a backup source: {source_path}")


def _select_stacks(config: BorgConfig, selected: list[str] | None) -> list[Stack]:
    names = selected or sorted(config.stacks)
    unknown = sorted(set(names) - set(config.stacks))
    if unknown:
        raise InventoryError(f"Unknown backup stacks: {', '.join(unknown)}")
    return [config.stacks[name] for name in names]


def _borg_env(config: BorgConfig) -> dict[str, str]:
    value = os.environ.get(config.passphrase_env)
    if not value:
        raise InventoryError(f"Required Borg passphrase environment variable is not set: {config.passphrase_env}")
    return {**os.environ, "BORG_PASSPHRASE": value}


def _require_tools(*names: str) -> None:
    missing = [name for name in names if not shutil.which(name)]
    if missing:
        raise InventoryError(f"Required executables are missing: {', '.join(missing)}")


def _run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, **kwargs)


def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InventoryError(f"{key} must be a non-empty string")
    return value


def _positive_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise InventoryError(f"retention.{key} must be a positive integer")
    return value


def _string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise InventoryError(f"{key} must be a list of non-empty strings")
    return value


def _reject_inline_secrets(value: Any, path: str = "") -> None:
    forbidden = {"passphrase", "password", "secret", "token", "key"}
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{path}.{key}" if path else str(key)
            if str(key).lower() in forbidden:
                raise InventoryError(f"Inline secret field is forbidden: {location}")
            _reject_inline_secrets(child, location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_inline_secrets(child, f"{path}[{index}]")


def _reject_unknown_keys(data: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise InventoryError(f"{path} contains unknown fields: {', '.join(unknown)}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="agent-homelab-borg-backup", description="Guarded Borg backups for Compose stacks"
    )
    root.add_argument("--config", default="backup.yaml")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate backup configuration without mutation")
    plan = sub.add_parser("plan", help="show backup actions without mutation")
    plan.add_argument("stacks", nargs="*")
    init = sub.add_parser("init", help="plan or initialize encrypted per-stack repositories")
    init.add_argument("stacks", nargs="*")
    init.add_argument("--apply", action="store_true")
    backup = sub.add_parser("backup", help="plan or execute stopped-stack backups")
    backup.add_argument("stacks", nargs="*")
    backup.add_argument("--apply", action="store_true")
    archives = sub.add_parser("archives", help="list archives for one stack")
    archives.add_argument("stack")
    check = sub.add_parser("check", help="check one stack repository")
    check.add_argument("stack")
    check.add_argument("--verify-data", action="store_true")
    restore = sub.add_parser("restore", help="plan or extract an archive to an empty staging directory")
    restore.add_argument("stack")
    restore.add_argument("archive")
    restore.add_argument("--target", required=True)
    restore.add_argument("--apply", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate":
            result: Any = {"status": "valid", "stacks": sorted(config.stacks)}
        elif args.command == "plan":
            result = plan_backup(config, args.stacks)
        elif args.command == "init":
            result = initialize_repositories(config, args.stacks, apply=args.apply)
        elif args.command == "backup":
            result = run_backup(config, args.stacks, apply=args.apply)
        elif args.command == "archives":
            result = {"stack": args.stack, "archives": list_archives(config, args.stack)}
        elif args.command == "check":
            result = check_repository(config, args.stack, verify_data=args.verify_data)
        elif args.command == "restore":
            result = restore_archive(config, args.stack, args.archive, args.target, apply=args.apply)
        else:
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (InventoryError, OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
