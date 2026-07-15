#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import tarfile
import tempfile
import zipfile
from pathlib import Path

from scan_public import scan


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract and privacy-scan built Python distributions")
    parser.add_argument("dist", nargs="?", default="dist")
    parser.add_argument("--patterns-file", default=os.environ.get("PRIVATE_PATTERNS_FILE"))
    args = parser.parse_args()
    patterns = []
    if args.patterns_file:
        patterns = [
            line.strip()
            for line in Path(args.patterns_file).expanduser().read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    artifacts = sorted(Path(args.dist).glob("*"))
    if not artifacts:
        print("No distribution artifacts found")
        return 1
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for artifact in artifacts:
            target = root / artifact.name
            target.mkdir()
            if artifact.suffix in {".whl", ".zip"}:
                with zipfile.ZipFile(artifact) as archive:
                    for member in archive.infolist():
                        destination = (target / member.filename).resolve()
                        if not destination.is_relative_to(target.resolve()):
                            raise ValueError(f"Unsafe wheel member: {member.filename}")
                    archive.extractall(target)  # noqa: S202 - every member path was bounded above
            elif artifact.name.endswith(".tar.gz"):
                with tarfile.open(artifact) as archive:
                    archive.extractall(target, filter="data")
            else:
                continue
            problems = scan(target, patterns)
            if problems:
                print(f"Artifact scan failed: {artifact}")
                for problem in problems:
                    print(f"- {problem}")
                return 1
    print(f"Distribution inspection passed: {len(artifacts)} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
