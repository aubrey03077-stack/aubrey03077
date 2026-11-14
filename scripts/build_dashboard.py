#!/usr/bin/env python3
"""Render dashboard.html from data/price_history.jsonl + data/source_check.jsonl.

price_history.jsonl — one JSON object per product listing per day:
  {"date": "2026-11-13", "brand": "Samsung", "model": "Galaxy A56 5G", "ram": "8GB", "rom": "256GB",
   "tier": "Mid-to-High",            # Entry-level | Mid-to-High | Flagship
   "channel": "Frávega",             # Frávega | OnCity | Personal | Claro
   "seller_type": "1P",              # 1P (platform-owned) | 3P (marketplace seller)
   "seller": "Frávega",
   "cash_price": 899999,             # Precio al contado, ARS
   "installments": {"n": 12, "amount": 99999, "total": 1199988, "interest_free": true} | null,
   "url": "https://...", "status": "ok"}   # status "待核实" when the product link is dead

Usage: build_dashboard.py [--history PATH] [--checks PATH] [--out PATH]
"""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_jsonl(p):
    p = Path(p)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=ROOT / "data" / "price_history.jsonl")
    ap.add_argument("--checks", default=ROOT / "data" / "source_check.jsonl")
    ap.add_argument("--out", default=ROOT / "dashboard.html")
    a = ap.parse_args()
    history = load_jsonl(a.history)
    checks = load_jsonl(a.checks)
    if checks:  # keep only the latest check per channel
        last = max(c["date"] for c in checks)
        checks = [c for c in checks if c["date"] == last]
        checks = list({c["channel"]: c for c in checks}.values())
    payload = json.dumps({"history": history, "checks": checks}, ensure_ascii=False).replace("</", "<\\/")
    html = (ROOT / "scripts" / "dashboard_template.html").read_text(encoding="utf-8")
    Path(a.out).write_text(html.replace("/*__DATA__*/null", payload), encoding="utf-8")
    print(f"wrote {a.out}: {len(history)} price rows, {len(checks)} source checks")


if __name__ == "__main__":
    main()
