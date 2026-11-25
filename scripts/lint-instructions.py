#!/usr/bin/env python3
"""Check instruction sources and print path-qualified findings."""

import argparse
import json
from pathlib import Path
import re


RULE_FIELDS = ("description", "load")
WORKFLOW_FIELDS = ("description", "phase", "step")
PHASES = frozenset({
    "discovery", "execution", "validation", "atomic-execution", "atomic-validation",
    "finalization", "orchestrated", "entry", "utility",
})
LOADS = frozenset({"always", "on-demand"})
FIELD = re.compile(r"([a-z_]+):(?: (.*))?")
STEP = re.compile(r"[1-9][0-9]*(?:\.[1-9][0-9]*|[a-z])?")
COMMENT = re.compile(r"(?:^| )#")
FORBIDDEN_SEPARATORS = re.compile(r"[\x1c-\x1f]")
UNSUPPORTED_SCALAR_PREFIXES = ("'", "[", "{", "|", ">", "&", "*", "!", "%", "@", "`")
ALWAYS_ON_WORD_LIMIT = 1200


class InstructionLint:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[str] = []

    def report(self, code: str, path: Path, line: int, message: str) -> None:
        relative = path.relative_to(self.root).as_posix()
        self.findings.append(f"{code} {relative}:{line} {message}")

    def read_text(self, path: Path) -> str | None:
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            self.report("input-encoding", path, 0, "File must be valid UTF-8.")
            return None
        except OSError as error:
            self.report("input-encoding", path, 0, f"Cannot read input: {error.strerror}.")
            return None
        separator = FORBIDDEN_SEPARATORS.search(text)
        if separator is not None:
            line = text.count("\n", 0, separator.start()) + 1
            self.report("input-encoding", path, line, "Forbidden text separator U+001C–U+001F.")
            return None
        return text


def scalar(raw: str) -> str:
    if raw.startswith('"'):
        # An opening quote selects the JSON string grammar for the entire value.
        return json.loads(raw)
    if not raw or raw.startswith(UNSUPPORTED_SCALAR_PREFIXES) or COMMENT.search(raw):
        raise ValueError("Expected a plain value or a JSON string.")
    return raw


def field_is_valid(key: str, value: str, raw: str) -> bool:
    match key:
        case "description":
            return bool(value.strip()) and value.splitlines() == [value]
        case "load":
            return value in LOADS
        case "phase":
            return value in PHASES
        case "step":
            if raw.startswith('"'):
                return value == "-"
            return STEP.fullmatch(value) is not None
    return False


def check_metadata(lint: InstructionLint, path: Path, lines: list[str], fields: tuple[str, ...]) -> None:
    if lines[0] != "---":
        lint.report("metadata-syntax", path, 1, "Expected an opening front matter delimiter.")
        return
    try:
        end = lines.index("---", 1)
    except ValueError:
        lint.report("metadata-syntax", path, 0, "Missing closing front matter delimiter.")
        return

    seen: set[str] = set()
    for number, line in enumerate(lines[1:end], 2):
        if not line:
            continue
        field = FIELD.fullmatch(line)
        if field is None or "\t" in line:
            lint.report("metadata-syntax", path, number, "Expected a single column-zero key and value.")
            continue
        key, raw = field.groups()
        if key in seen:
            lint.report("metadata-duplicate-key", path, number, f"Repeated field {key}.")
            continue
        seen.add(key)
        if key == "trigger":
            lint.report("trigger-present", path, number, "The trigger field is obsolete.")
        elif key not in fields:
            lint.report("metadata-unknown-field", path, number, f"Unregistered field {key}.")
        else:
            try:
                raw = (raw or "").rstrip(" ")
                value = scalar(raw)
            except ValueError:
                lint.report("metadata-syntax", path, number, f"Malformed value for {key}.")
                continue
            if not field_is_valid(key, value, raw):
                lint.report("metadata-invalid-value", path, number, f"Invalid value for {key}.")

    for key in fields:
        if key not in seen:
            lint.report("metadata-missing-field", path, 0, f"Missing field {key}.")


def check_invocation(lint: InstructionLint, path: Path, lines: list[str]) -> None:
    invocations = [number for number, line in enumerate(lines, 1) if line.startswith("Invocation: ")]
    if not invocations:
        lint.report("invocation-missing", path, 0, "Expected one Invocation line.")
    for number in invocations[1:]:
        lint.report("invocation-duplicate", path, number, "Repeated Invocation line.")


def check_source_metadata(lint: InstructionLint) -> None:
    for directory, fields in (("rules", RULE_FIELDS), ("workflows", WORKFLOW_FIELDS)):
        for path in sorted((lint.root / directory).glob("*.md")):
            # This navigation reference remains under workflows until it moves to docs.
            if path == lint.root / "workflows" / "PIPELINE.md":
                continue
            text = lint.read_text(path)
            if text is None:
                continue
            lines = text.replace("\r\n", "\n").split("\n")
            check_metadata(lint, path, lines, fields)
            if directory == "workflows":
                check_invocation(lint, path, lines)


def check_always_on(lint: InstructionLint) -> None:
    for path in sorted((lint.root / "harness").glob("*/always-on.md")):
        body = lint.read_text(path)
        if body is None:
            continue
        capability_path = path.with_name("capabilities.md")
        if capability_path.exists():
            declaration = lint.read_text(capability_path)
            if declaration is not None:
                body = body.replace(declaration.rstrip("\n"), "", 1)
        count = len(body.split())
        if count > ALWAYS_ON_WORD_LIMIT:
            lint.report("always-on-size", path, 0, f"Body has {count} words (limit {ALWAYS_ON_WORD_LIMIT}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        next(args.root.iterdir(), None)
    except OSError as error:
        parser.error(f"unreadable root {args.root}: {error.strerror}")

    lint = InstructionLint(args.root)
    check_source_metadata(lint)
    check_always_on(lint)
    for finding in lint.findings:
        print(finding)
    return int(bool(lint.findings))


if __name__ == "__main__":
    raise SystemExit(main())
