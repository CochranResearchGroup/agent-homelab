from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_homelab.oauth_relay import CommandAdapter, RelayApplication, RelayError, StateStore, redact_request_line


def provider_config() -> dict:
    return {
        "public_base_url": "https://oauth.example.net",
        "providers": {
            "example": {
                "state_mode": "relay",
                "authorization_hosts": ["accounts.example.com"],
                "start_command": ["adapter", "start"],
                "finish_command": ["adapter", "finish"],
                "tenants": {"personal": {}},
            }
        },
    }


def test_state_is_one_time_and_replay_is_rejected(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.json")
    state = store.issue("example", "personal")
    assert store.consume(state).tenant == "personal"
    with pytest.raises(RelayError, match="already consumed"):
        store.consume(state)


def test_expired_state_is_rejected(tmp_path: Path) -> None:
    now = [100.0]
    store = StateStore(tmp_path / "state.json", ttl_seconds=10, clock=lambda: now[0])
    state = store.issue("example", "personal")
    now[0] = 111.0
    with pytest.raises(RelayError, match="expired"):
        store.consume(state)


def test_adapter_rejects_state_mismatch_and_open_redirect() -> None:
    config = provider_config()["providers"]["example"]
    adapter = CommandAdapter("example", config, "personal", "https://oauth.example.net/callback")
    mismatch = subprocess.CompletedProcess(
        [], 0, json.dumps({"authorization_url": "https://accounts.example.com/a?state=wrong"}), ""
    )
    with patch("subprocess.run", return_value=mismatch), pytest.raises(RelayError, match="did not preserve"):
        adapter.start("a" * 43)
    redirect = subprocess.CompletedProcess(
        [], 0, json.dumps({"authorization_url": f"https://evil.example/a?state={'a' * 43}"}), ""
    )
    with patch("subprocess.run", return_value=redirect), pytest.raises(RelayError, match="not allowlisted"):
        adapter.start("a" * 43)


def test_callback_rejects_wrong_host_and_consumes_state_once(tmp_path: Path) -> None:
    config = provider_config()
    store = StateStore(tmp_path / "state.json")
    app = RelayApplication(config, store)
    state = store.issue("example", "personal")
    with pytest.raises(RelayError, match="host is not allowlisted"):
        app.callback(f"/callback?state={state}&code=redacted", "wrong.example.net")
    completed = subprocess.CompletedProcess([], 0, "", "")
    with patch("subprocess.run", return_value=completed):
        assert app.callback(f"/callback?state={state}&code=redacted", "oauth.example.net") == (
            "https://oauth.example.net/done"
        )
    with patch("subprocess.run", return_value=completed), pytest.raises(RelayError, match="already consumed"):
        app.callback(f"/callback?state={state}&code=redacted", "oauth.example.net")


def test_state_file_contains_hash_not_raw_state(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    state = StateStore(path).issue("example", "personal")
    assert state not in path.read_text()


def test_request_log_redacts_callback_query() -> None:
    line = "GET /callback?state=private-state&code=private-code HTTP/1.1"
    redacted = redact_request_line(line)
    assert "private-state" not in redacted
    assert "private-code" not in redacted
