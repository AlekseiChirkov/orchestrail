"""Derive an offline comparison report from frozen review records."""

import argparse
from fractions import Fraction
import json
import math
import re
import sys


ARMS = ("baseline", "treatment")
VERDICTS = {"confirmed", "refuted", "unresolved"}
OBSERVATION_FIELDS = (
    "case_id", "packet_digest", "variant", "attempt_id", "status",
    "elapsed_seconds", "settled_cost", "reason", "report_digest",
)
TERMINAL_STATUSES = {"completed", "partial", "failed", "timed out", "invalid", "not started"}


def decimal_amount(value, *, signed=False):
    pattern = r"-?[0-9]+(?:\.[0-9]+)?" if signed else r"[0-9]+(?:\.[0-9]+)?"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("expected a decimal currency string")
    return Fraction(value)


def decimal_text(value):
    """Format a finite decimal sum or difference exactly."""
    magnitude = abs(value)
    whole, remainder = divmod(magnitude.numerator, magnitude.denominator)
    digits = []
    while remainder:
        digit, remainder = divmod(remainder * 10, magnitude.denominator)
        digits.append(str(digit))
    sign = "-" if value < 0 else ""
    return f"{sign}{whole}.{''.join(digits)}" if digits else f"{sign}{whole}"


def seconds(value, *, signed=False):
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        raise ValueError("expected finite elapsed seconds")
    if value < 0 and not signed:
        raise ValueError("elapsed seconds must be nonnegative")
    return Fraction(str(value))


