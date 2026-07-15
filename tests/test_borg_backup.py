from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_homelab.borg_backup import load_config, plan_backup, restore_archive, run_backup
from agent_homelab.model import InventoryError


def write_config(tmp_path: Path, *, extra: str = "") -> Path:
    compose = tmp_path / "stack/compose.yaml"
    compose.parent.mkdir()
    compose.write_text("services: {}\n")
    data = tmp_path / "stack/data"
    data.mkdir()
    config = tmp_path / "backup.yaml"
    config.write_text(
        f"""schema_version: 1
repository_template: {tmp_path}/repos/{{stack}}
passphrase_env: TEST_BORG_PASSPHRASE
retention: {{daily: 7, weekly: 4, monthly: 6}}
stacks:
  app:
    compose_file: {compose}
    paths: [{data}]
    docker_volumes: [app-data]
{extra}"""
    )
    return config


def test_config_and_plan_are_non_mutating(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    plan = plan_backup(config)
    assert plan["status"] == "planned"
    assert plan["stacks"][0]["actions"][0] == "stop stack"
    assert not (tmp_path / "repos").exists()


def test_inline_secret_is_rejected(tmp_path: Path) -> None:
    path = write_config(tmp_path)
    path.write_text(path.read_text() + "passphrase: forbidden\n")
    with pytest.raises(InventoryError, match="Inline secret"):
        load_config(path)


def test_backup_restarts_stack_after_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    monkeypatch.setenv("TEST_BORG_PASSPHRASE", "synthetic-test-only")
    monkeypatch.setattr("agent_homelab.borg_backup._require_tools", lambda *_names: None)
    commands: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    result = run_backup(config, apply=True, runner=runner)
    assert result["status"] == "complete"
    assert any(command[-1] == "stop" for command in commands)
    assert commands[-1][-2:] == ["up", "-d"]
    assert any(command[:2] == ["borg", "create"] for command in commands)
    assert any(command[:2] == ["borg", "prune"] for command in commands)
    assert any(command[:2] == ["borg", "compact"] for command in commands)


def test_backup_restarts_stack_after_borg_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    monkeypatch.setenv("TEST_BORG_PASSPHRASE", "synthetic-test-only")
    monkeypatch.setattr("agent_homelab.borg_backup._require_tools", lambda *_names: None)
    commands: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[:2] == ["borg", "create"]:
            raise subprocess.CalledProcessError(2, command)
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(subprocess.CalledProcessError):
        run_backup(config, apply=True, runner=runner)
    assert commands[-1][-2:] == ["up", "-d"]


def test_preflight_failure_does_not_stop_stack(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    monkeypatch.setenv("TEST_BORG_PASSPHRASE", "synthetic-test-only")
    monkeypatch.setattr("agent_homelab.borg_backup._require_tools", lambda *_names: None)
    commands: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[-2:] == ["config", "--quiet"]:
            raise subprocess.CalledProcessError(2, command)
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(subprocess.CalledProcessError):
        run_backup(config, apply=True, runner=runner)
    assert not any(command[-1] == "stop" for command in commands)


def test_restore_is_staging_only(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    live = tmp_path / "stack/data/restore"
    with pytest.raises(InventoryError, match="overlaps live stack state"):
        restore_archive(config, "app", "app-20260101T000000Z", live)
    plan = restore_archive(config, "app", "app-20260101T000000Z", tmp_path / "restore")
    assert plan["status"] == "planned"


def test_repository_cannot_be_inside_source(tmp_path: Path) -> None:
    path = write_config(tmp_path)
    source = tmp_path / "stack/data"
    path.write_text(path.read_text().replace(f"{tmp_path}/repos/{{stack}}", f"{source}/repos/{{stack}}"))
    with pytest.raises(InventoryError, match="must not be inside a backup source"):
        load_config(path)


@pytest.mark.parametrize("repository", ["relative/{stack}", "/srv/{stack}/{other}"])
def test_repository_template_rejects_ambiguous_locations(tmp_path: Path, repository: str) -> None:
    path = write_config(tmp_path)
    path.write_text(path.read_text().replace(f"{tmp_path}/repos/{{stack}}", repository))
    with pytest.raises(InventoryError, match="repository_template"):
        load_config(path)
