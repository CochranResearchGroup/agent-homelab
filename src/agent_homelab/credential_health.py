from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml


def run_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    for check in config.get("checks", []):
        result = subprocess.run(
            check["command"],
            check=False,
            capture_output=True,
            text=True,
            timeout=int(check.get("timeout_seconds", 60)),
            env=os.environ.copy(),
        )
        if result.returncode != 0:
            failures.append({"name": check["name"], "exit_code": result.returncode})
    return failures


def fingerprint(failures: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(failures, sort_keys=True).encode()).hexdigest()[:16]


def notify(config: dict[str, Any], message: str) -> None:
    notifier = config.get("notifier", {"type": "stdout"})
    kind = notifier.get("type", "stdout")
    if kind == "stdout":
        print(message)
        return
    if kind == "webhook":
        url = os.environ.get(notifier.get("url_env", "OAUTH_HEALTH_WEBHOOK_URL"))
        if not url:
            raise ValueError("Webhook URL environment variable is not set")
        if urlsplit(url).scheme != "https":
            raise ValueError("Webhook URL must use HTTPS")
        payload = json.dumps({"text": message}).encode()
        request = urllib.request.Request(  # noqa: S310 - scheme is restricted to HTTPS above
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            if response.status >= 300:
                raise ValueError(f"Webhook returned HTTP {response.status}")
        return
    raise ValueError(f"Unknown notifier type: {kind}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check OAuth credential commands and notify once per failure state")
    parser.add_argument("--config", default="credential-health.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).expanduser().read_text())
    if not isinstance(config, dict):
        raise SystemExit("credential health config must be a mapping")
    failures = run_checks(config)
    state_path = Path(config.get("state_file", "credential-health-state.json")).expanduser()
    try:
        state = json.loads(state_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    current = fingerprint(failures) if failures else None
    changed = current != state.get("active_fingerprint")
    message = "OAuth credentials healthy"
    if failures:
        names = ", ".join(item["name"] for item in failures)
        message = f"OAuth credential checks failed: {names}. Use the configured relay to reauthorize."
    if args.dry_run:
        print(json.dumps({"failures": failures, "would_notify": changed, "message": message}, indent=2))
        return 1 if failures else 0
    if changed:
        notify(config, message)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"active_fingerprint": current}, indent=2) + "\n")
    os.chmod(state_path, 0o600)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
