#!/usr/bin/env python3
"""Check instruction sources and print path-qualified findings."""

import argparse
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import re
import stat


RULE_FIELDS = ("description", "load")
WORKFLOW_FIELDS = ("description", "phase", "step")
RULE_KINDS = frozenset({"bootstrap", "contract", "protocol", "procedure"})
SKILL_PREFIXES = {"rules": "rule-", "workflows": "", "principles": "principle-"}
BOOTSTRAP_HEADINGS = ["## Context Bootstrap", "## Phase Behaviors"]
BOOTSTRAP_WORD_LIMIT = 300
BOOTSTRAP_PHASES = (
    "discovery", "execution", "validation", "atomic-execution", "atomic-validation",
    "finalization",
)
PHASES = frozenset((*BOOTSTRAP_PHASES, "orchestrated", "entry", "utility"))
PHASE_CONTRACT = "rules/contract-phases.md"
RULE_REFERENCES_HEADING = "## Rule references"
RESOLUTION_LINE = "A reference to rule `<name>` resolves to skill `rule-<name>` on every supported harness."
OBSOLETE_RESOLUTION_PHRASE = "bare" + " basename"
LOADS = frozenset({"always", "on-demand"})
FIELD = re.compile(r"([a-z_]+):(?: (.*))?")
STEP = re.compile(r"[1-9][0-9]*(?:\.[1-9][0-9]*|[a-z])?")
COMMENT = re.compile(r"(?:^| )#")
FORBIDDEN_SEPARATORS = re.compile(r"[\x1c-\x1f]")
UNSUPPORTED_SCALAR_PREFIXES = ("'", "[", "{", "|", ">", "&", "*", "!", "%", "@", "`")
ALWAYS_ON_WORD_LIMIT = 1200
HARNESS_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DEPLOY_ENV_REQUIRED = frozenset({"skills_dir", "always_on_path"})
DEPLOY_ENV_FIELDS = DEPLOY_ENV_REQUIRED | {"project_skills_link_dir"}
DEPLOY_ENV_PATH = re.compile(r"[A-Za-z0-9._/-]+")
CAPABILITY_HEADING = "## Capability records"
CAPABILITY_NAME = re.compile(r"name: ([a-z0-9-]+)")
CAPABILITY_FIELD = re.compile(r"(state|runtime|verified|evidence): (.*)")
CAPABILITY_STATES = frozenset({"yes", "no", "unknown"})
CANONICAL_CAPABILITIES = (
    "sub-agents", "concurrent-sub-agents", "agent-messaging", "hooks", "worktrees", "git",
)
REQUIRED_BEHAVIOURS = {
    "Orchestrated run with Implementer, Validator and Arbiter workers": {"sub-agents", "agent-messaging", "git"},
    "Parallel children": {"worktrees", "concurrent-sub-agents"},
    "Devil's Advocate critic": {"sub-agents", "agent-messaging"},
    "Model-specific worker for a leaf": {"sub-agents"},
    "Hook-covered step logging": {"hooks"},
}
VERIFIED_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

INSTRUCTION_DIRECTORIES = ("rules", "workflows", "harness", "principles", "templates")
LEGACY_SCRIPTS = (
    "sync.sh", "setup-new-project.sh", "setup-all-repos.sh", "setup-umbrella.sh", "link-skills.sh",
)
LEGACY_NAME = re.compile(r"windsurf|codeium|\bdevin\b", re.IGNORECASE)
NAME_MAP = "docs/name-map.json"
USAGE = "docs/USAGE.md"
USAGE_HEADING = "## Renamed commands and rules"
REMOVED_HEADING = "## Removed integrations"
NAME_STEM = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REFERENCE_STEM = re.compile(r"[a-z0-9][a-z0-9-]*")
RESERVED_HEADER = re.compile(
    r"runtime: \S[^\r\n]*\n"
    r"verified: ([0-9]{4}-[0-9]{2}-[0-9]{2})\n"
    r"evidence: [A-Za-z][A-Za-z0-9+.-]*://[^\s/#?]+(?:[/?#]\S*)?\n\n"
)
MAP_PATH = re.compile(r"(rules|workflows|templates|harness|docs)(?:/[A-Za-z0-9_.-]+)+")
HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+|$)")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
BACKTICKS = re.compile(r"`+")
COMMENT_OR_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)|(?<!\\)<!--")
TABLE_PUNCTUATION = re.compile(r"\\.|\|")
BLOCK_CONTAINER = re.compile(r" {0,3}(?:>|(?:[*+-]|[0-9]{1,9}[.)])(?:[ \t]|$))")
THEMATIC_BREAK = re.compile(r" {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})")
HTML_BLOCK_START = re.compile(
    r" {0,3}<(?:!--|\?|![A-Z]|!\[CDATA\[|/?(?:"
    r"address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|"
    r"dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|"
    r"legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|pre|script|section|"
    r"source|style|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[ \t]|/?>|$))",
    re.IGNORECASE,
)
HTML_TAG_LINE = re.compile(r" {0,3}</?[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[^<>]*)?/?[ \t]*>[ \t]*")
COMMAND = re.compile(r"/([a-z0-9][a-z0-9-]*)(\.md)?(?: .*)?")
SECTION = re.compile(r"/?([a-z0-9][a-z0-9-]*)(\.md)? → (#{2,3} .+)")
NEXT_HEADING = re.compile(r" → (?=#{2,4} .)")
RULE_SKILL = re.compile(r"rule-([a-z0-9-]+)")
RULE_SUFFIX = re.compile(r" rules?\b")
REPOSITORY_PATH = re.compile(r"(?:rules|workflows|harness|templates)/[A-Za-z0-9_./-]+")
CHECK_DESCRIPTION = re.compile(r'(^[ \t]*check[ \t]+|(?<=[;&|])[ \t]*check[ \t]+)"(?:[^"\\]|\\.)*"')
MIGRATION_RECORD = "docs/audits/*-rule-migration-map.md"
FROZEN_FIXTURES = "tests/fixtures/validator-runtime/"
REFERENCE_EXCLUSIONS = frozenset({"scripts/check-lint-instructions.py", "scripts/check-deploy-skills.py"})
# Keep exact retired spellings out of the executable source scanned for them.
BARE_RULES = frozenset({
    "workflow" + "-globals", "workflow" + "-reference",
    *(f"phase-{phase}" for phase in (
        "discovery", "execution", "validation", "atomic-execution", "atomic-validation", "finalize",
    )),
})
BARE_FILES = frozenset({"global" + "-claude", "codex-global" + "-AGENTS"})


