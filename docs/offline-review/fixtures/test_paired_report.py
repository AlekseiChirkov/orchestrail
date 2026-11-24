"""Contract checks for a paired decision from frozen synthetic review evidence."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


BUILD_REPORT = Path(__file__).with_name("paired_report.py")
PACKET = "a" * 64
SETTINGS = "b" * 64


def observation(case, variant, cost, seconds, *, status="completed"):
    return {
        "case_id": case,
        "packet_digest": PACKET,
        "variant": variant,
        "attempt_id": f"{case}-{variant}",
        "status": status,
        "elapsed_seconds": seconds,
        "settled_cost": cost,
        "reason": None if status == "completed" else "No verified termination.",
        "report_digest": ("c" if variant == "baseline" else "d") * 64,
    }


def verdict(finding, outcome, canonical, *, severity="major"):
    return {
        "finding_id": finding,
        "verdict": outcome,
        "canonical_id": canonical,
        "severity": severity,
        "rationale": "Checked against the pinned composition.",
    }


def fixture():
    case = {
        "case_id": "paired",
        "packet_digest": PACKET,
        "contaminated": False,
        "observations": {
            "baseline": observation("paired", "baseline", "2", 10),
            "treatment": observation("paired", "treatment", "6", 30),
        },
        "finding_variants": {"f0": "baseline", "f1": "treatment", "f2": "treatment", "f3": "treatment"},
        "adjudication": {
            "status": "complete",
            "frozen_at": 45,
            "verdicts": [
                verdict("f0", "confirmed", "shared"),
                verdict("f1", "confirmed", "shared"),
                verdict("f2", "confirmed", "omission"),
                verdict("f3", "refuted", "false-claim"),
            ],
            "pending_claims": [],
        },
        "coverage_gaps": ["criterion rendering could not be observed"],
    }
    timed_out = {
        "case_id": "slow",
        "packet_digest": PACKET,
        "contaminated": False,
        "observations": {
            "baseline": observation("slow", "baseline", None, 50, status="timed out"),
            "treatment": observation("slow", "treatment", "0", 1),
        },
        "finding_variants": {},
        "adjudication": {"status": "incomplete", "frozen_at": 50, "verdicts": [], "pending_claims": []},
        "coverage_gaps": [],
    }
    return {
        "settings": {
            "digest": SETTINGS,
            "cutoff_seconds": 50,
            "minimum_pairs": 1,
            "minimum_incremental_defects": 1,
            "maximum_incremental_false": 1,
            "maximum_incremental_seconds": 20,
            "maximum_incremental_cost": "4",
            "consequential_severities": ["major", "critical"],
        },
        "cases": [case, timed_out],
        "cohort_contaminated": False,
        "common_cost": "3",
        "retry_cost": "0",
        "unresolved_reservations": ["2"],
    }


class PairedReportTests(unittest.TestCase):
    def evaluate(self, snapshot):
        self.assertTrue(BUILD_REPORT.is_file(), "Offline paired report procedure is unavailable")
        result = subprocess.run(
            [sys.executable, "-IB", str(BUILD_REPORT)],
            input=json.dumps(snapshot),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_equality_yields_trial_and_exposes_all_spend_separately(self):
        report = self.evaluate(fixture())

        self.assertEqual(report["recommendation"], "trial")
        self.assertEqual(report["settings_digest"], SETTINGS)
        self.assertEqual(report["enrolled_cases"], 2)
        self.assertEqual(report["eligible_pairs"], 1)
        self.assertEqual(report["deltas"], {
            "confirmed_defects": 1, "false_findings": 1, "elapsed_seconds": 20, "settled_cost": "4",
        })
        self.assertEqual(report["spend_exposure"], "13")
        self.assertEqual(report["exclusive_confirmed"], {"baseline": 0, "treatment": 1})
        self.assertEqual(report["pairs"]["slow"]["observations"]["baseline"]["status"], "timed out")
        self.assertEqual(report["pairs"]["paired"]["coverage_gaps"], ["criterion rendering could not be observed"])

    def test_each_independent_threshold_breach_yields_no_trial(self):
        scenarios = ("defects", "false", "time", "cost")
        for metric in scenarios:
            with self.subTest(metric=metric):
                snapshot = fixture()
                case = snapshot["cases"][0]
                if metric == "defects":
                    case["adjudication"]["verdicts"][2]["canonical_id"] = "shared"
                elif metric == "false":
                    case["finding_variants"]["f4"] = "treatment"
                    case["adjudication"]["verdicts"].append(verdict("f4", "refuted", "second-false"))
                elif metric == "time":
                    case["observations"]["treatment"]["elapsed_seconds"] = 31
                else:
                    case["observations"]["treatment"]["settled_cost"] = "6.01"

                report = self.evaluate(snapshot)

                self.assertEqual(report["recommendation"], "no trial")
                self.assertEqual(report["eligible_pairs"], 1)

    def test_deduplicates_same_canonical_claim_per_arm_and_reports_unresolved(self):
        snapshot = fixture()
        case = snapshot["cases"][0]
        case["finding_variants"].update({"f4": "treatment", "f5": "treatment", "f6": "baseline"})
        case["adjudication"]["verdicts"].extend([
            verdict("f4", "confirmed", "omission"),
            verdict("f5", "refuted", "false-claim"),
            verdict("f6", "unresolved", None),
        ])

        report = self.evaluate(snapshot)

        self.assertEqual(report["recommendation"], "trial")
        self.assertEqual(report["deltas"]["confirmed_defects"], 1)
        self.assertEqual(report["deltas"]["false_findings"], 1)
        self.assertEqual(report["per_variant"]["baseline"]["unresolved_findings"], 1)
        self.assertEqual(report["pairs"]["paired"]["unresolved_findings"], ["f6"])

    def test_insufficient_evidence_preserves_case_records_and_pending_claims(self):
        for gap in ("case-contamination", "cohort-contamination", "missing-cost", "unfinished"):
            with self.subTest(gap=gap):
                snapshot = fixture()
                case = snapshot["cases"][0]
                if gap == "case-contamination":
                    case["contaminated"] = True
                elif gap == "cohort-contamination":
                    snapshot["cohort_contaminated"] = True
                elif gap == "missing-cost":
                    case["observations"]["treatment"]["settled_cost"] = None
                else:
                    case["adjudication"]["status"] = "incomplete"
                    case["adjudication"]["verdicts"].pop()
                    case["adjudication"]["pending_claims"] = [
                        {"finding_id": "f3", "reason": "Adjudication unfinished at cutoff."},
                    ]

                report = self.evaluate(snapshot)

                self.assertEqual(report["recommendation"], "insufficient evidence")
                pair = report["pairs"]["paired"]
                self.assertEqual(pair["observations"], case["observations"])
                if gap == "unfinished":
                    self.assertEqual(report["eligible_pairs"], 0)
                    self.assertEqual(report["spend_exposure"], "13")
                    self.assertEqual(pair["pending_claims"], case["adjudication"]["pending_claims"])

    def test_frozen_composition_and_complete_adjudication_are_required(self):
        for gap in ("packet-mismatch", "absent-first-report", "late-verdicts", "missing-verdict"):
            with self.subTest(gap=gap):
                snapshot = fixture()
                case = snapshot["cases"][0]
                if gap == "packet-mismatch":
                    case["observations"]["treatment"]["packet_digest"] = "f" * 64
                elif gap == "absent-first-report":
                    case["observations"]["treatment"]["report_digest"] = None
                elif gap == "late-verdicts":
                    case["adjudication"]["frozen_at"] = 51
                else:
                    case["adjudication"]["verdicts"].pop()

                report = self.evaluate(snapshot)

                self.assertEqual(report["recommendation"], "insufficient evidence")
                self.assertEqual(report["eligible_pairs"], 0)
                self.assertTrue(report["pairs"]["paired"]["reasons"])


if __name__ == "__main__":
    unittest.main()
