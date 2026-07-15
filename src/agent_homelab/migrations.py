from __future__ import annotations

import copy
from typing import Any

from .model import InventoryError, validate_inventory

LATEST_SCHEMA_VERSION = 1


def migrate_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    migrated = copy.deepcopy(payload)
    version = migrated.get("schema_version", 0)
    changes: list[str] = []
    if version == 0:
        for service_name, service in migrated.get("services", {}).items():
            local = service.get("local", {})
            if "host" in local and "hostname" not in local:
                local["hostname"] = local.pop("host")
                changes.append(f"services.{service_name}.local.host -> hostname")
            if "external" in service and "public" not in service:
                public = service.pop("external")
                if "host" in public and "hostname" not in public:
                    public["hostname"] = public.pop("host")
                service["public"] = public
                changes.append(f"services.{service_name}.external -> public")
        migrated["schema_version"] = 1
        changes.append("schema_version 0 -> 1")
        version = 1
    if version != LATEST_SCHEMA_VERSION:
        raise InventoryError(
            f"No migration path from schema_version {version!r} to {LATEST_SCHEMA_VERSION}"
        )
    validate_inventory(migrated)
    return migrated, changes