@dataclass(frozen=True)
class NameRow:
    kind: str
    old: str
    new: tuple[str, ...]


class InstructionLint:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.resolved_root = root.resolve()
        self.findings: list[str] = []
        self.information: list[str] = []
        self.inputs: dict[tuple[Path, bool], str | None] = {}

    def report(self, code: str, path: Path, line: int, message: str) -> None:
        relative = path.relative_to(self.root).as_posix()
        self.findings.append(f"{code} {relative}:{line} {message}")

    def read_text(self, path: Path, error_code: str = "input-encoding", *, regular: bool = False) -> str | None:
        if not regular and (path, True) in self.inputs:
            return self.inputs[path, True]
        key = (path, regular)
        if key not in self.inputs:
            self.inputs[key] = self.read_input(path, error_code, regular=regular)
        return self.inputs[key]

    def read_input(self, path: Path, error_code: str, *, regular: bool) -> str | None:
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(self.resolved_root):
                self.report(error_code, path, 0, "Input points outside the source tree.")
                return None
            data = read_regular_bytes(path) if regular else resolved.read_bytes()
            if data is None:
                self.report(error_code, path, 0, "Expected a regular file.")
                return None
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            line = data.count(b"\n", 0, error.start) + 1 if error_code == "deploy-env-invalid" else 0
            self.report(error_code, path, line, "File must be valid UTF-8.")
            return None
        except OSError as error:
            self.report(error_code, path, 0, f"Cannot read input: {error.strerror}.")
            return None
        except RuntimeError:
            self.report(error_code, path, 0, "Cannot resolve input path.")
            return None
        separator = FORBIDDEN_SEPARATORS.search(text)
        if separator is not None:
            line = text.count("\n", 0, separator.start()) + 1
            self.report(error_code, path, line, "Forbidden text separator U+001C–U+001F.")
            return None
        return text


def read_regular_bytes(path: Path) -> bytes | None:
    if not stat.S_ISREG(path.lstat().st_mode):
        return None
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            return None
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(descriptor)


def outside_fences(lines: Iterable[str]) -> Iterator[tuple[int, str]]:
    fence = ""
    for number, line in enumerate(lines, 1):
        marker = FENCE.fullmatch(line)
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
        elif marker and (marker[1][0] == "~" or "`" not in marker[2]):
            fence = marker[1]
        else:
            yield number, line


def strip_markdown_comments(lines: list[str]) -> list[str]:
    visible = []
    fence = ""
    in_comment = False
    for line in lines:
        marker = FENCE.fullmatch(line)
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
        elif not in_comment and marker and (marker[1][0] == "~" or "`" not in marker[2]):
            fence = marker[1]
        elif in_comment or "<!--" in line:
            line, in_comment = strip_comment_line(line, in_comment)
        visible.append(line)
    return visible


def strip_comment_line(line: str, in_comment: bool) -> tuple[str, bool]:
    visible = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            close = line.find("-->", cursor)
            if close == -1:
                break
            cursor = close + 3
            in_comment = False
            continue

        match = COMMENT_OR_CODE.search(line, cursor)
        if match is None:
            visible.append(line[cursor:])
            break
        in_comment = match[1] is None
        visible.append(line[cursor:match.start() if in_comment else match.end()])
        cursor = match.end()
    return "".join(visible), in_comment


def markdown_sections(lines: list[str], heading: str) -> Iterator[tuple[int, int]]:
    start = None
    level = len(heading.split(maxsplit=1)[0])
    for number, line in outside_fences(lines):
        marker = HEADING.match(line)
        if marker and len(marker[1]) <= level and start is not None:
            yield start, number
            start = None
        if line == heading:
            start = number
    if start is not None:
        yield start, len(lines) + 1


def input_lines(text: str) -> list[str]:
    return text.replace("\r\n", "\n").split("\n")


def safe_parts(value: str) -> bool:
    return not {"", ".", ".."}.intersection(value.split("/"))


def source_paths(root: Path, patterns: Iterable[str]) -> Iterator[Path]:
    root_path = root.resolve()
    for path in sorted({path for pattern in patterns for path in root.glob(pattern)}):
        if ("__pycache__" not in path.relative_to(root).parts and path.is_file()
                and path.resolve().is_relative_to(root_path)):
            yield path


