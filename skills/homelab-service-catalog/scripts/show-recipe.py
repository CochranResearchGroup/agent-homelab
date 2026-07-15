#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Show one Agent Homelab service recipe")
    parser.add_argument("recipe", nargs="?")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        command = [sys.executable, "-m", "agent_homelab", "recipe", "list"]
    elif args.recipe:
        command = [sys.executable, "-m", "agent_homelab", "recipe", "show", args.recipe]
    else:
        parser.error("supply a recipe or --list")
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
