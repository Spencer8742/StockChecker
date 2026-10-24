#!/usr/bin/env python3
"""Check Apple Store stock for iPhone Duo / Night Sky / 512GB every 5 minutes.

Uses only the Python standard library. See README.md for usage.
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# iPhone Duo, 7.6-inch, Night Sky, 512GB (US). Confirmed from the part number
# Apple's own buy page requests for this configuration.
PART_NUMBER = "MK1H4LL/A"
PRODUCT_NAME = "iPhone Duo 512GB Night Sky"
PRODUCT_URL = (
    "https://www.apple.com/shop/buy-iphone/iphone-duo/"
    "7.6-inch-display-512gb-night-sky-unlocked"
)
# Apple's /shop/fulfillment-messages endpoint now rejects non-browser requests
# (HTTP 541); this one returns the same per-store pickup data.
PICKUP_URL = "https://www.apple.com/shop/pickup-message-recommendations"
DEFAULT_INTERVAL = 5 * 60

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


class BlockedError(Exception):
    """Apple refused the request (HTTP 541/403 or a non-JSON block page)."""


def fetch_json(url, params):
    req = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params, safe="/"),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Referer": PRODUCT_URL,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code in (403, 541):
            raise BlockedError(f"HTTP {e.code}") from e
        raise
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise BlockedError("non-JSON response (likely a block page)") from e


def fetch_pickup(zip_code):
    return fetch_json(PICKUP_URL, {
        "mts.0": "regular",
        "searchNearby": "true",
        "location": zip_code,
        "product": PART_NUMBER,
    })


def parse_pickup(data, part=PART_NUMBER):
    """Return [(store name, city, quote)] for stores with the part available for pickup."""
    pickup = (data.get("body") or {}).get("PickupMessage") or {}
    stores = []
    for store in pickup.get("stores") or []:
        info = (store.get("partsAvailability") or {}).get(part) or {}
        if info.get("pickupDisplay") == "available":
            quote = info.get("pickupSearchQuote") or info.get("storePickupQuote") or ""
            stores.append((store.get("storeName", "?"), store.get("city", ""), strip_html(quote)))
    return stores


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()


def notify(title, message, ntfy_topic=None):
    print(f"\a*** {title}: {message}", flush=True)
    if ntfy_topic:
        try:
            req = urllib.request.Request(
                f"https://ntfy.sh/{ntfy_topic}",
                data=message.encode("utf-8"),
                headers={"Title": title, "Priority": "high", "Click": PRODUCT_URL},
            )
            urllib.request.urlopen(req, timeout=15).close()
        except Exception as e:  # never let a notification failure stop the loop
            log(f"ntfy notification failed: {e}")
    try:
        system = platform.system()
        if system == "Darwin":
            script = f"display notification {json.dumps(message)} with title {json.dumps(title)} sound name \"Glass\""
            subprocess.run(["osascript", "-e", script], check=False)
        elif system == "Linux":
            subprocess.run(["notify-send", title, message], check=False)
    except FileNotFoundError:
        pass


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def check_once(args, state):
    try:
        data = fetch_pickup(args.zip)
    except BlockedError as e:
        log(f"Apple blocked the request ({e}).")
        return
    except Exception as e:
        log(f"Request failed: {e}")
        return

    stores = parse_pickup(data)[: args.max_stores]
    if stores:
        lines = [f"{name} ({city}) {quote}".strip() for name, city, quote in stores]
        log("IN STOCK for pickup: " + "; ".join(lines))
        names = tuple(s[0] for s in stores)
        if names != state.get("stores"):
            notify(f"{PRODUCT_NAME} in stock!", "Pickup at: " + ", ".join(names), args.ntfy)
        state["stores"] = names
    else:
        log(f"No pickup availability near {args.zip}.")
        state["stores"] = ()


def main(argv=None):
    p = argparse.ArgumentParser(description=f"Apple Store stock checker for {PRODUCT_NAME} ({PART_NUMBER}).")
    p.add_argument("--zip", default=os.environ.get("STOCK_ZIP"), help="US ZIP code to search nearby stores (or STOCK_ZIP env)")
    p.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="seconds between checks (default 300)")
    p.add_argument("--ntfy", default=os.environ.get("NTFY_TOPIC"), help="ntfy.sh topic for phone push notifications (or NTFY_TOPIC env)")
    p.add_argument("--max-stores", type=int, default=12, help="max nearby stores to report")
    p.add_argument("--once", action="store_true", help="check once and exit (for cron)")
    args = p.parse_args(argv)
    if not args.zip:
        p.error("--zip is required (or set STOCK_ZIP)")

    log(f"Watching {PRODUCT_NAME} ({PART_NUMBER}) near {args.zip}"
        + ("" if args.once else f", every {args.interval}s"))
    state = {}
    while True:
        check_once(args, state)
        if args.once:
            return 0
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main())
