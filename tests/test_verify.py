from __future__ import annotations

from dataclasses import dataclass

import pytest

from agent_homelab import verify


@dataclass
class FakeResponse:
    status: int
    location: str | None = None

    def getheader(self, name: str) -> str | None:
        return self.location if name == "Location" else None

    def read(self, _limit: int) -> bytes:
        return b""


class FakeConnection:
    response = FakeResponse(200)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def request(self, *_args: object, **_kwargs: object) -> None:
        pass

    def getresponse(self) -> FakeResponse:
        return self.response

    def close(self) -> None:
        pass


@pytest.mark.parametrize(
    "status,expected",
    [(200, True), (302, True), (400, False), (403, False), (404, False), (500, False)],
)
def test_unprotected_route_requires_success_or_redirect(
    monkeypatch: pytest.MonkeyPatch, status: int, expected: bool
) -> None:
    FakeConnection.response = FakeResponse(status)
    monkeypatch.setattr(verify.http.client, "HTTPConnection", FakeConnection)
    assert verify.probe("app", "local", "http://app.localhost").ok is expected


def test_protected_route_requires_auth_host_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeConnection.response = FakeResponse(302, "https://auth.example.net/")
    monkeypatch.setattr(verify.http.client, "HTTPSConnection", FakeConnection)
    result = verify.probe("app", "public", "https://app.example.net", expected_auth_redirect=True)
    assert result.ok is True

    FakeConnection.response = FakeResponse(302, "https://unrelated.example.net/")
    result = verify.probe("app", "public", "https://app.example.net", expected_auth_redirect=True)
    assert result.ok is False
