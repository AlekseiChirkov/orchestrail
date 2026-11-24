"""Verify the offline protocol against an integrated synthetic rehearsal."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


REHEARSE = Path(__file__).with_name("rehearsal_fixture.py")
CASES = {"case-amber", "case-cobalt", "case-jade"}


class RehearsalTests(unittest.TestCase):
    def run_rehearsal(
        self, *, fault=None, approved_main_inputs=False, locked_settings=False
    ):
        self.assertTrue(REHEARSE.is_file(), "Offline rehearsal procedure is unavailable")
        result = subprocess.run(
            [sys.executable, "-IB", str(REHEARSE)],
            input=json.dumps({
                "fault": fault,
                "approved_main_inputs": approved_main_inputs,
                "locked_settings": locked_settings,
            }),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_fresh_verified_rehearsal_allows_approved_main_dispatch(self):
        result = self.run_rehearsal(approved_main_inputs=True, locked_settings=True)

        self.assertEqual(result["rehearsal"], "passed")
        self.assertEqual(result["historical_execution"], "eligible")
        self.assertTrue(result["main_dispatch_permitted"])
        self.assertEqual(result["blocks"], [])
        observations = result["observations"]
        self.assertEqual(len(observations), 6)
        self.assertEqual(len({item["attempt_id"] for item in observations}), 6)
        self.assertEqual(len(result["packet_digests"]), 3)
        self.assertEqual(set(result["packet_digests"]), CASES)
        self.assertEqual(set(result["dispatch"]["admitted_first_wave"]), {
            item["attempt_id"] for item in observations
        })
        self.assertEqual(result["decision"]["eligible_pairs"], 3)
        self.assertEqual(result["decision"]["enrolled_cases"], 3)
        self.assertEqual(result["decision"]["recommendation"], "trial")
        for case_id in CASES:
            with self.subTest(case_id=case_id):
                pair = [item for item in observations if item["case_id"] == case_id]
                self.assertEqual({item["variant"] for item in pair}, {"baseline", "treatment"})
                self.assertEqual({item["status"] for item in pair}, {"completed"})
                self.assertEqual({item["packet_digest"] for item in pair}, {
                    result["packet_digests"][case_id]
                })
                for observation in pair:
                    self.assertRegex(observation["report_digest"], r"^[a-f0-9]{64}$")

    def test_mismatched_packet_blocks_main_with_case_and_reason(self):
        result = self.run_rehearsal(
            fault="packet-mismatch", approved_main_inputs=True, locked_settings=True
        )

        self.assertEqual(result["rehearsal"], "failed")
        self.assertFalse(result["main_dispatch_permitted"])
        self.assertEqual(result["blocks"], [
            {"case_id": "case-cobalt", "reason": "packet-mismatch"}
        ])
        self.assertEqual(len(result["observations"]), 6)
        observed = {
            item["packet_digest"]
            for item in result["observations"]
            if item["case_id"] == "case-cobalt"
        }
        self.assertEqual(len(observed), 2)
        self.assertEqual(result["decision"]["eligible_pairs"], 2)

    def test_verified_historical_exposure_blocks_main_with_case_and_reason(self):
        result = self.run_rehearsal(
            fault="historical-exposure", approved_main_inputs=True, locked_settings=True
        )

        self.assertEqual(result["rehearsal"], "failed")
        self.assertFalse(result["main_dispatch_permitted"])
        self.assertEqual(result["blocks"], [
            {"case_id": "case-jade", "reason": "historical-label-exposure"}
        ])
        self.assertEqual(len(result["observations"]), 6)
        self.assertEqual(result["decision"]["eligible_pairs"], 2)
        self.assertIn("case-contaminated", result["decision"]["pairs"]["case-jade"]["reasons"])

    def test_clean_rehearsal_preserves_pending_when_either_main_prerequisite_is_missing(self):
        for approvals, locked, reason in (
            (False, True, "main-inputs-unapproved"),
            (True, False, "comparison-settings-unlocked"),
        ):
            with self.subTest(reason=reason):
                result = self.run_rehearsal(
                    approved_main_inputs=approvals, locked_settings=locked
                )

                self.assertEqual(result["rehearsal"], "passed")
                self.assertEqual(result["historical_execution"], "pending")
                self.assertFalse(result["main_dispatch_permitted"])
                self.assertEqual(result["blocks"], [{"case_id": None, "reason": reason}])


if __name__ == "__main__":
    unittest.main()
