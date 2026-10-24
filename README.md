# StockChecker

Checks Apple's US online store every 5 minutes for **iPhone Duo / Night Sky / 512GB**
(part `MK1H4LL/A`). It reports in-store pickup availability near a ZIP code and the
online delivery estimate, for example "Ships Mon, Jan 25". It alerts you when a nearby
store gets stock or the delivery estimate changes. Apple gives one nationwide delivery
estimate, so the ZIP code only affects the pickup check.

Requires Python 3.8+. No dependencies.

## Usage

```sh
python3 stockchecker.py --zip 94103
```

It checks immediately, then every 5 minutes, until you stop it with Ctrl+C.

| Option | Default | Description |
| --- | --- | --- |
| `--zip` / `STOCK_ZIP` | required | ZIP code used to find nearby Apple Stores |
| `--interval` | `300` | Seconds between checks |
| `--ntfy` / `NTFY_TOPIC` | none | [ntfy.sh](https://ntfy.sh) topic for phone push alerts |
| `--once` | off | Check once and exit, for running from cron |

Alerts are always printed to the terminal. They also appear as desktop notifications on
macOS (`osascript`) and Linux (`notify-send`). For phone alerts, install the ntfy app,
subscribe to a hard-to-guess topic name, and pass it with `--ntfy`.

### Running from cron instead

```cron
*/5 * * * * STOCK_ZIP=94103 NTFY_TOPIC=my-secret-topic /usr/bin/python3 /path/to/stockchecker.py --once >> /tmp/stockchecker.log 2>&1
```

In `--once` mode each run starts fresh, so only pickup alerts fire. Delivery-change
alerts need the long-running mode.

## How it gets the data

Apple's combined `/shop/fulfillment-messages` endpoint now rejects requests that don't
come from its own web page (HTTP 541). So the checker calls two other endpoints the store
uses, `/shop/pickup-message-recommendations` and `/shop/delivery-message`. If Apple blocks
these too, the checker logs `Apple blocked the ... request` and keeps going.

## Tests

```sh
python3 -m unittest
```