def installed_source_paths(root: Path, directories: Iterable[str]) -> Iterator[Path]:
    for path in source_paths(root, (f"{directory}/*.md" for directory in directories)):
        if not path.is_symlink():
            yield path


def check_legacy_mentions(lint: InstructionLint) -> None:
    patterns = [f"{directory}/**/*" for directory in INSTRUCTION_DIRECTORIES]
    patterns.extend(f"scripts/{name}" for name in LEGACY_SCRIPTS)
    patterns.extend(("CLAUDE.md", USAGE))
    for path in source_paths(lint.root, patterns):
        text = lint.read_text(path)
        if text is None:
            continue
        lines = input_lines(text)
        excluded = list(markdown_sections(lines, REMOVED_HEADING)) if path == lint.root / USAGE else []
        for number, line in enumerate(lines, 1):
            if any(start <= number < end for start, end in excluded):
                continue
            for mention in LEGACY_NAME.finditer(line):
                lint.report("legacy-mention", path, number, f"Legacy integration mention: {mention[0]}.")


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Repeated JSON key {key!r}.")
        result[key] = value
    return result


def parse_name_map(text: str) -> list[NameRow]:
    data = json.loads(text, object_pairs_hook=unique_object)
    if (not isinstance(data, dict) or set(data) != {"schema_version", "rows"}
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or not isinstance(data["rows"], list)):
        raise ValueError("Expected schema_version 1 and a rows list.")
    rows = []
    old_names: set[str] = set()
    targets: set[str] = set()
    previous: tuple[str, str] | None = None
    for index, row in enumerate(data["rows"], 1):
        if not isinstance(row, dict) or set(row) != {"kind", "old", "new"}:
            raise ValueError(f"Row {index} must contain exactly kind, old and new.")
        kind, old, new = row["kind"], row["old"], row["new"]
        if (kind not in ("rule", "workflow", "file") or not isinstance(new, list)
                or not new or (kind != "rule" and len(new) != 1)):
            raise ValueError(f"Row {index} has an invalid kind or target count.")
        pattern = MAP_PATH if kind == "file" else NAME_STEM
        if any(not isinstance(value, str) or not pattern.fullmatch(value) or not safe_parts(value)
               for value in (old, *new)):
            raise ValueError(f"Row {index} contains an invalid name or path.")
        identity = (kind, old)
        if previous is not None and previous >= identity:
            raise ValueError(f"Row {index} repeats an identity or is out of order.")
        if len(set(new)) != len(new) or targets.intersection(new):
            raise ValueError(f"Row {index} repeats a target.")
        rows.append(NameRow(kind, old, tuple(new)))
        previous = identity
        old_names.add(old)
        targets.update(new)
    if old_names.intersection(targets):
        raise ValueError("A target is also listed as an old name.")
    return rows


def read_name_map(lint: InstructionLint) -> list[NameRow] | None:
    path = lint.root / NAME_MAP
    if not path.exists() and not path.is_symlink():
        return None
    text = lint.read_text(path)
    if text is None:
        return None
    try:
        return parse_name_map(text)
    except (ValueError, RecursionError) as error:
        lint.report("name-map-invalid", path, 0, str(error).split("\n", 1)[0])
        return None


def table_cells(line: str, *, optional_outer_pipes: bool = False) -> list[str]:
    line = line.strip()
    if not optional_outer_pipes:
        if not (line.startswith("|") and line.endswith("|")):
            return []
        return [cell.strip() for cell in re.split(r"(?<!\\)\|", line[1:-1])]

    pipes = [match.start() for match in TABLE_PUNCTUATION.finditer(line) if match[0] == "|"]
    if not pipes:
        return []
    bounds = [-1, *pipes, len(line)]
    if pipes[0] == 0:
        bounds.pop(0)
    if pipes[-1] == len(line) - 1:
        bounds.pop()
    return [line[start + 1:end].strip() for start, end in zip(bounds, bounds[1:])]


def is_table_divider(line: str, columns: int, *, optional_outer_pipes: bool = False) -> bool:
    cells = table_cells(line, optional_outer_pipes=optional_outer_pipes)
    pattern = r":?-+:?" if optional_outer_pipes else r":?-{3,}:?"
    return len(cells) == columns and all(re.fullmatch(pattern, cell) for cell in cells)


def starts_markdown_block(line: str) -> bool:
    return bool(HEADING.match(line) or BLOCK_CONTAINER.match(line) or THEMATIC_BREAK.fullmatch(line)
                or HTML_BLOCK_START.match(line) or HTML_TAG_LINE.fullmatch(line)
                or re.match(r"(?: {4}| {0,3}\t)", line))


def table_rows(
    lines: list[str], start: int, end: int, header: list[str], *, raw_phase_lines: list[str] | None = None,
) -> list[list[str]] | None:
    visible = {number: line for number, line in outside_fences(lines)}
    headers = [number for number in range(start + 1, end) if table_cells(visible.get(number, "")) == header]
    if len(headers) != 1:
        return None
    if raw_phase_lines is not None and raw_phase_lines[headers[0] - 1] != f"| {' | '.join(header)} |":
        return None
    phase_table = raw_phase_lines is not None
    number = headers[0] + 1
    if number >= end or not is_table_divider(visible.get(number, ""), len(header),
                                            optional_outer_pipes=phase_table):
        return None
    rows = []
    for number in range(number + 1, end):
        line = visible.get(number, "")
        if not line.strip() or (phase_table and starts_markdown_block(line)):
            break
        cells = table_cells(line, optional_outer_pipes=phase_table)
        if not cells:
            if not phase_table:
                break
            cells = [line.strip()]
        rows.append(cells)
    return rows


