"""Check OpenRouter API key balance. Uses OPEN_ROUTER_API_KEY from env."""

import json
import os
import sys
from urllib.request import Request, urlopen
from dotenv import load_dotenv

load_dotenv()


URL = "https://openrouter.ai/api/v1/key"


def main() -> None:
    key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not key:
        print("OPEN_ROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    req = Request(URL, headers={"Authorization": f"Bearer {key}"})
    try:
        with urlopen(req, timeout=10) as r:
            data = json.load(r).get("data", {})
    except OSError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    usage = data.get("usage", 0)
    limit = data.get("limit")
    remaining = data.get("limit_remaining")
    label = data.get("label", "API key")

    print(f"OpenRouter — {label}")
    print(f"  Used:    ${usage:.2f}")
    if limit is not None:
        print(f"  Limit:   ${limit:.2f}")
    if remaining is not None:
        print(f"  Left:    ${remaining:.2f}")
    else:
        print("  Left:    (no limit)")


if __name__ == "__main__":
    main()
