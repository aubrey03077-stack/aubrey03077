#!/usr/bin/env python3
"""Render dashboard.html from data/price_history.jsonl.

Each line of the history file is one product observed on one channel on one day:

    {"date": "2026-10-13", "channel": "Fravega", "brand": "Xiaomi",
     "model": "Redmi Note 14", "ram_gb": 8, "rom_gb": 256,
     "price_ars": 499999, "seller": "1P", "url": "https://..."}

The dashboard has three modules:
  1. Cross-channel comparison for the latest date (lowest price per SKU highlighted).
  2. Price history / trend per SKU.
  3. Competitive landscape & alerts: day-over-day moves above the threshold, and
     competitor SKUs priced within a band of each Xiaomi SKU (price-matching watch).

Stdlib only. Usage:
    python3 scripts/build_dashboard.py [--history PATH] [--out PATH]
"""

import argparse
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED = ("date", "channel", "brand", "model", "ram_gb", "rom_gb", "price_ars", "seller")
CHANGE_THRESHOLD = 0.10  # day-over-day move that raises an alert
MATCH_BAND = 0.10  # competitor within ±10% of a Xiaomi SKU counts as a price-match threat
HOME_BRAND = "Xiaomi"


def load_history(path):
    records = []
    if not path.exists():
        return records
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            missing = [k for k in REQUIRED if k not in rec]
            if missing:
                raise ValueError(f"{path}:{lineno}: missing fields {missing}")
            records.append(rec)
    return records


def sku_key(rec):
    return f"{rec['brand']} {rec['model']} {rec['ram_gb']}+{rec['rom_gb']}GB"


def fmt_ars(n):
    return "$" + f"{round(n):,}".replace(",", ".")


def latest_snapshot(records):
    """Return (latest_date, {sku: {channel: record}}) for the most recent date."""
    if not records:
        return None, {}
    latest = max(r["date"] for r in records)
    snap = defaultdict(dict)
    for r in records:
        if r["date"] == latest:
            snap[sku_key(r)][r["channel"]] = r
    return latest, snap


def day_over_day_alerts(records, threshold=CHANGE_THRESHOLD):
    """Moves larger than `threshold` between consecutive observations of a SKU on a channel."""
    series = defaultdict(list)
    for r in records:
        series[(sku_key(r), r["channel"])].append(r)
    alerts = []
    for (sku, channel), rows in series.items():
        rows.sort(key=lambda r: r["date"])
        for prev, cur in zip(rows, rows[1:]):
            if prev["price_ars"] <= 0:
                continue
            change = (cur["price_ars"] - prev["price_ars"]) / prev["price_ars"]
            if abs(change) > threshold:
                alerts.append({
                    "date": cur["date"], "sku": sku, "channel": channel,
                    "from": prev["price_ars"], "to": cur["price_ars"], "change": change,
                })
    alerts.sort(key=lambda a: (a["date"], abs(a["change"])), reverse=True)
    return alerts


def price_match_watch(snapshot, band=MATCH_BAND):
    """For each home-brand SKU on each channel, competitor SKUs on that channel within ±band."""
    by_channel = defaultdict(list)
    for channels in snapshot.values():
        for ch, r in channels.items():
            by_channel[ch].append(r)
    rows = []
    for ch, recs in by_channel.items():
        home = [r for r in recs if r["brand"] == HOME_BRAND]
        rivals = [r for r in recs if r["brand"] != HOME_BRAND]
        for h in home:
            close = [
                r for r in rivals
                if abs(r["price_ars"] - h["price_ars"]) <= band * h["price_ars"]
            ]
            if close:
                close.sort(key=lambda r: r["price_ars"])
                rows.append({"channel": ch, "home": h, "rivals": close})
    rows.sort(key=lambda x: (x["channel"], x["home"]["price_ars"]))
    return rows


