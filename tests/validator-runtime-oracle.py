#!/usr/bin/env python3
"""Contracts for the frozen validator inventory and measurement manifest."""

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validator_runtime_oracle", ROOT / "tests/fixtures/validator-runtime/oracle.py")
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)

# Fingerprint the immutable compressed inventory before parsing it.
FROZEN_INVENTORY_SHA256 = "57f7872d3525f608b57b29410792e2e02106542f28456f806319e2e7065557a1"


AMENDMENT_SHA256 = "99e49fe3f792a3b094230783e5cf9ec7d929a152879f1fff085ef59aa85db04e"
APPROVED_PATHS = frozenset({
    "scripts/model-catalog.py", "scripts/model_selection.py", "tests/model-plan.py",
    "tests/usage-observation-bundle-schema.py", "tests/usage-status-large-authority.py",
    "tests/usage-status-large-parts.py", "tests/usage-status-parts-cli.py",
    "tests/usage-bounded-source-reads.py", "tests/usage-usage-publication.py",
    "tests/usage-usage-receipt-schema.py", "tests/model-selection.py",
    "tests/model-workflow.py", "tests/log-step-hook.sh",
    "tests/usage-duration-analysis.py", "tests/usage-lifecycle-projection-token-scalars.py",
    "tests/usage-cumulative-epochs.py", "tests/usage-resolution-measurement-finality.py",
    "tests/git-rails.sh", "tests/hook-install.sh", "tests/hook-shell-quality.sh",
    "tests/usage-inventory-schema.py", "tests/usage-resolution-epochs.py",
    "tests/usage-status-integration.py", "tests/usage-stream-revisions.py",
    "tests/usage-warning-delivery-boundary.py", "tests/usage-analysis-corpus-schema.py",
    "tests/usage-current-run-snapshot-schema.py", "tests/usage-lifecycle-projection-schema.py",
    "tests/usage-resolution-evidence.py", "tests/usage-source-selection.py",
    "tests/usage-status-input-schema.py",
})


# The one approved extension of the frozen inventory, by name: the state tool contract
# results, its acceptance result, focused mode and resource row. Each entry is inserted
# directly after its anchor; any other addition, rename or omission is rejected.
ADDED_NAMES = {
    "results": [
        "RECEIPTS: workflow-globals defines state_receipts: on one anchored line and keeps blocks without it valid",
        "RECEIPTS: the Protected Sections Contract protects state_receipts: lines",
        "RECEIPTS: the state tool vocabulary constants equal the anchored status lines",
        "test_state_tool_acceptance",
    ],
    "expressions": ["test_state_tool_acceptance"],
    "focused": ["--state-tool-only"],
    "resources": ["test_state_tool_acceptance"],
}
ADDED_RESOURCE_PATHS = frozenset({"scripts/state-tool.py", "tests/state-tool.py"})
ADDED_ANCHORS_SHA256 = "5d4655f1e170686d5dd0a57674ee59ae4202332355a478fc158b40d03c534227"
CONTRACT_REQUIREMENTS = frozenset({
    "REQ-05", "REQ-06", "REQ-09", "REQ-10", "REQ-11", "REQ-12", "REQ-14", "REQ-15",
    "REQ-23", "REQ-36", "REQ-55", "REQ-66",
})
BASE_AMENDMENT_FIELDS = {"schema", "paths", "removed_results", "resources", "added"}
AMENDMENT_FIELDS = {
    1: BASE_AMENDMENT_FIELDS,
    2: BASE_AMENDMENT_FIELDS | {"name_map_sha256", "path_changes", "contract_changes"},
}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MAP_PATH = re.compile(r"(?:rules|workflows|templates|harness|docs)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*")
GENERIC_PATH = re.compile(r"(?:rules|workflows|principles|harness|templates|docs)/[A-Za-z0-9_./-]+")
REPOSITORY_PATH = re.compile(
    r"(?<![A-Za-z0-9_./-])(?:(?:\$[A-Za-z_][A-Za-z0-9_]*|\$\{[A-Za-z_][A-Za-z0-9_]*\}|\.)/)?"
    r"(?:(?:rules|workflows|principles|harness|templates|docs|scripts|tests|"
    r"hooks|\.ai|\.github|\.agents|\.claude|\.codex)/[A-Za-z0-9_./-]+|"
    r"(?:AGENTS\.md|CLAUDE\.md|README\.md|deploy\.env))(?![A-Za-z0-9_./-])"
)
HELPER_CALL = re.compile(r"\$\([ \t]*(?!echo\b)[A-Za-z_][A-Za-z0-9_]*\b")
RESULT_EXPRESSION = re.compile(r'^check "((?:\\.|[^"\\\n])+)"[ \t]+(?:\\\n[ \t]*)?([^\n]+)', re.M)
CHECK_LABEL = re.compile(r'^[ \t]*check[ \t]+"((?:\\.|[^"\\\n])+)"', re.M)


