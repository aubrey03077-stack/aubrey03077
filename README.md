# Argentina GTM Price Dashboard

Automated daily pipeline that scrapes phone prices (Xiaomi, Samsung, Motorola, Honor) from Argentina's
main KA and carrier channels, tracks day-over-day price changes, and publishes an interactive HTML
price dashboard.

## Status: BLOCKED — network egress denied to all four target domains

Re-checked 2026-10-13: still denied (curl → proxy CONNECT 403 on all four hosts; WebFetch → DNS
resolution failure). No prices scraped and no dashboard published for this date.

This session's outbound network policy rejects connections to every source required by the task:

| Channel  | URL                                                        | Result |
|----------|-------------------------------------------------------------|--------|
| Frávega  | https://www.fravega.com/l/celulares/celulares-liberados/    | `EGRESS_BLOCKED` (proxy CONNECT → 403) |
| OnCity   | https://www.oncity.com/                                     | `EGRESS_BLOCKED` (proxy CONNECT → 403) |
| Personal | https://www.personal.com.ar/tienda/celulares                | fetch failed / CONNECT → 403 |
| Claro    | https://tienda.claro.com.ar/                                 | `EGRESS_BLOCKED` (proxy CONNECT → 403) |

Both raw `curl` (through the environment's agent proxy) and the `WebFetch` tool were tried against
all four domains; all four are denied by organization network policy (`agentproxy` status shows
`connect_rejected` / "policy denial" for each host). No data could be retrieved, so **no scraped
price data or dashboard has been generated for this run** — publishing a dashboard with fabricated
numbers would be worse than publishing nothing.

### What needs to change for this task to run

One of the following, granted by whoever administers this environment's network policy:
1. Add `www.fravega.com`, `www.oncity.com`, `www.personal.com.ar`, and `tienda.claro.com.ar`
   (plus any CDN/API subdomains they redirect to) to the outbound allowlist, or
2. Run the scraping step somewhere with broader/allowlisted egress (e.g. a different environment
   or a scraping proxy service already permitted here) and hand the resulting JSON to this repo.

### Planned pipeline (ready to build once access is available)

- `scripts/scrape_<channel>.py` — one scraper per channel, extracting model, RAM/ROM, cash price
  (`Precio al contado`, ARS), and 1P vs. 3P seller tag.
- `data/price_history.jsonl` — one append-only record per product per day, the source of truth for
  trend charts and day-over-day (>10%) change detection.
- `scripts/build_dashboard.py` — **built** (stdlib only, tested). Reads `data/price_history.jsonl` and
  renders a self-contained `dashboard.html` with the three modules: cross-channel comparison (lowest
  price per SKU highlighted, 1P/3P tag), per-SKU price trend chart, and competitive landscape &
  alerts (day-over-day moves >10%, competitor SKUs within ±10% of each Xiaomi SKU per channel).
  Run: `python3 scripts/build_dashboard.py`. Tests: `python3 -m unittest discover -s tests`.

History record schema (one JSON object per line), which the scrapers must emit:

```json
{"date": "2026-10-13", "channel": "Fravega", "brand": "Xiaomi", "model": "Redmi Note 14",
 "ram_gb": 8, "rom_gb": 256, "price_ars": 499999, "seller": "1P", "url": "https://..."}
```

These weren't scaffolded with guessed CSS selectors in this run, since none of the four sites could
actually be loaded to verify page structure — writing scrapers blind against unseen markup would
just create broken code that looks done. They'll be written against real page structure as soon as
egress is unblocked.