def check_usage_map(lint: InstructionLint, rows: list[NameRow]) -> None:
    path = lint.root / USAGE
    text = lint.read_text(path) if path.exists() or path.is_symlink() else None
    lines = input_lines(text) if text is not None else []
    sections = list(markdown_sections(lines, USAGE_HEADING))
    actual = table_rows(lines, *sections[0], ["Kind", "Old", "New"]) if len(sections) == 1 else None
    expected = [[row.kind, f"`{row.old}`", ", ".join(f"`{name}`" for name in row.new)] for row in rows]
    if actual != expected:
        line = sections[0][0] if sections else 0
        lint.report("usage-map-mismatch", path, line, "The renamed names table must match the name map in order.")


def inline_references(line: str) -> Iterator[tuple[str, str]]:
    ticks = list(BACKTICKS.finditer(line))
    following: dict[int, int] = {}
    next_tick: dict[int, int] = {}
    for i in range(len(ticks) - 1, -1, -1):
        length = len(ticks[i][0])
        if length in following:
            next_tick[i] = following[length]
        following[length] = i

    i = 0
    while i < len(ticks):
        opening = ticks[i]
        preceding = opening.start()
        while preceding and line[preceding - 1] == "\\":
            preceding -= 1
        if (opening.start() - preceding) % 2 or i not in next_tick:
            i += 1
            continue
        i = next_tick[i]
        if opening[0] == "`":
            yield line[opening.end():ticks[i].start()], line[ticks[i].end():]
        i += 1


def headings_in_order(reference: str, headings: list[str]) -> bool:
    target = iter(headings)
    return all(any(line == heading or line.startswith(heading + " — ") for line in target)
               for heading in NEXT_HEADING.split(reference))


def reference_findings(
    lint: InstructionLint, span: str, after: str, rules: dict[str, list[str]], workflows: dict[str, list[str]],
) -> Iterator[tuple[str, str]]:
    if " → " in span:
        section = SECTION.fullmatch(span)
        if section is None:
            return
        stem, suffix, headings = section.groups()
        targets = [sources[stem] for sources in (rules, workflows) if stem in sources]
        if suffix:
            if not targets:
                return
            yield "reference-md-suffix", f"Use {stem} without the .md suffix."
        if not targets:
            yield "reference-missing", f"Instruction {stem} does not exist."
        elif not any(headings_in_order(headings, target) for target in targets):
            yield "heading-missing", f"Could not find {headings} in order in {stem}."
        return

    command = COMMAND.fullmatch(span)
    if command:
        stem, suffix = command.groups()
        if suffix:
            yield "reference-md-suffix", f"Use /{stem} without the .md suffix."
        if stem not in workflows:
            yield "reference-missing", f"Workflow {stem} does not exist."
        return

    skill = RULE_SKILL.fullmatch(span)
    if skill or (REFERENCE_STEM.fullmatch(span) and RULE_SUFFIX.match(after)):
        stem = skill[1] if skill else span
        if stem not in rules:
            yield "reference-missing", f"Rule {stem} does not exist."
    elif REPOSITORY_PATH.fullmatch(span):
        target = lint.root / span
        if (not safe_parts(span) or not target.exists()
                or not target.resolve().is_relative_to(lint.resolved_root)):
            yield "reference-missing", f"Path {span} does not exist in the source tree."


def check_executable_references(lint: InstructionLint) -> dict[Path, list[str]]:
    sources = {
        path: input_lines(text)
        for path in source_paths(lint.root, ("harness/*/always-on.md",))
        if (text := lint.read_text(path)) is not None
    }
    instruction_lines = {
        path: input_lines(text)
        for path in installed_source_paths(lint.root, ("rules", "workflows"))
        if (text := lint.read_text(path, regular=True)) is not None
    }
    sources.update(instruction_lines)
    visible = {path: list(outside_fences(lines)) for path, lines in sources.items()}

    def by_stem(directory: str) -> dict[str, list[str]]:
        return {path.stem: [line for _, line in lines if HEADING.match(line)]
                for path, lines in visible.items() if path.parent == lint.root / directory}

    rules, workflows = by_stem("rules"), by_stem("workflows")
    for path, lines in visible.items():
        for number, line in lines:
            for span, after in inline_references(line):
                for code, message in reference_findings(lint, span, after, rules, workflows):
                    lint.report(code, path, number, message)
    return instruction_lines


def whole_token(pattern: str) -> str:
    return rf"(?<![A-Za-z0-9_-])(?:{pattern})(?![A-Za-z0-9_-])"


