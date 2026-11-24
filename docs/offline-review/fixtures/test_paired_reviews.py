"""Contract checks for synthetic paired-review sessions."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest

from test_case_packets import admitted_source


PAIRED_REVIEW = Path(__file__).with_name("paired_review.py")


class PairedReviewTests(unittest.TestCase):
    def invoke(self, *arguments: object, value: object = None) -> dict:
        self.assertTrue(PAIRED_REVIEW.is_file(), "Paired review procedure is unavailable")
        result = subprocess.run(
            [sys.executable, "-IB", str(PAIRED_REVIEW), *map(str, arguments)],
            input=json.dumps(value),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_each_session_reads_approved_packet_and_can_only_write_its_report(self) -> None:
        packet = admitted_source("pr")["packet"]
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet_path = root / "input" / "packet.json"
            packet_path.parent.mkdir()
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            history = root / "history" / "labels.txt"
            history.parent.mkdir()
            history.write_text("synthetic historical label", encoding="utf-8")
            outputs = {variant: root / variant for variant in ("baseline", "treatment")}
            for directory in outputs.values():
                directory.mkdir()
                (directory / "sibling-report.json").write_text(
                    "synthetic sibling result", encoding="utf-8"
                )
            probe = root / "probe.py"
            probe.write_text(
                textwrap.dedent(
                    """
                    import json
                    from pathlib import Path
                    import sys

                    packet, own, *private = map(Path, sys.argv[1:])
                    with packet.open(encoding="utf-8") as source:
                        identity = json.load(source)["case_id"]
                    denied_reads = []
                    for path in private:
                        try:
                            path.read_text()
                        except PermissionError:
                            denied_reads.append(str(path))
                    denied_writes = []
                    for path in (packet, private[0], private[1]):
                        try:
                            with path.open("r+"):
                                pass
                        except PermissionError:
                            denied_writes.append(str(path))
                    report = {
                        "case_id": identity,
                        "denied_reads": denied_reads,
                        "denied_writes": denied_writes,
                    }
                    (own / "submitted.json").write_text(json.dumps(report))
                    print(json.dumps(report))
                    """
                ),
                encoding="utf-8",
            )

            for variant in outputs:
                with self.subTest(variant=variant):
                    own = outputs[variant]
                    sibling = next(directory for key, directory in outputs.items() if key != variant)
                    sibling_report = sibling / "sibling-report.json"
                    history_link = own / "history-link"
                    history_link.symlink_to(history)
                    sibling_link = own / "sibling-link"
                    sibling_link.symlink_to(sibling_report)
                    denied = [history, sibling_report, history_link, sibling_link]

                    # Prove the seeded files and both links can be read outside the boundary.
                    self.assertEqual(
                        [path.read_text() for path in denied],
                        ["synthetic historical label", "synthetic sibling result"] * 2,
                    )
                    report = self.invoke(
                        "isolate", packet_path, own, probe, history, sibling_report,
                        history_link, sibling_link,
                    )
                    self.assertEqual(report["case_id"], packet["case_id"])
                    self.assertEqual(report["denied_reads"], list(map(str, denied)))
                    self.assertEqual(
                        report["denied_writes"], list(map(str, (packet_path, *denied[:2])))
                    )
                    self.assertEqual(json.loads((own / "submitted.json").read_text()), report)
                    self.assertEqual(json.loads(packet_path.read_text()), packet)

    def test_terminal_observation_preserves_the_first_report_after_late_replacement(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "private-observation"
            archive.mkdir()
            submitted = root / "submission.json"
            original = b'{"findings":[]}'
            submitted.write_bytes(original)
            record = {
                "case_id": "case-1",
                "packet_digest": "a" * 64,
                "variant": "baseline",
                "attempt_id": "attempt-1",
                "status": "partial",
                "elapsed_seconds": 13,
                "settled_cost": "2",
                "reason": "reviewer stopped before completion",
            }

            frozen = self.invoke("freeze", archive, submitted)
            submitted.write_bytes(b'{"findings":["late replacement"]}')
            repeated_freeze = self.invoke("freeze", archive, submitted)
            terminal = self.invoke("capture", archive, value=record)
            retry = self.invoke(
                "capture", archive, value={**record, "attempt_id": "retry", "status": "completed"}
            )

            expected_digest = hashlib.sha256(original).hexdigest()
            self.assertEqual(frozen["report_digest"], expected_digest)
            self.assertEqual(repeated_freeze, frozen)
            self.assertEqual((archive / "first-report").read_bytes(), original)
            self.assertEqual(terminal, {**record, "report_digest": expected_digest})
            self.assertEqual(retry, terminal)

    def test_terminal_observation_without_first_report_keeps_the_missing_evidence(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "private-observation"
            archive.mkdir()
            record = {
                "case_id": "case-1",
                "packet_digest": "a" * 64,
                "variant": "treatment",
                "attempt_id": "attempt-2",
                "status": "timed out",
                "elapsed_seconds": 30,
                "settled_cost": None,
                "reason": "terminal response missing",
            }

            first = self.invoke("capture", archive, value=record)
            submitted = root / "late-submission.json"
            submitted.write_bytes(b'{"findings":["late result"]}')
            frozen = self.invoke("freeze", archive, submitted)
            replay = self.invoke("capture", archive, value=record)

            self.assertEqual(first, {**record, "report_digest": None})
            self.assertEqual(frozen["report_digest"], None)
            self.assertEqual(replay, first)
            self.assertFalse((archive / "first-report").exists())

    @staticmethod
    def coverage_inputs() -> dict:
        return {
            "assignment": {"due": ["positive", "omitted", "unobserved"], "future": ["future"]},
            "coverage": {
                "due": [
                    {
                        "criterion": "positive",
                        "status": "satisfied",
                        "evidence": "widgets.py:17 exercises the returned label",
                    },
                    {
                        "criterion": "omitted",
                        "status": "violated",
                        "evidence": "unchanged routing.py:9 never invokes the approval rule",
                    },
                    {"criterion": "unobserved", "status": "undetermined", "gap": "audit data absent"},
                ],
                "future": ["future"],
            },
        }

    def test_treatment_reports_each_due_criterion_and_keeps_future_scope_separate(self) -> None:
        inputs = self.coverage_inputs()
        result = self.invoke("coverage", value=inputs)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["due_count"], 3)
        self.assertEqual(result["coverage"], inputs["coverage"])

    def test_treatment_rejects_missing_duplicate_or_unsupported_due_rows(self) -> None:
        def omit(rows: list) -> list:
            return rows[1:]

        def duplicate(rows: list) -> list:
            return [*rows, rows[0]]

        def leak_future(rows: list) -> list:
            return [*rows, {**rows[0], "criterion": "future"}]

        def omit_gap(rows: list) -> list:
            return [*rows[:2], {"criterion": "unobserved", "status": "undetermined"}]

        for mutate in (omit, duplicate, leak_future, omit_gap):
            with self.subTest(mutation=mutate.__name__):
                inputs = self.coverage_inputs()
                inputs["coverage"]["due"] = mutate(inputs["coverage"]["due"])
                result = self.invoke("coverage", value=inputs)
                self.assertEqual(result["status"], "invalid")
                self.assertTrue(result["reason"])


if __name__ == "__main__":
    unittest.main()
