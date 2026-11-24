"""Regression checks for unresolved canonical severity in offline decisions."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from test_paired_report import fixture, verdict


BUILD_REPORT = Path(__file__).with_name("paired_report.py")


class AdjudicationConsistencyTests(unittest.TestCase):
    def test_conflicting_severity_cannot_make_a_shared_defect_incremental(self):
        snapshot = fixture()
        case = snapshot["cases"][0]
        case["finding_variants"].pop("f2")
        case["adjudication"]["verdicts"] = [
            verdict("f0", "confirmed", "shared", severity="minor"),
            verdict("f1", "confirmed", "shared", severity="major"),
            verdict("f3", "refuted", "false-claim"),
        ]

        result = subprocess.run(
            [sys.executable, "-IB", str(BUILD_REPORT)],
            input=json.dumps(snapshot),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["recommendation"], "insufficient evidence")
        self.assertEqual(report["eligible_pairs"], 0)
        self.assertEqual(report["spend_exposure"], "13")
        pair = report["pairs"]["paired"]
        self.assertIn("adjudication-severity-conflict", pair["reasons"])
        self.assertEqual(pair["observations"], case["observations"])
        self.assertEqual(pair["conflicting_severity_ids"], ["shared"])


if __name__ == "__main__":
    unittest.main()
