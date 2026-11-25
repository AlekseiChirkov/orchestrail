#!/usr/bin/env python3
"""Exercise inventory amendments through the existing oracle in isolated trees."""

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ORACLE = Path("tests/validator-runtime-oracle.py")
VALIDATOR = Path("scripts/validate-contracts.sh")
FIXTURES = Path("tests/fixtures/validator-runtime")
AMENDMENT = FIXTURES / "inventory-amendment.json"
MAP_ROWS = [
    {"kind": "file", "old": "workflows/PIPELINE.md", "new": ["docs/PIPELINE.md"]},
    {"kind": "rule", "old": "phase-discovery", "new": ["bootstrap-discovery"]},
    {"kind": "rule", "old": "tdd", "new": ["contract-tdd", "contract-tdd-guide"]},
    {"kind": "workflow", "old": "pae-tests", "new": ["atomic-execution-tests"]},
    {"kind": "workflow", "old": "phase-discovery", "new": ["discovery"]},
]
ORACLE_CHECK = "OracleContract.test_frozen_source_detects_actual_name_expression_and_order_changes"


class AmendmentContract(unittest.TestCase):
    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory(prefix="inventory-amendment-")
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        for directory in ("docs", "scripts", FIXTURES, "home"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for directory, skip in (
            ("scripts", {"validate-contracts.sh"}),
            ("tests", {"fixtures", ORACLE.name}),
            ("tests/fixtures", {"validator-runtime"}),
            (FIXTURES, {AMENDMENT.name}),
        ):
            for child in (ROOT / directory).iterdir():
                if child.name not in skip:
                    (self.root / directory / child.name).symlink_to(child)
        self.validator = (ROOT / VALIDATOR).read_text(encoding="utf-8")
        self.original_oracle = (ROOT / ORACLE).read_text(encoding="utf-8")
        current = json.loads((ROOT / AMENDMENT).read_bytes())
        self.legacy = {k: copy.deepcopy(current[k])
                       for k in ("paths", "removed_results", "resources", "added")}
        self.legacy["schema"] = 1
        payload = json.dumps({"schema_version": 1, "rows": MAP_ROWS}).encode()
        (self.root / "docs/name-map.json").write_bytes(payload)
        self.amendment = {
            **self.legacy, "schema": 2, "name_map_sha256": hashlib.sha256(payload).hexdigest(),
            "path_changes": [], "contract_changes": [],
        }

    def expression(self, name: str) -> str:
        pattern = r'^check "' + re.escape(name) + r'"[ \t]+(?:\\\n[ \t]*)?([^\n]+)'
        matches = re.findall(pattern, self.validator, re.M)
        self.assertEqual(len(matches), 1, name)
        return matches[0]

    def rule_path_change(self) -> dict:
        name = "TDD: rules/tdd.md exists"
        before = self.expression(name)
        return {"target": "result", "key": name, "before": before,
                "after": before.replace("rules/tdd.md", "rules/contract-tdd.md")}

    def contract_change(self) -> dict:
        name = "TDD: rules/tdd.md is always_on"
        before = self.expression(name)
        return {
            "target": "result", "key": name, "before": before,
            "after": before.replace("trigger: always_on", "load: always"),
            "reason": "The rule metadata contract uses a load field.",
            "requirement": "REQ-12",
        }

    def run_oracle(self, amendment: dict, source: str) -> subprocess.CompletedProcess[str]:
        data = json.dumps(amendment, ensure_ascii=False).encode()
        (self.root / AMENDMENT).write_bytes(data)
        (self.root / VALIDATOR).write_text(source, encoding="utf-8")
        revised, count = re.subn(
            r'(?m)^AMENDMENT_SHA256 = "[a-f0-9]{64}"$',
            f'AMENDMENT_SHA256 = "{hashlib.sha256(data).hexdigest()}"', self.original_oracle,
        )
        self.assertEqual(count, 1)
        (self.root / ORACLE).write_text(revised, encoding="utf-8")
        home = str(self.root / "home")
        env = {**os.environ, "HOME": home, "XDG_CONFIG_HOME": home, "XDG_STATE_HOME": home,
               "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([sys.executable, "-B", str(self.root / ORACLE), ORACLE_CHECK],
                              cwd=self.root, env=env, capture_output=True, text=True, timeout=30)

    def accepts(self, amendment: dict, source: str) -> None:
        result = self.run_oracle(amendment, source)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def rejects(self, amendment: dict, source: str) -> None:
        result = self.run_oracle(amendment, source)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ValueError:", result.stderr)

    def rewrite(self, entry: dict) -> str:
        self.assertEqual(self.validator.count(entry["before"]), 1)
        return self.validator.replace(entry["before"], entry["after"], 1)

    def test_schema_upgrade_preserves_existing_inventory(self) -> None:
        self.accepts(self.legacy, self.validator)
        self.accepts(self.amendment, self.validator)
        bad = copy.deepcopy(self.amendment)
        bad["added"]["results"][0]["after"] = {"name": "untested check", "expression": "pass"}
        self.rejects(bad, self.validator)
        bad = copy.deepcopy(self.amendment)
        bad["added"]["results"].pop()
        self.rejects(bad, self.validator)
        bad = copy.deepcopy(self.amendment)
        bad["added"]["results"].append(copy.deepcopy(bad["added"]["results"][0]))
        self.rejects(bad, self.validator)

    def test_name_equivalent_changes_reconstruct_frozen_inventory(self) -> None:
        entry = self.rule_path_change()
        self.amendment["path_changes"] = [entry]
        source = self.rewrite(entry)
        self.accepts(self.amendment, source)

        wrong_class = {**entry, "after": entry["after"].replace("contract-tdd", "bootstrap-discovery")}
        self.rejects({**self.amendment, "path_changes": [wrong_class]}, self.rewrite(wrong_class))
        wrong_token = {**entry, "after": entry["after"].replace("echo pass", "echo fail")}
        self.rejects({**self.amendment, "path_changes": [wrong_token]}, self.rewrite(wrong_token))
        self.rejects({**self.amendment, "name_map_sha256": "0" * 64}, source)

    def test_contract_replacements_are_bounded_and_exact(self) -> None:
        entry = self.contract_change()
        self.amendment["contract_changes"] = [entry]
        self.accepts(self.amendment, self.rewrite(entry))

        for mutation in ({"requirement": "REQ-99"}, {"after": "pass"}, {"target": "unknown"},
                         {"key": "unknown check"}, {"reason": ""}):
            with self.subTest(mutation=mutation):
                invalid = {**entry, **mutation}
                self.rejects({**self.amendment, "contract_changes": [invalid]}, self.rewrite(invalid))
        missing = {key: value for key, value in entry.items() if key != "requirement"}
        self.rejects({**self.amendment, "contract_changes": [missing]}, self.rewrite(entry))
        self.rejects({**self.amendment, "path_changes": [self.rule_path_change()],
                      "contract_changes": [{**entry, "key": self.rule_path_change()["key"]}]},
                     self.rewrite(entry))
        self.rejects(self.amendment, self.rewrite(entry) + "\n" + entry["after"] + "\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
