"""Offline end-to-end contract tests for the complete sitemap review pipeline.

All fixtures use synthetic example.com URLs; no network or real-site data.
"""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def sitemap(entries):
    body = "".join(
        f"<url><loc>https://example.com/{slug}</loc><lastmod>{date}</lastmod></url>"
        for slug, date in entries
    )
    return f'<urlset xmlns="{NS}">{body}</urlset>'


class PipelineContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def run_cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(TOOLS / script), *map(str, args)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def snapshots(self):
        for label, entries in (
            ("before", [("a", "2026-10-01"), ("b", "2026-10-01")]),
            ("after", [("b", "2026-10-02"), ("c", "2026-10-02")]),
        ):
            folder = self.root / label
            folder.mkdir()
            (folder / "sitemap.xml").write_text(sitemap(entries), encoding="utf-8")
            result = self.run_cli(
                "seo_sitemap_audit.py", "--root", folder,
                "--base-url", "https://example.com/", "--as-of", "2026-10-24",
                "--urls-csv", self.root / f"{label}.csv",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["csv_export"]["rows"], 2)
            (self.root / f"{label}.json").write_text(result.stdout, encoding="utf-8")

    def compare(self):
        return self.run_cli(
            "seo_sitemap_compare.py",
            "--before", self.root / "before.csv",
            "--before-report", self.root / "before.json",
            "--after", self.root / "after.csv",
            "--after-report", self.root / "after.json",
        )

    def test_complete_pipeline_keeps_evidence_and_ranking_contract(self):
        self.snapshots()
        comparison = self.compare()
        self.assertEqual(comparison.returncode, 1, comparison.stderr)
        diff = json.loads(comparison.stdout)
        self.assertEqual(diff["summary"]["added_urls"], 1)
        self.assertEqual(diff["summary"]["removed_urls"], 1)
        self.assertEqual(diff["summary"]["changed_existing_urls"], 1)
        self.assertEqual(
            diff["verification"]["status"], "complete_audit_csv_sha256_checked"
        )
        diff_path = self.root / "diff.json"
        diff_path.write_text(comparison.stdout, encoding="utf-8")

        triage = self.run_cli("seo_sitemap_triage.py", "--diff", diff_path)
        self.assertEqual(triage.returncode, 0, triage.stderr)
        rows = list(csv.DictReader(io.StringIO(triage.stdout)))
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            [(row["priority"], row["change"], row["url"].rsplit("/", 1)[-1])
             for row in rows],
            [("P1", "removed", "a"), ("P3", "added", "c"),
             ("P3", "changed", "b")],
        )
        self.assertEqual({row["evidence"] for row in rows}, {"local_csv_sha_checked"})
        queue_path = self.root / "queue.csv"
        queue_path.write_text(triage.stdout, encoding="utf-8")

        labels_path = self.root / "labels.csv"
        with labels_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["url", "review_worthy", "severity"])
            writer.writerows([
                ["https://example.com/a", "yes", "high"],
                ["https://example.com/b", "no", "normal"],
                ["https://example.com/c", "yes", "normal"],
            ])
        scored = self.run_cli(
            "seo_sitemap_budget_eval.py", "--queue", queue_path,
            "--labels", labels_path, "--budget", "1",
        )
        self.assertEqual(scored.returncode, 0, scored.stderr)
        result = json.loads(scored.stdout)
        self.assertEqual(result["evidence"], "local_csv_sha_checked")
        self.assertEqual(result["priority_queue"]["true_positives"], 1)
        self.assertEqual(result["priority_queue"]["high_impact_misses"], 0)
        self.assertEqual(result["priority_queue"]["recall_at_budget"], 0.5)
        self.assertEqual(result["total_changed_urls"], 3)

    def test_tampered_export_fails_before_triage(self):
        self.snapshots()
        before = self.root / "before.csv"
        original = before.read_text(encoding="utf-8")
        self.assertIn("https://example.com/a", original)
        before.write_text(
            original.replace("https://example.com/a", "https://example.com/z"),
            encoding="utf-8",
        )
        comparison = self.compare()
        self.assertEqual(comparison.returncode, 2)
        self.assertEqual(comparison.stdout, "")
        self.assertIn("SHA-256", comparison.stderr)


if __name__ == "__main__":
    unittest.main()