def json_object(pairs: list) -> dict:
    values = dict(pairs)
    if len(values) != len(pairs):
        raise ValueError("Duplicate JSON field")
    return values


def amendment_schema(amendment: dict) -> int:
    schema = amendment.get("schema") if isinstance(amendment, dict) else None
    if type(schema) is not int or set(amendment) != AMENDMENT_FIELDS.get(schema):
        raise ValueError("Invalid amendment fields")
    return schema


def load_name_map(path: Path, digest: str | None) -> list:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        if digest is not None:
            raise ValueError("Pinned name map is missing") from None
        return []
    except OSError as error:
        raise ValueError("Cannot read pinned name map") from error
    if digest != hashlib.sha256(data).hexdigest():
        raise ValueError("Name map digest differs")
    document = json.loads(data, object_pairs_hook=json_object)
    if (not isinstance(document, dict) or set(document) != {"schema_version", "rows"}
            or type(document["schema_version"]) is not int or document["schema_version"] != 1
            or not isinstance(document["rows"], list)):
        raise ValueError("Invalid name map")
    rows = document["rows"]
    identities, old_names, new_names = [], set(), set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"kind", "old", "new"}:
            raise ValueError("Invalid name map row")
        kind, old, new = row["kind"], row["old"], row["new"]
        if (kind not in ("rule", "workflow", "file") or not isinstance(new, list)
                or not new or (kind != "rule" and len(new) != 1)):
            raise ValueError("Invalid name map kind or targets")
        pattern = MAP_PATH if kind == "file" else SLUG
        if any(not isinstance(value, str) or not pattern.fullmatch(value) for value in [old, *new]):
            raise ValueError("Invalid name map token")
        if len(set(new)) != len(new) or new_names.intersection(new):
            raise ValueError("Repeated name map target")
        identities.append((kind, old))
        old_names.add(old)
        new_names.update(new)
    if identities != sorted(set(identities)) or old_names & new_names:
        raise ValueError("Repeated, overlapping or unsorted name map rows")
    return rows


def mask_replacements(rows: list) -> tuple[dict, dict]:
    """Build equivalence classes over shared tokens, keeping path kinds distinct."""
    classes = []
    for row in rows:
        kind = row["kind"]
        tokens = {row["old"], *row["new"]}
        if kind == "file":
            paths, names = {path: "F" for path in tokens}, set()
        else:
            directory, marker = ("rules", "R") if kind == "rule" else ("workflows", "W")
            paths = {f"{directory}/{name}.md": marker for name in tokens}
            names = tokens | {f"rule-{name}" for name in tokens} if kind == "rule" else tokens
        shared = set(paths) | names
        separate = []
        for group_paths, group_names in classes:
            if shared.intersection(set(group_paths) | group_names):
                paths = {**group_paths, **paths}
                paths.update({path: "F" for path, marker in group_paths.items() if marker == "F"})
                names |= group_names
            else:
                separate.append((group_paths, group_names))
        classes = [*separate, (paths, names)]
    return (
        {path: f"<{marker} {index}>" for index, (paths, _) in enumerate(classes)
         for path, marker in paths.items()},
        {name: f"<N {index}>" for index, (_, names) in enumerate(classes) for name in names},
    )


def token_pattern(replacements: dict) -> re.Pattern | None:
    if not replacements:
        return None
    alternatives = "|".join(map(re.escape, sorted(replacements, key=lambda token: (-len(token), token))))
    return re.compile(r"(?<![A-Za-z0-9_-])(?:" + alternatives + r")(?![A-Za-z0-9_-])")


