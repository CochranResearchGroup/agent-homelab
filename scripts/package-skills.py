#!/usr/bin/env python3
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic bundle of Agent Homelab skills")
    parser.add_argument("--output", default="dist/agent-homelab-skills-v0.1.0-rc.1.zip")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in (root / "skills").rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIMESTAMP)
            info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
