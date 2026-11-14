#!/usr/bin/env python3
"""Self-check: probe each source URL and append the result to data/source_check.jsonl.

Status per source: "ok" (HTTP 2xx/3xx), "待核实" (404 / other HTTP error), or
"blocked" (could not connect at all, e.g. network policy denial).
"""
import json, sys, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

SOURCES = {
    "Frávega": "https://www.fravega.com/l/celulares/celulares-liberados/",
    "OnCity": "https://www.oncity.com/",
    "Personal": "https://www.personal.com.ar/tienda/celulares",
    "Claro": "https://tienda.claro.com.ar/",
}
ART = timezone(timedelta(hours=-3))
OUT = Path(__file__).resolve().parent.parent / "data" / "source_check.jsonl"


def probe(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (price-dashboard)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return "ok", r.status, ""
    except urllib.error.HTTPError as e:
        return "待核实", e.code, str(e.reason)
    except Exception as e:  # DNS / proxy / TLS / timeout
        return "blocked", None, f"{type(e).__name__}: {e}"[:200]


def main():
    now = datetime.now(ART)
    rows = []
    for ch, url in SOURCES.items():
        status, code, detail = probe(url)
        rows.append({"ts": now.isoformat(timespec="seconds"), "date": now.date().isoformat(),
                     "channel": ch, "url": url, "status": status, "http": code, "detail": detail})
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for r in rows:
        print(f"{r['channel']:9} {r['status']:8} {r['http']} {r['detail']}")
    return 0 if all(r["status"] == "ok" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