def render(records):
    latest, snap = latest_snapshot(records)
    channels = sorted({r["channel"] for r in records})
    alerts = day_over_day_alerts(records)
    watch = price_match_watch(snap)
    e = html.escape

    # Module 1: cross-channel comparison
    if snap:
        head = "".join(f"<th>{e(c)}</th>" for c in channels)
        body = []
        for sku in sorted(snap):
            row = snap[sku]
            low = min(r["price_ars"] for r in row.values())
            cells = []
            for c in channels:
                r = row.get(c)
                if not r:
                    cells.append('<td class="na">—</td>')
                    continue
                cls = "low" if r["price_ars"] == low and len(row) > 1 else ""
                cells.append(
                    f'<td class="num {cls}">{fmt_ars(r["price_ars"])}'
                    f'<span class="tag">{e(r["seller"])}</span></td>'
                )
            body.append(f"<tr><th scope=row>{e(sku)}</th>{''.join(cells)}</tr>")
        compare = (
            f'<div class="scroll"><table><thead><tr><th>SKU</th>{head}</tr></thead>'
            f"<tbody>{''.join(body)}</tbody></table></div>"
        )
    else:
        compare = '<p class="empty">No price data yet.</p>'

    # Module 3a: day-over-day alerts
    if alerts:
        items = "".join(
            f'<tr><td>{e(a["date"])}</td><td>{e(a["sku"])}</td><td>{e(a["channel"])}</td>'
            f'<td class="num">{fmt_ars(a["from"])}</td><td class="num">{fmt_ars(a["to"])}</td>'
            f'<td class="num {"down" if a["change"] < 0 else "up"}">{a["change"]:+.1%}</td></tr>'
            for a in alerts
        )
        alert_html = (
            '<div class="scroll"><table><thead><tr><th>Date</th><th>SKU</th><th>Channel</th>'
            '<th>From</th><th>To</th><th>Change</th></tr></thead>'
            f"<tbody>{items}</tbody></table></div>"
        )
    else:
        alert_html = f'<p class="empty">No moves above {CHANGE_THRESHOLD:.0%}.</p>'

    # Module 3b: price-match watch
    if watch:
        items = "".join(
            f'<tr><td>{e(w["channel"])}</td><td>{e(sku_key(w["home"]))}<br>'
            f'<span class="sub">{fmt_ars(w["home"]["price_ars"])}</span></td><td>'
            + "<br>".join(
                f'{e(sku_key(r))} <span class="sub">{fmt_ars(r["price_ars"])} '
                f'({(r["price_ars"] - w["home"]["price_ars"]) / w["home"]["price_ars"]:+.1%})</span>'
                for r in w["rivals"]
            )
            + "</td></tr>"
            for w in watch
        )
        watch_html = (
            f'<div class="scroll"><table><thead><tr><th>Channel</th><th>{HOME_BRAND} SKU</th>'
            f"<th>Competitors within ±{MATCH_BAND:.0%}</th></tr></thead>"
            f"<tbody>{items}</tbody></table></div>"
        )
    else:
        watch_html = '<p class="empty">No competitor SKUs in range.</p>'

    # Module 2: trend data, rendered client-side as inline SVG
    trend = defaultdict(lambda: defaultdict(list))
    for r in sorted(records, key=lambda r: r["date"]):
        trend[sku_key(r)][r["channel"]].append([r["date"], r["price_ars"]])
    trend_json = json.dumps(trend, ensure_ascii=False).replace("</", "<\\/")

    subtitle = f"Latest data: {e(latest)}" if latest else "Waiting for first scrape"
    return TEMPLATE.format(
        subtitle=subtitle, compare=compare, alerts=alert_html,
        watch=watch_html, trend_json=trend_json,
        threshold=f"{CHANGE_THRESHOLD:.0%}",
    )


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AR Price Dashboard</title>
<style>
:root{{--bg:#fafaf9;--fg:#1c1917;--mut:#78716c;--line:#e7e5e4;--card:#fff;--low:#dcfce7;--up:#b91c1c;--down:#15803d;
--s1:#2563eb;--s2:#d97706;--s3:#7c3aed;--s4:#0d9488}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#0c0a09;--fg:#f5f5f4;--mut:#a8a29e;--line:#292524;--card:#1c1917;--low:#14532d;--up:#f87171;--down:#4ade80;
--s1:#60a5fa;--s2:#fbbf24;--s3:#a78bfa;--s4:#2dd4bf}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px}}
h1{{font-size:22px;margin:0}} h2{{font-size:16px;margin:0 0 12px}}
.subtitle,.sub,.na,.empty{{color:var(--mut)}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-top:16px}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.low{{background:var(--low)}} .up{{color:var(--up)}} .down{{color:var(--down)}}
.tag{{font-size:11px;color:var(--mut);margin-left:6px}}
select{{font:inherit;padding:4px;max-width:100%}} svg{{width:100%;height:auto;display:block}}
.legend span{{margin-right:14px}} .legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px}}
</style></head><body><main>
<h1>Argentina Phone Price Dashboard</h1>
<div class="subtitle">{subtitle} · Cash price (ARS), 1P/3P seller tag</div>
<section><h2>1 · Cross-channel comparison</h2>{compare}</section>
<section><h2>2 · Price trend</h2><div id="trend"></div></section>
<section><h2>3 · Competitive landscape &amp; alerts</h2>
<h3>Day-over-day moves &gt; {threshold}</h3>{alerts}
<h3>Price-match watch</h3>{watch}</section>
</main>
<script>
const DATA={trend_json};
const box=document.getElementById('trend');const skus=Object.keys(DATA).sort();
if(!skus.length){{box.innerHTML='<p class="empty">No history yet.</p>'}}else{{
const sel=document.createElement('select');skus.forEach(s=>sel.add(new Option(s,s)));
const chart=document.createElement('div');box.append(sel,chart);
const colors=['--s1','--s2','--s3','--s4'];
const fmt=n=>'$'+Math.round(n).toLocaleString('es-AR');
function draw(){{const series=DATA[sel.value];const chs=Object.keys(series).sort();
const pts=chs.flatMap(c=>series[c]);const dates=[...new Set(pts.map(p=>p[0]))].sort();
const vals=pts.map(p=>p[1]);let lo=Math.min(...vals),hi=Math.max(...vals);if(lo===hi){{lo*=.95;hi*=1.05}}
const W=800,H=280,L=90,R=16,T=12,B=30;
const x=d=>dates.length<2?(L+W-R)/2:L+(W-L-R)*dates.indexOf(d)/(dates.length-1);
const y=v=>T+(H-T-B)*(1-(v-lo)/(hi-lo));
let s=`<svg viewBox="0 0 ${{W}} ${{H}}" role="img">`;
for(let i=0;i<=4;i++){{const v=lo+(hi-lo)*i/4;s+=`<line x1="${{L}}" x2="${{W-R}}" y1="${{y(v)}}" y2="${{y(v)}}" stroke="var(--line)"/><text x="${{L-6}}" y="${{y(v)+4}}" text-anchor="end" font-size="11" fill="var(--mut)">${{fmt(v)}}</text>`}}
[...new Set([dates[0],dates[dates.length-1]])].forEach((d,i)=>{{s+=`<text x="${{x(d)}}" y="${{H-8}}" text-anchor="${{i?'end':'start'}}" font-size="11" fill="var(--mut)">${{d}}</text>`}});
chs.forEach((c,i)=>{{const col=`var(${{colors[i%4]}})`;const p=series[c];
s+=`<polyline fill="none" stroke="${{col}}" stroke-width="2" points="${{p.map(q=>x(q[0])+','+y(q[1])).join(' ')}}"/>`;
p.forEach(q=>{{s+=`<circle cx="${{x(q[0])}}" cy="${{y(q[1])}}" r="3" fill="${{col}}"><title>${{c}} ${{q[0]}}: ${{fmt(q[1])}}</title></circle>`}})}});
chart.innerHTML=s+'</svg><div class="legend">'+chs.map((c,i)=>`<span><i style="background:var(${{colors[i%4]}})"></i>${{c}}</span>`).join('')+'</div>'}}
sel.onchange=draw;draw()}}
</script></body></html>
"""


def main(argv=None):
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--history", type=Path, default=root / "data" / "price_history.jsonl")
    ap.add_argument("--out", type=Path, default=root / "dashboard.html")
    args = ap.parse_args(argv)
    records = load_history(args.history)
    args.out.write_text(render(records), encoding="utf-8")
    print(f"Wrote {args.out} from {len(records)} records", file=sys.stderr)


if __name__ == "__main__":
    main()
