"""Contract checks for preparing controlled offline review packets."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from uuid import uuid4


COMPILE_PACKET = Path(__file__).with_name("prepare_case.py")


def digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def admitted_source(kind: str) -> dict:
    composition = {"kind": kind, "target": uuid4().hex, "base": uuid4().hex}
    if kind == "pr":
        composition["head"] = uuid4().hex
    else:
        composition["integrated_tree"] = uuid4().hex
        composition["constituents"] = [uuid4().hex, uuid4().hex]

    specification = {
        "content": "The widget accepts the selected label.",
        "annexes": [{"name": "labels.txt", "content": "A valid label is nonempty."}],
    }
    assignment = {
        "version": uuid4().hex,
        "due": ["Accept a valid label"],
        "future": ["Suggest labels"],
    }
    return {
        "packet": {
            "case_id": uuid4().hex,
            "composition": composition,
            "base_tree": {"widget.txt": "No label."},
            "tested_tree": {"widget.txt": "Label set."},
            "diff": "Set the label.",
            "tests": ["Exercise the selected label."],
            "owned_paths": ["widget.txt"],
            "task_design": "Update the widget's selected label.",
            "upstream_contract": "Only valid labels may be displayed.",
            "review_instructions": "Review the pinned composition and its tests.",
            "specification": specification,
            "assignment": assignment,
        },
        "coordinator": {
            "feature_group": uuid4().hex,
            "cohort": "rehearsal",
            "historical_labels": ["coordinator-only historical label"],
            "source_reference": "private/source",
            "approvals": {
                "specification": {"reference": "trusted/spec", "digest": digest(specification)},
                "assignment": {"reference": "trusted/assignment", "digest": digest(assignment)},
            },
        },
    }


class CasePacketTests(unittest.TestCase):
    def prepare(self, source: dict) -> dict:
        # Mark the absent implementation as a normal test failure before the helper exists.
        self.assertTrue(COMPILE_PACKET.is_file(), "Case packet preparation is unavailable")
        result = subprocess.run(
            [sys.executable, "-I", str(COMPILE_PACKET)],
            input=json.dumps(source),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_admission_pins_one_packet_for_both_variants(self) -> None:
        for kind in ("pr", "milestone"):
            with self.subTest(kind=kind):
                source = admitted_source(kind)

                result = self.prepare(source)

                packet = result["packet"]
                self.assertEqual(result["status"], "admitted")
                self.assertEqual(packet["composition"], source["packet"]["composition"])
                self.assertEqual(packet["specification"], source["packet"]["specification"])
                self.assertEqual(packet["assignment"], source["packet"]["assignment"])
                self.assertEqual(
                    result["variant_packet_digests"],
                    dict.fromkeys(("baseline", "treatment"), digest(packet)),
                )
                self.assertNotIn("coordinator-only historical label", json.dumps(packet))
                self.assertNotIn("trusted/assignment", json.dumps(packet))

    def test_admission_without_approval_records_exclusion(self) -> None:
        for approval in ("specification", "assignment"):
            with self.subTest(approval=approval):
                source = admitted_source("pr")
                del source["coordinator"]["approvals"][approval]

                result = self.prepare(source)

                self.assertEqual(result["status"], "excluded")
                self.assertEqual(result["case_id"], source["packet"]["case_id"])
                self.assertEqual(result["reason"], f"missing-{approval}-approval")
                self.assertNotIn("packet", result)
                self.assertNotIn("variant_packet_digests", result)

    def test_admission_after_annex_change_rejects_stale_approval(self) -> None:
        source = admitted_source("milestone")
        source["packet"]["specification"]["annexes"][0]["content"] = "A changed requirement."

        result = self.prepare(source)

        self.assertEqual(result["status"], "excluded")
        self.assertEqual(result["reason"], "specification-approval-digest-mismatch")
        self.assertNotIn("packet", result)


if __name__ == "__main__":
    unittest.main()
