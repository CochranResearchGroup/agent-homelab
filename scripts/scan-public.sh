#!/usr/bin/env sh
set -eu

root=${1:-.}
patterns_file=${PRIVATE_PATTERNS_FILE:-}

if [ -n "$patterns_file" ]; then
  python3 "$root/scripts/scan_public.py" "$root" --patterns-file "$patterns_file"
else
  python3 "$root/scripts/scan_public.py" "$root"
fi

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --no-git --source "$root" --redact --exit-code 1
  if git -C "$root" rev-parse --verify HEAD >/dev/null 2>&1; then
    gitleaks git "$root" --redact --exit-code 1
  fi
else
  echo "gitleaks is required for a release gate" >&2
  exit 2
fi
