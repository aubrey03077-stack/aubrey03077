# Argentina GTM Price Dashboard

Automated daily pipeline that scrapes phone prices (Xiaomi, Samsung, Motorola, Honor) from Argentina's
main KA and carrier channels, tracks day-over-day price changes, and publishes an interactive HTML
price dashboard.

## Status: BLOCKED — network egress denied to all four target domains

**Run log:** 2026-11-12 blocked · 2026-11-13 blocked again (all four hosts: proxy CONNECT → 403; see `data/source_check.jsonl`).

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

### Pipeline

| Piece | State |
|-------|-------|
| `scripts/source_check.py` — probes the 4 source URLs, appends to `data/source_check.jsonl` (`ok` / `待核实` / `blocked`) | ✅ built, runs daily |
| `scripts/build_dashboard.py` + `scripts/dashboard_template.html` — renders `dashboard.html` from `data/price_history.jsonl` | ✅ built, verified in Chromium against a synthetic fixture (not committed) |
| `scripts/scrape_<channel>.py` — per-channel scrapers (model, RAM/ROM, cash price, 1P/3P, cuotas) | ⏳ blocked: they need the real page markup, and none of the sites can be loaded yet |

The record schema for `data/price_history.jsonl` is documented at the top of `scripts/build_dashboard.py`.
The dashboard has the self-check panel plus all three modules (cross-channel 1P/3P cash and installment comparison;
history line chart and table filtered by brand, channel and tier; per-tier landscape with cross-brand ±3% price matches,
>15% price gaps and >10% day-over-day alerts). Until scrapers land it shows only the self-check results
and empty states. It contains no made-up prices.

Daily run: `python3 scripts/source_check.py && python3 scripts/build_dashboard.py`
