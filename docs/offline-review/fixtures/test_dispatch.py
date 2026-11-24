"""Contract fixtures for manually planning bounded offline review dispatch."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


CHECK_DISPATCH = Path(__file__).with_name("dispatch_fixture.py")


def unit(identity, case, variant=None, *, cost="3", seconds=10, attempt=None):
    return {
        "id": identity,
        "case_id": case,
        "kind": "adjudication" if variant is None else "review",
        "variant": variant,
        "maximum_cost": cost,
        "maximum_seconds": seconds,
        "attempt": attempt,
    }


def attempt(identity, state, *, cost="2", end=20):
    return {"id": identity, "state": state, "reserved_cost": cost, "deadline": end}


def plan(*units, now=0, settled="5"):
    return {
        "settings": {
            "slots": 2,
            "spend_limit": "10",
            "session_spend_limit": "4",
            "session_seconds": 25,
            "cutoff_seconds": 30,
        },
        "elapsed_seconds": now,
        "settled_cost": settled,
        "units": list(units),
    }


class DispatchTests(unittest.TestCase):
    def evaluate(self, snapshot):
        self.assertTrue(CHECK_DISPATCH.is_file(), "Offline dispatch fixture procedure is unavailable")
        result = subprocess.run(
            [sys.executable, "-IB", str(CHECK_DISPATCH)],
            input=json.dumps(snapshot),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_spare_capacity_allows_later_review_at_exact_budget(self):
        report = self.evaluate(plan(
            unit("slow", "case-slow", "baseline", attempt=attempt("first-slow", "active")),
            unit("over", "case-big", "baseline", cost="4"),
            unit("fits", "case-small", "baseline", cost="3"),
        ))

        self.assertEqual(report["occupied_slots"], 1)
        self.assertEqual(report["spend_exposure"], "7")
        self.assertEqual(report["eligible"], ["fits"])
        self.assertEqual(report["waiting"], {"over": "shared-spend-limit"})
        self.assertFalse(report["close"])

    def test_blinded_work_is_ready_once_its_own_pair_has_finished(self):
        report = self.evaluate(plan(
            unit("slow", "case-slow", "baseline", attempt=attempt("first-slow", "active")),
            unit("finished-b", "case-finished", "baseline", attempt=attempt("done-b", "terminal")),
            unit("finished-t", "case-finished", "treatment", attempt=attempt("done-t", "terminal")),
            unit("not-ready", "case-slow", cost="1"),
            unit("ready", "case-finished", cost="3"),
        ))

        self.assertEqual(report["eligible"], ["ready"])
        self.assertEqual(report["waiting"], {"not-ready": "pair-not-terminal"})
        self.assertFalse(report["close"])

    def test_full_pool_waits_then_reconsiders_queued_work(self):
        slow = unit("slow", "case-slow", "baseline", attempt=attempt("first-slow", "active"))
        other = unit("other", "case-other", "treatment", attempt=attempt("first-other", "active", cost="1"))
        queued = unit("queued", "case-later", "baseline")
        full = self.evaluate(plan(slow, other, queued, settled="4"))
        self.assertEqual(full["waiting"], {"queued": "no-free-slot"})
        self.assertFalse(full["close"])

        other["attempt"] = attempt("first-other", "terminal", cost="1")
        freed = self.evaluate(plan(slow, other, queued, settled="5"))
        self.assertEqual(freed["eligible"], ["queued"])
        self.assertEqual(freed["spend_exposure"], "7")

    def test_unverified_timeout_survives_restart_until_cutoff(self):
        slow = unit("slow", "case-slow", "baseline", attempt=attempt("first-slow", "active", end=10))
        other = unit("other", "case-other", "baseline", attempt=attempt("first-other", "active"))
        queued = unit("queued", "case-later", "treatment", cost="1")
        adjudication = unit("pending", "case-other")
        snapshot = plan(slow, other, queued, adjudication, now=12, settled="4")
        before = self.evaluate(snapshot)
        after_restart = self.evaluate(json.loads(json.dumps(snapshot)))
        self.assertEqual(before, after_restart)
        self.assertEqual(before["uncertain_attempts"], ["first-slow"])
        self.assertEqual(before["occupied_slots"], 2)
        self.assertEqual(before["spend_exposure"], "8")
        self.assertEqual(before["eligible"], [])
        self.assertFalse(before["close"])

        snapshot["elapsed_seconds"] = 30
        closed = self.evaluate(snapshot)
        self.assertTrue(closed["close"])
        self.assertEqual(closed["spend_exposure"], "8")
        self.assertEqual(closed["eligible"], [])
        self.assertEqual(closed["terminal_updates"], [
            {"id": "slow", "attempt_id": "first-slow", "status": "timed out"},
            {"id": "other", "attempt_id": "first-other", "status": "timed out"},
            {"id": "queued", "attempt_id": None, "status": "not started"},
            {"id": "pending", "attempt_id": None, "status": "incomplete"},
        ])

    def test_session_limits_and_remaining_time_restrict_admission(self):
        report = self.evaluate(plan(
            unit("price", "case-big", "baseline", cost="4.01", seconds=2),
            unit("time", "case-long", "baseline", cost="1", seconds=26),
            unit("cutoff", "case-late", "baseline", cost="1", seconds=6),
            unit("fits", "case-small", "baseline", cost="0.3", seconds=5),
            now=25,
            settled="9.7",
        ))
        self.assertEqual(report["eligible"], ["fits"])
        self.assertEqual(report["waiting"], {
            "price": "session-spend-limit",
            "time": "session-time-limit",
            "cutoff": "comparison-cutoff",
        })


if __name__ == "__main__":
    unittest.main()