def validate_replacements(amendment: dict, root: Path) -> list:
    paths, names = mask_replacements(load_name_map(root / "docs/name-map.json", amendment["name_map_sha256"]))
    path_pattern, name_pattern = token_pattern(paths), token_pattern(names)

    def mask(value: str) -> str:
        if path_pattern is not None:
            value = path_pattern.sub(lambda match: paths[match.group()], value)
        value = GENERIC_PATH.sub("<PATH>", value)
        if name_pattern is not None:
            value = name_pattern.sub(lambda match: names[match.group()], value)
        return value

    replacements, seen = [], set()
    for section in ("path_changes", "contract_changes"):
        contract = section == "contract_changes"
        fields = {"target", "key", "before", "after"} | ({"requirement", "reason"} if contract else set())
        entries = amendment[section]
        if not isinstance(entries, list):
            raise ValueError("Invalid source amendment list")
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != fields:
                raise ValueError("Invalid source amendment fields")
            target, key, before, after = (entry[field] for field in ("target", "key", "before", "after"))
            valid_key = (type(key) is int and 0 <= key < 94 if target == "nonstandard"
                         else isinstance(key, str) and bool(key))
            if (target not in ("result", "body", "nonstandard") or not valid_key
                    or not all(isinstance(value, str) and value for value in (before, after)) or before == after):
                raise ValueError("Invalid source amendment target or text")
            if (target, key) in seen:
                raise ValueError("Repeated source amendment target")
            seen.add((target, key))
            if contract:
                requirement, reason = entry["requirement"], entry["reason"]
                if (not isinstance(requirement, str) or requirement not in CONTRACT_REQUIREMENTS
                        or not isinstance(reason, str) or not reason.strip() or reason.splitlines() != [reason]
                        or after.strip() in ("pass", "$(echo pass)") or "echo pass" not in after
                        or not (REPOSITORY_PATH.search(after) or HELPER_CALL.search(after))):
                    raise ValueError("Invalid contract change")
            elif mask(before) != mask(after):
                raise ValueError("Source change exceeds the path and name mask")
            replacements.append(entry)
    return replacements


def reconstruct_source(source: str, replacements: list) -> str:
    labels = CHECK_LABEL.findall(source)
    for entry in replacements:
        after = entry["after"]
        position = source.find(after)
        if position < 0 or source.find(after, position + 1) >= 0:
            raise ValueError("Source amendment text is missing or repeated")
        source = source[:position] + entry["before"] + source[position + len(after):]

    if CHECK_LABEL.findall(source) != labels:
        raise ValueError("Source amendment changes a check description")
    results = RESULT_EXPRESSION.findall(source)
    nonstandard = [line for line in source.splitlines()
                   if re.search(r"\bcheck\b", line) and not line.startswith('check "')]
    for entry in replacements:
        target, key = entry["target"], entry["key"]
        if target == "result":
            matches = [expression for name, expression in results if name == key]
        elif target == "body":
            pattern = r"^" + re.escape(key) + r"\(\)[ \t]+(?:\{\n.*?^\}$|\(\n.*?^\)$)"
            matches = re.findall(pattern, source, re.M | re.S)
        else:
            matches = nonstandard[key:key + 1]
        if matches != [entry["before"]]:
            raise ValueError("Source amendment key differs from the reconstructed text")
    return source


def add_named_entries(amended: dict, added: dict) -> None:
    """Insert exactly the approved named entries into the amended inventory in place."""
    if not isinstance(added, dict) or set(added) != set(ADDED_NAMES):
        raise ValueError("Invalid amendment additions")
    for section, names in ADDED_NAMES.items():
        key = "flag" if section == "focused" else "name"
        items, target = added[section], amended[section]
        if (not isinstance(items, list)
                or any(not isinstance(item, dict) or set(item) != {"after", "value"}
                       or not isinstance(item["value"], dict) or set(item["value"]) != set(target[0])
                       for item in items)
                or [item["value"][key] for item in items] != names):
            raise ValueError("Unexpected added entries")
        for item in items:
            if any(entry[key] == item["value"][key] for entry in target):
                raise ValueError("Added entry already exists")
            anchors = [index for index, entry in enumerate(target)
                       if (entry if section == "results" else entry[key]) == item["after"]]
            if len(anchors) != 1:
                raise ValueError("Added entry anchor is missing or repeated")
            target.insert(anchors[0] + 1, copy.deepcopy(item["value"]))
    # A different existing anchor could reorder the approved registrations.
    anchors = {section: [item["after"] for item in items] for section, items in added.items()}
    encoded_anchors = json.dumps(anchors, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded_anchors).hexdigest() != ADDED_ANCHORS_SHA256:
        raise ValueError("Approved addition anchors differ")
    name = ADDED_NAMES["expressions"][0]
    result = next(entry for entry in amended["results"] if entry["name"] == name)
    expression = next(entry for entry in amended["expressions"] if entry["name"] == name)
    if result["expression"] != expression["expression"]:
        raise ValueError("Added acceptance expression differs")
    row = next(entry for entry in amended["resources"] if entry["name"] == name)
    paths = {item["path"] for item in row["source_references"] + row["dynamic_dependencies"]}
    paths |= {item["path"] for values in row["observations"].values() for item in values}
    paths |= {path for item in row["dynamic_dependencies"]
              for field in ("target_candidates", "callsite_candidates") for path in item.get(field, [])}
    if not paths or not paths <= ADDED_RESOURCE_PATHS:
        raise ValueError("Added resource path is not approved")


