"""Prepare one offline review case from a JSON record on stdin."""

import argparse
import hashlib
import json
import sys
from typing import Any


PACKET_FIELDS = (
    "case_id",
    "composition",
    "base_tree",
    "tested_tree",
    "diff",
    "tests",
    "owned_paths",
    "task_design",
    "upstream_contract",
    "review_instructions",
    "specification",
    "assignment",
)
COMPOSITION_FIELDS = {
    "pr": ("kind", "target", "base", "head"),
    "milestone": ("kind", "target", "base", "integrated_tree", "constituents"),
}


def digest(value: Any) -> str:
    """Hash the canonical JSON value shared by the two review variants."""
    data = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def populated_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def project_packet(raw: dict[str, Any]) -> dict[str, Any]:
    """Select fields for a packet whose content the coordinator has sanitized."""
    packet = {field: raw[field] for field in PACKET_FIELDS}
    for field in ("base_tree", "tested_tree"):
        tree = packet[field]
        if not isinstance(tree, dict) or any(
            not populated_string(path) or not isinstance(content, str)
            for path, content in tree.items()
        ):
            raise ValueError(f"missing readable tree: {field}")

    composition = packet["composition"]
    kind = composition["kind"]
    packet["composition"] = {field: composition[field] for field in COMPOSITION_FIELDS[kind]}
    composition = packet["composition"]
    for field in ("target", "base", "head" if kind == "pr" else "integrated_tree"):
        if not populated_string(composition[field]):
            raise ValueError(f"missing composition identity: {field}")
    if kind == "milestone":
        constituents = composition["constituents"]
        if (
            not isinstance(constituents, list)
            or not constituents
            or not all(populated_string(item) for item in constituents)
        ):
            raise ValueError("missing milestone constituent revisions")

    spec = packet["specification"]
    if not populated_string(spec["content"]) or not isinstance(spec["annexes"], list):
        raise ValueError("missing specification contents or annex inventory")
    if any(
        not populated_string(annex["name"]) or not isinstance(annex["content"], str)
        for annex in spec["annexes"]
    ):
        raise ValueError("missing annex name or contents")
    packet["specification"] = {
        "content": spec["content"],
        "annexes": [{"name": annex["name"], "content": annex["content"]} for annex in spec["annexes"]],
    }
    assignment = packet["assignment"]
    if not populated_string(assignment["version"]) or any(
        not isinstance(assignment[field], list) for field in ("due", "future")
    ):
        raise ValueError("missing assignment version or coverage roster")
    packet["assignment"] = {field: assignment[field] for field in ("version", "due", "future")}
    return packet


def prepare_case(source: dict[str, Any], *, historical: bool = False) -> dict[str, Any]:
    """Project and pin an eligible case, or report the reason for exclusion."""
    raw_packet = source["packet"]
    case_id = raw_packet["case_id"]
    if not populated_string(case_id):
        raise ValueError("missing opaque case identity")
    coordinator = source.get("coordinator")
    approvals = coordinator.get("approvals") if isinstance(coordinator, dict) else None

    def exclude(reason: str) -> dict[str, Any]:
        return {"status": "excluded", "case_id": case_id, "reason": reason}

    approval_fields = () if historical else ("specification", "assignment")
    for field in approval_fields:
        approval = approvals.get(field) if isinstance(approvals, dict) else None
        if not isinstance(approval, dict) or not populated_string(approval.get("reference")):
            return exclude(f"missing-{field}-approval")
        if approval.get("digest") != digest(raw_packet.get(field)):
            return exclude(f"{field}-approval-digest-mismatch")

    try:
        packet = project_packet(raw_packet)
    except (ValueError, TypeError, KeyError):
        return exclude("incomplete-packet")

    for field in approval_fields:
        if digest(packet[field]) != approvals[field]["digest"]:
            return exclude(f"{field}-approval-digest-mismatch")

    pinned_digest = digest(packet)
    return {
        "status": "admitted",
        "case_id": case_id,
        "packet": packet,
        "variant_packet_digests": dict.fromkeys(("baseline", "treatment"), pinned_digest),
        "content_digests": {
            "specification": digest(packet["specification"]),
            "assignment": digest(packet["assignment"]),
            "annexes": [
                {"name": item["name"], "digest": digest(item)}
                for item in packet["specification"]["annexes"]
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", action="store_true", help="pin reconstructed historical inputs")
    args = parser.parse_args()
    try:
        result = prepare_case(json.load(sys.stdin), historical=args.historical)
    except (ValueError, TypeError, KeyError):
        print("Expected one coordinator record with a case identity.", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