def stale_pattern(row: NameRow) -> re.Pattern[str]:
    old = re.escape(row.old)
    quoted_forms = []
    if row.kind == "workflow":
        forms = [rf"workflows/{old}\.md", rf"/{old}", rf"{old}\.md", old]
    elif row.kind == "rule":
        forms = [rf"rule-{old}", rf"rules/{old}\.md", rf"{old}\.md"]
        quoted_forms = [rf"`{old}`(?= rules?\b)", rf"`{old} → "]
        if row.old in BARE_RULES:
            forms.append(old)
    else:
        forms = [old]
        stem = Path(row.old).stem
        if stem in BARE_FILES:
            forms.extend((rf"{re.escape(stem)}\.md", re.escape(stem)))
    return re.compile("|".join([whole_token("|".join(forms)), *quoted_forms]))


def successor_paths(row: NameRow) -> re.Pattern[str]:
    paths = row.new if row.kind == "file" else tuple(f"{row.kind}s/{value}.md" for value in row.new)
    return re.compile(whole_token("|".join(re.escape(path) for path in paths)))


def read_migration_record(lint: InstructionLint) -> list[str]:
    records = list(source_paths(lint.root, (MIGRATION_RECORD,)))
    if len(records) != 1:
        if records:
            lint.report("semantics-record-ambiguous", records[0], 0, "Expected at most one migration record.")
        return []
    text = lint.read_text(records[0])
    return input_lines(text) if text is not None else []


def migration_table(lines: list[str], heading: str, header: list[str]) -> list[list[str]]:
    sections = list(markdown_sections(lines, heading))
    entries = table_rows(lines, *sections[0], header) if len(sections) == 1 else None
    return entries or []


def retained_names(lines: list[str]) -> set[tuple[str, str]]:
    retained = set()
    for entry in migration_table(lines, "## Retained old names", ["Path", "Line text", "Reason"]):
        if len(entry) != 3 or not entry[2]:
            continue
        path, line = (unquote_record_cell(cell) for cell in entry[:2])
        retained.add((path, line))
    return retained


def unquote_record_cell(cell: str) -> str:
    quoted = re.fullmatch(r"(`+)(.+?)\1", cell)
    if quoted:
        cell = quoted[2]
        if cell.startswith(" ") and cell.endswith(" ") and cell.strip():
            cell = cell[1:-1]
    return cell.replace(r"\|", "|")


def check_active_references(lint: InstructionLint, rows: list[NameRow], retained: set[tuple[str, str]]) -> int:
    names = [(row.old, stale_pattern(row), successor_paths(row)) for row in rows]
    patterns = [f"{directory}/**/*" for directory in (*INSTRUCTION_DIRECTORIES, "hooks", "scripts", "tests")]
    patterns.extend(("CLAUDE.md", "README.md", "docs/*.md", ".ai/principles/*.md", ".ai/context/*.md",
                     ".ai/memory/architecture.md"))
    anchor_count = 0
    for path in source_paths(lint.root, patterns):
        relative = path.relative_to(lint.root).as_posix()
        if relative in REFERENCE_EXCLUSIONS or relative.startswith(FROZEN_FIXTURES):
            continue
        text = lint.read_text(path)
        if text is None:
            continue
        lines = input_lines(text)
        excluded = list(markdown_sections(lines, USAGE_HEADING)) if relative == USAGE else []
        contract_lines = strip_markdown_comments(lines) if path.suffix == ".md" else None
        for number, line in enumerate(lines, 1):
            if any(start <= number < end for start, end in excluded):
                continue
            original_line = line
            if relative == "scripts/validate-contracts.sh":
                if line.lstrip().startswith("#"):
                    continue
                line = CHECK_DESCRIPTION.sub(r"\1", line)
            contract_line = contract_lines[number - 1] if contract_lines is not None else line
            if original_line == contract_line == RESOLUTION_LINE:
                anchor_count += 1
            if OBSOLETE_RESOLUTION_PHRASE in line.casefold():
                lint.report("resolution-rule-missing", path, number, "Obsolete wording in a rule reference.")
            if "rules file" in contract_line.casefold() and number < len(lines):
                cells = table_cells(contract_line, optional_outer_pipes=True)
                divider = (contract_lines if contract_lines is not None else lines)[number]
                if (any(unquote_record_cell(cell).lstrip(" `*_").casefold().startswith("rules file") for cell in cells)
                        and is_table_divider(divider, len(cells), optional_outer_pipes=True)):
                    lint.report("resolution-rule-missing", path, number, "Obsolete rule reference column.")
            if (relative, original_line) not in retained:
                stale = sorted({old for old, pattern, allowed in names if pattern.search(allowed.sub(" ", line))})
                if stale:
                    lint.report("stale-name", path, number, f"Stale names: {', '.join(stale)}.")
    return anchor_count


def phase_section(lines: list[str], heading: str) -> tuple[int, int]:
    sections = list(markdown_sections(lines, heading))
    return sections[0] if len(sections) == 1 else (0, 0)


def check_bootstrap_table(
    lint: InstructionLint, path: Path, lines: list[str], raw_lines: list[str], rule_names: set[str],
) -> None:
    start, end = phase_section(lines, BOOTSTRAP_HEADINGS[0])
    rows = table_rows(lines, start, end, ["Phase", "Skill", "Loaded by"], raw_phase_lines=raw_lines)
    expected = {(phase.replace("-", " ").title(), f"`rule-bootstrap-{phase}`") for phase in BOOTSTRAP_PHASES}
    skills = {f"bootstrap-{phase}" for phase in BOOTSTRAP_PHASES}
    if (rows is None or len(rows) != len(expected) or not skills <= rule_names
            or {(row[0], row[1]) for row in rows if len(row) == 3 and row[2]} != expected):
        lint.report("bootstrap-table-invalid", path, start, "Expected one row for each phase and its bootstrap skill.")