def apply_amendment(frozen: dict, amendment: dict) -> dict:
    """Apply exact approved test-resource changes to a copy of the frozen inventory."""
    if amendment_schema(amendment) == 2:
        validate_replacements(amendment, ROOT)
    if amendment["paths"] != sorted(APPROVED_PATHS):
        raise ValueError("Invalid amendment scope")
    amended = copy.deepcopy(frozen)
    removed_results = amendment["removed_results"]
    expected_names = ["pd-analyze references architecture.md",
                      "SAFETY: git-flow defines the Enforcement vocabulary on one anchored line"]
    if (not isinstance(removed_results, list) or any(not isinstance(item, dict) for item in removed_results)
            or [item.get("name") for item in removed_results] != expected_names):
        raise ValueError("Unexpected removed results")
    for removed in removed_results:
        if amended["results"].count(removed) != 1:
            raise ValueError("Unexpected removed result")
        amended["results"].remove(removed)
    names = [row["name"] for row in amended["resources"]]
    touched = set()
    patches = amendment["resources"]
    if not isinstance(patches, list):
        raise ValueError("Invalid amendment resources")
    for patch in patches:
        if (not isinstance(patch, dict) or set(patch) != {"name", "changes"}
                or names.count(patch["name"]) != 1 or patch["name"] in touched
                or not isinstance(patch["changes"], list)):
            raise ValueError("Invalid amendment resource")
        touched.add(patch["name"])
        row = amended["resources"][names.index(patch["name"])]
        seen = set()
        for change in patch["changes"]:
            if not isinstance(change, dict):
                raise ValueError("Invalid resource change")
            field, path = change.get("field"), change.get("path")
            kind = change.get("kind")
            fields = {"field", "path", "before", "after"} | ({"kind"} if field == "observations" else set())
            key = (field, kind, path)
            if (set(change) != fields or not isinstance(field, str) or not isinstance(path, str)
                    or (kind is not None and not isinstance(kind, str)) or path not in APPROVED_PATHS or key in seen):
                raise ValueError("Invalid resource change")
            seen.add(key)
            if field == "observations" and kind in row["observations"]:
                items = row["observations"][kind]
            elif field in {"source_references", "dynamic_dependencies"} and kind is None:
                items = row[field]
            else:
                raise ValueError("Invalid resource field")
            before, after = change["before"], change["after"]
            if (not isinstance(before, list) or not isinstance(after, list)
                    or any(not isinstance(item, dict) or item.get("path") != path
                           or type(item.get("line", 0)) is not int for item in before + after)):
                raise ValueError("Resource path differs")
            if [item for item in items if item["path"] == path] != before:
                raise ValueError("Frozen resource differs")
            items[:] = sorted([item for item in items if item["path"] != path] + copy.deepcopy(after),
                              key=lambda item: (item["path"], item.get("line", 0)))
    add_named_entries(amended, amendment["added"])
    return amended


