"""Read a synthetic packet and submit one report inside the fixture boundary."""

import hashlib
import json
from pathlib import Path
import sys


def run(packet_path, output, variant, private_paths):
    delivered = packet_path.read_bytes()
    packet = json.loads(delivered)
    denied = []
    for path in private_paths:
        try:
            Path(path).read_bytes()
        except PermissionError:
            denied.append(path)
    missing_label = not packet["tested_tree"]["widget.txt"].startswith("Label:")
    findings = []
    report = {
        "case_id": packet["case_id"],
        "packet_digest": hashlib.sha256(delivered).hexdigest(),
        "observed_design": packet["task_design"],
        "denied_paths": denied,
        "findings": findings,
    }
    if variant == "treatment":
        report["coverage"] = {
            "due": [{
                "criterion": "show-label",
                "status": "violated" if missing_label else "satisfied",
                "evidence": "widget.txt:1",
            }],
            "future": ["suggest-label"],
        }
        if missing_label:
            findings.append({"finding_id": "claim-01", "anchor": "widget.txt:1"})
    (output / "report.json").write_text(json.dumps(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    packet, output, variant, *private_paths = sys.argv[1:]
    print(json.dumps(run(Path(packet), Path(output), variant, private_paths)))
