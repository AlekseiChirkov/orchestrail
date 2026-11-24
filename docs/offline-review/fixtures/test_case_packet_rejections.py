"""Regression checks for unavailable approval and snapshot records."""

import json
import subprocess
import sys
import unittest

from test_case_packets import COMPILE_PACKET, admitted_source


class CasePacketRejectionTests(unittest.TestCase):
    def prepare(self, source: dict) -> dict:
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

    def test_admission_with_malformed_approval_inventory_records_exclusion(self) -> None:
        for malformed in (None, [], "invalid"):
            with self.subTest(approvals=malformed):
                source = admitted_source("pr")
                source["coordinator"]["approvals"] = malformed

                result = self.prepare(source)

                self.assertEqual(result, {
                    "status": "excluded",
                    "case_id": source["packet"]["case_id"],
                    "reason": "missing-specification-approval",
                })

    def test_admission_requires_readable_trees_and_allows_empty_trees(self) -> None:
        for field in ("base_tree", "tested_tree"):
            with self.subTest(tree=field):
                source = admitted_source("milestone")
                source["packet"][field] = None

                result = self.prepare(source)

                self.assertEqual(result, {
                    "status": "excluded",
                    "case_id": source["packet"]["case_id"],
                    "reason": "incomplete-packet",
                })

        source = admitted_source("milestone")
        source["packet"]["base_tree"] = {}
        source["packet"]["tested_tree"] = {}

        result = self.prepare(source)

        self.assertEqual(result["status"], "admitted")
        self.assertEqual(result["packet"]["base_tree"], {})
        self.assertEqual(result["packet"]["tested_tree"], {})