def load_pinned_amendment(path: Path) -> dict:
    data = path.with_name("inventory-amendment.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != AMENDMENT_SHA256:
        raise ValueError("Inventory amendment digest differs")
    return json.loads(data, object_pairs_hook=json_object)


def load_frozen_inventory(path: Path) -> dict:
    if hashlib.sha256(path.read_bytes()).hexdigest() != FROZEN_INVENTORY_SHA256:
        raise ValueError("Frozen inventory digest differs")
    return apply_amendment(ORACLE.load_inventory(path), load_pinned_amendment(path))


def amended_source_inventory(source: Path, amendment: dict, include_resources=True) -> dict:
    if amendment_schema(amendment) == 1:
        return ORACLE.inventory(source, include_resources=include_resources)
    replacements = validate_replacements(amendment, ROOT)
    if not replacements:
        return ORACLE.inventory(source, include_resources=include_resources)

    reconstructed = reconstruct_source(source.read_bytes().decode("utf-8"), replacements)
    with tempfile.TemporaryDirectory(prefix="oracle-reconstructed-") as temp:
        root = Path(temp)
        scripts = root / "scripts"
        scripts.mkdir()
        for entry in (ROOT / "scripts").iterdir():
            if entry.name != "validate-contracts.sh":
                (scripts / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        (root / "tests").symlink_to(ROOT / "tests", target_is_directory=True)
        candidate = scripts / "validate-contracts.sh"
        candidate.write_bytes(reconstructed.encode("utf-8"))
        return ORACLE.inventory(candidate, include_resources=include_resources)


class SecurityContracts(unittest.TestCase):
    def test_version_fixture_isolates_inherited_log_root(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-version-isolation.py")],
                                capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_security(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-security.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_allowlist(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-allowlist.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_allowlist_guard(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-allowlist-guard.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_shell_guard(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-allowlist-shell.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_integrated_registrations(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-integrated.py")],
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def test_runtime_wrapper_shadow(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-wrapper-shadow.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sourceguard_allowlist(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-sourceguard-allowlist.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


# The one approved extension of the frozen inventory: the state tool contract results,
# its acceptance result, focused mode and resource row. Nothing else may be added.
NAMED_RESULTS = [
    "RECEIPTS: workflow-globals defines state_receipts: on one anchored line and keeps blocks without it valid",
    "RECEIPTS: the Protected Sections Contract protects state_receipts: lines",
    "RECEIPTS: the state tool vocabulary constants equal the anchored status lines",
    "test_state_tool_acceptance",
]
NAMED_ACCEPTANCE = "test_state_tool_acceptance"
NAMED_FLAG = "--state-tool-only"


def sample(seconds: float) -> dict:
    return {"exit_code": 0, "failures": 0, "elapsed_seconds": seconds,
            "user_seconds": 10.0, "system_seconds": 2.0,
            "max_rss_kb": 1000, "pass_count": 500, "skip_count": 2,
            "stdout": "stdout.txt", "stderr": "stderr.txt",
            "time_output": "time.txt"}


def manifest() -> dict:
    return {"commit": "a" * 40, "payload_sha256": "b" * 64,
            "configuration_sha256": "c" * 64, "locale": "C", "cache_policy": "warm",
            "source_blob": "d" * 40, "dirty_paths": [], "machine": "fixture",
            "cpu_quota": "unlimited", "ram_bytes": 1000000,
            "python_version": "3.11", "bash_version": "5.2", "grep_version": "3.8",
            "bytecode_existed": False, "hygiene_policy": "isolated",
            "cpu_count": 4, "jobs": 1,
            "samples": [sample(100), sample(102)]}



class OracleContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.amendment = load_pinned_amendment(ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz")
        cls.inventory = amended_source_inventory(ROOT / "scripts/validate-contracts.sh", cls.amendment)

    def test_runtime_checks_registered_once_after_focused_dispatch(self) -> None:
        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        end_of_focused = source.index('if [ "${1:-}" = --run-log-contract-only ]; then')
        for name in ("test_validator_runtime_characterization", "test_validator_runtime_oracle"):
            with self.subTest(name=name):
                call = 'check "' + name + '"'
                self.assertEqual(source.count(call), 1)
                self.assertGreater(source.index(call), end_of_focused)

    def test_result_extraction_distinguishes_nested_diagnostics(self) -> None:
        output = (b"[PASS] first\n[FAIL] outer: [PASS] first\n[FAIL] inner: details\n"
                  b"[PASS] last\n=== Contract Validation ===\n  Passed: 2\n  Failed: 1\n  Skipped: 0\n")
        self.assertEqual(ORACLE.extract_results(output, ["first", "outer", "last"]),
                         [("PASS", "first"), ("FAIL", "outer"), ("PASS", "last")])
        self.assertIsNone(ORACLE.extract_results(output, None))

    def test_time_output_fields_are_parsed_and_missing_fields_fail(self) -> None:
        output = (b"\tUser time (seconds): 10.00\n\tSystem time (seconds): 2.00\n"
                  b"\tElapsed (wall clock) time (h:mm:ss or m:ss): 1:40.00\n"
                  b"\tMaximum resident set size (kbytes): 1000\n\tExit status: 0\n")
        self.assertEqual(ORACLE.parse_time(output), {"user_seconds": 10.0, "system_seconds": 2.0,
                                                    "elapsed_seconds": 100.0, "max_rss_kb": 1000,
                                                    "exit_code": 0})
        self.assertIsNone(ORACLE.parse_time(output.replace(b"Exit status: 0", b"Exit missing")))

    def test_nonfinite_sample_values_are_rejected(self) -> None:
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                record = manifest()
                record["samples"][0]["elapsed_seconds"] = value
                self.assertIs(ORACLE.valid_manifest(record, "b" * 64, "c" * 64), False)

    def test_evidence_checks_file_bytes_digests_result_inventory_and_median(self) -> None:
        with tempfile.TemporaryDirectory(prefix="measurement-evidence-") as temp:
            root = Path(temp)
            (root / "source.txt").write_bytes(b"source payload\n")
            payload_hash = hashlib.sha256((root / "source.txt").read_bytes()).hexdigest()
            record = manifest()
            record["payload_sha256"] = payload_hash
            record["configuration"] = {"locale": "C", "cache_policy": "warm", "jobs": 1}
            configuration_hash = hashlib.sha256(json.dumps(record["configuration"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            record["configuration_sha256"] = configuration_hash
            record["source_files"] = {"source.txt": payload_hash}
            record["result_inventory"] = ["example"]
            record["baseline_median_seconds"] = 101
            for index, item in enumerate(record["samples"]):
                item.update(payload_sha256=payload_hash, configuration_sha256=configuration_hash,
                            pass_count=1, skip_count=0, process_exit_code=0,
                            source_files_unchanged=True, dirty_after="")
                time_output = ("User time (seconds): 10.00\nSystem time (seconds): 2.00\n"
                               f"Elapsed (wall clock) time (h:mm:ss or m:ss): 1:{40 + 2 * index:02d}.00\n"
                               "Maximum resident set size (kbytes): 1000\nExit status: 0\n").encode()
                contents = {"stdout": b"[PASS] example\n=== Contract Validation ===\n  Passed: 1\n  Failed: 0\n  Skipped: 0\n",
                            "stderr": b"", "time_output": time_output}
                item["file_sha256"] = {}
                for kind, data in contents.items():
                    item[kind] = f"{index}-{kind}.txt"
                    (root / item[kind]).write_bytes(data)
                    item["file_sha256"][kind] = hashlib.sha256(data).hexdigest()
            self.assertIs(ORACLE.verify_evidence(record, root), True)
            trusted = {key: copy.deepcopy(record[key]) for key in
                       ("commit", "source_blob", "source_files", "configuration", "result_inventory")}
            self.assertIs(ORACLE.verify_provenance(record, root, trusted), True)
            for key in trusted:
                altered = copy.deepcopy(trusted)
                if isinstance(altered[key], dict):
                    altered[key]["unexpected"] = "different"
                elif isinstance(altered[key], list):
                    altered[key].append("unexpected")
                else:
                    altered[key] = "different"
                with self.subTest(trusted_field=key):
                    self.assertIs(ORACLE.verify_provenance(record, root, altered), False)
            for mutation in ("source", "output", "sample_config", "inventory", "median",
                             "process_exit", "source_changed", "dirty"):
                changed = copy.deepcopy(record)
                path = root / ("source.txt" if mutation == "source" else "0-stdout.txt")
                old = path.read_bytes()
                if mutation in ("source", "output"):
                    path.write_bytes(old + b"tampered")
                elif mutation == "sample_config":
                    changed["samples"][0]["configuration_sha256"] = "d" * 64
                elif mutation == "inventory":
                    changed["result_inventory"] = ["different"]
                elif mutation == "median":
                    changed["baseline_median_seconds"] = 100
                elif mutation == "process_exit":
                    changed["samples"][0]["process_exit_code"] = 1
                elif mutation == "source_changed":
                    changed["samples"][0]["source_files_unchanged"] = False
                else:
                    changed["samples"][0]["dirty_after"] = " M source.txt"
                with self.subTest(mutation=mutation):
                    self.assertIs(ORACLE.verify_evidence(changed, root), False)
                path.write_bytes(old)

    def test_frozen_source_detects_actual_name_expression_and_order_changes(self) -> None:
        frozen = load_frozen_inventory(ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz")
        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        self.assertTrue(ORACLE.matches(frozen, self.inventory))
        first, second = frozen["expressions"][:2]
        changes = (
            source.replace('check "' + first["name"] + '"', 'check "altered name"', 1),
            source.replace(first["expression"], first["expression"] + " # changed", 1),
            source.replace('check "' + first["name"] + '"', 'check "TEMPORARY_NAME"', 1)
                  .replace('check "' + second["name"] + '"', 'check "' + first["name"] + '"', 1)
                  .replace('check "TEMPORARY_NAME"', 'check "' + second["name"] + '"', 1),
        )
        with tempfile.TemporaryDirectory(prefix="oracle-mutation-") as temp:
            scripts = Path(temp) / "scripts"
            scripts.mkdir()
            for entry in (ROOT / "scripts").iterdir():
                if entry.name != "validate-contracts.sh":
                    (scripts / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
            (Path(temp) / "tests").symlink_to(ROOT / "tests", target_is_directory=True)
            candidate = scripts / "validate-contracts.sh"
            candidate.write_text(source)
            self.assertTrue(ORACLE.matches(frozen, amended_source_inventory(candidate, self.amendment)))
            for changed in changes:
                with self.subTest(change=changes.index(changed)):
                    candidate.write_text(changed)
                    try:
                        observed = amended_source_inventory(candidate, self.amendment, include_resources=False)
                    except ValueError:
                        continue
                    self.assertFalse(ORACLE.matches_structure(frozen, observed))

    def test_amendment_pins_unrelated_fields_order_and_resource_changes(self) -> None:
        path = ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz"
        raw = ORACLE.load_inventory(path)
        amendment = json.loads(path.with_name("inventory-amendment.json").read_bytes())
        amended = apply_amendment(raw, amendment)
        self.assertTrue(ORACLE.matches(amended, self.inventory))
        unrelated = copy.deepcopy(self.inventory)
        unrelated["resources"][0]["evidence"] += " unexpected"
        self.assertFalse(ORACLE.matches(amended, unrelated))
        unrelated = copy.deepcopy(self.inventory)
        unrelated["results"][0], unrelated["results"][1] = unrelated["results"][1], unrelated["results"][0]
        self.assertFalse(ORACLE.matches(amended, unrelated))
        unrelated = copy.deepcopy(self.inventory)
        unrelated["resources"][0]["source_references"][0]["sha256"] = "0" * 64
        self.assertFalse(ORACLE.matches(amended, unrelated))
        with_observation = next(i for i, row in enumerate(self.inventory["resources"])
                                if any(row["observations"].values()))
        unrelated = copy.deepcopy(self.inventory)
        observations = unrelated["resources"][with_observation]["observations"]
        kind = next(k for k, values in observations.items() if values)
        observations[kind][0]["line_sha256"] = "0" * 64
        self.assertFalse(ORACLE.matches(amended, unrelated))
        with_dynamic = next(i for i, row in enumerate(self.inventory["resources"])
                            if row["dynamic_dependencies"])
        unrelated = copy.deepcopy(self.inventory)
        unrelated["resources"][with_dynamic]["dynamic_dependencies"][0]["reason"] += " unexpected"
        self.assertFalse(ORACLE.matches(amended, unrelated))
        bad = copy.deepcopy(amendment)
        bad["resources"][0]["changes"][0]["path"] = "tests/unapproved.py"
        with self.assertRaises(ValueError):
            apply_amendment(raw, bad)
        bad = copy.deepcopy(amendment)
        bad["resources"][0]["changes"][0]["before"] = [{"path": bad["resources"][0]["changes"][0]["path"], "sha256": "0" * 64}]
        with self.assertRaises(ValueError):
            apply_amendment(raw, bad)

    def test_inventory_extension_accepts_only_the_named_additions(self) -> None:
        path = ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz"
        raw = ORACLE.load_inventory(path)
        amendment = json.loads(path.with_name("inventory-amendment.json").read_bytes())
        added = amendment.get("added", {})
        self.assertEqual([item["value"]["name"] for item in added.get("results", [])], NAMED_RESULTS)
        self.assertEqual([item["value"]["name"] for item in added.get("expressions", [])],
                         [NAMED_ACCEPTANCE])
        self.assertEqual([item["value"]["flag"] for item in added.get("focused", [])], [NAMED_FLAG])
        self.assertEqual([item["value"]["name"] for item in added.get("resources", [])],
                         [NAMED_ACCEPTANCE])
        self.assertTrue(ORACLE.matches(apply_amendment(raw, amendment), self.inventory))

        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        def statement(name: str) -> str:
            start = source.index('check "' + name + '" \\\n')
            return source[start:source.index("\n", source.index("\n", start) + 1) + 1]
        contract, acceptance = statement(NAMED_RESULTS[2]), statement(NAMED_ACCEPTANCE)
        dispatch = re.search(r'^if \[ "\$\{1:-\}" = ' + NAMED_FLAG + r' \]; then\n.*?^fi\n',
                             source, re.M | re.S).group(0)
        candidates = {
            "unlisted contract check": source.replace(
                contract, contract + contract.replace(NAMED_RESULTS[2], "RECEIPTS: an unlisted check"), 1),
            "unlisted acceptance check": source.replace(
                acceptance, acceptance + acceptance.replace(
                    'check "' + NAMED_ACCEPTANCE, 'check "test_unlisted_acceptance', 1), 1),
            "unlisted focused mode": source.replace(
                dispatch, dispatch + dispatch.replace(NAMED_FLAG, "--unlisted-only"), 1),
            "named contract check missing": source.replace(contract, "", 1),
            "named focused mode missing": source.replace(dispatch, "", 1),
        }
        with tempfile.TemporaryDirectory(prefix="oracle-extension-") as temp:
            candidate = Path(temp) / "validate-contracts.sh"
            for label, text in candidates.items():
                with self.subTest(source=label):
                    self.assertNotEqual(text, source)
                    candidate.write_text(text)
                    try:
                        accepted = ORACLE.matches_structure(
                            apply_amendment(raw, amendment),
                            amended_source_inventory(candidate, amendment, include_resources=False))
                    except ValueError:
                        accepted = False
                    self.assertFalse(accepted, label)

        def changed(section: str, change) -> dict:
            altered = copy.deepcopy(amendment)
            change(altered["added"][section])
            return altered
        def extra(items: list) -> None:
            item = copy.deepcopy(items[-1])
            key = "flag" if "flag" in item["value"] else "name"
            item["after"] = item["value"][key] if isinstance(item["after"], str) else copy.deepcopy(item["value"])
            item["value"][key] = "unlisted-addition"
            items.append(item)
        def rename(items: list) -> None:
            key = "flag" if "flag" in items[0]["value"] else "name"
            items[0]["value"][key] += " renamed"
        def foreign_path(items: list) -> None:
            items[0]["value"]["source_references"].append(
                {"path": "tests/unapproved.py", "sha256": "0" * 64, "provenance": "direct lexical reference"})
        def missing_anchor(items: list) -> None:
            items[0]["after"] = "no such entry" if isinstance(items[0]["after"], str) else {"name": "none", "expression": "none"}
        bad_amendments = {"unlisted result": changed("results", extra),
                          "unlisted focused flag": changed("focused", extra),
                          "unlisted acceptance expression": changed("expressions", extra),
                          "unlisted resource row": changed("resources", extra),
                          "renamed result": changed("results", rename),
                          "renamed focused flag": changed("focused", rename),
                          "named result missing": changed("results", lambda items: items.pop()),
                          "resource path outside the suite": changed("resources", foreign_path),
                          "missing anchor": changed("results", missing_anchor)}
        unknown_section = copy.deepcopy(amendment)
        unknown_section["added"]["unlisted"] = []
        bad_amendments["unknown section"] = unknown_section
        for label, altered in bad_amendments.items():
            with self.subTest(amendment=label), self.assertRaises(ValueError):
                apply_amendment(raw, altered)

    def test_unapproved_nonstandard_check_is_rejected(self) -> None:
        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        with tempfile.TemporaryDirectory(prefix="oracle-syntax-") as temp:
            candidate = Path(temp) / "validate-contracts.sh"
            candidate.write_text(source + "\n  check unexpected\n")
            with self.assertRaisesRegex(ValueError, "Unapproved check syntax"):
                amended_source_inventory(candidate, self.amendment, include_resources=False)

    def test_inventory_contains_all_source_contracts(self) -> None:
        inventory = self.inventory
        self.assertIsInstance(inventory, dict)
        self.assertEqual(len(inventory["expressions"]), 37)
        self.assertEqual(len(inventory["focused"]), 38)
        self.assertGreater(len(inventory["results"]), 37)
        self.assertEqual(len(inventory["resources"]), 37)
        self.assertTrue(all(row["classification"] in {"independent", "exclusive", "conflict"}
                            and row["evidence"] for row in inventory["resources"]))

    def test_matching_inventory_is_accepted(self) -> None:
        inventory = {"results": ["first", "second"],
                     "expressions": [{"name": "first", "body": "true"}],
                     "focused": ["--example-only"], "resources": []}
        self.assertIs(ORACLE.matches(inventory, copy.deepcopy(inventory)), True)

    def test_independent_name_expression_and_order_mutations_rejected(self) -> None:
        inventory = {"results": ["first", "second"],
                     "expressions": [{"name": "first", "body": "true"}],
                     "focused": ["--example-only"], "resources": []}
        mutations = []
        changed = copy.deepcopy(inventory)
        changed["expressions"][0]["name"] = "changed"
        mutations.append(changed)
        changed = copy.deepcopy(inventory)
        changed["expressions"][0]["body"] = "false"
        mutations.append(changed)
        changed = copy.deepcopy(inventory)
        changed["results"].reverse()
        mutations.append(changed)
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assertIs(ORACLE.matches(inventory, changed), False)

    def test_two_consistent_successful_samples_accepted(self) -> None:
        self.assertIs(ORACLE.valid_manifest(manifest(), "b" * 64, "c" * 64), True)

    def test_incomplete_failed_or_drifted_manifest_rejected(self) -> None:
        examples = []
        missing = manifest()
        del missing["locale"]
        examples.append((missing, "b" * 64, "c" * 64))
        failed = manifest()
        failed["samples"][0]["failures"] = 1
        examples.append((failed, "b" * 64, "c" * 64))
        incomplete = manifest()
        del incomplete["samples"][0]["max_rss_kb"]
        examples.append((incomplete, "b" * 64, "c" * 64))
        bad_exit = manifest()
        bad_exit["samples"][0]["exit_code"] = 1
        examples.append((bad_exit, "b" * 64, "c" * 64))
        examples.append((manifest(), "d" * 64, "c" * 64))
        examples.append((manifest(), "b" * 64, "d" * 64))
        for record, payload, config in examples:
            with self.subTest(record=record, payload=payload, config=config):
                self.assertIs(ORACLE.valid_manifest(record, payload, config), False)

    def test_high_variance_requires_third_retained_sample(self) -> None:
        record = manifest()
        record["samples"][1]["elapsed_seconds"] = 120
        self.assertIs(ORACLE.valid_manifest(record, "b" * 64, "c" * 64), False)
        record["samples"].append(sample(110))
        self.assertIs(ORACLE.valid_manifest(record, "b" * 64, "c" * 64), True)


if __name__ == "__main__":
    unittest.main()