def table_names(cell: str) -> set[str]:
    return {unquote_record_cell(name.strip()) for name in cell.split(",")}


def check_behaviour_table(
    lint: InstructionLint, path: Path, lines: list[str], raw_lines: list[str], workflow_names: set[str],
    declared_keys: set[str],
) -> None:
    code = "capability-behaviour-table-invalid"
    start, end = phase_section(lines, "## Capabilities")
    rows = table_rows(lines, start, end, ["Behaviour", "Workflow", "Requires", "Without it"], raw_phase_lines=raw_lines)
    if rows is None:
        lint.report(code, path, start, "Expected the capability behaviour table.")
        return

    seen: set[str] = set()
    for cells in rows:
        if len(cells) != 4 or not all(cells):
            lint.report(code, path, start, "Every behaviour must name workflows, capabilities and a fallback.")
            continue
        behaviour, workflow_cell, requires_cell, _ = cells
        workflows, required = table_names(workflow_cell), table_names(requires_cell)
        expected = REQUIRED_BEHAVIOURS.get(behaviour)
        if (behaviour in seen or not workflows <= workflow_names or not required <= declared_keys
                or (expected is not None and required != expected)):
            lint.report(code, path, start, f"Invalid capability behaviour row: {behaviour}.")
        seen.add(behaviour)
    missing = set(REQUIRED_BEHAVIOURS) - seen
    if missing:
        lint.report(code, path, start, f"Missing required behaviours: {', '.join(sorted(missing))}.")


def check_phase_contract(
    lint: InstructionLint, instructions: dict[Path, list[str]], anchor_count: int, adapter_keys: list[set[str]],
) -> None:
    path = lint.root / PHASE_CONTRACT
    raw_lines = instructions.get(path, [])
    lines = strip_markdown_comments(raw_lines)
    start, end = phase_section(lines, RULE_REFERENCES_HEADING)
    anchor_in_section = any(
        start < number < end and raw_lines[number - 1] == line == RESOLUTION_LINE
        for number, line in outside_fences(lines)
    )
    if anchor_count != 1 or not anchor_in_section:
        lint.report("resolution-rule-missing", path, start, "Expected one canonical rule-reference line.")

    rules = {file.stem for file in instructions if file.parent == lint.root / "rules"}
    workflows = {file.stem for file in instructions
                 if file.parent == lint.root / "workflows" and NAME_STEM.fullmatch(file.stem)}
    shared = set.intersection(*adapter_keys) if adapter_keys else set()
    check_bootstrap_table(lint, path, lines, raw_lines, rules)
    check_behaviour_table(lint, path, lines, raw_lines, workflows, shared.union(CANONICAL_CAPABILITIES))


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


def check_metadata(lint: InstructionLint, path: Path, lines: list[str], fields: tuple[str, ...]) -> int | None:
    if lines[0] != "---":
        lint.report("metadata-syntax", path, 1, "Expected an opening front matter delimiter.")
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        lint.report("metadata-syntax", path, 0, "Missing closing front matter delimiter.")
        return None

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
    return end + 1


def check_invocation(lint: InstructionLint, path: Path, lines: list[str]) -> None:
    invocations = [number for number, line in enumerate(lines, 1) if line.startswith("Invocation: ")]
    if not invocations:
        lint.report("invocation-missing", path, 0, "Expected one Invocation line.")
    for number in invocations[1:]:
        lint.report("invocation-duplicate", path, number, "Repeated Invocation line.")


def bootstrap_size_exceptions(lines: list[str]) -> dict[str, int | None]:
    counts: dict[str, int | None] = {}
    for entry in migration_table(lines, "## Bootstrap size exceptions", ["Rule", "Words", "Reason"]):
        if len(entry) != 3:
            continue
        name = unquote_record_cell(entry[0])
        if name.startswith("rules/") and name.endswith(".md"):
            name = name.removeprefix("rules/").removesuffix(".md")
        if not name.startswith("bootstrap-") or NAME_STEM.fullmatch(name) is None:
            continue
        count, reason = entry[1:]
        try:
            allowed = int(count) if re.fullmatch(r"[1-9][0-9]*", count) else 0
        except ValueError:
            allowed = 0
        counts[name] = allowed if allowed > BOOTSTRAP_WORD_LIMIT and reason and name not in counts else None
    return counts


def check_bootstrap(
    lint: InstructionLint, path: Path, text: str, body: list[str], exception_count: int | None,
) -> None:
    headings = [
        (len(marker[1]), line) for _, line in outside_fences(body)
        if (marker := HEADING.match(line)) and len(marker[1]) <= 2
    ]
    if headings and headings[0][0] == 1:
        headings = headings[1:]
    if [line for _, line in headings] != BOOTSTRAP_HEADINGS:
        lint.report("bootstrap-sections", path, 0, "Expected Context Bootstrap then Phase Behaviors as the only sections.")
    count = len(text.split())
    if exception_count is not None and count != exception_count:
        lint.report("bootstrap-size", path, 0, f"Expected the audited count of {exception_count} words, found {count}.")
    elif exception_count is None and count > BOOTSTRAP_WORD_LIMIT:
        lint.report("bootstrap-size", path, 0, f"Expected at most {BOOTSTRAP_WORD_LIMIT} words, found {count}.")


