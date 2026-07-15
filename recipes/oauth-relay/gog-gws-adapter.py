#!/usr/bin/env python3
"""Configuration-driven GOG/GWS adapter for the generic OAuth relay protocol."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def config() -> tuple[dict, dict]:
    path = Path(os.environ.get("GOG_GWS_ADAPTER_CONFIG", "gog-gws-adapter.yaml")).expanduser()
    payload = yaml.safe_load(path.read_text())
    tenant_name = os.environ["OAUTH_RELAY_TENANT"]
    tenant = payload["tenants"][tenant_name]
    return payload, tenant


def environment(payload: dict, tenant: dict) -> dict[str, str]:
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(Path(tenant["gws_config_dir"]).expanduser())
    env.setdefault("GOG_KEYRING_BACKEND", payload.get("keyring_backend", "file"))
    env.setdefault("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND", payload.get("keyring_backend", "file"))
    return env


def gog_command(payload: dict, tenant: dict, *arguments: str) -> list[str]:
    command = [str(Path(payload.get("gog_bin", "gog")).expanduser())]
    if tenant.get("client"):
        command.extend(["--client", tenant["client"]])
    command.extend(arguments)
    return command


def run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=120, env=env)


def start(payload: dict, tenant: dict, env: dict[str, str]) -> int:
    result = run(
        gog_command(
            payload,
            tenant,
            "--json",
            "auth",
            "add",
            tenant["account"],
            "--remote",
            "--step",
            "1",
            "--redirect-uri",
            os.environ["OAUTH_RELAY_REDIRECT_URI"],
            "--force-consent",
            "--services",
            payload.get("services", "all"),
        ),
        env,
    )
    response = json.loads(result.stdout)
    print(json.dumps({"authorization_url": response["auth_url"]}))
    return 0


def finish(payload: dict, tenant: dict, env: dict[str, str]) -> int:
    run(
        gog_command(
            payload,
            tenant,
            "auth",
            "add",
            tenant["account"],
            "--remote",
            "--step",
            "2",
            "--auth-url",
            os.environ["OAUTH_RELAY_CALLBACK_URL"],
            "--redirect-uri",
            os.environ["OAUTH_RELAY_REDIRECT_URI"],
            "--force-consent",
            "--services",
            payload.get("services", "all"),
        ),
        env,
    )
    Path(tenant["gws_config_dir"]).expanduser().mkdir(parents=True, exist_ok=True)
    run(
        [
            payload.get("gws_bin", "gws"),
            "auth",
            "sync-gog",
            "--account",
            tenant["account"],
            "--gog-bin",
            payload.get("gog_bin", "gog"),
            "--client",
            tenant.get("client", "default"),
        ],
        env,
    )
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"start", "finish"}:
        print("usage: gog-gws-adapter.py start|finish", file=sys.stderr)
        return 2
    payload, tenant = config()
    env = environment(payload, tenant)
    return start(payload, tenant, env) if sys.argv[1] == "start" else finish(payload, tenant, env)


if __name__ == "__main__":
    raise SystemExit(main())
