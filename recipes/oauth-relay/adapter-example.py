#!/usr/bin/env python3
"""Protocol example only; replace the authorization endpoint with a real provider adapter."""

from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlencode


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"start", "finish"}:
        print("usage: adapter-example.py start|finish", file=sys.stderr)
        return 2
    if sys.argv[1] == "start":
        query = urlencode(
            {
                "redirect_uri": os.environ["OAUTH_RELAY_REDIRECT_URI"],
                "state": os.environ["OAUTH_RELAY_STATE"],
                "response_type": "code",
            }
        )
        print(json.dumps({"authorization_url": f"https://accounts.example.com/authorize?{query}"}))
        return 0
    callback_url = os.environ["OAUTH_RELAY_CALLBACK_URL"]
    if not callback_url.startswith(os.environ["OAUTH_RELAY_REDIRECT_URI"] + "?"):
        print("callback URL mismatch", file=sys.stderr)
        return 1
    # A real adapter exchanges the code and stores credentials without printing them.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
