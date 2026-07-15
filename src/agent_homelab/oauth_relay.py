from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import yaml


class RelayError(ValueError):
    """Raised when an OAuth relay request violates the configured contract."""


@dataclass(frozen=True)
class StateRecord:
    provider: str
    tenant: str
    created_at: float
    expires_at: float


class StateStore:
    def __init__(self, path: str | Path, ttl_seconds: int = 600, clock: Any = time.time) -> None:
        self.path = Path(path).expanduser()
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._lock = threading.Lock()

    def issue(self, provider: str, tenant: str) -> str:
        raw = secrets.token_urlsafe(32)
        self.register(raw, provider, tenant)
        return raw

    def register(self, raw: str, provider: str, tenant: str) -> None:
        if len(raw) < 32:
            raise RelayError("OAuth state must contain at least 32 characters")
        now = float(self.clock())
        with self._lock:
            state = self._load()
            self._purge(state, now)
            state[self._digest(raw)] = {
                "provider": provider,
                "tenant": tenant,
                "created_at": now,
                "expires_at": now + self.ttl_seconds,
            }
            self._save(state)

    def consume(self, raw: str) -> StateRecord:
        now = float(self.clock())
        with self._lock:
            state = self._load()
            key = self._digest(raw)
            payload = state.pop(key, None)
            self._purge(state, now)
            self._save(state)
        if payload is None:
            raise RelayError("OAuth state is unknown, expired, or already consumed")
        if float(payload["expires_at"]) < now:
            raise RelayError("OAuth state has expired")
        return StateRecord(
            provider=str(payload["provider"]),
            tenant=str(payload["tenant"]),
            created_at=float(payload["created_at"]),
            expires_at=float(payload["expires_at"]),
        )

    @staticmethod
    def _digest(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    def _load(self) -> dict[str, dict[str, Any]]:
        try:
            payload = json.loads(self.path.read_text())
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, OSError) as exc:
            raise RelayError(f"State store is unreadable: {exc}") from exc
        if not isinstance(payload, dict):
            raise RelayError("State store root must be an object")
        return payload

    def _save(self, state: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, self.path)

    @staticmethod
    def _purge(state: dict[str, dict[str, Any]], now: float) -> None:
        for key in [key for key, value in state.items() if float(value.get("expires_at", 0)) < now]:
            state.pop(key, None)


class CommandAdapter:
    def __init__(self, provider_name: str, provider: dict[str, Any], tenant: str, redirect_uri: str) -> None:
        self.provider_name = provider_name
        self.provider = provider
        self.tenant = tenant
        self.redirect_uri = redirect_uri

    def start(self, state: str) -> tuple[str, str]:
        result = self._run(self.provider["start_command"], state=state)
        try:
            payload = json.loads(result.stdout)
            auth_url = str(payload["authorization_url"])
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RelayError("Provider adapter did not return JSON with authorization_url") from exc
        parsed = urlsplit(auth_url)
        returned_state = parse_qs(parsed.query).get("state", [None])[0]
        if parsed.scheme != "https" or not parsed.hostname:
            raise RelayError("Provider authorization URL must use HTTPS")
        state_mode = self.provider.get("state_mode", "relay")
        if state_mode not in {"relay", "adapter"}:
            raise RelayError("Provider state_mode must be relay or adapter")
        if state_mode == "relay" and returned_state != state:
            raise RelayError("Provider authorization URL did not preserve relay state")
        if not returned_state or len(returned_state) < 32:
            raise RelayError("Provider authorization URL returned weak or missing state")
        allowed_hosts = set(self.provider.get("authorization_hosts", []))
        if not allowed_hosts or parsed.hostname not in allowed_hosts:
            raise RelayError("Provider authorization host is not allowlisted")
        return auth_url, returned_state

    def finish(self, callback_url: str, state: str) -> None:
        self._run(self.provider["finish_command"], state=state, callback_url=callback_url)

    def _run(self, command: list[str], *, state: str, callback_url: str = "") -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "OAUTH_RELAY_PROVIDER": self.provider_name,
                "OAUTH_RELAY_TENANT": self.tenant,
                "OAUTH_RELAY_REDIRECT_URI": self.redirect_uri,
                "OAUTH_RELAY_STATE": state,
                "OAUTH_RELAY_CALLBACK_URL": callback_url,
            }
        )
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=int(self.provider.get("timeout_seconds", 120)),
            env=env,
        )


