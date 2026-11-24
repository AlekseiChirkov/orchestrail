"""Evaluate an offline dispatch ledger snapshot with synthetic data."""

from fractions import Fraction
import json
import re
import sys


VARIANTS = {"baseline", "treatment"}
ATTEMPT_STATES = {"active", "uncertain", "terminated", "terminal"}
REVIEW_STATUSES = {"completed", "partial", "failed", "timed out", "invalid", "not started"}
ADJUDICATION_STATUSES = {"complete", "incomplete"}


def money(value):
    """Read a finite nonnegative decimal amount without rounding."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
        raise ValueError("charges and limits must be nonnegative decimal strings")
    return Fraction(value)


def money_text(value):
    whole, remainder = divmod(value.numerator, value.denominator)
    digits = []
    while remainder:
        digit, remainder = divmod(remainder * 10, value.denominator)
        digits.append(str(digit))
    return f"{whole}.{''.join(digits)}" if digits else str(whole)


def seconds(value, *, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(f"expected an integer at least {minimum} for time or slot count")
    return value


def identity(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("unit, case and attempt identities must be nonempty strings")
    return value


def index_units(units):
    """Validate the closed fixture vocabulary and index frozen review observations."""
    unit_ids, attempt_ids, case_slots = set(), set(), set()
    finished_reviews = {}
    for item in units:
        unit_id, case = identity(item["id"]), identity(item["case_id"])
        kind, variant = item["kind"], item["variant"]
        if kind == "review" and variant in VARIANTS:
            statuses = REVIEW_STATUSES
        elif kind == "adjudication" and variant is None:
            statuses = ADJUDICATION_STATUSES
        else:
            raise ValueError("expected a review variant or a variant-free adjudication")
        if unit_id in unit_ids or (case, variant) in case_slots:
            raise ValueError("unit identities and case slots must be unique")
        unit_ids.add(unit_id)
        case_slots.add((case, variant))
        money(item["maximum_cost"])
        seconds(item["maximum_seconds"])
        attempt = item["attempt"]
        if attempt is None:
            continue
        attempt_id = identity(attempt["id"])
        if attempt_id in attempt_ids or attempt["state"] not in ATTEMPT_STATES:
            raise ValueError("first attempt identities must be unique with known states")
        attempt_ids.add(attempt_id)
        seconds(attempt["deadline"])
        money(attempt["reserved_cost"])
        observation_status = attempt.get("observation_status")
        if observation_status is not None and observation_status not in statuses:
            raise ValueError("first observation must have a known terminal status")
        if kind == "review" and (
            attempt["state"] in {"terminal", "terminated"} or observation_status is not None
        ):
            finished_reviews.setdefault(case, set()).add(variant)
    return finished_reviews


def admission_reason(item, settings, now, slots, exposure, finished_reviews):
    """Give the first applicable reason an otherwise queued unit cannot run now."""
    cost = money(item["maximum_cost"])
    duration = item["maximum_seconds"]
    if item["kind"] == "adjudication" and finished_reviews.get(item["case_id"]) != VARIANTS:
        return "pair-not-terminal"
    if not slots:
        return "no-free-slot"
    if cost > money(settings["session_spend_limit"]):
        return "session-spend-limit"
    if duration > settings["session_seconds"]:
        return "session-time-limit"
    if now + duration > settings["cutoff_seconds"]:
        return "comparison-cutoff"
    if exposure + cost > money(settings["spend_limit"]):
        return "shared-spend-limit"
    return None


def closing_updates(units):
    """Project closure statuses while preserving already frozen observations."""
    updates = []
    for item in units:
        attempt = item["attempt"]
        if attempt and (
            attempt["state"] in {"terminated", "terminal"} or attempt.get("observation_status")
        ):
            continue
        if item["kind"] == "adjudication":
            status = "incomplete"
        else:
            status = "timed out" if attempt else "not started"
        updates.append({
            "id": item["id"],
            "attempt_id": attempt["id"] if attempt else None,
            "status": status,
        })
    return updates


def evaluate(snapshot):
    """Evaluate candidates independently and project closure without mutating a ledger."""
    settings = snapshot["settings"]
    slots = seconds(settings["slots"])
    seconds(settings["session_seconds"])
    cutoff = seconds(settings["cutoff_seconds"])
    money(settings["session_spend_limit"])
    money(settings["spend_limit"])
    now = seconds(snapshot["elapsed_seconds"], minimum=0)
    exposure = money(snapshot["settled_cost"])
    units = snapshot["units"]
    if not isinstance(units, list):
        raise ValueError("units must be an ordered list")
    finished_reviews = index_units(units)

    attempts = [item["attempt"] for item in units if item["attempt"] is not None]
    occupied = [entry for entry in attempts if entry["state"] in {"active", "uncertain"}]
    uncertain = [
        entry["id"] for entry in occupied
        if entry["state"] == "uncertain" or entry["deadline"] <= now
    ]
    for entry in attempts:
        if entry["state"] != "terminal":
            exposure += money(entry["reserved_cost"])

    eligible, waiting = [], {}
    if now < cutoff:
        for item in units:
            if item["attempt"] is not None:
                continue
            reason = admission_reason(
                item, settings, now, max(0, slots - len(occupied)), exposure, finished_reviews
            )
            if reason:
                waiting[item["id"]] = reason
            else:
                eligible.append(item["id"])

    reconcilable = any(entry["state"] != "terminal" for entry in attempts)
    updates = closing_updates(units)
    close = now >= cutoff or not updates or (not eligible and not reconcilable)
    return {
        "eligible": eligible,
        "waiting": waiting,
        "occupied_slots": len(occupied),
        "uncertain_attempts": uncertain,
        "spend_exposure": money_text(exposure),
        "close": close,
        "terminal_updates": updates if close else [],
    }


def main():
    try:
        result = evaluate(json.load(sys.stdin))
    except (KeyError, TypeError, ValueError) as error:
        print(f"Invalid synthetic dispatch snapshot: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
