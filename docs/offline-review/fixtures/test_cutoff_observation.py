"""Contract checks across cutoff projection, first observation capture, and scoring."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from test_dispatch import plan, unit
from test_paired_report import fixture


FIXTURES = Path(__file__).parent


def run_fixture(script, *args, data=None):
    return subprocess.run(
        [sys.executable, "-IB", str(FIXTURES / script), *map(str, args)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def queued_observation():
    case = fixture()["cases"][0]
    return {
        "case_id": case["case_id"],
        "packet_digest": case["packet_digest"],
        "variant": "baseline",
        "attempt_id": None,
        "status": "not started",
        "elapsed_seconds": None,
        "settled_cost": None,
        "reason": "Comparison cutoff reached before launch.",
    }


class CutoffObservationTests(unittest.TestCase):
    def read_result(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_cutoff_observation_is_frozen_and_reported_as_incomplete(self):
        observation = queued_observation()
        dispatch = self.read_result(run_fixture(
            "dispatch_fixture.py",
            data=plan(unit("queued", observation["case_id"], observation["variant"]), now=30),
        ))
        self.assertEqual(dispatch["terminal_updates"], [
            {"id": "queued", "attempt_id": None, "status": "not started"},
        ])
        update, = dispatch["terminal_updates"]
        observation.update(attempt_id=update["attempt_id"], status=update["status"])

        with TemporaryDirectory() as temporary:
            archive = Path(temporary)
            captured = self.read_result(run_fixture("paired_review.py", "capture", archive, data=observation))
            self.assertEqual(captured, {**observation, "report_digest": None})
            stored = json.loads((archive / "first-observation.json").read_text(encoding="utf-8"))
            self.assertEqual(stored, captured)

        snapshot = fixture()
        case = snapshot["cases"][0]
        case["observations"]["baseline"] = stored
        report = self.read_result(run_fixture("paired_report.py", data=snapshot))
        pair = report["pairs"][case["case_id"]]
        self.assertEqual(pair["status"], "incomplete")
        self.assertIn("baseline-not-completed", pair["reasons"])
        self.assertEqual(pair["observations"]["baseline"], stored)
        self.assertEqual(report["eligible_pairs"], 0)

    def test_capture_rejects_launched_null_and_unstarted_report_evidence(self):
        observation = queued_observation()
        with TemporaryDirectory() as temporary:
            archive = Path(temporary)
            launched = dict(observation, status="timed out", elapsed_seconds=1, reason="Deadline elapsed.")
            result = run_fixture("paired_review.py", "capture", archive, data=launched)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("attempt ID", result.stderr)
            self.assertFalse((archive / "first-observation.json").exists())

            submission = archive / "submission.json"
            submission.write_text("{}", encoding="utf-8")
            self.read_result(run_fixture("paired_review.py", "freeze", archive, submission))
            result = run_fixture("paired_review.py", "capture", archive, data=observation)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("report", result.stderr)
            self.assertFalse((archive / "first-observation.json").exists())


if __name__ == "__main__":
    unittest.main()