class RelayApplication:
    def __init__(self, config: dict[str, Any], store: StateStore) -> None:
        self.config = config
        self.store = store
        self.public_base_url = str(config["public_base_url"]).rstrip("/")
        parsed = urlsplit(self.public_base_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RelayError("public_base_url must be an absolute HTTPS URL")
        self.public_host = parsed.hostname
        self.redirect_uri = f"{self.public_base_url}/callback"

    def provider_tenant(self, provider_name: str, tenant_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
        provider = self.config.get("providers", {}).get(provider_name)
        if not isinstance(provider, dict):
            raise RelayError("Unknown OAuth provider")
        tenant = provider.get("tenants", {}).get(tenant_name)
        if not isinstance(tenant, dict):
            raise RelayError("Unknown OAuth tenant")
        return provider, tenant

    def connect(self, provider_name: str, tenant_name: str) -> str:
        provider, _tenant = self.provider_tenant(provider_name, tenant_name)
        state = secrets.token_urlsafe(32)
        adapter = CommandAdapter(provider_name, provider, tenant_name, self.redirect_uri)
        auth_url, returned_state = adapter.start(state)
        self.store.register(returned_state, provider_name, tenant_name)
        return auth_url

    def callback(self, raw_path: str, host_header: str) -> str:
        if host_header.split(":", 1)[0].lower() != self.public_host.lower():
            raise RelayError("Callback host is not allowlisted")
        parsed = urlsplit(raw_path)
        if parsed.path != "/callback":
            raise RelayError("Invalid callback path")
        query = parse_qs(parsed.query)
        state = query.get("state", [""])[0]
        if not state:
            raise RelayError("Callback is missing state")
        record = self.store.consume(state)
        provider, _tenant = self.provider_tenant(record.provider, record.tenant)
        callback_url = f"{self.redirect_uri}?{urlencode({key: values[0] for key, values in query.items()})}"
        CommandAdapter(record.provider, provider, record.tenant, self.redirect_uri).finish(callback_url, state)
        return f"{self.public_base_url}/done"


def redact_request_line(value: str) -> str:
    """Remove query material such as authorization codes before request logging."""
    return value.split("?", 1)[0]


def handler_for(app: RelayApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                parsed = urlsplit(self.path)
                if parsed.path == "/healthz":
                    self._text(HTTPStatus.OK, "ok\n")
                    return
                if parsed.path == "/done":
                    self._text(HTTPStatus.OK, "Authorization completed. You may close this window.\n")
                    return
                if parsed.path == "/callback":
                    location = app.callback(self.path, self.headers.get("Host", ""))
                    self._redirect(location)
                    return
                parts = [part for part in parsed.path.split("/") if part]
                if len(parts) == 3 and parts[0] == "connect":
                    self._redirect(app.connect(parts[1], parts[2]))
                    return
                self._text(HTTPStatus.NOT_FOUND, "not found\n")
            except RelayError as exc:
                self._text(HTTPStatus.BAD_REQUEST, f"request rejected: {exc}\n")
            except subprocess.SubprocessError:
                self._text(HTTPStatus.BAD_GATEWAY, "provider adapter failed\n")

        def log_message(self, format_string: str, *args: Any) -> None:
            sanitized = list(args)
            if sanitized:
                sanitized[0] = redact_request_line(str(sanitized[0]))
            super().log_message(format_string, *sanitized)

        def _text(self, status: HTTPStatus, body: str) -> None:
            payload = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def _redirect(self, location: str) -> None:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

    return Handler


def load_config(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).expanduser().read_text())
    if not isinstance(payload, dict):
        raise RelayError("OAuth relay config must be a mapping")
    allowed = {
        "public_base_url",
        "bind_host",
        "port",
        "state_ttl_seconds",
        "state_file",
        "providers",
        "allow_non_loopback",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise RelayError(f"Unknown OAuth relay config keys: {sorted(unknown)}")
    if not payload.get("providers"):
        raise RelayError("At least one provider is required")
    if payload.get("bind_host", "127.0.0.1") not in {"127.0.0.1", "::1"} and not payload.get(
        "allow_non_loopback", False
    ):
        raise RelayError("OAuth relay binds to loopback by default; expose it through authenticated ingress")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the generic headless OAuth callback relay")
    parser.add_argument("--config", default=os.environ.get("OAUTH_RELAY_CONFIG", "oauth-relay.yaml"))
    args = parser.parse_args(argv)
    config = load_config(args.config)
    store = StateStore(
        config.get("state_file", "oauth-relay-state.json"), ttl_seconds=int(config.get("state_ttl_seconds", 600))
    )
    app = RelayApplication(config, store)
    address = (config.get("bind_host", "127.0.0.1"), int(config.get("port", 8797)))
    server = ThreadingHTTPServer(address, handler_for(app))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
