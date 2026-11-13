"""Testes unitários para agregação de métricas e geração de relatórios de carga."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from load_tests.metrics import RequestRecord, SLAConfig, percentile, summarize_results
from load_tests.report import render_html_report, render_markdown_report, write_reports


class LoadSuiteUnitTests(unittest.TestCase):
    def test_percentile_interpolation(self) -> None:
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        self.assertEqual(percentile(values, 50), 30.0)
        self.assertEqual(percentile(values, 0), 10.0)
        self.assertEqual(percentile(values, 100), 50.0)
        self.assertAlmostEqual(percentile(values, 95), 48.0)

    def test_summarize_and_reports(self) -> None:
        start = 100.0
        records = [
            RequestRecord("/dashboard/", "GET", 200, 120.0, 4096, True, start + 0.5),
            RequestRecord("/dashboard/", "GET", 200, 180.0, 4096, True, start + 1.5),
            RequestRecord("/api/notebook/save/", "POST", 200, 250.0, 128, True, start + 2.5),
            RequestRecord("/api/notebook/save/", "POST", 500, 900.0, 64, False, start + 3.5, "database is locked"),
        ]
        summary = summarize_results(
            records=records,
            start_time=start,
            end_time=start + 4.1,
            metadata={
                "executed_at": "12/11/2026 19:45:00",
                "mode": "standalone",
                "target_url": "http://127.0.0.1:8000",
                "database_engine": "sqlite3",
                "debug_toolbar_enabled": False,
                "users": 4,
                "duration_seconds": 4,
                "ramp_up_seconds": 1,
                "think_time_range": "0.1-0.3s",
            },
            sla=SLAConfig(max_error_rate_pct=5.0, max_p95_ms=800.0, max_p99_ms=1000.0),
        )

        self.assertEqual(summary["global"]["total_requests"], 4)
        self.assertEqual(summary["global"]["failures"], 1)
        self.assertFalse(summary["sla"]["passed"])  # 25% error rate > 5%
        self.assertTrue(any("SQLite" in d for d in summary["diagnostics"]))

        md = render_markdown_report(summary)
        self.assertIn("# Relatório de Teste de Carga — TaskFlow", md)
        self.assertIn("`GET` | `/dashboard/`", md)

        html_out = render_html_report(summary)
        self.assertIn("Relatório de Teste de Carga — TaskFlow", html_out)
        self.assertIn("<svg", html_out)

        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reports(summary, Path(tmp), "testrun")
            for p in paths.values():
                self.assertTrue(p.exists())


if __name__ == "__main__":
    unittest.main()
