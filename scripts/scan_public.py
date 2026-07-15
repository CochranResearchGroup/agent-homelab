#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import re
import subprocess
from pathlib import Path

SKIP_PARTS = {".git", ".venv", "build", "dist", "rendered", "__pycache__"}
DENIED_BASENAMES = {"homelab.yaml", ".env", "oauth-relay-state.json", "credential-health-state.json"}
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,}|example\.invalid)\b")
IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
HIGH_RISK = {
    "absolute user home": re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "dynamic DNS hostname": re.compile(r"(?i)\b(?:dyndns|duckdns|no-ip)\b"),
    "Tailscale tailnet hostname": re.compile(r"(?i)\b[a-z0-9-]+\.ts\.net\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
}
DOCUMENTATION_NETWORKS = [
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
]
ALLOWED_SPECIAL_ADDRESSES = {
    ipaddress.ip_address(0),
    ipaddress.ip_address(2130706433),
}


def files_to_scan(root: Path) -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        return [root / line for line in result.stdout.splitlines() if line]
    return [path for path in root.rglob("*") if path.is_file() and not (set(path.relative_to(root).parts) & SKIP_PARTS)]


def scan(root: Path, private_patterns: list[str]) -> list[str]:
    problems: list[str] = []
    for path in files_to_scan(root):
        relative = path.relative_to(root)
        if set(relative.parts) & SKIP_PARTS:
            continue
        if path.name in DENIED_BASENAMES:
            problems.append(f"{relative}: denied runtime-state filename")
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if relative.as_posix() != "scripts/scan_public.py":
            for label, pattern in HIGH_RISK.items():
                if pattern.search(text):
                    problems.append(f"{relative}: {label}")
        for match in EMAIL_RE.finditer(text):
            domain = match.group(1).lower()
            if domain not in {"example.invalid", "example.com", "example.net"}:
                problems.append(f"{relative}: non-synthetic email domain {domain}")
        for raw in IPV4_RE.findall(text):
            try:
                address = ipaddress.ip_address(raw)
            except ValueError:
                continue
            if address in ALLOWED_SPECIAL_ADDRESSES:
                continue
            if address.is_private and not any(address in network for network in DOCUMENTATION_NETWORKS):
                problems.append(f"{relative}: non-documentation private IPv4 address {raw}")
            if address.is_global and not any(address in network for network in DOCUMENTATION_NETWORKS):
                problems.append(f"{relative}: public IPv4 address {raw}")
        for pattern in private_patterns:
            if pattern in text or pattern in relative.as_posix():
                problems.append(f"{relative}: matched private denylist entry")
    return sorted(set(problems))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan a public tree for identity, topology, runtime state, and secrets"
    )
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--patterns-file")
    args = parser.parse_args()
    patterns = []
    if args.patterns_file:
        patterns = [
            line.strip()
            for line in Path(args.patterns_file).expanduser().read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    root = Path(args.root).resolve()
    problems = scan(root, patterns)
    if problems:
        print("Public-tree scan failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"Public-tree scan passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