def check_installed_names(lint: InstructionLint) -> None:
    rules = {path.stem: path for path in installed_source_paths(lint.root, ("rules",))}
    for path in installed_source_paths(lint.root, ("workflows",)):
        if rule := rules.get(path.stem):
            lint.report("name-collision", path, 0, f"Stem {path.stem} is also used by {rule.relative_to(lint.root)}.")

    installed: dict[str, Path] = {}
    for path in installed_source_paths(lint.root, SKILL_PREFIXES):
        name = SKILL_PREFIXES[path.parent.name] + path.stem
        identity = name.casefold()
        previous = installed.setdefault(identity, path)
        if previous != path:
            lint.report(
                "installed-name-collision", path, 0,
                f"Installed name {name} collides with the name from {previous.relative_to(lint.root)}.",
            )


def check_source_metadata(lint: InstructionLint, exceptions: dict[str, int | None]) -> None:
    for directory, fields in (("rules", RULE_FIELDS), ("workflows", WORKFLOW_FIELDS)):
        for path in sorted((lint.root / directory).glob("*.md")):
            # This navigation reference remains under workflows until it moves to docs.
            if path == lint.root / "workflows" / "PIPELINE.md":
                continue
            if path.is_dir() and not path.is_symlink():
                continue
            kind, _, subject = path.stem.partition("-")
            valid_kind = kind in RULE_KINDS and bool(subject) and NAME_STEM.fullmatch(path.stem) is not None
            if directory == "rules" and not valid_kind:
                lint.report("kind-prefix-invalid", path, 0, "Expected a rule kind and a hyphenated subject.")
            text = lint.read_text(path, regular=True)
            if text is None:
                continue
            lines = input_lines(text)
            body_start = check_metadata(lint, path, lines, fields)
            if directory == "workflows":
                check_invocation(lint, path, lines)
            elif kind == "bootstrap" and valid_kind and body_start is not None:
                check_bootstrap(lint, path, text, lines[body_start:], exceptions.get(path.stem))


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
) -> tuple[str | None, bool]:
    fields: dict[str, str] = {}
    valid = True
    for number, line in enumerate(lines, record_line + 1):
        field = CAPABILITY_FIELD.fullmatch(line)
        if field is None:
            lint.report("capability-schema", path, number, "Expected a capability field.")
            valid = False
            continue
        key, value = field.groups()
        if key != "evidence" and key in fields:
            lint.report("capability-schema", path, number, f"Repeated capability field {key}.")
            valid = False
            continue
        fields[key] = value
        if not valid_capability_field(key, value):
            lint.report("capability-schema", path, number, f"Invalid capability field {key}.")
            valid = False

    state = fields.get("state")
    required = ("state", "runtime", "verified", "evidence") if state in {"yes", "no"} else ("state",)
    for key in required:
        if key not in fields:
            lint.report("capability-schema", path, record_line, f"Missing capability field {key}.")
            valid = False
    return state, valid


def check_capability_records(
    lint: InstructionLint, path: Path, lines: list[str], start: int, end: int,
) -> tuple[dict[str, tuple[int, str | None]], set[str]]:
    records: dict[str, tuple[int, str | None]] = {}
    valid_names: set[str] = set()
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
        state, valid = check_capability_fields(lint, path, record_line, lines[fields_start:fields_end])
        if name in records:
            lint.report("capability-schema", path, record_line, f"Repeated capability {name}.")
            valid_names.discard(name)
        else:
            records[name] = (record_line, state)
            if valid:
                valid_names.add(name)
        if name in CANONICAL_CAPABILITIES:
            following_line = lines[index] if index < end else ""
            limitations = following_line.removeprefix("Limitations: ")
            if following_line == limitations or not limitations.strip():
                lint.report("capability-schema", path, record_line, f"Missing limitations for {name}.")
    return records, valid_names


def check_capabilities(lint: InstructionLint, path: Path, declaration: str, always_on_path: str) -> set[str]:
    lines = declaration.replace("\r\n", "\n").split("\n")
    headings = [index for index, line in enumerate(lines) if line == CAPABILITY_HEADING]
    if not headings:
        lint.report("capability-schema", path, 0, "Missing Capability records section.")
    for index in headings[1:]:
        lint.report("capability-schema", path, index + 1, "Repeated Capability records section.")
    heading = headings[0] if headings else len(lines)
    start = heading + 1
    end = next((index for index in range(start, len(lines)) if lines[index].startswith(("# ", "## "))), len(lines))
    records, valid_names = check_capability_records(lint, path, lines, start, end)
    canonical_order = [name for name in CANONICAL_CAPABILITIES if name in records]
    for name in CANONICAL_CAPABILITIES:
        if name not in records:
            lint.report("capability-key-missing", path, 0, f"Missing canonical capability {name}.")
    if [name for name in records if name in CANONICAL_CAPABILITIES] != canonical_order:
        lint.report("capability-schema", path, start, "Canonical capabilities are out of order.")

    locations = [(index, line) for index, line in enumerate(lines) if line.startswith("always-on-path:")]
    if len(locations) != 1:
        lint.report("always-on-path-mismatch", path, 0, "Expected one always-on-path line.")
    else:
        index, line = locations[0]
        label, _, value = line.partition(": ")
        if not (start <= index < end and label == "always-on-path" and value == always_on_path):
            lint.report("always-on-path-mismatch", path, index + 1, "Location must match deploy.env.")

    if "hooks" in records:
        number, state = records["hooks"]
        legacy_hooks = [line for line in lines[:heading] if line.startswith("hooks:")]
        if state not in {"yes", "no"} or legacy_hooks != [f"hooks: {state}"]:
            lint.report("hooks-state-mismatch", path, number, "Hooks state must match the existing hooks line.")
    return valid_names if len(headings) == 1 else set()


