"""Exercise paired review contracts on controlled local fixtures."""

import argparse
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Iterator


TERMINAL = {"completed", "partial", "failed", "timed out", "invalid", "not started"}
OBSERVATION_FIELDS = (
    "case_id", "packet_digest", "variant", "attempt_id", "status", "elapsed_seconds",
    "settled_cost", "reason",
)
REPORT_NAME = "first-report"
OBSERVATION_NAME = "first-observation.json"


def isolated_probe(packet: Path, output: Path, probe: Path, arguments: list[str]) -> dict:
    """Run a trusted Python fixture probe under a deny-by-default Landlock rule set."""
    setpriv = shutil.which("setpriv")
    if setpriv is None:
        raise ValueError("setpriv with Landlock support is required for the isolation fixture")
    executable = Path(sys.executable).resolve(strict=True)
    packet, output, probe = (path.resolve(strict=True) for path in (packet, output, probe))
    if not packet.is_file() or not probe.is_file() or not output.is_dir():
        raise ValueError("expected packet and probe files and a separate writable output directory")
    if packet.is_relative_to(output) or probe.is_relative_to(output):
        raise ValueError("packet and trusted probe must be outside the writable output directory")
    libraries = {
        candidate.resolve()
        for candidate in (Path("/usr/lib"), Path(sys.base_prefix) / "lib")
        if candidate.is_dir()
    }
    if any(output.is_relative_to(path) or path.is_relative_to(output) for path in libraries):
        raise ValueError("output directory must be separate from runtime libraries")
    command = [setpriv, "--no-new-privs", "--landlock-access", "fs"]
    permissions = [
        ("execute,read-file", executable),
        ("read-file", packet),
        ("read-file", probe),
        ("read-file,read-dir,write-file,make-reg,truncate", output),
        *(("execute,read-file,read-dir", path) for path in sorted(libraries)),
    ]
    for access, path in permissions:
        command.extend(("--landlock-rule", f"path-beneath:{access}:{path}"))
    command.extend((str(executable), "-IB", str(probe), str(packet), str(output), *arguments))
    result = subprocess.run(
        command,
        cwd=output,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={"LANG": "C.UTF-8"},
    )
    if result.returncode:
        raise ValueError(f"isolated fixture probe failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def read_regular_file(path: Path) -> bytes:
    """Read a submitted regular file without following a symbolic link or opening a FIFO."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("submission must be a regular file")
        return stream.read()


@contextmanager
def locked_archive(directory: Path) -> Iterator[None]:
    if not directory.is_dir():
        raise ValueError("coordinator must create a private observation directory first")
    with (directory / "observation.lock").open("ab") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def write_archive_file(path: Path, content: bytes) -> None:
    """Publish complete bytes in the private coordinator directory."""
    stage = None
    try:
        with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stage = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(stage, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)


def report_digest(directory: Path) -> str | None:
    report = directory / REPORT_NAME
    return hashlib.sha256(read_regular_file(report)).hexdigest() if report.exists() else None


def freeze(directory: Path, submission: Path) -> dict:
    with locked_archive(directory):
        terminal = directory / OBSERVATION_NAME
        if terminal.exists():
            return {"report_digest": json.loads(terminal.read_bytes())["report_digest"]}
        if not (directory / REPORT_NAME).exists():
            write_archive_file(directory / REPORT_NAME, read_regular_file(submission))
        return {"report_digest": report_digest(directory)}


def populated_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def terminal_record(value: Any, *, historical: bool = False) -> dict:
    if not isinstance(value, dict) or any(field not in value for field in OBSERVATION_FIELDS):
        raise ValueError("terminal observation is missing required fields")
    record = {field: value[field] for field in OBSERVATION_FIELDS}
    if not populated_string(record["case_id"]):
        raise ValueError("case ID must be populated")
    digest = record["packet_digest"]
    if not isinstance(digest, str) or len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError("packet digest must be a lowercase SHA-256 digest")
    if record["variant"] not in ("baseline", "treatment") or record["status"] not in TERMINAL:
        raise ValueError("expected a known variant and terminal observation status")
    attempt = record["attempt_id"]
    if not populated_string(attempt) and not (record["status"] == "not started" and attempt is None):
        raise ValueError("attempt ID must be populated for a launched review")
    elapsed = record["elapsed_seconds"]
    if record["status"] == "not started":
        if elapsed is not None:
            raise ValueError("a review that was not started has no elapsed time")
    elif not (historical and elapsed is None) and (
        type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0
    ):
        raise ValueError("elapsed seconds must be a finite nonnegative number")
    if record["status"] != "completed" and not populated_string(record["reason"]):
        raise ValueError("an incomplete observation requires a reason")
    cost = record["settled_cost"]
    if cost is not None:
        try:
            decimal = Decimal(cost) if isinstance(cost, str) else None
        except InvalidOperation:
            decimal = None
        if decimal is None or not decimal.is_finite() or decimal < 0:
            raise ValueError("settled cost must be a nonnegative decimal string or null")
    return record


def capture(directory: Path, observation: Any, *, historical: bool = False) -> dict:
    with locked_archive(directory):
        terminal = directory / OBSERVATION_NAME
        if terminal.exists():
            return json.loads(terminal.read_bytes())
        record = terminal_record(observation, historical=historical)
        record["report_digest"] = report_digest(directory)
        if record["status"] == "not started" and record["report_digest"] is not None:
            raise ValueError("a review that was not started cannot have a frozen report")
        write_archive_file(terminal, json.dumps(record, ensure_ascii=False).encode("utf-8"))
        return record


def roster(values: Any) -> set[str]:
    if not isinstance(values, list) or not all(populated_string(item) for item in values):
        raise ValueError("a criterion roster must be a list of populated identifiers")
    if len(set(values)) != len(values):
        raise ValueError("a criterion roster must not contain duplicates")
    return set(values)


def validate_coverage(value: Any) -> dict:
    try:
        assignment, coverage = value["assignment"], value["coverage"]
        due, future = roster(assignment["due"]), roster(assignment["future"])
        if due & future or roster(coverage["future"]) != future:
            raise ValueError("future roster must match the approved separate future scope")
        rows = coverage["due"]
        if not isinstance(rows, list) or roster([row["criterion"] for row in rows]) != due:
            raise ValueError("each approved due criterion requires exactly one disposition")
        for row in rows:
            status = row["status"]
            if status == "undetermined" and populated_string(row.get("gap")):
                continue
            if status in ("satisfied", "violated") and populated_string(row.get("evidence")):
                continue
            raise ValueError(f"criterion {row['criterion']} requires a disposition with evidence or a gap")
    except (KeyError, TypeError, ValueError) as error:
        return {"status": "invalid", "reason": str(error)}
    return {"status": "valid", "due_count": len(rows), "coverage": coverage}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    isolate = modes.add_parser("isolate")
    isolate.add_argument("packet", type=Path)
    isolate.add_argument("output", type=Path)
    isolate.add_argument("probe", type=Path)
    isolate.add_argument("arguments", nargs=argparse.REMAINDER)
    freeze_parser = modes.add_parser("freeze")
    freeze_parser.add_argument("archive", type=Path)
    freeze_parser.add_argument("submission", type=Path)
    capture_parser = modes.add_parser("capture")
    capture_parser.add_argument("archive", type=Path)
    capture_parser.add_argument("--historical", action="store_true", help="preserve unknown elapsed time")
    modes.add_parser("coverage")
    args = parser.parse_args()
    try:
        match args.mode:
            case "isolate":
                result = isolated_probe(args.packet, args.output, args.probe, args.arguments)
            case "freeze":
                result = freeze(args.archive, args.submission)
            case "capture":
                result = capture(args.archive, json.load(sys.stdin), historical=args.historical)
            case "coverage":
                result = validate_coverage(json.load(sys.stdin))
    except (OSError, TypeError, ValueError, OverflowError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
