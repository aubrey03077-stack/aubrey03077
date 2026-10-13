"""Tests for scripts/build_dashboard.py. Prices here are synthetic fixtures, not market data."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_dashboard as bd  # noqa: E402


def rec(date, channel, brand, model, price, seller="1P"):
    return {"date": date, "channel": channel, "brand": brand, "model": model,
            "ram_gb": 8, "rom_gb": 256, "price_ars": price, "seller": seller}


FIXTURE = [
    rec("2026-01-01", "A", "Xiaomi", "X1", 100000),
    rec("2026-01-02", "A", "Xiaomi", "X1", 85000),   # -15% -> alert
    rec("2026-01-02", "B", "Xiaomi", "X1", 90000),
    rec("2026-01-01", "A", "Samsung", "S1", 95000),
    rec("2026-01-02", "A", "Samsung", "S1", 90000),  # -5.3% -> no alert; within band of X1 on A
    rec("2026-01-02", "A", "Motorola", "M1", 200000),  # outside band
]


class BuildDashboardTest(unittest.TestCase):
    def test_latest_snapshot(self):
        latest, snap = bd.latest_snapshot(FIXTURE)
        self.assertEqual(latest, "2026-01-02")
        self.assertEqual(set(snap["Xiaomi X1 8+256GB"]), {"A", "B"})

    def test_alerts_only_above_threshold(self):
        alerts = bd.day_over_day_alerts(FIXTURE)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["sku"], "Xiaomi X1 8+256GB")
        self.assertAlmostEqual(alerts[0]["change"], -0.15)

    def test_price_match_watch(self):
        _, snap = bd.latest_snapshot(FIXTURE)
        watch = bd.price_match_watch(snap)
        self.assertEqual(len(watch), 1)
        self.assertEqual(watch[0]["channel"], "A")
        self.assertEqual([r["model"] for r in watch[0]["rivals"]], ["S1"])

    def test_end_to_end_and_empty(self):
        with tempfile.TemporaryDirectory() as d:
            hist, out = Path(d) / "h.jsonl", Path(d) / "o.html"
            hist.write_text("\n".join(json.dumps(r) for r in FIXTURE))
            bd.main(["--history", str(hist), "--out", str(out)])
            page = out.read_text()
            self.assertIn("Latest data: 2026-01-02", page)
            self.assertIn("-15.0%", page)
            bd.main(["--history", str(Path(d) / "missing.jsonl"), "--out", str(out)])
            self.assertIn("Waiting for first scrape", out.read_text())

    def test_missing_field_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            hist = Path(d) / "h.jsonl"
            hist.write_text(json.dumps({"date": "2026-01-01"}))
            with self.assertRaises(ValueError):
                bd.load_history(hist)


if __name__ == "__main__":
    unittest.main()