def check_always_on(lint: InstructionLint, path: Path, body: str, declaration: str | None) -> None:
    if declaration is not None:
        body = body.replace(declaration.rstrip("\n"), "", 1)
    count = len(body.split())
    if count > ALWAYS_ON_WORD_LIMIT:
        lint.report("always-on-size", path, 0, f"Body has {count} words (limit {ALWAYS_ON_WORD_LIMIT}).")


def read_deploy_env(lint: InstructionLint, path: Path) -> dict[str, str] | None:
    text = lint.read_text(path, "deploy-env-invalid")
    if text is None:
        return None

    entries: dict[str, str] = {}
    for number, line in enumerate(text.split("\n"), 1):
        if "\r" in line or "\0" in line:
            lint.report("deploy-env-invalid", path, number, "Invalid character in adapter declaration.")
            return None
        if not line or line.startswith("#"):
            continue
        key, equals, value = line.partition("=")
        required = key in DEPLOY_ENV_REQUIRED
        relative = value.removeprefix("$HOME/") if required else value
        if (not equals or key not in DEPLOY_ENV_FIELDS or key in entries
                or (required and not value.startswith("$HOME/"))
                or not DEPLOY_ENV_PATH.fullmatch(relative) or not safe_parts(relative)):
            lint.report("deploy-env-invalid", path, number, "Invalid adapter assignment.")
            return None
        entries[key] = value

    missing = DEPLOY_ENV_REQUIRED - entries.keys()
    if missing:
        lint.report("deploy-env-invalid", path, 0, f"Missing required keys: {', '.join(sorted(missing))}.")
        return None
    return entries


def check_reserved_names(lint: InstructionLint, directory: Path, commands: set[str]) -> None:
    path = directory / "reserved-names.txt"
    if not path.exists() and not path.is_symlink():
        lint.information.append(f"info reserved-names-absent {directory.name}")
        return
    text = lint.read_text(path, regular=True)
    if text is None:
        return
    text = text.replace("\r\n", "\n")
    header = RESERVED_HEADER.match(text)
    if header is None or not valid_capability_field("verified", header[1]):
        return
    entries = [
        (number, name)
        for number, name in enumerate(text[header.end():].removesuffix("\n").split("\n"), 5)
        if name and not name.startswith("#")
    ]
    if any(REFERENCE_STEM.fullmatch(name) is None for _, name in entries):
        return
    for number, name in entries:
        if name in commands:
            lint.report(
                "reserved-name-collision", path, number,
                f"Workflow {name} is reserved by {directory.name}. Use orchestrail-{name} in the name map.",
            )


def check_harness_instructions(lint: InstructionLint, commands: set[str]) -> list[set[str]]:
    adapter_keys: list[set[str]] = []
    for directory in sorted((lint.root / "harness").glob("*")):
        if not HARNESS_NAME.fullmatch(directory.name) or directory.is_symlink() or not directory.is_dir():
            continue
        body_path = directory / "always-on.md"
        capability_path = directory / "capabilities.md"
        deploy_path = directory / "deploy.env"
        if not any(path.exists() or path.is_symlink() for path in (deploy_path, capability_path)):
            continue
        missing = [path for path in (deploy_path, capability_path, body_path)
                   if path.is_symlink() or not path.is_file()]
        if missing:
            for path in missing:
                lint.report("adapter-incomplete", path, 0, "Expected a regular adapter file.")
            adapter_keys.append(set())
            continue

        check_reserved_names(lint, directory, commands)
        deployment = read_deploy_env(lint, deploy_path)
        declaration = lint.read_text(capability_path)
        body = lint.read_text(body_path)
        if body is not None:
            check_always_on(lint, body_path, body, declaration)
        if deployment is not None and declaration is not None:
            adapter_keys.append(check_capabilities(lint, capability_path, declaration, deployment["always_on_path"]))
        else:
            adapter_keys.append(set())
    return adapter_keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        next(args.root.iterdir(), None)
    except OSError as error:
        parser.error(f"unreadable root {args.root}: {error.strerror}")

    lint = InstructionLint(args.root)
    record = read_migration_record(lint)
    rows = read_name_map(lint)
    commands = {name for row in rows or [] if row.kind == "workflow" for name in row.new}
    check_source_metadata(lint, bootstrap_size_exceptions(record))
    check_installed_names(lint)
    adapter_keys = check_harness_instructions(lint, commands)
    check_legacy_mentions(lint)
    instructions = check_executable_references(lint)
    if rows is not None:
        check_usage_map(lint, rows)
    anchor_count = check_active_references(lint, rows or [], retained_names(record))
    check_phase_contract(lint, instructions, anchor_count, adapter_keys)
    for line in (*lint.findings, *lint.information):
        print(line)
    return int(bool(lint.findings))


if __name__ == "__main__":
    raise SystemExit(main())
