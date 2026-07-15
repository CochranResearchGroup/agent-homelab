from __future__ import annotations

import http.client
import json
import ssl
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlsplit

from .model import Inventory


@dataclass(frozen=True)
class ProbeResult:
    service: str
    surface: str
    url: str
    status: int | None
    location: str | None
    ok: bool
    detail: str


def verify_inventory(inventory: Inventory, timeout: float = 10.0) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for name, service in inventory.services.items():
        local = service.get("local", {})
        if local.get("enabled"):
            results.append(probe(name, "local", f"http://{local['hostname']}", timeout=timeout))
        public = service.get("public", {})
        if public.get("enabled"):
            expected_redirect = public.get("auth", {}).get("provider") == "authelia"
            results.append(
                probe(
                    name,
                    "public",
                    f"https://{public['hostname']}",
                    timeout=timeout,
                    expected_auth_redirect=expected_redirect,
                )
            )
    return results


def probe(
    service: str,
    surface: str,
    url: str,
    *,
    timeout: float = 10.0,
    expected_auth_redirect: bool = False,
) -> ProbeResult:
    parsed = urlsplit(url)
    connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    kwargs: dict[str, Any] = {"timeout": timeout}
    if parsed.scheme == "https":
        kwargs["context"] = ssl.create_default_context()
    try:
        connection = connection_class(parsed.hostname, parsed.port, **kwargs)
        connection.request("GET", parsed.path or "/", headers={"User-Agent": "agent-homelab-verify/1"})
        response = connection.getresponse()
        location = response.getheader("Location")
        response.read(4096)
        connection.close()
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(service, surface, url, None, None, False, f"request failed: {exc}")

    if expected_auth_redirect:
        ok = response.status in {301, 302, 303, 307, 308} and bool(location and "auth." in location)
        detail = "authentication redirect observed" if ok else "expected redirect to the authentication host"
    else:
        ok = 200 <= response.status < 400
        detail = "route responded" if ok else "route missing or unavailable"
    return ProbeResult(service, surface, url, response.status, location, ok, detail)


def results_json(results: list[ProbeResult]) -> str:
    return json.dumps([asdict(result) for result in results], indent=2, sort_keys=True)