def count(value, *, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        raise ValueError("invalid count in locked settings")
    return value


def identity(value):
    return isinstance(value, str) and bool(value.strip())


def valid_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def require_boolean(value):
    if type(value) is not bool:
        raise ValueError("expected an explicit contamination flag")
    return value


def adjudicated_claims(batch, mapping, cutoff):
    findings = {}
    pending = {}
    for entry in batch["verdicts"]:
        finding = entry["finding_id"]
        outcome = entry["verdict"]
        if (finding not in mapping or finding in findings or outcome not in VERDICTS
                or not identity(entry["rationale"]) or not identity(entry["severity"])
                or (outcome != "unresolved" and not identity(entry["canonical_id"]))):
            raise ValueError("invalid or duplicate independent finding disposition")
        findings[finding] = entry
    for entry in batch["pending_claims"]:
        finding = entry["finding_id"]
        if finding not in mapping or finding in findings or finding in pending or not identity(entry["reason"]):
            raise ValueError("pending claim must have a unique opaque identifier and gap reason")
        pending[finding] = {"finding_id": finding, "reason": entry["reason"]}
    for finding in sorted(mapping.keys() - findings.keys() - pending.keys()):
        pending[finding] = {"finding_id": finding, "reason": "No independent disposition recorded."}
    complete = batch["status"] == "complete" and not pending
    if complete:
        frozen_at = seconds(batch["frozen_at"])
        complete = cutoff is None or frozen_at <= cutoff
    return findings, list(pending.values()), complete


def pair_record(case, cohort_contaminated, cutoff):
    case_id = case["case_id"]
    packet = case["packet_digest"]
    observations = case["observations"]
    if not identity(case_id) or not valid_digest(packet) or observations.keys() != set(ARMS):
        raise ValueError("expected a pinned case and two first observations")
    projected = {}
    reasons = []
    for arm, entry in observations.items():
        observation = {field: entry[field] for field in OBSERVATION_FIELDS}
        status = observation["status"]
        attempt = observation["attempt_id"]
        if status not in TERMINAL_STATUSES or (
            not identity(attempt) and not (status == "not started" and attempt is None)
        ):
            raise ValueError("invalid first observation identity or terminal status")
        if observation["case_id"] != case_id or observation["variant"] != arm:
            reasons.append(f"{arm}-first-observation-identity-mismatch")
        if observation["packet_digest"] != packet:
            reasons.append(f"{arm}-packet-mismatch")
        if status != "completed":
            reasons.append(f"{arm}-not-completed")
        elif not valid_digest(observation["report_digest"]):
            reasons.append(f"{arm}-first-report-missing-or-invalid")
        projected[arm] = observation
    mapping = case["finding_variants"]
    if any(not identity(finding) or arm not in ARMS for finding, arm in mapping.items()):
        raise ValueError("invalid private finding-to-arm map")
    batch = case["adjudication"]
    if batch["status"] not in ("complete", "incomplete"):
        raise ValueError("invalid adjudication batch status")
    findings, pending, adjudication_complete = adjudicated_claims(batch, mapping, cutoff)
    if not adjudication_complete:
        reasons.append("adjudication-incomplete-or-late")
    canonical_severities = {}
    severity_conflicts = set()
    for entry in findings.values():
        if entry["verdict"] == "confirmed":
            canonical = entry["canonical_id"]
            severity = entry["severity"]
            if canonical_severities.setdefault(canonical, severity) != severity:
                severity_conflicts.add(canonical)
    if severity_conflicts:
        reasons.append("adjudication-severity-conflict")
    if require_boolean(case["contaminated"]):
        reasons.append("case-contaminated")
    if cohort_contaminated:
        reasons.append("cohort-contaminated")
    record = {
        "status": "incomplete" if reasons else "complete",
        "reasons": reasons,
        "packet_digest": packet,
        "observations": projected,
        "adjudication_status": batch["status"],
        "adjudication_frozen_at": batch["frozen_at"],
        "conflicting_severity_ids": sorted(severity_conflicts),
        "pending_claims": pending,
        "unresolved_findings": [
            finding for finding, entry in findings.items() if entry["verdict"] == "unresolved"
        ],
        "coverage_gaps": case["coverage_gaps"],
    }
    return record, findings


def tally_pair(totals, exclusive, case, record, findings, severities):
    confirmed = {arm: set() for arm in ARMS}
    consequential = {arm: set() for arm in ARMS}
    refuted = {arm: set() for arm in ARMS}
    for finding, entry in findings.items():
        arm = case["finding_variants"][finding]
        outcome = entry["verdict"]
        canonical = entry["canonical_id"]
        if outcome == "confirmed":
            confirmed[arm].add(canonical)
            if entry["severity"] in severities:
                consequential[arm].add(canonical)
        elif outcome == "refuted":
            refuted[arm].add(canonical)
        else:
            totals[arm]["unresolved_findings"] += 1
    for arm in ARMS:
        metrics = totals[arm]
        other = "baseline" if arm == "treatment" else "treatment"
        exclusive[arm] += len(confirmed[arm] - confirmed[other])
        metrics["confirmed_defects"] += len(confirmed[arm])
        metrics["consequential_defects"] += len(consequential[arm])
        metrics["false_findings"] += len(refuted[arm])
        observation = record["observations"][arm]
        for metric, parse in (("elapsed_seconds", seconds), ("settled_cost", decimal_amount)):
            value = observation[metric]
            if value is None:
                metrics[metric] = None
            elif metrics[metric] is not None:
                metrics[metric] += parse(value)


def json_seconds(value):
    if value is None or value.denominator == 1:
        return None if value is None else value.numerator
    return float(value)


def report(snapshot, *, historical=False):
    settings = snapshot.get("settings", {}) if historical else snapshot["settings"]
    settings_digest = None if historical else settings["digest"]
    if not historical and not valid_digest(settings_digest):
        raise ValueError("expected a pinned settings digest")
    cutoff = None if historical else seconds(settings["cutoff_seconds"])
    minimum = count(settings.get("minimum_pairs", 1) if historical else settings["minimum_pairs"], minimum=1)
    criteria = None if historical else {
        "confirmed_defects": count(settings["minimum_incremental_defects"]),
        "false_findings": count(settings["maximum_incremental_false"]),
        "elapsed_seconds": seconds(settings["maximum_incremental_seconds"], signed=True),
        "settled_cost": decimal_amount(settings["maximum_incremental_cost"], signed=True),
    }
    severity_roster = (settings.get("consequential_severities", ["major", "critical"])
                       if historical else settings["consequential_severities"])
    if not isinstance(severity_roster, list) or not severity_roster or not all(map(identity, severity_roster)):
        raise ValueError("expected a locked consequential severity roster")
    severities = set(severity_roster)
    unresolved_policy = "record" if historical else settings.get("unresolved_policy", "record")
    if unresolved_policy not in ("record", "insufficient-evidence"):
        raise ValueError("unknown unresolved finding policy")
    extras = {
        "common_cost": decimal_amount(snapshot["common_cost"]),
        "retry_cost": decimal_amount(snapshot["retry_cost"]),
        "unresolved_reservations": sum(map(decimal_amount, snapshot["unresolved_reservations"]), Fraction()),
    } if not historical else {
        key: decimal_amount(snapshot[key]) if snapshot.get(key) is not None else None
        for key in ("common_cost", "retry_cost")
    }
    spend = sum((value for value in extras.values() if value is not None), Fraction())
    cost_observed = any(value is not None for value in extras.values())
    contaminated = require_boolean(snapshot["cohort_contaminated"])
    totals = {
        arm: {
            "confirmed_defects": 0, "consequential_defects": 0, "false_findings": 0,
            "unresolved_findings": 0, "elapsed_seconds": Fraction(), "settled_cost": Fraction(),
        }
        for arm in ARMS
    }
    exclusive = dict.fromkeys(ARMS, 0)
    attempts = set()
    unknown_cost_attempts = []
    pairs = {}
    eligible = 0
    missing_measurements = []
    for case in snapshot["cases"]:
        case_id = case["case_id"]
        if case_id in pairs:
            raise ValueError("enrolled case identities must be unique")
        record, findings = pair_record(case, contaminated, cutoff)
        pairs[case_id] = record
        for arm, observation in record["observations"].items():
            attempt = observation["attempt_id"]
            if attempt is not None:
                if attempt in attempts:
                    raise ValueError("original attempt identities must be unique")
                attempts.add(attempt)
            value = observation["settled_cost"]
            if value is not None:
                spend += decimal_amount(value)
                cost_observed = True
            elif observation["status"] != "not started":
                unknown_cost_attempts.append(attempt)
            if record["status"] == "complete":
                for field in ("settled_cost", "elapsed_seconds"):
                    if observation[field] is None:
                        missing_measurements.append({"case_id": case_id, "arm": arm, "field": field})
        if record["status"] == "complete":
            eligible += 1
            tally_pair(totals, exclusive, case, record, findings, severities)

    deltas = {}
    for metric in ("confirmed_defects", "false_findings", "elapsed_seconds", "settled_cost"):
        key = "consequential_defects" if metric == "confirmed_defects" else metric
        baseline, treatment = (totals[arm][key] for arm in ARMS)
        deltas[metric] = None if baseline is None or treatment is None else treatment - baseline
    breached = []
    recommendation = "insufficient evidence"
    unresolved_blocks = unresolved_policy == "insufficient-evidence" and any(
        metrics["unresolved_findings"] for metrics in totals.values()
    )
    if historical and eligible:
        recommendation = "exploratory"
    elif eligible >= minimum and not missing_measurements and not unresolved_blocks:
        for metric, maximum in criteria.items():
            if metric == "confirmed_defects":
                failed = deltas[metric] < maximum
            else:
                failed = deltas[metric] > maximum
            if failed:
                breached.append(metric)
        recommendation = "no trial" if breached else "trial"

    reasons = []
    if contaminated:
        reasons.append("cohort-contaminated")
    if eligible < minimum:
        reasons.append("too-few-eligible-pairs")
    if missing_measurements:
        reasons.append("measurements-unavailable" if historical else "missing-required-measurements")
    if unresolved_blocks:
        reasons.append("unresolved-claims-under-locked-policy")
    for values in ((criteria,) if criteria else ()) + (deltas, *totals.values()):
        if values["settled_cost"] is not None:
            values["settled_cost"] = decimal_text(values["settled_cost"])
        values["elapsed_seconds"] = json_seconds(values["elapsed_seconds"])
    return {
        "settings_digest": settings_digest,
        "recommendation": recommendation,
        "enrolled_cases": len(pairs),
        "completed_cases": sum(
            all(observation["status"] == "completed" for observation in pair["observations"].values())
            for pair in pairs.values()
        ),
        "eligible_pairs": eligible,
        "minimum_pairs": minimum,
        "unresolved_policy": unresolved_policy,
        "thresholds": criteria,
        "breached_thresholds": breached,
        "reasons": reasons,
        "missing_measurements": missing_measurements,
        "pairs": pairs,
        "per_variant": totals,
        "exclusive_confirmed": exclusive,
        "deltas": deltas,
        "spend_exposure": None if historical else decimal_text(spend),
        "spend_breakdown": {key: None if value is None else decimal_text(value) for key, value in extras.items()},
        "unknown_cost_attempts": unknown_cost_attempts,
        **({"observed_spend": decimal_text(spend) if cost_observed else None} if historical else {}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", action="store_true", help="report descriptive historical results")
    args = parser.parse_args()
    try:
        result = report(json.load(sys.stdin), historical=args.historical)
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        print(f"Invalid synthetic comparison snapshot: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
