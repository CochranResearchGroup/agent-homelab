from __future__ import annotations

from pathlib import Path

import yaml

from agent_homelab.migrations import migrate_payload

FIXTURES = Path(__file__).parent / "fixtures"


def test_v0_host_and_external_fields_migrate_to_v1() -> None:
    data = yaml.safe_load((FIXTURES / "direct.yaml").read_text())
    data.pop("schema_version")
    service = data["services"]["hello"]
    service["local"]["host"] = service["local"].pop("hostname")
    service["external"] = service.pop("public")
    service["external"]["host"] = service["external"].pop("hostname")
    migrated, changes = migrate_payload(data)
    assert migrated["schema_version"] == 1
    assert migrated["services"]["hello"]["local"]["hostname"] == "hello.localhost"
    assert migrated["services"]["hello"]["public"]["hostname"] == "hello.example.net"
    assert changes
