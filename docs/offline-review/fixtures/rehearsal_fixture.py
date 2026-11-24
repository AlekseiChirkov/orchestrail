"""Exercise the offline review procedure on three fresh synthetic cases."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
ARMS = ("baseline", "treatment")
CASES = ("case-amber", "case-cobalt", "case-jade")
HISTORY_MARKER = "fixture-only-historical-label"
LIMITS = {
    "slots": 6, "spend_limit": "9", "session_spend_limit": "1",
    "session_seconds": 10, "cutoff_seconds": 30,
}
DECISION_SETTINGS = {
    "cutoff_seconds": LIMITS["cutoff_seconds"],
    "minimum_pairs": 1,
    "minimum_incremental_defects": 1,
    "maximum_incremental_false": 0,
    "maximum_incremental_seconds": 0,
    "maximum_incremental_cost": "0",
    "consequential_severities": ["major"],
}


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def check(script, *arguments, payload=None):
    result = subprocess.run(
        [sys.executable, "-IB", str(HERE / script), *map(str, arguments)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=15, check=False,
    )
    if result.returncode:
        raise ValueError(f"{script} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def prepare(case_id, fault):
    specification = {"content": "Show the label on the widget.", "annexes": []}
    assignment = {"version": "fixture-v1", "due": ["show-label"], "future": ["suggest-label"]}
    composition = {"kind": "pr", "target": "fixture-target", "base": f"{case_id}-base"}
    if case_id == "case-jade":
        composition.update(
            kind="milestone", integrated_tree="jade-integrated",
            constituents=["jade-first", "jade-second"],
        )
    else:
        composition["head"] = f"{case_id}-head"
    design = "Render the assigned label."
    if case_id == "case-jade" and fault == "historical-exposure":
        design += f" {HISTORY_MARKER}"
    raw = {
        "packet": {
            "case_id": case_id,
            "composition": composition,
            "base_tree": {"widget.txt": "Label: blue"},
            "tested_tree": {"widget.txt": "Hidden" if case_id == "case-cobalt" else "Label: blue"},
            "diff": "Update widget styling.",
            "tests": ["Check styling."],
            "owned_paths": ["widget.txt"],
            "task_design": design,
            "upstream_contract": "Only the approved label is eligible.",
            "review_instructions": "Inspect the pinned composition and tests.",
            "specification": specification,
            "assignment": assignment,
        },
        "coordinator": {
            "approvals": {
                "specification": {"reference": "fixture/spec", "digest": digest(specification)},
                "assignment": {"reference": "fixture/assignment", "digest": digest(assignment)},
            },
        },
    }
    approved = check("prepare_case.py", payload=raw)
    if approved["status"] != "admitted":
        raise ValueError(f"{case_id} packet admission failed: {approved['reason']}")
    return approved


def unit(case_id, arm=None):
    return {
        "id": f"{case_id}-{arm or 'adjudication'}",
        "case_id": case_id,
        "kind": "review" if arm else "adjudication",
        "variant": arm,
        "maximum_cost": "1",
        "maximum_seconds": 5,
        "attempt": None,
    }


def dispatch(units, elapsed, settled):
    return check("dispatch_fixture.py", payload={
        "settings": LIMITS,
        "elapsed_seconds": elapsed,
        "settled_cost": str(settled),
        "units": units,
    })


def reserve(queued, units, elapsed, settled):
    admitted = []
    for item in queued:
        snapshot = dispatch(units, elapsed, settled)
        if item["id"] not in snapshot["eligible"]:
            raise ValueError(f"fixture unit {item['id']} was not admitted")
        item["attempt"] = {
            "id": item["id"], "state": "active",
            "reserved_cost": item["maximum_cost"], "deadline": elapsed + item["maximum_seconds"],
        }
        admitted.append(item["id"])
    return admitted


def observe(root, packet, item, history, fault):
    variant = item["variant"]
    own = root / variant
    sibling = next(root / arm for arm in ARMS if arm != variant)
    archive = root / f"{variant}-archive"
    archive.mkdir()
    packet_path = root / f"{variant}-packet.json"
    delivered = dict(packet)
    if item["case_id"] == "case-cobalt" and variant == "treatment" and fault == "packet-mismatch":
        delivered["task_design"] += " A later edit."
    packet_path.write_bytes(canonical_bytes(delivered))
    sibling_path = sibling / "private.txt"
    links = (own / "history-link", own / "sibling-link")
    links[0].symlink_to(history)
    links[1].symlink_to(sibling_path)
    private_paths = (history, sibling_path, *links)
    probe = check(
        "paired_review.py", "isolate", packet_path, own, HERE / "rehearsal_probe.py",
        variant, *private_paths,
    )
    if probe["denied_paths"] != list(map(str, private_paths)):
        raise ValueError(f"{item['case_id']} fixture filesystem boundary failed")
    if probe["case_id"] != item["case_id"]:
        raise ValueError("isolated probe returned the wrong case")
    frozen = check("paired_review.py", "freeze", archive, own / "report.json")
    observation = check("paired_review.py", "capture", archive, payload={
        "case_id": item["case_id"], "packet_digest": probe["packet_digest"],
        "variant": variant, "attempt_id": item["attempt"]["id"],
        "status": "completed", "elapsed_seconds": 5, "settled_cost": "1", "reason": None,
    })
    report = (archive / "first-report").read_bytes()
    if observation["report_digest"] != frozen["report_digest"] or (
        hashlib.sha256(report).hexdigest() != observation["report_digest"]
    ):
        raise ValueError("first report failed digest reconciliation")
    return observation, json.loads(report)


def adjudicate(directory, packet, reports):
    # Derive the blind batch from the frozen claims before applying the private arm map.
    claims = [claim for report in reports.values() for claim in report["findings"]]
    verdicts = []
    for claim in claims:
        if claim["anchor"] != "widget.txt:1":
            raise ValueError("synthetic claim could not be matched to the tested boundary")
        missing_label = not packet["tested_tree"]["widget.txt"].startswith("Label:")
        verdicts.append({
            "finding_id": claim["finding_id"],
            "verdict": "confirmed" if missing_label else "refuted",
            "canonical_id": "label-display", "severity": "major",
            "rationale": "Checked the displayed text against the approved label requirement.",
        })
    batch = {"status": "complete", "frozen_at": 10, "verdicts": verdicts, "pending_claims": []}
    batch_path = directory / "blind-adjudication.json"
    with batch_path.open("x", encoding="utf-8") as archive:
        json.dump(batch, archive, ensure_ascii=False)
    frozen = json.loads(batch_path.read_bytes())
    if digest(frozen) != digest(batch):
        raise ValueError("blind adjudication failed digest reconciliation")
    mapping = {
        claim["finding_id"]: arm for arm, report in reports.items() for claim in report["findings"]
    }
    return frozen, mapping


def rehearse(root, fault, approved_main_inputs, locked_settings):
    prepared = {case_id: prepare(case_id, fault) for case_id in CASES}
    packets = {case_id: item["packet"] for case_id, item in prepared.items()}
    packet_digests = {
        case_id: item["variant_packet_digests"]["baseline"] for case_id, item in prepared.items()
    }
    if any(
        tuple(item["variant_packet_digests"].values()) != (packet_digests[case_id],) * 2
        for case_id, item in prepared.items()
    ):
        raise ValueError("prepared case packets must pin one digest across variants")

    history = root / "historical-label.txt"
    history.write_text(HISTORY_MARKER, encoding="utf-8")
    reviews = [unit(case_id, arm) for case_id in CASES for arm in ARMS]
    adjudications = [unit(case_id) for case_id in CASES]
    units = reviews + adjudications
    admitted = reserve(reviews, units, elapsed=0, settled=0)
    ledger = dispatch(units, elapsed=0, settled=0)
    if ledger["occupied_slots"] != len(reviews) or ledger["spend_exposure"] != str(len(reviews)):
        raise ValueError("first wave reservation did not account for every review")

    for case_id in CASES:
        for arm in ARMS:
            output = root / case_id / arm
            output.mkdir(parents=True)
            (output / "private.txt").write_text("Synthetic sibling-only result", encoding="utf-8")
    observations = {}
    reports = {}
    for item in reviews:
        case_id = item["case_id"]
        observation, report = observe(root / case_id, packets[case_id], item, history, fault)
        observations.setdefault(case_id, {})[item["variant"]] = observation
        reports.setdefault(case_id, {})[item["variant"]] = report
        item["attempt"].update(state="terminal", observation_status=observation["status"])

    adjudication_ids = reserve(adjudications, units, elapsed=5, settled=len(reviews))
    batches = {}
    blocks = []
    for item in adjudications:
        case_id = item["case_id"]
        packet = packets[case_id]
        pair = observations[case_id]
        pair_reports = reports[case_id]
        if any(entry["packet_digest"] != packet_digests[case_id] for entry in pair.values()):
            blocks.append({"case_id": case_id, "reason": "packet-mismatch"})
        exposed = any(HISTORY_MARKER in entry["observed_design"] for entry in pair_reports.values())
        if exposed:
            blocks.append({"case_id": case_id, "reason": "historical-label-exposure"})
        coverage = check("paired_review.py", "coverage", payload={
            "assignment": packet["assignment"], "coverage": pair_reports["treatment"]["coverage"],
        })
        if coverage["status"] != "valid":
            blocks.append({"case_id": case_id, "reason": "invalid-coverage"})
        batch, mapping = adjudicate(root / case_id, packet, pair_reports)
        batches[case_id] = {
            "case_id": case_id, "packet_digest": packet_digests[case_id],
            "observations": pair, "contaminated": exposed, "adjudication": batch,
            "finding_variants": mapping, "coverage_gaps": [],
        }
        item["attempt"].update(state="terminal", observation_status="complete")

    closure = dispatch(units, elapsed=10, settled=len(units))
    if not closure["close"] or closure["spend_exposure"] != LIMITS["spend_limit"]:
        raise ValueError("fixture did not close at the exact shared spend limit")
    settings = {**DECISION_SETTINGS, "digest": digest({**LIMITS, **DECISION_SETTINGS})}
    decision = check("paired_report.py", payload={
        "settings": settings, "cases": list(batches.values()), "cohort_contaminated": False,
        "common_cost": str(len(adjudications)), "retry_cost": "0", "unresolved_reservations": [],
    })
    if not blocks and (decision["eligible_pairs"] != len(CASES) or decision["recommendation"] != "trial"):
        blocks.append({"case_id": None, "reason": "decision-verification-failed"})
    rehearsal = "failed" if blocks else "passed"
    if not approved_main_inputs:
        blocks.append({"case_id": None, "reason": "main-inputs-unapproved"})
    if not locked_settings:
        blocks.append({"case_id": None, "reason": "comparison-settings-unlocked"})
    return {
        "rehearsal": rehearsal, "historical_execution": "pending" if blocks else "eligible",
        "main_dispatch_permitted": not blocks, "blocks": blocks, "packet_digests": packet_digests,
        "observations": [observation for pair in observations.values() for observation in pair.values()],
        "dispatch": {"admitted_first_wave": admitted, "admitted_adjudications": adjudication_ids},
        "decision": decision,
    }


def main():
    try:
        options = json.load(sys.stdin)
        fault = options.get("fault")
        approvals = options.get("approved_main_inputs", False)
        locked = options.get("locked_settings", False)
        if fault not in (None, "packet-mismatch", "historical-exposure"):
            raise ValueError("unknown synthetic rehearsal fault")
        if type(approvals) is not bool or type(locked) is not bool:
            raise ValueError("synthetic prerequisites must be explicit boolean flags")
        with TemporaryDirectory(prefix="offline-review-rehearsal-") as temporary:
            result = rehearse(Path(temporary), fault, approvals, locked)
    except (AttributeError, KeyError, OSError, TypeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Invalid synthetic rehearsal: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
