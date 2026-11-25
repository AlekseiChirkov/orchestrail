"""Contract checks for exploratory historical comparison without formal gates."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from test_case_packets import admitted_source
from test_paired_report import fixture


FIXTURES = Path(__file__).parent


class HistoricalModeTests(unittest.TestCase):
    def run_helper(self, name, payload):
        result = subprocess.run(
            [sys.executable, "-IB", str(FIXTURES / name), "--historical"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_pin_source_backed_packet_without_approvals(self):
        source = admitted_source("milestone")
        del source["coordinator"]["approvals"]

        result = self.run_helper("prepare_case.py", source)

        self.assertEqual(result["status"], "admitted")
        self.assertEqual(result["packet"]["composition"], source["packet"]["composition"])
        self.assertEqual(len(set(result["variant_packet_digests"].values())), 1)

        source["packet"]["tested_tree"] = None
        result = self.run_helper("prepare_case.py", source)
        self.assertEqual(result["reason"], "incomplete-packet")

    def test_descriptive_report_keeps_unknown_measurements_visible(self):
        source = fixture()
        source["settings"] = {"consequential_severities": ["major", "critical"]}
        source.pop("unresolved_reservations")
        source["cases"][0]["observations"]["treatment"]["settled_cost"] = None
        source["cases"][0]["observations"]["treatment"]["elapsed_seconds"] = None

        result = self.run_helper("paired_report.py", source)

        self.assertEqual(result["eligible_pairs"], 1)
        self.assertEqual(result["recommendation"], "exploratory")
        self.assertEqual(result["deltas"]["confirmed_defects"], 1)
        self.assertEqual(result["deltas"]["false_findings"], 1)
        self.assertIsNone(result["deltas"]["settled_cost"])
        self.assertIsNone(result["deltas"]["elapsed_seconds"])
        self.assertIsNone(result["spend_exposure"])
        self.assertIsNone(result["settings_digest"])
        self.assertEqual(result["observed_spend"], "5")

        source.pop("settings")
        source.pop("common_cost")
        source.pop("retry_cost")
        for case in source["cases"]:
            for observation in case["observations"].values():
                observation["settled_cost"] = None
        result = self.run_helper("paired_report.py", source)
        self.assertIsNone(result["observed_spend"])

    def test_historical_rehearsal_requires_prepared_cohort_but_no_formal_gates(self):
        prepared = self.run_helper("rehearsal_fixture.py", {"prepared_main_inputs": True})
        pending = self.run_helper("rehearsal_fixture.py", {})

        self.assertEqual(prepared["rehearsal"], "passed")
        self.assertEqual(len(prepared["observations"]), 6)
        self.assertTrue(prepared["main_dispatch_permitted"])
        self.assertEqual(prepared["blocks"], [])
        self.assertFalse(pending["main_dispatch_permitted"])
        self.assertEqual(pending["blocks"], [{"case_id": None, "reason": "main-inputs-missing"}])

    def test_historical_rehearsal_still_blocks_packet_fault(self):
        result = self.run_helper("rehearsal_fixture.py", {
            "prepared_main_inputs": True, "fault": "packet-mismatch",
        })

        self.assertFalse(result["main_dispatch_permitted"])
        self.assertEqual(result["rehearsal"], "failed")
        self.assertIn("packet-mismatch", {entry["reason"] for entry in result["blocks"]})

    def test_capture_preserves_unmeasured_elapsed_time(self):
        observation = fixture()["cases"][0]["observations"]["baseline"]
        observation.update(elapsed_seconds=None, settled_cost=None)

        with TemporaryDirectory() as archive:
            result = subprocess.run(
                [sys.executable, "-IB", str(FIXTURES / "paired_review.py"),
                 "capture", archive, "--historical"],
                input=json.dumps(observation),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads(result.stdout)["elapsed_seconds"])

    def test_dispatch_without_budgets_preserves_uncertain_attempt(self):
        snapshot = {"settings": {"slots": 2}, "units": [
            {"id": "open", "case_id": "earlier", "kind": "review", "variant": "baseline",
             "attempt": {"id": "attempt-open", "state": "uncertain"}},
            {"id": "ready", "case_id": "later", "kind": "review", "variant": "baseline",
             "attempt": None},
            {"id": "adjudication", "case_id": "later", "kind": "adjudication", "variant": None,
             "attempt": None},
        ]}

        result = self.run_helper("dispatch_fixture.py", snapshot)

        self.assertEqual(result["eligible"], ["ready"])
        self.assertEqual(result["waiting"], {"adjudication": "pair-not-terminal"})
        self.assertEqual(result["uncertain_attempts"], ["attempt-open"])
        self.assertEqual(result["occupied_slots"], 1)
        self.assertIsNone(result["spend_exposure"])
        self.assertFalse(result["close"])

        snapshot["operator_close"] = True
        result = self.run_helper("dispatch_fixture.py", snapshot)
        self.assertEqual(result["eligible"], [])
        self.assertTrue(result["close"])
        self.assertEqual(result["terminal_updates"], [
            {"id": "open", "attempt_id": "attempt-open", "status": "partial"},
            {"id": "ready", "attempt_id": None, "status": "not started"},
            {"id": "adjudication", "attempt_id": None, "status": "incomplete"},
        ])
