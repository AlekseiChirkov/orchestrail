#!/usr/bin/env python3
"""Check instruction sources and print path-qualified findings."""

import argparse
from datetime import date
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
HARNESS_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CAPABILITY_HEADING = "## Capability records"
CAPABILITY_NAME = re.compile(r"name: ([a-z0-9-]+)")
CAPABILITY_FIELD = re.compile(r"(state|runtime|verified|evidence): (.*)")
CAPABILITY_STATES = frozenset({"yes", "no", "unknown"})
CANONICAL_CAPABILITIES = (
    "sub-agents", "concurrent-sub-agents", "agent-messaging", "hooks", "worktrees", "git",
)
VERIFIED_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


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


def valid_capability_field(key: str, value: str) -> bool:
    if key == "state":
        return value in CAPABILITY_STATES
    if key == "runtime":
        return bool(value.strip())
    if key == "evidence":
        return re.fullmatch(r"\S+", value) is not None
    if VERIFIED_DATE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def check_capability_fields(
    lint: InstructionLint, path: Path, record_line: int, lines: list[str],
) -> str | None:
    fields: dict[str, str] = {}
    for number, line in enumerate(lines, record_line + 1):
        field = CAPABILITY_FIELD.fullmatch(line)
        if field is None:
            lint.report("capability-schema", path, number, "Expected a capability field.")
            continue
        key, value = field.groups()
        if key != "evidence" and key in fields:
            lint.report("capability-schema", path, number, f"Repeated capability field {key}.")
            continue
        fields[key] = value
        if not valid_capability_field(key, value):
            lint.report("capability-schema", path, number, f"Invalid capability field {key}.")

    state = fields.get("state")
    required = ("state", "runtime", "verified", "evidence") if state in {"yes", "no"} else ("state",)
    for key in required:
        if key not in fields:
            lint.report("capability-schema", path, record_line, f"Missing capability field {key}.")
    return state


def check_capability_records(
    lint: InstructionLint, path: Path, lines: list[str], start: int, end: int,
) -> dict[str, tuple[int, str | None]]:
    records: dict[str, tuple[int, str | None]] = {}
    index = start
    while index < end:
        title = lines[index]
        index += 1
        if not title.startswith("name:"):
            continue
        record_line = index
        fields_start = index
        while index < end and lines[index]:
            index += 1
        fields_end = index
        while index < end and not lines[index]:
            index += 1

        match = CAPABILITY_NAME.fullmatch(title)
        if match is None or match[1] == "always-on-path":
            lint.report("capability-schema", path, record_line, "Invalid capability name.")
            continue
        name = match[1]
        state = check_capability_fields(lint, path, record_line, lines[fields_start:fields_end])
        if name in records:
            lint.report("capability-schema", path, record_line, f"Repeated capability {name}.")
        else:
            records[name] = (record_line, state)
        if name in CANONICAL_CAPABILITIES:
            following_line = lines[index] if index < end else ""
            limitations = following_line.removeprefix("Limitations: ")
            if following_line == limitations or not limitations.strip():
                lint.report("capability-schema", path, record_line, f"Missing limitations for {name}.")
    return records


def check_capabilities(lint: InstructionLint, path: Path, declaration: str, deploy_env: str) -> None:
    lines = declaration.replace("\r\n", "\n").split("\n")
    headings = [index for index, line in enumerate(lines) if line == CAPABILITY_HEADING]
    if not headings:
        lint.report("capability-schema", path, 0, "Missing Capability records section.")
    for index in headings[1:]:
        lint.report("capability-schema", path, index + 1, "Repeated Capability records section.")
    heading = headings[0] if headings else len(lines)
    start = heading + 1
    end = next((index for index in range(start, len(lines)) if lines[index].startswith(("# ", "## "))), len(lines))
    records = check_capability_records(lint, path, lines, start, end)
    canonical_order = [name for name in CANONICAL_CAPABILITIES if name in records]
    for name in CANONICAL_CAPABILITIES:
        if name not in records:
            lint.report("capability-key-missing", path, 0, f"Missing canonical capability {name}.")
    if [name for name in records if name in CANONICAL_CAPABILITIES] != canonical_order:
        lint.report("capability-schema", path, start, "Canonical capabilities are out of order.")

    locations = [(index, line) for index, line in enumerate(lines) if line.startswith("always-on-path:")]
    declared_paths = [line.removeprefix("always_on_path=") for line in deploy_env.split("\n")
                      if line.startswith("always_on_path=")]
    if len(locations) != 1:
        lint.report("always-on-path-mismatch", path, 0, "Expected one always-on-path line.")
    else:
        index, line = locations[0]
        label, _, value = line.partition(": ")
        if not (start <= index < end and label == "always-on-path" and value and declared_paths == [value]):
            lint.report("always-on-path-mismatch", path, index + 1, "Location must match deploy.env.")

    if "hooks" in records:
        number, state = records["hooks"]
        legacy_hooks = [line for line in lines[:heading] if line.startswith("hooks:")]
        if state not in {"yes", "no"} or legacy_hooks != [f"hooks: {state}"]:
            lint.report("hooks-state-mismatch", path, number, "Hooks state must match the existing hooks line.")


def check_always_on(lint: InstructionLint, path: Path, body: str, declaration: str | None) -> None:
    if declaration is not None:
        body = body.replace(declaration.rstrip("\n"), "", 1)
    count = len(body.split())
    if count > ALWAYS_ON_WORD_LIMIT:
        lint.report("always-on-size", path, 0, f"Body has {count} words (limit {ALWAYS_ON_WORD_LIMIT}).")


def check_harness_instructions(lint: InstructionLint) -> None:
    for directory in sorted((lint.root / "harness").glob("*")):
        body_path = directory / "always-on.md"
        capability_path = directory / "capabilities.md"
        deploy_path = directory / "deploy.env"
        body = lint.read_text(body_path) if body_path.exists() or body_path.is_symlink() else None
        has_deploy = HARNESS_NAME.fullmatch(directory.name) is not None and deploy_path.exists()
        declaration = None
        if (body is not None or has_deploy) and (capability_path.exists() or capability_path.is_symlink()):
            declaration = lint.read_text(capability_path)
        if body is not None:
            check_always_on(lint, body_path, body, declaration)
        if has_deploy and declaration is not None:
            deploy_env = lint.read_text(deploy_path)
            if deploy_env is not None:
                check_capabilities(lint, capability_path, declaration, deploy_env)


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
    check_harness_instructions(lint)
    for finding in lint.findings:
        print(finding)
    return int(bool(lint.findings))


if __name__ == "__main__":
    raise SystemExit(main())
