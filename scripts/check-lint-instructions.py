#!/usr/bin/env python3
"""Check the instruction lint command with isolated source trees."""

from collections import Counter
from functools import cache
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().with_name("lint-instructions.py")
SOURCE = CHECKER.parents[1]
RULE = '---\ndescription: Check the contract\nload: on-demand\n---\n'
CAPABILITY_KEYS = (
    "sub-agents",
    "concurrent-sub-agents",
    "agent-messaging",
    "hooks",
    "worktrees",
    "git",
)
RECEIPT_HISTORY_FRAME = (
    "The following historical verification record preserves its original citation.\n"
    "The current policy is `contract-git-flow → ## Finalization Git ownership`.\n\n"
)
ALWAYS_ON_RELOCATIONS = (
    ("rules/global-claude.md", "harness/claude/always-on.md"),
    ("templates/codex-global-AGENTS.md", "harness/codex/always-on.md"),
)
PHASE_CONTRACT = "rules/contract-phases.md"
RESOLUTION_LINE = "A reference to rule `<name>` resolves to skill `rule-<name>` on every supported harness."
BOOTSTRAP_HEADER = "| Phase | Skill | Loaded by |"
BOOTSTRAP_ROWS = (
    "| Discovery | `rule-bootstrap-discovery` | `/discovery`, `/discovery-analyze` |",
    "| Execution | `rule-bootstrap-execution` | `/execution`, `/execution-execute` |",
    "| Validation | `rule-bootstrap-validation` | `/validation`, `/validation-contract`, `/validation-review` |",
    "| Finalization | `rule-bootstrap-finalization` | `/finalization` |",
    "| Atomic Execution | `rule-bootstrap-atomic-execution` | `/atomic-execution`, "
    "`/atomic-execution-tests`, `/atomic-execution-implement` |",
    "| Atomic Validation | `rule-bootstrap-atomic-validation` | `/atomic-validation`, `/atomic-validation-check` |",
)
BEHAVIOUR_HEADER = "| Behaviour | Workflow | Requires | Without it |"
BEHAVIOUR_ROWS = (
    "| Orchestrated run with Implementer, Validator and Arbiter workers | `spec-run` | "
    "`sub-agents`, `agent-messaging`, `git` | Stop before Step 0; use `/pipeline <task-directory>` |",
    "| Parallel children | `spec-run` | `worktrees`, `concurrent-sub-agents` | "
    "Sequential path with a reason until parallel support is established |",
    "| Devil's Advocate critic | `spec-draft` | `sub-agents`, `agent-messaging` | Inline review, `critic: inline` |",
    "| Model-specific worker for a leaf | `atomic-execution`, `execution-execute` | `sub-agents` | "
    "Run inline when no explicit switch is required, otherwise stop |",
    "| Hook-covered step logging | `discovery`, `execution`, `validation`, `finalization`, `pipeline`, "
    "`spec-run`, `retro` | `hooks` | Prompt logging with `note: approximate` |",
)
MISSING_PHASE_CONTRACT_FINDINGS = (
    f"resolution-rule-missing {PHASE_CONTRACT}:0 Expected one canonical rule-reference line.",
    f"bootstrap-table-invalid {PHASE_CONTRACT}:0 Expected one row for each phase and its bootstrap skill.",
    f"capability-behaviour-table-invalid {PHASE_CONTRACT}:0 Expected the capability behaviour table.",
)
MISSING_PHASE_CONTRACT_OUTPUT = "\n".join(MISSING_PHASE_CONTRACT_FINDINGS) + "\n"


def workflow(step: str, phase: str = "discovery", name: str = "demo") -> str:
    return (
        f'---\ndescription: A workflow\nphase: {phase}\nstep: {step}\n---\n\n'
        f'Invocation: `/{name}`\n'
    )


def words(count: int) -> str:
    return " ".join(["word"] * count)


def sized_bootstrap(count: int) -> str:
    template = RULE + "\n# Bootstrap\n\n## Context Bootstrap\n\n```text\n{}\n```\n\n## Phase Behaviors\n"
    return template.format(words(count - len(template.format("").split())))


def capability_record(name: str, state: str) -> str:
    fields = f"name: {name}\nstate: {state}"
    if state != "unknown":
        fields += "\nruntime: Fixture runtime 1.0\nverified: 2024-02-29\nevidence: docs/example.md"
    return f"{fields}\n\nLimitations: none known"


def capability_declaration(name: str, hooks: str) -> str:
    states = {"hooks": hooks, "worktrees": "unknown"}
    records = "\n\n".join(capability_record(key, states.get(key, "yes")) for key in CAPABILITY_KEYS)
    return (
        f"# Fixture capabilities\n\nhooks: {hooks}\n\n## Capability records\n\n"
        f"always-on-path: $HOME/{name}/instructions.md\n\n{records}"
    )


class InstructionMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.root = self.workspace / "source tree"
        self.root.mkdir()
        self.environment = os.environ.copy()
        for variable in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
            directory = self.workspace / variable.lower()
            directory.mkdir()
            self.environment[variable] = str(directory)

    def write(self, relative: str, contents: str | bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = contents.encode("utf-8") if isinstance(contents, str) else contents
        path.write_bytes(data)

    def run_checker(self, root: Path | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-I", str(CHECKER), "--root", str(self.root if root is None else root)],
            cwd=self.workspace,
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        return result

    def assert_finding(self, result: subprocess.CompletedProcess[str], code: str, relative: str) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertTrue(
            any(line.startswith(f"{code} {relative}:") for line in result.stdout.splitlines()),
            f"Expected {code} for {relative}. Output:\n{result.stdout}{result.stderr}",
        )

    def findings_for_minimal_fixture(self, result: subprocess.CompletedProcess[str]) -> list[str]:
        findings = result.stdout.splitlines()
        for expected in MISSING_PHASE_CONTRACT_FINDINGS:
            self.assertEqual(findings.count(expected), 1, result.stdout)
            findings.remove(expected)
        return findings

    def test_accepts_valid_rule_and_workflow_metadata(self) -> None:
        self.write("rules/contract-demo.md", RULE)
        for name, step in (("demo-decimal", "2.5"), ("demo-letter", "4b"), ("demo-entry", '"-"')):
            phase = "entry" if name == "demo-entry" else "discovery"
            self.write(f"workflows/{name}.md", workflow(step, phase, name))
        self.write("workflows/finalization.md", workflow('"-"', "finalization", "finalization"))

        result = self.run_checker()

        scoped = ("metadata-", "trigger-present ", "invocation-")
        self.assertFalse(any(line.startswith(scoped) for line in result.stdout.splitlines()), result.stdout)

    def test_rejects_missing_duplicate_unknown_and_malformed_metadata(self) -> None:
        fixtures = {
            "missing-load": (RULE.replace("load: on-demand\n", ""), "metadata-missing-field"),
            "trigger": (RULE.replace("load:", "trigger: always_on\nload:"), "trigger-present"),
            "repeated-key": (RULE.replace("load: on-demand", "load: on-demand\nload: always"), "metadata-duplicate-key"),
            "unknown-key": (RULE.replace("load:", "unregistered: value\nload:"), "metadata-unknown-field"),
            "invalid-value": (RULE.replace("on-demand", "sometimes"), "metadata-invalid-value"),
            "bad-delimiter": (RULE.removesuffix("---\n"), "metadata-syntax"),
            "continuation": (RULE.replace("contract\n", "contract\n  another line\n"), "metadata-syntax"),
            "tab": (RULE.replace("load: ", "load:\t"), "metadata-syntax"),
            "missing-description": (RULE.replace("description: Check the contract\n", ""), "metadata-missing-field"),
        }
        for label, (contents, _) in fixtures.items():
            self.write(f"rules/contract-{label}.md", contents)

        result = self.run_checker()

        for label, (_, code) in fixtures.items():
            with self.subTest(fixture=label):
                self.assert_finding(result, code, f"rules/contract-{label}.md")

    def test_rejects_invalid_workflow_steps_phases_and_invocations(self) -> None:
        fixtures = {
            "zero-step": (workflow("0", name="zero-step"), "metadata-invalid-value"),
            "multiple-decimals": (workflow("2.5.1", name="multiple-decimals"), "metadata-invalid-value"),
            "unknown-phase": (workflow("1", "editor", "unknown-phase"), "metadata-invalid-value"),
            "unknown-extension": (
                workflow("1", name="unknown-extension").replace("step:", "unregistered: value\nstep:"),
                "metadata-unknown-field",
            ),
            "missing-invocation": (workflow("1").split("Invocation:")[0], "invocation-missing"),
            "duplicate-invocation": (workflow("1", name="duplicate-invocation") * 2, "invocation-duplicate"),
        }
        for label, (contents, _) in fixtures.items():
            self.write(f"workflows/{label}.md", contents)

        result = self.run_checker()

        for label, (_, code) in fixtures.items():
            with self.subTest(fixture=label):
                self.assert_finding(result, code, f"workflows/{label}.md")

    def write_adapter(self, name: str, body: str, capabilities: str) -> None:
        directory = f"harness/{name}"
        self.write(
            f"{directory}/deploy.env",
            f"skills_dir=$HOME/{name}/skills\nalways_on_path=$HOME/{name}/instructions.md\n",
        )
        self.write(f"{directory}/capabilities.md", capabilities + "\n")
        self.write(f"{directory}/always-on.md", body)

    def write_phase_contract_fixture(self) -> str:
        bootstrap_phases = ("discovery", "execution", "validation", "finalization", "atomic-execution", "atomic-validation")
        for phase in bootstrap_phases:
            self.write(f"rules/bootstrap-{phase}.md", sized_bootstrap(30))
            self.write(f"workflows/{phase}.md", workflow('"-"', phase, phase))
        for name, phase in (
            ("discovery-analyze", "discovery"), ("execution-execute", "execution"),
            ("validation-contract", "validation"), ("validation-review", "validation"),
            ("atomic-execution-tests", "atomic-execution"), ("atomic-execution-implement", "atomic-execution"),
            ("atomic-validation-check", "atomic-validation"), ("pipeline", "orchestrated"),
            ("spec-run", "orchestrated"), ("spec-draft", "entry"), ("retro", "utility"),
        ):
            self.write(f"workflows/{name}.md", workflow('"-"', phase, name))
        for name, hooks in (("fixture-first", "yes"), ("fixture-second", "no")):
            self.write_adapter(name, "Fixture instructions", capability_declaration(name, hooks))

        contract = "\n".join((
            RULE, "# Phase contracts", "", "## Rule references", "", RESOLUTION_LINE, "",
            "## Context Bootstrap", "", BOOTSTRAP_HEADER, "| --- | --- | --- |", *BOOTSTRAP_ROWS, "",
            "## Capabilities", "",
            "Read the always-on records. No, unknown and absent capabilities are unavailable.",
            "A yes still requires tool access and permission. Supply new evidence when a record changes.", "",
            BEHAVIOUR_HEADER, "| --- | --- | --- | --- |", *BEHAVIOUR_ROWS, "",
        ))
        self.write(PHASE_CONTRACT, contract)
        return contract

    def test_rule_resolution_requires_one_canonical_anchor_in_the_scan_set(self) -> None:
        contract = self.write_phase_contract_fixture()
        self.write("docs/audits/historical-example.md", RESOLUTION_LINE + "\n")
        self.write("README.md", "# Guide\n")

        with self.subTest(anchor="canonical, with a historical copy"):
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        mutations = {
            "missing": contract.replace(RESOLUTION_LINE, ""),
            "embedded in prose": contract.replace(RESOLUTION_LINE, f"As a reminder, {RESOLUTION_LINE}"),
            "outside the section": contract.replace(RESOLUTION_LINE, "") + f"\n## History\n\n{RESOLUTION_LINE}\n",
            "fenced": contract.replace(RESOLUTION_LINE, f"```text\n{RESOLUTION_LINE}\n```"),
            "repeated in the section": contract.replace(RESOLUTION_LINE, f"{RESOLUTION_LINE}\n\n{RESOLUTION_LINE}"),
        }
        for label, mutation in mutations.items():
            with self.subTest(anchor=label):
                self.write(PHASE_CONTRACT, mutation)
                self.assert_finding(self.run_checker(), "resolution-rule-missing", PHASE_CONTRACT)

        self.write(PHASE_CONTRACT, contract)
        for label, extra in {
            "second active copy": RESOLUTION_LINE,
            "obsolete wording": "The rule uses a bare basename.",
            "obsolete column": "| Phase | Rules file (on disk) |\n| --- | --- |\n| Discovery | Bootstrap |",
        }.items():
            with self.subTest(anchor=label):
                self.write("README.md", f"# Guide\n\n{extra}\n")
                result = self.run_checker()
                self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
                self.assertTrue(
                    any(line.startswith("resolution-rule-missing ") for line in result.stdout.splitlines()),
                    result.stdout,
                )

    def test_phase_contract_requires_the_canonical_source(self) -> None:
        self.write_phase_contract_fixture()
        (self.root / PHASE_CONTRACT).rename(self.root / "rules/workflow-globals.md")

        result = self.run_checker()

        for code in ("resolution-rule-missing", "bootstrap-table-invalid", "capability-behaviour-table-invalid"):
            with self.subTest(diagnostic=code):
                self.assert_finding(result, code, PHASE_CONTRACT)

    def test_bootstrap_table_requires_exact_phases_and_existing_skills(self) -> None:
        contract = self.write_phase_contract_fixture()
        first_bootstrap = BOOTSTRAP_ROWS[0]
        with self.subTest(table="six canonical rows"):
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        mutations = {
            "wrong header": contract.replace(BOOTSTRAP_HEADER, "| Phase | Skill name | Loaded by |"),
            "missing row": contract.replace(first_bootstrap + "\n", ""),
            "seventh row": contract.replace(BOOTSTRAP_ROWS[-1], f"{BOOTSTRAP_ROWS[-1]}\n{first_bootstrap}"),
            "duplicate phase": contract.replace("| Execution |", "| Discovery |"),
            "skill for another phase": contract.replace("`rule-bootstrap-discovery`", "`rule-bootstrap-execution`"),
            "legacy skill": contract.replace("`rule-bootstrap-discovery`", "`rule-phase-discovery`"),
            "extra cell": contract.replace(first_bootstrap, first_bootstrap + " Additional |"),
            "wrong section": contract.replace("## Context Bootstrap", "## Example Bootstrap"),
        }
        for label, mutation in mutations.items():
            with self.subTest(table=label):
                self.write(PHASE_CONTRACT, mutation)
                self.assert_finding(self.run_checker(), "bootstrap-table-invalid", PHASE_CONTRACT)

        self.write(PHASE_CONTRACT, contract)
        (self.root / "rules/bootstrap-discovery.md").unlink()
        with self.subTest(table="referenced rule is missing"):
            self.assert_finding(self.run_checker(), "bootstrap-table-invalid", PHASE_CONTRACT)

    def test_capability_behaviour_table_requires_behaviours_workflows_and_fallbacks(self) -> None:
        contract = self.write_phase_contract_fixture()
        with self.subTest(table="five canonical behaviours"):
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        mutations = {
            "wrong header": contract.replace(BEHAVIOUR_HEADER, "| Behavior | Workflow | Requires | Without it |"),
            "missing behaviour": contract.replace(BEHAVIOUR_ROWS[1] + "\n", ""),
            "changed behaviour label": contract.replace("| Parallel children |", "| Parallel work |"),
            "duplicate behaviour": contract.replace(BEHAVIOUR_ROWS[1], f"{BEHAVIOUR_ROWS[1]}\n{BEHAVIOUR_ROWS[1]}"),
            "wrong capability key": contract.replace("`sub-agents`", "`subagents`", 1),
            "wrong canonical capability": contract.replace("| `hooks` |", "| `git` |"),
            "unknown workflow": contract.replace("`retro`", "`missing-command`"),
            "path instead of workflow name": contract.replace("`retro`", "`workflows/retro.md`"),
            "missing fallback": contract.replace("Inline review, `critic: inline`", ""),
            "wrong section": contract.replace("## Capabilities", "## Capability Examples"),
        }
        for label, mutation in mutations.items():
            with self.subTest(table=label):
                self.write(PHASE_CONTRACT, mutation)
                self.assert_finding(self.run_checker(), "capability-behaviour-table-invalid", PHASE_CONTRACT)

        self.write(PHASE_CONTRACT, contract)
        (self.root / "workflows/retro.md").unlink()
        self.write("workflows/archive.md", workflow('"-"', "utility", "archive"))
        (self.root / "workflows/retro.md").symlink_to("archive.md")
        with self.subTest(table="named workflow is a symlink"):
            self.assert_finding(self.run_checker(), "capability-behaviour-table-invalid", PHASE_CONTRACT)

    def test_capability_behaviour_extension_requires_a_record_in_every_harness(self) -> None:
        contract = self.write_phase_contract_fixture()
        extension = "| Set worker effort | `spec-run` | `sub-agent-effort` | Use the default effort |\n"
        self.write(PHASE_CONTRACT, contract + extension)
        declarations = {
            "fixture-first": capability_declaration("fixture-first", "yes"),
            "fixture-second": capability_declaration("fixture-second", "no"),
        }
        for name, declaration in declarations.items():
            record = capability_record("sub-agent-effort", "unknown" if name == "fixture-first" else "yes")
            self.write(f"harness/{name}/capabilities.md", f"{declaration}\n\n{record}\n")

        with self.subTest(extension="declared by both adapters, including an unknown state"):
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        with self.subTest(extension="misspelled"):
            self.write(PHASE_CONTRACT, contract + extension.replace("sub-agent-effort", "subagent-effort"))
            self.assert_finding(self.run_checker(), "capability-behaviour-table-invalid", PHASE_CONTRACT)

        self.write(PHASE_CONTRACT, contract + extension)
        second = declarations["fixture-second"]
        with self.subTest(extension="absent from the second adapter"):
            self.write("harness/fixture-second/capabilities.md", second + "\n")
            self.assert_finding(self.run_checker(), "capability-behaviour-table-invalid", PHASE_CONTRACT)

        with self.subTest(extension="named outside the record section"):
            record = capability_record("sub-agent-effort", "yes")
            self.write("harness/fixture-second/capabilities.md", f"{second}\n\n## Example\n\n{record}\n")
            self.assert_finding(self.run_checker(), "capability-behaviour-table-invalid", PHASE_CONTRACT)

    def test_bootstrap_table_counts_rows_without_outer_pipes(self) -> None:
        contract = self.write_phase_contract_fixture()
        last = BOOTSTRAP_ROWS[-1]

        with self.subTest(table="six rows with mixed pipe styles"):
            self.write(PHASE_CONTRACT, contract.replace(last, last.strip("| ")))
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        with self.subTest(table="seventh row without outer pipes"):
            extra = BOOTSTRAP_ROWS[0].strip("| ")
            self.write(PHASE_CONTRACT, contract.replace(last, f"{last}\n{extra}"))
            self.assert_finding(self.run_checker(), "bootstrap-table-invalid", PHASE_CONTRACT)

    def test_capability_table_validates_rows_without_outer_pipes(self) -> None:
        contract = self.write_phase_contract_fixture()
        last = BEHAVIOUR_ROWS[-1]

        with self.subTest(table="five rows with mixed pipe styles"):
            self.write(PHASE_CONTRACT, contract.replace(last, last.strip("| ")))
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        for label, row in (
            ("undeclared extension", "Set worker effort | `spec-run` | `sub-agent-effort` | Use default effort"),
            ("uninstalled workflow", "Send a message | `missing-command` | `agent-messaging` | Run inline"),
        ):
            with self.subTest(table=label):
                self.write(PHASE_CONTRACT, contract + row + "\n")
                self.assert_finding(self.run_checker(), "capability-behaviour-table-invalid", PHASE_CONTRACT)

    def test_rule_reference_rejects_obsolete_markdown_column_variants(self) -> None:
        self.write_phase_contract_fixture()

        for label, table in (
            ("no outer pipes", "Phase | Rules file\n--- | ---\nDiscovery | Bootstrap"),
            ("code span", "| Phase | `Rules file` |\n| --- | --- |\n| Discovery | Bootstrap |"),
        ):
            with self.subTest(header=label):
                self.write("README.md", f"# Guide\n\n{table}\n")
                self.assert_finding(self.run_checker(), "resolution-rule-missing", "README.md")

    def test_phase_contract_uses_visible_markdown_content(self) -> None:
        contract = self.write_phase_contract_fixture()

        with self.subTest(markdown="comment-only anchor"):
            self.write(PHASE_CONTRACT, contract.replace(RESOLUTION_LINE, f"<!--\n{RESOLUTION_LINE}\n-->"))
            self.assert_finding(self.run_checker(), "resolution-rule-missing", PHASE_CONTRACT)

        with self.subTest(markdown="comment-only phase sections"):
            self.write(PHASE_CONTRACT, RULE + f"\n<!--\n{contract.removeprefix(RULE)}-->\n")
            result = self.run_checker()
            for code in ("resolution-rule-missing", "bootstrap-table-invalid", "capability-behaviour-table-invalid"):
                with self.subTest(diagnostic=code):
                    self.assert_finding(result, code, PHASE_CONTRACT)

        with self.subTest(markdown="commented heading beside the live table"):
            self.write(PHASE_CONTRACT, contract.replace("## Capabilities", "<!--\n## Capabilities\n-->\n\n## Capabilities"))
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        with self.subTest(markdown="comment opener inside a fenced example"):
            self.write(PHASE_CONTRACT, contract.replace("## Capabilities", "```text\n<!--\n```\n\n## Capabilities"))
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

    def test_phase_tables_continue_after_a_pipe_less_body_row(self) -> None:
        contract = self.write_phase_contract_fixture()
        last = BOOTSTRAP_ROWS[-1]
        trailing_bootstrap = BOOTSTRAP_ROWS[0]

        with self.subTest(table="bootstrap"):
            self.write(PHASE_CONTRACT, contract.replace(last, f"{last}\nSingle cell\n{trailing_bootstrap}"))
            self.assert_finding(self.run_checker(), "bootstrap-table-invalid", PHASE_CONTRACT)

        invalid_behaviour = "Send a message | `missing-command` | `agent-messaging` | Run inline"
        with self.subTest(table="capabilities"):
            self.write(PHASE_CONTRACT, contract + f"Single cell\n{invalid_behaviour}\n")
            result = self.run_checker()
            self.assert_finding(result, "capability-behaviour-table-invalid", PHASE_CONTRACT)
            self.assertIn("Invalid capability behaviour row: Send a message.", result.stdout)

        for label, boundary in (
            ("heading", "### Appendix"), ("blank line", ""), ("blockquote", "> Appendix | Project notes"),
        ):
            with self.subTest(boundary=label):
                self.write(PHASE_CONTRACT, contract + f"{boundary}\n{invalid_behaviour}\n")
                result = self.run_checker()
                self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

    def test_phase_table_delimiter_accepts_single_dashes(self) -> None:
        contract = self.write_phase_contract_fixture()

        with self.subTest(delimiter="canonical tables with single dashes and alignment"):
            compact = contract.replace("| --- | --- | --- |", "| - | :-: | -: |")
            self.write(PHASE_CONTRACT, compact.replace("| - | :-: | -: | --- |", "| - | :-: | -: | :- |"))
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)

        with self.subTest(delimiter="obsolete header with single dashes"):
            self.write(PHASE_CONTRACT, contract)
            self.write("README.md", "# Guide\n\nPhase | Rules file\n- | :-:\nDiscovery | Bootstrap\n")
            self.assert_finding(self.run_checker(), "resolution-rule-missing", "README.md")

        for label, obsolete in (("bold", "**Rules file** (old)"), ("italic", "_Rules file_")):
            with self.subTest(delimiter="ordinary", header=label):
                self.write("README.md", f"# Guide\n\n| Phase | {obsolete} |\n| --- | --- |\n| Discovery | Bootstrap |\n")
                self.assert_finding(self.run_checker(), "resolution-rule-missing", "README.md")

    def test_phase_table_headers_remain_exact_after_filtering_comments(self) -> None:
        contract = self.write_phase_contract_fixture()

        for header, code in (
            (BOOTSTRAP_HEADER, "bootstrap-table-invalid"),
            (BEHAVIOUR_HEADER, "capability-behaviour-table-invalid"),
        ):
            with self.subTest(header=header):
                self.write(PHASE_CONTRACT, contract.replace(header, header + "<!-- header note -->"))
                self.assert_finding(self.run_checker(), code, PHASE_CONTRACT)

    def test_visible_rule_reference_anchor_requires_exact_source_text(self) -> None:
        contract = self.write_phase_contract_fixture()
        synthetic_anchor = RESOLUTION_LINE.replace("resolves", "re<!-- hidden -->solves")
        self.write(PHASE_CONTRACT, contract.replace(RESOLUTION_LINE, synthetic_anchor))

        self.assert_finding(self.run_checker(), "resolution-rule-missing", PHASE_CONTRACT)

    def test_counts_only_the_always_on_body_at_the_size_limit(self) -> None:
        capabilities = words(1607)
        self.write_adapter("at-limit", words(1200), capabilities)
        self.write_adapter("over-limit", words(1201), capabilities)
        self.write_adapter("embedded", words(1000) + "\n\n" + capabilities, capabilities)

        result = self.run_checker()

        self.assert_finding(result, "always-on-size", "harness/over-limit/always-on.md")
        findings = [line for line in result.stdout.splitlines() if line.startswith("always-on-size ")]
        self.assertEqual(len(findings), 1, result.stdout)

    def test_reports_invalid_utf8_and_forbidden_word_separators(self) -> None:
        self.write("rules/contract-invalid-utf8.md", b"\xff\n")
        self.write("workflows/invalid-separator.md", workflow("1").replace("A workflow", "A\x1cworkflow"))

        result = self.run_checker()

        self.assert_finding(result, "input-encoding", "rules/contract-invalid-utf8.md")
        self.assert_finding(result, "input-encoding", "workflows/invalid-separator.md")

    def test_requires_a_canonical_rule_kind_and_subject(self) -> None:
        invalid = ("guide", "rules-tdd", "contract", "protocol-")
        for name in (*invalid, "contract-guide", "protocol-guide", "procedure-guide"):
            self.write(f"rules/{name}.md", RULE)
        self.write("rules/bootstrap-guide.md", sized_bootstrap(30))

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertCountEqual(
            [(line.split()[0], line.split()[1].rsplit(":", 1)[0])
             for line in self.findings_for_minimal_fixture(result)],
            [("kind-prefix-invalid", f"rules/{name}.md") for name in invalid],
        )

    def test_reports_equal_rule_and_workflow_stems(self) -> None:
        self.write("rules/discovery.md", RULE)
        self.write("workflows/discovery.md", workflow("1", name="discovery"))

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertCountEqual(
            [line.split()[0] for line in self.findings_for_minimal_fixture(result)],
            ["kind-prefix-invalid", "name-collision"],
        )

    def test_reports_collisions_after_adding_installed_prefixes(self) -> None:
        self.write("rules/tdd.md", RULE)
        self.write("workflows/rule-tdd.md", workflow("1", name="rule-tdd"))
        self.write("principles/quality.md", "# Quality\n")
        self.write("workflows/principle-quality.md", workflow("1", name="principle-quality"))

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertCountEqual(
            [line.split()[0] for line in self.findings_for_minimal_fixture(result)],
            ["kind-prefix-invalid", "installed-name-collision", "installed-name-collision"],
        )
        for name in ("rule-tdd", "principle-quality"):
            with self.subTest(installed_name=name):
                self.assertTrue(
                    any(line.startswith("installed-name-collision ") and name in line
                        for line in result.stdout.splitlines()),
                    result.stdout,
                )

    def test_reports_casefolded_installed_workflow_names(self) -> None:
        self.write("workflows/retro.md", workflow("1", name="retro"))
        if (self.root / "workflows/Retro.md").exists():
            self.skipTest("The temporary filesystem is case-insensitive.")
        self.write("workflows/Retro.md", workflow("1", name="Retro"))

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertEqual([line.split()[0] for line in self.findings_for_minimal_fixture(result)],
                         ["installed-name-collision"])

    def test_requires_exact_ordered_bootstrap_headings(self) -> None:
        context = "## Context Bootstrap\n"
        behaviors = "## Phase Behaviors\n"
        self.write("rules/bootstrap-valid.md", RULE + context + "```md\n## Fenced example\n```\n" + behaviors)
        fixtures = {
            "extra": context + behaviors + "## Additional Notes\n",
            "duplicate": context + context + behaviors,
            "missing": context,
            "reversed": behaviors + context,
            "renamed": "## Context Bootstrap — Notes\n" + behaviors,
        }
        for name, body in fixtures.items():
            self.write(f"rules/bootstrap-{name}.md", RULE + body)

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertCountEqual(
            [(line.split()[0], line.split()[1].rsplit(":", 1)[0])
             for line in self.findings_for_minimal_fixture(result)],
            [("bootstrap-sections", f"rules/bootstrap-{name}.md") for name in fixtures],
        )

    def test_bootstrap_word_limit_includes_front_matter_and_fenced_code(self) -> None:
        self.write("rules/bootstrap-at-limit.md", sized_bootstrap(300))
        self.write("rules/bootstrap-over-limit.md", sized_bootstrap(301))
        self.write("rules/contract-long.md", RULE + words(301))

        result = self.run_checker()

        self.assert_finding(result, "bootstrap-size", "rules/bootstrap-over-limit.md")
        self.assertEqual(len(self.findings_for_minimal_fixture(result)), 1, result.stdout)

    def test_bootstrap_size_exception_applies_to_the_named_rule_at_the_listed_count(self) -> None:
        for name in ("exact", "changed", "unlisted"):
            self.write(f"rules/bootstrap-{name}.md", sized_bootstrap(316))
        self.write(
            "docs/audits/2024-02-29-rule-migration-map.md",
            "## Bootstrap size exceptions\n\n| Rule | Words | Reason |\n| --- | --- | --- |\n"
            "| `bootstrap-exact` | 316 | Context and citing line exceed 300 words |\n"
            "| `bootstrap-changed` | 315 | Context and citing line exceed 300 words |\n",
        )

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertCountEqual(
            [(line.split()[0], line.split()[1].rsplit(":", 1)[0])
             for line in self.findings_for_minimal_fixture(result)],
            [("bootstrap-size", f"rules/bootstrap-{name}.md") for name in ("changed", "unlisted")],
        )

    def write_pipeline_command(self, name: str) -> None:
        self.write(f"workflows/{name}.md", workflow('"-"', "orchestrated", name))
        self.write("docs/name-map.json", json.dumps({
            "schema_version": 1,
            "rows": [{"kind": "workflow", "old": "phase-pipeline", "new": [name]}],
        }))
        self.write(
            "docs/USAGE.md",
            "## Renamed commands and rules\n\n| Kind | Old | New |\n| --- | --- | --- |\n"
            f"| workflow | `phase-pipeline` | `{name}` |\n",
        )

    def test_absent_reserved_listing_is_informational(self) -> None:
        self.write_pipeline_command("pipeline")
        self.write_adapter("demo", "Fixture instructions", capability_declaration("demo", "no"))

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (1, MISSING_PHASE_CONTRACT_OUTPUT + "info reserved-names-absent demo\n", ""))

    def test_reserved_command_requires_the_prefixed_workflow_and_invocation(self) -> None:
        self.write_pipeline_command("pipeline")
        self.write_adapter("demo", "Fixture instructions", capability_declaration("demo", "no"))
        self.write_adapter("another", "Fixture instructions", capability_declaration("another", "no"))
        self.write(
            "harness/demo/reserved-names.txt",
            "runtime: Fixture runtime 1.0\nverified: 2024-02-29\nevidence: https://example.org/skills\n\n"
            "# Names from the fixture listing\npipeline\n",
        )

        with self.subTest(command="reserved"):
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
            findings = [line for line in self.findings_for_minimal_fixture(result) if not line.startswith("info ")]
            self.assertEqual(len(findings), 1, result.stdout)
            self.assertTrue(findings[0].startswith("reserved-name-collision "), result.stdout)
            self.assertIn("orchestrail-pipeline", findings[0])

        (self.root / "workflows/pipeline.md").unlink()
        self.write_pipeline_command("orchestrail-pipeline")
        source = "rules/contract-caller.md"
        self.write(source, RULE + "\nInvoke `/pipeline`.\n")
        with self.subTest(command="uninstalled"):
            self.assert_finding(self.run_checker(), "reference-missing", source)

        self.write(source, RULE + "\nInvoke `/orchestrail-pipeline`.\n")
        with self.subTest(command="prefixed"):
            result = self.run_checker()
            self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
            self.assertTrue(all(line.startswith("info ") for line in self.findings_for_minimal_fixture(result)),
                            result.stdout)

    def test_workflow_symlink_does_not_resolve_as_an_installed_command(self) -> None:
        self.write_pipeline_command("orchestrail-pipeline")
        (self.root / "workflows/pipeline.md").symlink_to("orchestrail-pipeline.md")
        caller = "workflows/caller.md"
        self.write(
            caller,
            workflow("1", name="caller") + "\nCall `/orchestrail-pipeline`.\nCall `/pipeline`.\n",
        )

        result = self.run_checker()

        self.assert_finding(result, "reference-missing", caller)
        missing = [line for line in result.stdout.splitlines() if line.startswith("reference-missing ")]
        self.assertEqual(len(missing), 1, result.stdout)
        self.assertTrue(missing[0].startswith(f"reference-missing {caller}:10 "), result.stdout)

    def test_rejects_a_reserved_names_fifo_without_blocking(self) -> None:
        self.write_pipeline_command("pipeline")
        self.write_adapter("demo", "Fixture instructions", capability_declaration("demo", "no"))
        relative = "harness/demo/reserved-names.txt"
        os.mkfifo(self.root / relative)

        try:
            result = subprocess.run(
                [sys.executable, "-I", str(CHECKER), "--root", str(self.root)],
                cwd=self.workspace,
                env=self.environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            self.fail("The checker blocked while opening the reserved-names FIFO.")

        self.assert_finding(result, "input-encoding", relative)

    def test_checks_capability_records_for_each_adapter(self) -> None:
        first = capability_declaration("fixture-first", "yes").replace(
            "evidence: docs/example.md", "evidence: docs/example.md\nevidence: docs/another.md", 1,
        )
        second = capability_declaration("fixture-second", "no")
        self.write_adapter("fixture-first", "Fixture instructions", first)
        self.write_adapter("fixture-second", "Fixture instructions", second)

        baseline = self.run_checker()
        self.assertEqual((baseline.returncode, baseline.stderr), (1, ""), baseline.stdout)
        self.assertEqual(self.findings_for_minimal_fixture(baseline),
                         ["info reserved-names-absent fixture-first", "info reserved-names-absent fixture-second"],
                         baseline.stdout)

        disabled_hooks = capability_record("hooks", "no")
        mutations = {
            "yes without evidence": (
                second.replace("\nevidence: docs/example.md", "", 1), "capability-schema",
            ),
            "no without evidence": (
                second.replace(disabled_hooks, disabled_hooks.replace("\nevidence: docs/example.md", "")),
                "capability-schema",
            ),
            "impossible date": (second.replace("2024-02-29", "2023-02-29", 1), "capability-schema"),
            "duplicate record": (f"{second}\n\n{capability_record('git', 'yes')}", "capability-schema"),
            "duplicate records section": (
                f"{second}\n\n## Capability records\n\n{capability_record('extension', 'unknown')}",
                "capability-schema",
            ),
            "invalid state": (second.replace("state: unknown", "state: maybe"), "capability-schema"),
            "missing limitations": (
                second.replace("\n\nLimitations: none known", "", 1), "capability-schema",
            ),
            "missing canonical record": (
                second.removesuffix(f"\n\n{capability_record('git', 'yes')}"), "capability-key-missing",
            ),
            "different location": (
                second.replace("always-on-path: $HOME/fixture-second", "always-on-path: $HOME/fixture-first"),
                "always-on-path-mismatch",
            ),
            "different hook state": (second.replace("\nhooks: no\n", "\nhooks: yes\n"), "hooks-state-mismatch"),
        }
        for label, (declaration, code) in mutations.items():
            with self.subTest(mutation=label):
                self.write("harness/fixture-second/capabilities.md", declaration + "\n")
                self.assert_finding(self.run_checker(), code, "harness/fixture-second/capabilities.md")

    def test_delivers_harness_adapter_paths(self) -> None:
        adapters = {
            "claude": {
                "skills_dir": "$HOME/.claude/skills",
                "always_on_path": "$HOME/.claude/CLAUDE.md",
                "project_skills_link_dir": ".claude/skills",
            },
            "codex": {
                "skills_dir": "$HOME/.codex/skills",
                "always_on_path": "$HOME/.codex/AGENTS.md",
            },
        }
        for name, expected in adapters.items():
            with self.subTest(adapter=name):
                relative = f"harness/{name}/deploy.env"
                adapter = SOURCE / relative
                self.assertTrue(adapter.is_file(), f"Missing delivered adapter declaration: {relative}")
                lines = adapter.read_bytes().decode("utf-8").split("\n")
                actual = [line for line in lines if line and not line.startswith("#")]
                self.assertCountEqual(actual, [f"{key}={value}" for key, value in expected.items()])

    def test_delivered_capabilities_preserve_prior_text_and_validate(self) -> None:
        legacy_rules = ("git-flow", "phase-finalize", "tdd", "workflow-globals")
        for name in legacy_rules:
            self.write(f"rules/{name}.md", RULE)
        for name in ("contract-git-flow", "contract-tdd", "contract-phases"):
            self.write(f"rules/{name}.md", RULE)
        self.write("rules/bootstrap-finalization.md", sized_bootstrap(100))
        for name in ("atomic-execution-tests", "atomic-execution-implement", "finalization", "phase-finalize"):
            self.write(f"workflows/{name}.md", workflow('"-"', name=name))

        # Hash the original prefix to protect existing text without copying it into the fixtures.
        originals = {
            "claude": (11057, "c46c9d152c9e62c4a2961c3860e49302fc232ff7509d133f3e0e995c33779f3c", "yes"),
            "codex": (672, "3c646d8e248e84f846900f785338a58104809201789b47da7279ee2971f16613", "no"),
        }
        for name, (length, digest, hooks) in originals.items():
            with self.subTest(adapter=name):
                relative = f"harness/{name}/capabilities.md"
                declaration = (SOURCE / relative).read_bytes()
                original_declaration = declaration
                if name == "claude":
                    heading = b"## Finalization receipt support\n\n"
                    framed = heading + RECEIPT_HISTORY_FRAME.encode("utf-8")
                    self.assertEqual(declaration.count(framed), 1, relative)
                    original_declaration = declaration.replace(framed, heading, 1)
                self.assertEqual(hashlib.sha256(original_declaration[:length]).hexdigest(), digest)
                lines = original_declaration[length:].decode("utf-8").lstrip("\n").splitlines()
                self.assertTrue(lines and lines[0] == "## Capability records", f"Missing records in {relative}")
                record_names = [line.removeprefix("name: ") for line in lines if line.startswith("name: ")]
                canonical = [key for key in record_names if key in CAPABILITY_KEYS]
                self.assertEqual(canonical, list(CAPABILITY_KEYS))

                adapter = f"harness/{name}/deploy.env"
                self.assertTrue((SOURCE / adapter).is_file(), f"Missing delivered adapter declaration: {adapter}")
                self.write(adapter, (SOURCE / adapter).read_bytes())
                body = f"harness/{name}/always-on.md"
                self.write(body, (SOURCE / body).read_bytes())
                self.write(relative, declaration)
                result = self.run_checker()
                self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
                self.assertCountEqual(
                    [" ".join(line.split()[:2]) for line in self.findings_for_minimal_fixture(result)
                     if not line.startswith("info ")],
                    [
                        *(f"kind-prefix-invalid rules/{rule}.md:0" for rule in legacy_rules),
                        "name-collision workflows/phase-finalize.md:0",
                    ],
                    result.stdout,
                )

                text = declaration.decode("utf-8")
                path_line = next(line for line in lines if line.startswith("always-on-path: "))
                other_hooks = "no" if hooks == "yes" else "yes"
                mutations = {
                    "capability-key-missing": text.replace("\nname: git\n", "\nname: auxiliary-git\n"),
                    "always-on-path-mismatch": text.replace(path_line, "always-on-path: $HOME/other/instructions.md"),
                    "hooks-state-mismatch": text.replace(f"\nhooks: {hooks}\n", f"\nhooks: {other_hooks}\n", 1),
                }
                for code, invalid in mutations.items():
                    self.write(relative, invalid)
                    self.assert_finding(self.run_checker(), code, relative)
                self.write(relative, declaration)

    def test_reports_legacy_mentions_with_source_lines_and_exclusions(self) -> None:
        self.write("rules/contract-guide.md", RULE + "\n\nWindsurf integration\n")
        self.write("scripts/report-legacy-artifacts.sh", "Windsurf integration\n")
        self.write(
            "docs/USAGE.md",
            "# Usage\n\n## Removed integrations\n\nWindsurf\n\n### Notes\nDevin\n"
            "\n## Setup\nCODEIUM and developing projects\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        locations = {line.split()[1] for line in result.stdout.splitlines() if line.startswith("legacy-mention ")}
        self.assertEqual(locations, {"rules/contract-guide.md:7", "docs/USAGE.md:11"}, result.stdout)

    def test_delivers_relocated_always_on_sources(self) -> None:
        for former, current in ALWAYS_ON_RELOCATIONS:
            with self.subTest(source=current):
                source = SOURCE / current
                self.assertTrue(source.is_file(), f"Missing relocated source: {current}")
                self.assertTrue(source.read_text(encoding="utf-8").strip(), f"Empty relocated source: {current}")
                self.assertFalse((SOURCE / former).exists(), f"Former source still exists: {former}")

    def test_accepts_current_always_on_source_references(self) -> None:
        former_sources = {former for former, _ in ALWAYS_ON_RELOCATIONS}

        result = self.run_checker(SOURCE)

        findings = []
        for line in result.stdout.splitlines():
            if line.startswith("stale-name "):
                names = line.partition(" Stale names: ")[2].removesuffix(".").split(", ")
                if former_sources.intersection(names):
                    findings.append(line)
        self.assertFalse(findings, "References to former always-on sources:\n" + "\n".join(findings))

    def test_rejects_invalid_name_maps_without_hiding_metadata_errors(self) -> None:
        valid_row = {"kind": "rule", "old": "guide", "new": ["contract-guide"]}
        invalid_rows = {
            "missing target": [{**valid_row, "new": []}],
            "workflow split": [{**valid_row, "kind": "workflow", "new": ["main", "extra"]}],
            "unknown row field": [{**valid_row, "reason": "Move"}],
            "malformed name": [{**valid_row, "old": "Guide"}],
            "unsafe file path": [{"kind": "file", "old": "../README.md", "new": ["docs/Guide.md"]}],
            "duplicate identity": [valid_row, {**valid_row, "new": ["contract-reference"]}],
            "duplicate target in a row": [{**valid_row, "new": ["contract-guide", "contract-guide"]}],
            "duplicate target across rows": [valid_row, {**valid_row, "old": "reference"}],
            "target is an old name": [valid_row, {**valid_row, "old": "contract-guide", "new": ["main"]}],
            "unsorted rows": [{**valid_row, "old": "reference", "new": ["contract-reference"]}, valid_row],
        }
        invalid_maps = {label: json.dumps({"schema_version": 1, "rows": rows}) for label, rows in invalid_rows.items()}
        invalid_maps.update({
            "duplicate JSON key": '{"schema_version": 1, "rows": [], "rows": []}',
            "incorrect schema version": '{"schema_version": true, "rows": []}',
            "invalid JSON": "[",
        })
        self.write("rules/contract-unrelated.md", RULE.replace("load: on-demand\n", ""))

        for label, document in invalid_maps.items():
            with self.subTest(mutation=label):
                self.write("docs/name-map.json", document)

                result = self.run_checker()

                self.assert_finding(result, "metadata-missing-field", "rules/contract-unrelated.md")
                self.assert_finding(result, "name-map-invalid", "docs/name-map.json")

    def test_requires_the_usage_table_to_list_each_split_target(self) -> None:
        self.write("docs/name-map.json", json.dumps({
            "schema_version": 1,
            "rows": [{"kind": "rule", "old": "guide", "new": ["contract-guide", "contract-guide-extra"]}],
        }))
        heading = "## Renamed commands and rules\n\n| Kind | Old | New |\n| --- | --- | --- |\n"
        row = "| rule | `guide` | `contract-guide`"
        self.write("docs/USAGE.md", f"{heading}{row} |\n")

        self.assert_finding(self.run_checker(), "usage-map-mismatch", "docs/USAGE.md")

        self.write("docs/USAGE.md", f"{heading}{row}, `contract-guide-extra` |\n")
        aligned = self.run_checker()
        self.assertEqual((aligned.returncode, aligned.stdout, aligned.stderr),
                         (1, MISSING_PHASE_CONTRACT_OUTPUT, ""))

    def test_resolves_executable_references_and_section_order(self) -> None:
        self.write("rules/contract-target.md", RULE + "\n## Guide — Notes\n### Run\n#### Finish\n## End\n")
        self.write("workflows/run.md", workflow("1", name="run"))
        examples = (
            ("Invoke `/run.md --dry-run`.", "reference-md-suffix"),
            ("Read `contract-target.md → ## Guide`.", "reference-md-suffix"),
            ("Invoke `/absent --dry-run`.", "reference-missing"),
            ("Read `no-such-stem → ## Guide`.", "reference-missing"),
            ("Load `rule-contract-absent`.", "reference-missing"),
            ("Load `contract-absent` rules.", "reference-missing"),
            ("Read `rules/contract-absent.md`.", "reference-missing"),
            ("Read `contract-target → ## End → ### Run`.", "heading-missing"),
            ("Read `contract-target → ## Absent`.", "heading-missing"),
            ("Run `/run --dry-run` and read `rules/contract-target.md`.", None),
            ("Read `/contract-target → ## Guide → ### Run → #### Finish`.", None),
            ("Read `state.md → ## Guide` and `principles/consumer.md`.", None),
            ("`` Rule `rule-contract-absent` goes in the example. ``", None),
            ("~~~md\n`/fenced-example`\n~~~", None),
        )
        source = "rules/contract-source.md"
        self.write(source, RULE + "\n" + "\n".join(example for example, _ in examples) + "\n")
        expected = {
            f"{code} {source}:{i}"
            for i, (_, code) in enumerate(examples, start=6) if code is not None
        }

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual({" ".join(line.split()[:2]) for line in self.findings_for_minimal_fixture(result)},
                         expected, result.stdout)

    def test_reports_stale_names_with_scan_and_retention_exceptions(self) -> None:
        self.write("docs/name-map.json", json.dumps({"schema_version": 1, "rows": [
            {"kind": "file", "old": "workflows/GUIDE.md", "new": ["docs/GUIDE.md"]},
            {"kind": "rule", "old": "guide", "new": ["contract-guide"]},
            {"kind": "workflow", "old": "old-command", "new": ["new-command"]},
        ]}))
        self.write(
            "docs/USAGE.md",
            "## Renamed commands and rules\n\n| Kind | Old | New |\n| --- | --- | --- |\n"
            "| file | `workflows/GUIDE.md` | `docs/GUIDE.md` |\n"
            "| rule | `guide` | `contract-guide` |\n"
            "| workflow | `old-command` | `new-command` |\n",
        )
        self.write("README.md", "Use /old-command\nSee docs/GUIDE.md\nSee workflows/GUIDE.md\n")
        self.write("templates/.ai/example.md", "Load `guide` rule.\nUse my-old-command.\nUse guide.\n")
        self.write("tests/fixtures/validator-runtime/source.txt", "old-command\n")
        self.write("scripts/check-lint-instructions.py", "old-command\n")
        self.write(
            "scripts/validate-contracts.sh",
            '  # old-command\ncheck "old-command" "$(old-command)"\nkeep old-command\n',
        )
        self.write(
            "docs/audits/2024-02-29-rule-migration-map.md",
            "## Retained old names\n\n| Path | Line text | Reason |\n| --- | --- | --- |\n"
            "| `scripts/validate-contracts.sh` | `keep old-command` | Fixed historical label |\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        locations = {line.split()[1] for line in result.stdout.splitlines() if line.startswith("stale-name ")}
        self.assertEqual(locations, {
            "README.md:1", "README.md:3", "templates/.ai/example.md:1", "scripts/validate-contracts.sh:2",
        }, result.stdout)


    def test_delivered_rule_metadata_preserves_rule_names_and_load_policy(self) -> None:
        rules = {
            "always": (
                "contract-git-flow", "contract-language", "contract-orchestration",
                "contract-quick-flow", "contract-run-log", "contract-tdd", "contract-phases",
            ),
            "on-demand": (
                *BOOTSTRAPS.values(), "contract-state-files",
                "protocol-autonomous-decision", "protocol-subtask-classifier", "protocol-discovery-conduct",
                "protocol-atomic-execution-conduct", "protocol-atomic-validation-conduct",
                "protocol-finalization-conduct", "procedure-blocker-reconciliation",
            ),
        }
        self.assertCountEqual(
            [path.stem for path in (SOURCE / "rules").glob("*.md")],
            [name for names in rules.values() for name in names],
        )
        for load, names in rules.items():
            for name in names:
                with self.subTest(rule=name):
                    metadata = self.source_metadata(f"rules/{name}.md")
                    self.assertIn(f"load: {load}", metadata)

    def test_delivered_workflow_metadata_preserves_workflow_names_and_step_order(self) -> None:
        phases = {phase: dict.fromkeys(names, '"-"') for phase, names in UNCHANGED_WORKFLOWS.items()}
        for _, new, phase, step, _ in COMMANDS:
            phases.setdefault(phase, {})[new] = step
        self.assertCountEqual(
            [path.stem for path in (SOURCE / "workflows").glob("*.md")],
            [name for workflows in phases.values() for name in workflows],
        )
        for phase, workflows in phases.items():
            for name, step in workflows.items():
                with self.subTest(workflow=name):
                    metadata = self.source_metadata(f"workflows/{name}.md")
                    self.assertIn(f"phase: {phase}", metadata)
                    self.assertIn(f"step: {step}", metadata)

    def source_metadata(self, relative: str) -> list[str]:
        lines = (SOURCE / relative).read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "---")
        metadata = lines[1:lines.index("---", 1)]
        self.assertEqual(sum(line.startswith("description: ") for line in metadata), 1, metadata)
        return metadata

    def test_delivered_active_documents_record_legacy_integrations_as_removed(self) -> None:
        active_paths = {"rules/contract-phases.md", "CLAUDE.md", "docs/USAGE.md"}
        usage = (SOURCE / "docs/USAGE.md").read_bytes().splitlines(keepends=True)
        self.assertIn(b"## Removed integrations\n", usage)
        setup = section(current("docs/USAGE.md"), "## 4. Initial Setup (new machine / standalone project)")
        self.assertEqual(
            [hashlib.sha256(line.encode()).hexdigest() for line in setup.splitlines(keepends=True)
             if line.startswith("git clone ")],
            ["76ca60298a3212a6b48f4f8de8668ab06e4d2d246278bc9ff37889af11210809"],
        )

        result = self.run_checker(SOURCE)

        findings = [
            line for line in result.stdout.splitlines()
            if line.startswith("legacy-mention ") and line.split()[1].rsplit(":", 1)[0] in active_paths
        ]
        self.assertEqual(findings, [], "\n".join(findings))

    def test_orchestration_implementer_references_keep_the_step_locator(self) -> None:
        orchestration = (SOURCE / "rules/contract-orchestration.md").read_text(encoding="utf-8")
        implementer = orchestration.split("\n### Implementer\n", 1)[1].split("\n### ", 1)[0]
        loop = "`/spec-run → ## Step 4 — Subtask loop`"
        references = [paragraph for paragraph in implementer.split("\n\n") if loop in paragraph]

        self.assertEqual(len(references), 2, implementer)
        for paragraph in references:
            prose = " ".join(paragraph.split("`")[::2])
            self.assertIn("4.2", prose)

    def test_delivered_source_tree_has_only_recorded_migration_findings(self) -> None:
        result = self.run_checker(SOURCE)

        self.assertEqual(result.stderr, "")
        findings = [line for line in result.stdout.splitlines() if not line.startswith("info ")]
        if any(row["kind"] == "workflow" for row in name_map()["rows"]):
            self.assertEqual((result.returncode, findings), (0, []), result.stdout)
        else:
            record, = SOURCE.glob("docs/audits/*-rule-migration-map.md")
            evidence = section(current(record), "## Pending command checks")
            trace = "\n".join(findings) + "\n"
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn(f"Findings: {len(findings)}", evidence)
            self.assertIn(f"SHA-256: {hashlib.sha256(trace.encode()).hexdigest()}", evidence)

    def test_rejects_invalid_deploy_env_as_data(self) -> None:
        env_path = "harness/demo/deploy.env"
        self.write_adapter("demo", "Fixture instructions", capability_declaration("demo", "no"))
        original = (self.root / env_path).read_bytes()
        baseline = self.run_checker()
        info = "info reserved-names-absent demo"
        self.assertEqual((baseline.returncode, baseline.stdout, baseline.stderr),
                         (1, MISSING_PHASE_CONTRACT_OUTPUT + info + "\n", ""))
        skills_line = b"skills_dir=$HOME/demo/skills\n"
        marker = self.workspace / "command-executed"
        fixtures = {
            "quotes": (original.replace(skills_line, b'skills_dir="$HOME/demo/skills"\n'), 1),
            "command substitution": (original.replace(skills_line, f'skills_dir=$(touch "{marker}")\n'.encode()), 1),
            "path traversal": (original.replace(skills_line, b"skills_dir=$HOME/demo/../skills\n"), 1),
            "trailing spaces": (original.replace(skills_line, b"skills_dir=$HOME/demo/skills \n"), 1),
            "unknown key": (original + b"extra=value\n", 3),
            "repeated key": (original + skills_line, 3),
            "invalid line ending": (original.replace(skills_line, skills_line.replace(b"\n", b"\r\n")), 1),
            "invalid UTF-8": (original + b"# \xff\n", 3),
            "missing required key": (original.replace(skills_line, b""), None),
        }
        for label, (contents, line) in fixtures.items():
            with self.subTest(fixture=label):
                self.write(env_path, contents)

                result = self.run_checker()

                self.assertFalse(marker.exists(), "The checker executed an adapter command.")
                self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
                findings = self.findings_for_minimal_fixture(result)
                self.assertIn(info, findings)
                findings.remove(info)
                self.assertEqual(len(findings), 1, result.stdout)
                prefix = f"deploy-env-invalid {env_path}:"
                if line is not None:
                    prefix += f"{line} "
                self.assertTrue(findings[0].startswith(prefix), result.stdout)

    def test_reports_an_incomplete_harness_adapter(self) -> None:
        for name, missing in (
            ("missing-body", "always-on.md"),
            ("missing-capabilities", "capabilities.md"),
            ("missing-declaration", "deploy.env"),
        ):
            self.write_adapter(name, "Fixture instructions", capability_declaration(name, "no"))
            (self.root / "harness" / name / missing).unlink()

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        findings = [line.split(maxsplit=2)[:2] for line in self.findings_for_minimal_fixture(result)]
        self.assertCountEqual(
            findings,
            [
                ["adapter-incomplete", "harness/missing-body/always-on.md:0"],
                ["adapter-incomplete", "harness/missing-capabilities/capabilities.md:0"],
                ["adapter-incomplete", "harness/missing-declaration/deploy.env:0"],
            ],
        )

    def test_ignores_hidden_adapters_and_orphaned_always_on_bodies(self) -> None:
        self.write("harness/orphan/always-on.md", words(1201))
        self.write("harness/.hidden/always-on.md", words(1201))
        self.write("harness/.hidden/deploy.env", "invalid adapter input\n")

        result = self.run_checker()

        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, MISSING_PHASE_CONTRACT_OUTPUT, ""))


    def test_frozen_rule_load_checks_follow_front_matter_scalar_grammar(self) -> None:
        source = (SOURCE / "scripts/validate-contracts.sh").read_text(encoding="utf-8")
        # Run only the three kept check expressions and their shared helper, if present.
        _, helper, remainder = source.partition("\nrule_loads_always() {\n")
        definition = ""
        if helper:
            body, closing, _ = remainder.partition("\n}\n")
            self.assertTrue(closing, "The rule load helper must have a complete definition")
            definition = helper + body + closing

        checks = {
            "TDD: rules/tdd.md is always_on": ("rules/contract-tdd.md",),
            "ORCH: $f is always_on": ("rules/contract-git-flow.md", "rules/contract-orchestration.md"),
            "LOG: rules/run-log.md is always_on": ("rules/contract-run-log.md",),
        }
        plain = RULE.replace("Check the contract", "Fixture — UTF-8").replace("on-demand", "always")
        fixtures = (
            ("plain", plain, True),
            ("JSON quoted", plain.replace("load: always", 'load: "always"'), True),
            ("JSON escaped", plain.replace("load: always", r'load: "\u0061lways"'), True),
            ("CRLF", plain.replace("\n", "\r\n"), True),
            ("wrong load", plain.replace("load: always", "load: on-demand"), False),
            ("duplicate load", plain.replace("load: always", "load: always\nload: always"), False),
            ("body-only load", plain.replace("load: always\n---", "---\n\nload: always"), False),
            ("missing opener", plain.removeprefix("---\n"), False),
            ("missing closer", plain.removesuffix("---\n"), False),
            ("malformed JSON", plain.replace("load: always", 'load: "always" extra'), False),
            ("invalid UTF-8", plain.encode("utf-8").replace(b"load: always", b"load: \xff"), False),
        )
        environment = dict(self.environment, BASH_ENV="/dev/null", LC_ALL="C")
        for label, paths in checks.items():
            marker = f'check "{label}" \\\n'
            self.assertEqual(source.count(marker), 1, label)
            expression = source.partition(marker)[2].splitlines()[0].strip()
            program = definition + f'f="$1"\nprintf "%s\\n" {expression}\n'
            for relative in paths:
                for fixture, contents, accepted in fixtures:
                    with self.subTest(check=label, path=relative, fixture=fixture):
                        self.write(relative, contents)
                        result = subprocess.run(
                            ["bash", "-c", program, "rule-load-check", relative], cwd=self.root,
                            env=environment, capture_output=True, text=True, timeout=5, check=False,
                        )
                        expected = "pass" if accepted else f"{relative} must declare load: always in its front matter"
                        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected + "\n", ""))


class GlobalInstructionGuidanceTests(unittest.TestCase):
    guidance_paths = ("rules/contract-language.md", "docs/USAGE.md")
    global_paths = ("~/.claude/CLAUDE.md", "~/.codex/AGENTS.md")

    def test_chat_language_guidance_points_to_project_local_instructions(self) -> None:
        self.assertTrue((SOURCE / "CLAUDE.md").is_file())
        self.assertTrue((SOURCE / "templates/AGENTS.md").is_file())

        for relative in self.guidance_paths:
            with self.subTest(document=relative):
                contents = (SOURCE / relative).read_text(encoding="utf-8")
                prose = contents.replace("`", "").lower()
                for global_path in self.global_paths:
                    self.assertFalse(
                        any(
                            advice + global_path.lower() in prose
                            for advice in ("set this in your personal ", "belongs in the user's personal ")
                        ),
                        f"{relative} still directs chat language preferences to {global_path}",
                    )
                paragraphs = [" ".join(part.split()) for part in contents.split("\n\n")]
                self.assertTrue(
                    any(
                        "chat language" in paragraph.lower()
                        and "project-local" in paragraph
                        and "`CLAUDE.md`" in paragraph
                        and "`AGENTS.md`" in paragraph
                        for paragraph in paragraphs
                    ),
                    f"{relative} must direct chat language preferences to both project-local instruction files",
                )

    def test_global_instruction_guidance_explains_sync_ownership_conflicts(self) -> None:
        for relative in self.guidance_paths:
            with self.subTest(document=relative):
                contents = (SOURCE / relative).read_text(encoding="utf-8")
                paragraphs = [" ".join(part.split()) for part in contents.split("\n\n")]
                self.assertTrue(
                    any(
                        all(f"`{path}`" in paragraph for path in self.global_paths)
                        and "`scripts/sync.sh` manages" in paragraph
                        and "edit" in paragraph.partition("next sync")[0].lower()
                        and "stop" in paragraph.partition("next sync")[2]
                        and "`ownership-conflict`" in paragraph.partition("next sync")[2]
                        for paragraph in paragraphs
                    ),
                    f"{relative} must describe sync ownership and the result of editing either global file",
                )


class InstructionSourceIsolationTests(unittest.TestCase):
    def test_checker_and_deployment_source_only_use_offline_programs(self) -> None:
        deployment_suite = SOURCE / "scripts/check-deploy-skills.py"
        offline_source_findings = runpy.run_path(str(deployment_suite))["offline_source_findings"]
        for path in (CHECKER, SOURCE / "scripts/deploy-skills.py", Path(__file__)):
            with self.subTest(path=path.name):
                self.assertEqual(offline_source_findings(path.read_text(encoding="utf-8")), [])


BASELINE_SHA256 = "9a11abfcfda9db1ff7411fc6f9b879f98e3c20ac967dc61c282df4dbc79ce7bc"
STATE_RULE = "workflow" + "-reference"
PHASE_RULE = "workflow" + "-globals"
BOOTSTRAPS = {
    f"phase-{phase if phase != 'finalization' else 'finalize'}": f"bootstrap-{phase}"
    for phase in ("discovery", "execution", "validation", "atomic-execution", "atomic-validation", "finalization")
}
CONTRACTS = {
    name: f"contract-{name}"
    for name in ("tdd", "git-flow", "orchestration", "quick-flow", "run-log", "language")
}
DISCOVERY = next(old for old, new in BOOTSTRAPS.items() if new == "bootstrap-discovery")
ATOMIC_EXECUTION = next(old for old, new in BOOTSTRAPS.items() if new == "bootstrap-atomic-execution")
RULE_TARGETS = {
    **{old: [new] for old, new in (CONTRACTS | BOOTSTRAPS).items()},
    PHASE_RULE: ["contract-phases"],
    STATE_RULE: ["contract-state-files", "protocol-autonomous-decision", "protocol-subtask-classifier"],
    DISCOVERY: ["bootstrap-discovery", "protocol-discovery-conduct"],
    ATOMIC_EXECUTION: ["bootstrap-atomic-execution", "procedure-blocker-reconciliation"],
}
PIPELINE = Path("workflows", "PIPELINE.md")
PUBLIC_PIPELINE = Path("docs", PIPELINE.name)
CONTEXT = "## Context Bootstrap"
BEHAVIORS = "## Phase Behaviors"
BLOCKER = "## Blocker Reconciliation"
PROTECTED = "## Protected Sections Contract"
DISCOVERY_HEADINGS = ("## Codebase Reading Rules", "## Decision Protocol")
STATE_SPLITS = {
    "## Autonomous Decision Protocol": "protocol-autonomous-decision",
    **dict.fromkeys(
        ("## Autonomous Subtask Classifier", "## Decomposition Decisions", "## Decomposition Rules"),
        "protocol-subtask-classifier",
    ),
}


def source(stem: str, group: str = "rules") -> Path:
    return Path(group, f"{stem}.md")


def current(path: Path | str) -> str:
    return (SOURCE / path).read_bytes().decode("utf-8")


@cache
def migration_baseline() -> dict:
    data = (SOURCE / "docs/audits/rule-migration-baseline.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != BASELINE_SHA256:
        raise ValueError("Rule migration baseline differs from the audited fixture")
    return json.loads(data)


def original_section(path: Path, heading: str) -> str:
    return migration_baseline()["rules"][path.as_posix()][heading]["text"]


def headings(document: str) -> list[tuple[str, str]]:
    starts = list(re.finditer(r"(?m)^## [^\n]+", document))
    ends = [match.start() for match in starts[1:]] + ([len(document)] if starts else [])
    return [(start.group(), document[start.start():end]) for start, end in zip(starts, ends, strict=True)]


def cells(line: str) -> tuple[str, ...]:
    values = (cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", line.strip().strip("|")))
    return tuple(re.sub(r"^(`{2,}) (.+) \1$", r"`\2`", cell) for cell in values)


def section(document: str, heading: str) -> str:
    return next((section for title, section in headings(document) if title == heading), "")


def name_map() -> dict:
    return json.loads(current("docs/name-map.json"))


def normalized(text: str, rows: list[dict]) -> str:
    for row in rows:
        old = row["old"]
        new = row["new"][0]
        if row["kind"] == "file":
            text = text.replace(old, new)
        elif row["kind"] == "workflow":
            text = re.sub(r"/" + re.escape(old) + r"(?![\w-])", f"/{new}", text)
            text = text.replace(str(source(old, "workflows")), str(source(new, "workflows")))
            text = re.sub(r"`" + re.escape(old) + r"(?= → )", f"`/{new}", text)
            text = re.sub(r"(?<![\w-])" + re.escape(old) + r"(?![\w-]| DONE\b| done\b)", new, text)
        else:
            for title, owner in STATE_SPLITS.items() if old == STATE_RULE else ():
                text = text.replace(f"`{old} → {title}", f"`{owner} → {title}")
            if old == ATOMIC_EXECUTION:
                text = text.replace(f"**Blocker Reconciliation** (`{old}` rules)",
                                    "**Blocker Reconciliation** (`procedure-blocker-reconciliation` rule)")
            text = text.replace(str(source(old)), str(source(new)))
            text = re.sub(r"(?<![\w-])rule-" + re.escape(old) + r"(?![\w-])", f"rule-{new}", text)
            text = re.sub(r"`" + re.escape(old) + r"(?:\.md)?(?= → |` rules?\b)", f"`{new}", text)
            if old in CONTRACTS:
                text = text.replace(f"`{old}`", f"`{new}`")
    return text


class RuleSourceMigration(unittest.TestCase):
    def record(self) -> str:
        records = list(SOURCE.glob("docs/audits/*-rule-migration-map.md"))
        self.assertEqual(len(records), 1, "Expected one rule migration semantics record")
        return current(records[0])

    def migrated_sections(self, first_target: str, title: str) -> str:
        if first_target == "contract-state-files":
            return STATE_SPLITS.get(title, first_target)
        if first_target == "bootstrap-discovery" and title in DISCOVERY_HEADINGS:
            return "protocol-discovery-conduct"
        if first_target == "bootstrap-atomic-execution" and title == BLOCKER:
            return "procedure-blocker-reconciliation"
        return first_target

    def isolated_command(self, *command: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="rule-source-contract-") as directory:
            paths = {name: str(Path(directory, leaf)) for name, leaf in (
                ("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_STATE_HOME", "state"),
            )}
            for path in paths.values():
                Path(path).mkdir()
            return subprocess.run(
                [sys.executable, *command], cwd=directory,
                env={**os.environ, **paths, "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True, text=True, check=False, timeout=timeout,
            )

    def test_name_map_and_usage_declare_each_canonical_source(self) -> None:
        rows = name_map()["rows"]
        mapped_rules = {row["old"]: row["new"] for row in rows if row["kind"] == "rule"}
        self.assertEqual(set(mapped_rules), set(RULE_TARGETS))
        for old, targets in RULE_TARGETS.items():
            with self.subTest(source=old):
                self.assertEqual(mapped_rules[old][:len(targets)], targets)
                extras = mapped_rules[old][len(targets):]
                allowed = [f"protocol-{BOOTSTRAPS[old].removeprefix('bootstrap-')}-conduct"] if old in BOOTSTRAPS else []
                self.assertTrue(set(extras) <= set(allowed), extras)
                self.assertFalse((SOURCE / source(old)).exists(), "The old rule is still present")
                for target in mapped_rules[old]:
                    load = "always" if target.startswith("contract-") and target != "contract-state-files" else "on-demand"
                    self.assertIn(f"\nload: {load}\n", current(source(target)).split("---", 2)[1])
        self.assertEqual({path.stem for path in (SOURCE / "rules").glob("*.md")},
                         {target for values in mapped_rules.values() for target in values})
        self.assertIn({"kind": "file", "old": str(PIPELINE), "new": [str(PUBLIC_PIPELINE)]}, rows)
        expected = [
            (row["kind"], f"`{row['old']}`", ", ".join(f"`{name}`" for name in row["new"]))
            for row in rows
        ]
        usage = section(current("docs/USAGE.md"), "## Renamed commands and rules")
        table = [cells(line) for line in usage.splitlines() if line.startswith("|")]
        self.assertEqual(table[0], ("Kind", "Old", "New"))
        self.assertEqual(table[2:], expected)

    def test_bootstrap_registry_and_size_exceptions_match_delivery(self) -> None:
        path = source("contract-phases")
        self.assertTrue((SOURCE / path).is_file(), "The shared phase contract has not moved")
        phase_contract = current(path)
        references = section(phase_contract, "## Rule references").splitlines()
        anchor = "A reference to rule `<name>` resolves to skill `rule-<name>` on every supported harness."
        self.assertEqual(references.count(anchor), 1)
        self.assertTrue(all(any(f"`{prefix}" in line for line in references)
                            for prefix in ("principle-", "ref-")))
        registry = section(phase_contract, CONTEXT)
        table = [cells(line) for line in registry.splitlines() if line.startswith("|")]
        self.assertEqual(table[0], ("Phase", "Skill", "Loaded by"))
        self.assertEqual(Counter(row[1] for row in table[2:]), Counter(f"`rule-{name}`" for name in BOOTSTRAPS.values()))
        for _, _, loaders in table[2:]:
            commands = re.findall(r"`/([a-z-]+)`", loaders)
            self.assertTrue(commands, loaders)
            for command in commands:
                self.assertTrue((SOURCE / source(command, "workflows")).is_file(), loaders)
        exceptions = section(self.record(), "## Bootstrap size exceptions").splitlines()
        sizes = {row[0].strip("`"): int(row[1]) for row in map(cells, exceptions)
                 if len(row) == 3 and row[1].isdecimal()}
        observed = {}
        for target in BOOTSTRAPS.values():
            with self.subTest(rule=target):
                text = current(source(target))
                self.assertEqual([heading for heading, _ in headings(text)], [CONTEXT, BEHAVIORS])
                if len(text.split()) > 300:
                    observed[target] = len(text.split())
                    preamble, behavior = text.split(BEHAVIORS, 1)
                    overflow = f"protocol-{target.removeprefix('bootstrap-')}-conduct"
                    self.assertEqual(behavior.strip(), f"Load the `{overflow}` rule before acting.")
                    self.assertTrue((SOURCE / source(overflow)).is_file())
                    self.assertGreater(len((preamble + BEHAVIORS + behavior).split()), 300)
        self.assertEqual(sizes, observed)

    def test_every_rule_section_has_its_canonical_owner_and_parent_digest(self) -> None:
        record = self.record()
        self.assertIn("SHA-256", record)
        rows = [cells(line) for line in record.splitlines() if line.startswith("|")]
        indexed = Counter((row[0].strip("`"), row[1].strip("`"), row[2].strip("`"), row[3].strip("`"))
                          for row in rows if len(row) == 8 and re.fullmatch(r"[a-f0-9]{64}", row[2].strip("`")))
        missing = []
        installed = {path.stem: current(path).splitlines() for path in (SOURCE / "rules").glob("*.md")}
        baseline = migration_baseline()["rules"]
        for old, paths in RULE_TARGETS.items():
            old_path = source(old)
            for title, evidence in baseline[old_path.as_posix()].items():
                target = source(self.migrated_sections(paths[0], title))
                owners = [str(source(name)) for name in (*paths, old)
                          for line in installed.get(name, ()) if line == title]
                record_key = (str(old_path), title, evidence["sha256"], str(target))
                if owners != [str(target)] or indexed[record_key] != 1:
                    missing.append((str(old_path), title, str(target), owners, indexed[record_key]))
        self.assertFalse(bool(missing), f"{len(missing)} invalid section owners or digests. First: {missing[:3]}")

    def test_blocker_reconciliation_and_discovery_conduct_have_one_authority(self) -> None:
        owner = source("procedure-blocker-reconciliation")
        self.assertTrue((SOURCE / owner).is_file(), "Blocker reconciliation is still embedded in the bootstrap")
        rows = name_map()["rows"]
        self.assertEqual(section(current(owner), BLOCKER).rstrip("\n"),
                         normalized(original_section(source(ATOMIC_EXECUTION), BLOCKER), rows).rstrip("\n"))
        owners = [path.stem for path in (SOURCE / "rules").glob("*.md") if BLOCKER in current(path).splitlines()]
        self.assertEqual(owners, [owner.stem])
        workflows = {row["old"]: row["new"][0] for row in rows if row["kind"] == "workflow"}
        for old in (ATOMIC_EXECUTION, "pae-implement"):
            command = workflows.get(old, old)
            self.assertRegex(current(source(command, "workflows")),
                             rf"`(?:rule-)?{owner.stem}(?:` rules?\b| → {BLOCKER}`)")
        conduct = source("protocol-discovery-conduct")
        rules = {path.stem: current(path) for path in (SOURCE / "rules").glob("*.md")}
        for title in DISCOVERY_HEADINGS:
            with self.subTest(section=title):
                self.assertEqual([name for name, body in rules.items() if title in body.splitlines()], [conduct.stem])
                self.assertEqual(section(rules[conduct.stem], title).rstrip("\n"),
                                 normalized(original_section(source(DISCOVERY), title), rows).rstrip("\n"))

    def test_protected_body_and_status_stop_lines_survive_rule_migration(self) -> None:
        path = source("contract-state-files")
        self.assertTrue((SOURCE / path).is_file(), "The protected sections contract has not moved")
        rows = name_map()["rows"]
        self.assertEqual(normalized(original_section(source(STATE_RULE), PROTECTED), rows),
                         section(current(path), PROTECTED))

        def protected_lines(texts: list[str]) -> Counter[str]:
            return Counter(line for text in texts for line in normalized(text, rows).splitlines()
                           if line.startswith("Status values for") or any(marker in line for marker in (
                               "**stop**", "atomic-tests", "pre-TDD task, TDD step skipped",
                           )))

        delivered = list(SOURCE.glob("rules/*.md")) + list(SOURCE.glob("workflows/*.md"))
        delivered += list(SOURCE.glob("harness/*/always-on.md")) + [SOURCE / PUBLIC_PIPELINE]
        expected_lines = protected_lines(["\n".join(lines) for lines in migration_baseline()["protected_lines"].values()])
        actual_lines = protected_lines([current(path) for path in delivered])
        self.assertFalse(expected_lines - actual_lines, f"Changed protected lines: {expected_lines - actual_lines}")
        if any(row["kind"] == "workflow" for row in rows):
            preflight = section(current("workflows/spec-run.md"), "## Guard")
            self.assertEqual(actual_lines - expected_lines, protected_lines([preflight]),
                             "The capability refusal is the only additional protected line")

    def test_isolated_deployment_installs_canonical_rules_and_omits_the_reference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rule-source-installation-") as directory:
            fixture = Path(directory)
            result = subprocess.run(
                [sys.executable, "-I", str(SOURCE / "scripts/deploy-skills.py"), "deploy",
                 "--from", str(SOURCE), "--hook-result", '{"status":"unavailable","reason":"fixture"}'],
                cwd=fixture, env={**os.environ, "HOME": str(fixture / "home"),
                                  "XDG_CONFIG_HOME": str(fixture / "config"), "XDG_STATE_HOME": str(fixture / "state")},
                capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for adapter in sorted(SOURCE.glob("harness/*/deploy.env")):
                with self.subTest(adapter=adapter.parent.name):
                    setting = next(line for line in current(adapter).splitlines() if line.startswith("skills_dir="))
                    skills = fixture / "home" / setting.removeprefix("skills_dir=$HOME/")
                    self.assertTrue(skills.is_dir(), f"Fixture installation did not create {skills}")
                    self.assertFalse(any(entry.name == PIPELINE.stem
                                         for entry in skills.iterdir()), "The pipeline reference was installed as a skill")
                    for source_rule in (SOURCE / "rules").glob("*.md"):
                        installed = skills / ("rule-" + source_rule.stem) / "SKILL.md"
                        self.assertEqual(installed.read_bytes(), source_rule.read_bytes(), str(installed))
        self.assertTrue((SOURCE / PUBLIC_PIPELINE).is_file())
        self.assertFalse((SOURCE / PIPELINE).exists())
        self.assertTrue(all(current(path).count("\nInvocation: ") == 1 for path in SOURCE.glob("workflows/*.md")))

    def test_current_rule_readers_and_frozen_inventory_are_coherent(self) -> None:
        lint = self.isolated_command("-I", str(SOURCE / "scripts/lint-instructions.py"), "--root", str(SOURCE))
        findings = [line for line in lint.stdout.splitlines() if not line.startswith("info ")]
        workflow_rows = [row for row in name_map()["rows"] if row["kind"] == "workflow"]
        self.assertEqual(lint.stderr, "")
        if workflow_rows:
            self.assertEqual((lint.returncode, findings), (0, []), lint.stdout)
        else:
            self.assertEqual(lint.returncode, 1, lint.stdout)
            for finding in findings:
                match = re.fullmatch(r"stale-name (.+):(\d+) Stale names: (.+)\.", finding)
                self.assertIsNotNone(match, finding)
                path, line_number, names = match.groups()
                line = current(path).splitlines()[int(line_number) - 1]
                for name in names.split(", "):
                    self.assertIn(name, BOOTSTRAPS, finding)
                    self.assertTrue((SOURCE / source(name, "workflows")).is_file(), finding)
                    self.assertRegex(line, rf"(?<![\w-]){name}(?![\w-])", finding)
                    self.assertNotRegex(line, rf"rule-{name}\b|rules/{name}\.md|`{name}` rules?\b", finding)
            trace = "\n".join(findings) + "\n"
            evidence = section(self.record(), "## Pending command checks")
            self.assertIn(f"Findings: {len(findings)}", evidence)
            self.assertIn(f"SHA-256: {hashlib.sha256(trace.encode()).hexdigest()}", evidence)
        oracle = self.isolated_command(
            "-B", str(SOURCE / "tests/validator-runtime-oracle.py"),
            "OracleContract.test_frozen_source_detects_actual_name_expression_and_order_changes",
            "OracleContract.test_amendment_pins_unrelated_fields_order_and_resource_changes",
        )
        self.assertEqual(oracle.returncode, 0, oracle.stdout + oracle.stderr)


class RuleMigrationRepairTests(unittest.TestCase):
    def test_export_checks_preserved_sections_without_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rule-migration-source-export-") as name:
            directory = Path(name)
            package = directory / "source package"
            package.mkdir()
            for relative in ("rules", "workflows", "harness", "docs/audits"):
                shutil.copytree(SOURCE / relative, package / relative)
            for relative in ("scripts/check-lint-instructions.py", "docs/name-map.json", "docs/PIPELINE.md"):
                target = package / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE / relative, target)
            self.assertFalse((package / ".git").exists())
            environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
            environment.update(HOME=name, XDG_CONFIG_HOME=name, XDG_STATE_HOME=name)
            arguments = [
                "-B", str(package / "scripts/check-lint-instructions.py"),
                "RuleSourceMigration.test_every_rule_section_has_its_canonical_owner_and_parent_digest",
                "RuleSourceMigration.test_protected_body_and_status_stop_lines_survive_rule_migration",
            ]

            result = subprocess.run([sys.executable, *arguments], cwd=package, env=environment, capture_output=True,
                                    text=True, check=False, timeout=30)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            target = package / "rules/protocol-subtask-classifier.md"
            target.write_text(target.read_text().replace("## Decomposition Rules", "## Removed section", 1))
            invalid = subprocess.run([sys.executable, *arguments], cwd=package, env=environment, capture_output=True,
                                     text=True, check=False, timeout=30)
            self.assertEqual(invalid.returncode, 1, invalid.stdout + invalid.stderr)
            self.assertIn("invalid section owners or digests", invalid.stderr)
            self.assertNotIn("CalledProcessError", invalid.stderr)

    def test_finalization_capability_frames_the_old_citation_as_historical(self) -> None:
        receipt = section(current("harness/claude/capabilities.md"), "## Finalization receipt support")
        framing, printed_record, historical = receipt.partition("The source git-rails core additionally recognizes")

        self.assertTrue(printed_record, receipt)
        self.assertIn("Canonical policy: `rules/git-flow.md → Finalization Git\nownership`.", historical)
        self.assertRegex(framing, r"(?i)historical")
        self.assertIn("`contract-git-flow → ## Finalization Git ownership`", framing)


# Public names, metadata and arguments are independent of the delivered name map.
COMMAND_MOVES = """\
phase-discovery discovery discovery "-" <path-to-spec> [--phase N] [--step-by-step]
pd-analyze discovery-analyze discovery 1 <task-directory> [--step-by-step]
pd-decompose discovery-decompose discovery 2 <task-directory> [--step-by-step]
pd-select-model discovery-select-model discovery 2.5 <path-to-atomic-description | task-directory> [--refresh]
pd-design discovery-design discovery 3 <task-directory> [--step-by-step]
pd-finalize discovery-finalize discovery 4 <task-directory> [--step-by-step]
pd-archive discovery-archive discovery 4b <task-directory>
phase-execution execution execution "-" <task-directory>
pe-execute execution-execute execution 1 <task-directory>
pe-finalize execution-finalize execution 2 <task-directory>
phase-validation validation validation "-" <task-directory>
pv-contract validation-contract validation 1 <task-directory>
pv-review validation-review validation 2 <task-directory>
pv-issues validation-issues validation 3 <task-directory>
pv-create-fixes validation-create-fixes validation 4 <task-directory>
pv-classify-fixes validation-classify-fixes validation 4a <task-directory>
pv-execute-fixes validation-execute-fixes validation 5 <task-directory>
pv-finalize validation-finalize validation 6 <task-directory>
phase-atomic-execution atomic-execution atomic-execution "-" <path-to-atomic-description>
pae-tests atomic-execution-tests atomic-execution 1 <path-to-atomic-description> [--batch] [--characterize]
pae-implement atomic-execution-implement atomic-execution 2 <path-to-atomic-description>
pae-finalize atomic-execution-finalize atomic-execution 3 <path-to-atomic-description>
phase-atomic-validation atomic-validation atomic-validation "-" <path-to-atomic-description> [--batch]
pav-check atomic-validation-check atomic-validation 1 <path-to-atomic-description>
pav-propose atomic-validation-propose atomic-validation 2 <path-to-atomic-description> [--batch]
pav-close atomic-validation-close atomic-validation 3 <path-to-atomic-description>
phase-composite-validation composite-validation atomic-validation "-" <path-to-composite-description>
phase-finalize finalization finalization "-" <task-directory|spec-path> [--dry-run]
phase-pipeline pipeline orchestrated "-" <spec-path|task-directory>
"""
COMMANDS = tuple(tuple(line.split(maxsplit=4)) for line in COMMAND_MOVES.splitlines())
UNCHANGED_WORKFLOWS = {
    "orchestrated": ("spec-run",),
    "entry": ("spec-draft", "spec-sync", "bugfix", "onboard-legacy-project"),
    "utility": ("adr-new", "context-pack", "retro", "restack", "compress-state",
                "suggest-commit-message", "suggest-commit-pr", "suggest-pr-description"),
}


class CanonicalWorkflowMigration(unittest.TestCase):
    def test_command_map_usage_and_invocations_agree(self) -> None:
        rows = name_map()["rows"]
        expected = [{"kind": "workflow", "old": old, "new": [new]} for old, new, *_ in sorted(COMMANDS)]
        observed = [row for row in rows if row["kind"] == "workflow"]
        self.assertEqual(observed, expected, "The map must publish all command renames in old-name order")
        usage = section(current("docs/USAGE.md"), "## Renamed commands and rules")
        table = [cells(line) for line in usage.splitlines() if line.startswith("|")]
        self.assertEqual(table[2:], [
            (row["kind"], f"`{row['old']}`", ", ".join(f"`{name}`" for name in row["new"]))
            for row in rows
        ])
        for old, new, phase, step, arguments in COMMANDS:
            with self.subTest(command=new):
                self.assertFalse((SOURCE / source(old, "workflows")).exists(), old)
                self.assertTrue((SOURCE / source(new, "workflows")).is_file(), new)
                document = current(source(new, "workflows"))
                metadata = document.split("---", 2)[1].splitlines()
                self.assertIn(f"phase: {phase}", metadata)
                self.assertIn(f"step: {step}", metadata)
                self.assertEqual(re.findall(r"(?m)^Invocation: .+$", document),
                                 [f"Invocation: `/{new} {arguments}`"])
        for phase, names in UNCHANGED_WORKFLOWS.items():
            for name in names:
                with self.subTest(command=name):
                    document = current(source(name, "workflows"))
                    metadata = document.split("---", 2)[1].splitlines()
                    self.assertIn(f"phase: {phase}", metadata)
                    self.assertIn('step: "-"', metadata)
                    self.assertRegex(document, rf"(?m)^Invocation: `/{name}(?:`| )")

    def test_dispatches_and_capability_table_use_installed_commands(self) -> None:
        dispatches = {
            "pipeline": ("discovery", "execution", "validation", "finalization"),
            "discovery": ("discovery-analyze", "discovery-decompose", "discovery-select-model",
                          "discovery-design", "discovery-finalize"),
            "discovery-finalize": ("discovery-archive",),
            "execution": ("execution-execute", "execution-finalize"),
            "execution-execute": ("atomic-execution", "atomic-validation"),
            "atomic-execution": ("atomic-execution-tests", "atomic-execution-implement",
                                 "atomic-execution-finalize"),
            "atomic-validation": ("atomic-validation-check", "atomic-validation-propose",
                                  "atomic-validation-close"),
            "atomic-validation-close": ("composite-validation",),
            "validation": ("validation-contract", "validation-review", "validation-issues",
                           "validation-create-fixes", "validation-execute-fixes", "validation-finalize"),
            "validation-create-fixes": ("validation-classify-fixes",),
        }
        for caller, children in dispatches.items():
            with self.subTest(caller=caller):
                path = SOURCE / source(caller, "workflows")
                self.assertTrue(path.is_file(), f"Missing installed dispatch source {caller}")
                references = set(re.findall(r"`/([a-z0-9-]+)(?=[ `])", path.read_text()))
                self.assertFalse(set(children) - references, f"Missing child calls in {caller}")
        capability = section(current(PHASE_CONTRACT), "## Capabilities")
        delivered = {row[0]: row[1:] for row in map(cells, capability.splitlines()) if len(row) == 4}
        for required in BEHAVIOUR_ROWS:
            behaviour, workflows, requires, _ = cells(required)
            with self.subTest(behaviour=behaviour):
                self.assertIn(behaviour, delivered)
                self.assertEqual(delivered[behaviour][:2], (workflows, requires))
        self.assertIn("`/pipeline <task-directory>`", delivered[cells(BEHAVIOUR_ROWS[0])[0]][2])
        self.assertIn("`note: approximate`", delivered[cells(BEHAVIOUR_ROWS[-1])[0]][2])

    def test_spec_run_stops_at_first_unavailable_sequential_capability_before_side_effects(self) -> None:
        document = current("workflows/spec-run.md")
        guard = section(document, "## Guard")
        self.assertTrue(guard)
        order = ("sub-agents", "agent-messaging", "git")
        mentions = re.findall(r"`(sub-agents|agent-messaging|git)`", guard)
        self.assertEqual(tuple(dict.fromkeys(mentions)), order)
        self.assertRegex(guard, r"(?i)first\s+(?:required\s+)?(?:unavailable|failing|failure|key)")
        self.assertIn("always-on", guard)
        stop = [line for line in guard.splitlines() if "**stop**" in line]
        message = ("spec-run requires capability <key> (declared: <yes|no|unknown|absent>; "
                   "session tool: <available|unavailable>). <next-step>")
        self.assertEqual(len(stop), 1, guard)
        self.assertIn(message, stop[0])
        self.assertTrue(any(
            "Use /pipeline <task-directory> for the single-session path." in line and "**stop**" not in line
            for line in guard.splitlines()
        ), guard)
        self.assertRegex(guard, r"(?is)state: yes.{0,180}(?:session|tool)")
        self.assertRegex(guard, r"(?is)before.{0,200}writ.{0,200}branch.{0,100}commit.{0,100}spawn.{0,100}(?:log|telemetry)")
        for heading in ("## Run Logging", "## Step 0"):
            self.assertLess(document.index("## Guard"), document.index(heading))
        self.assertNotRegex(guard, r"(?m)\brequire\b[^\n]*(?:worktrees|concurrent-sub-agents)")

    def test_isolated_export_installation_matches_all_resolved_sources(self) -> None:
        commands = {new for _, new, *_ in COMMANDS} | {name for names in UNCHANGED_WORKFLOWS.values() for name in names}
        paths = {name: source(name, "workflows") for name in commands}
        for directory, prefix in (("rules", "rule-"), ("principles", "principle-")):
            paths.update({prefix + path.stem: path.relative_to(SOURCE)
                          for path in (SOURCE / directory).glob("*.md")})
        with tempfile.TemporaryDirectory(prefix="command-installation-") as directory:
            fixture = Path(directory)
            package = fixture / "source export"
            for relative in ("workflows", "rules", "principles", "harness"):
                shutil.copytree(SOURCE / relative, package / relative)
            (package / "docs").mkdir()
            shutil.copyfile(SOURCE / "docs/name-map.json", package / "docs/name-map.json")
            (package / "scripts").mkdir()
            shutil.copyfile(SOURCE / "scripts/deploy-skills.py", package / "scripts/deploy-skills.py")
            environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
            environment.update(HOME=str(fixture / "home"), XDG_CONFIG_HOME=str(fixture / "config"),
                               XDG_STATE_HOME=str(fixture / "state"), GIT_CEILING_DIRECTORIES=str(fixture))
            hook = '{"reason":"fixture","status":"unavailable"}'
            result = subprocess.run(
                [sys.executable, "-I", str(package / "scripts/deploy-skills.py"), "deploy",
                 "--from", str(package), "--hook-result", hook],
                cwd=package, env=environment, capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for adapter in sorted((package / "harness").glob("*/deploy.env")):
                with self.subTest(harness=adapter.parent.name):
                    settings = dict(line.split("=", 1) for line in adapter.read_text().splitlines()
                                    if line.startswith(("skills_dir=", "always_on_path=")))
                    skills = fixture / "home" / settings["skills_dir"].removeprefix("$HOME/")
                    self.assertEqual({entry.name for entry in skills.iterdir()}, set(paths))
                    for name, relative in paths.items():
                        self.assertEqual({p.name for p in (skills / name).iterdir()}, {"SKILL.md"}, name)
                        self.assertEqual((skills / name / "SKILL.md").read_bytes(), (package / relative).read_bytes(), name)
                    installed = fixture / "home" / settings["always_on_path"].removeprefix("$HOME/")
                    hook_result = hook if (adapter.parent / "hooks.json").is_file() else (
                        '{"reason":"no-native-adapter","status":"unavailable"}'
                    )
                    instructions = (adapter.parent / "always-on.md").read_bytes()
                    declaration = (adapter.parent / "capabilities.md").read_bytes()
                    self.assertEqual(installed.read_bytes(), instructions + b"\n<!-- Logging capabilities -->\n"
                                     + declaration + b"\n## Current hook installation\n\ninstallation-result: "
                                     + hook_result.encode() + b"\n")

    def test_strict_checker_accepts_the_complete_migration(self) -> None:
        result = subprocess.run([sys.executable, "-I", str(CHECKER)], cwd=SOURCE,
                                capture_output=True, text=True, check=False, timeout=30)
        findings = [line for line in result.stdout.splitlines() if not line.startswith("info ")]
        self.assertEqual((result.returncode, result.stderr, findings), (0, "", []), result.stdout)

    def test_audited_pipeline_reference_rows_name_the_applied_command_fixes(self) -> None:
        record, = SOURCE.glob("docs/audits/*-rule-migration-map.md")
        table = section(current(record), "## Pre-existing reference defects")
        pipeline = SOURCE / "workflows/pipeline.md"
        self.assertTrue(pipeline.is_file(), "Missing the pipeline that dispatches the canonical commands")
        current_pipeline = pipeline.read_text()
        mapped = {old: new for old, new, *_ in COMMANDS}
        mapped["compress-state"] = "compress-state"
        fixes = [
            (old.strip("`").removesuffix(".md"), fix)
            for location, old, fix in (row for row in map(cells, table.splitlines()) if len(row) == 3)
            if location.startswith("`workflows/phase-pipeline.md:")
        ]
        self.assertEqual(len(fixes), 22, table)
        for old, fix in fixes:
            with self.subTest(audited_reference=old):
                self.assertIn(old, mapped)
                self.assertIn(f"`/{mapped[old]}`", fix)
                self.assertRegex(current_pipeline, rf"`/{mapped[old]}(?=[ `])")

    def test_finalization_retains_journal_authority_and_uses_the_new_log_name(self) -> None:
        old = "phase-finalize"
        canonical = "finalization"
        fixtures = runpy.run_path(str(SOURCE / "scripts/check-phase-finalize.py"))
        case = fixtures["FinalizationChecks"]()
        self.addCleanup(case.doCleanups)
        case.setUp()
        prior = case.prepare()
        journal = Path(prior["journal_path"])
        prepared = json.loads(journal.read_bytes())
        authority = {"invocation": old, "task_path": str(case.task), "cleanup": True}
        self.assertEqual(prepared["authorization"], authority)
        recorded = case.checkpoint("record", prior)
        self.assertEqual(recorded["status"], "recorded", recorded)
        valid = journal.read_bytes()
        invalid = json.loads(valid)
        self.assertEqual(invalid["authorization"], authority)
        invalid["authorization"]["invocation"] = canonical
        journal.write_text(json.dumps(invalid, sort_keys=True, indent=2) + "\n")
        changed = journal.read_bytes()
        revision = hashlib.sha256(changed).hexdigest()
        case.blocked(case.checkpoint("attempt", {"revision": revision}), "authorization-required")
        self.assertEqual(journal.read_bytes(), changed)

        path = SOURCE / source(canonical, "workflows")
        self.assertTrue(path.is_file(), "The compatible finalization command has not been installed under its new name")
        logging = section(path.read_text(), "## Run Logging")
        pipeline = re.search(r"\brun-start --pipeline ([a-z-]+)\b", logging)
        step = re.search(r"\bstep --run [^\s]+ --step ([a-z-]+)\b", logging)
        self.assertIsNotNone(pipeline, logging)
        self.assertIsNotNone(step, logging)
        self.assertEqual((pipeline[1], step[1]), (canonical, canonical), logging)

        current_producer = SOURCE / "scripts/log-step.sh"
        old_source = case.root / "pre-migration source"
        old_producer = old_source / "scripts/log-step.sh"
        old_producer.parent.mkdir(parents=True)
        old_workflow = old_source / source(old, "workflows")
        old_workflow.parent.mkdir()
        old_workflow.write_text(workflow('"-"', phase=canonical, name=old))
        shutil.copyfile(current_producer, old_producer)

        def log(*arguments: str, producer: Path = current_producer) -> str:
            result = subprocess.run(
                ["bash", str(producer), *arguments], cwd=case.root,
                env={**case.environment(), "ORCHESTRAIL_HOME": str(producer.parents[1]),
                     "ORCHESTRAIL_LOG_ROOT": str(case.root / "telemetry")},
                capture_output=True, text=True, check=False, timeout=10,
            )
            self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)
            return result.stdout.strip()

        history = log("run-start", "--pipeline", old, producer=old_producer)
        history_file = Path(log("path", "--run", history))
        log("step", "--run", history, "--step", old, "--outcome", "ok", producer=old_producer)
        log("run-end", "--run", history, "--outcome", "completed", producer=old_producer)
        history_bytes = history_file.read_bytes()

        current_run = log("run-start", "--pipeline", pipeline[1])
        current_file = Path(log("path", "--run", current_run))
        log("step", "--run", current_run, "--step", step[1], "--outcome", "ok")
        log("run-end", "--run", current_run, "--outcome", "completed")
        entries = [json.loads(line) for line in current_file.read_bytes().splitlines()]
        self.assertEqual([entry["pipeline"] for entry in entries], [canonical] * 3)
        self.assertEqual(entries[1]["step"], canonical)
        self.assertEqual(history_file.read_bytes(), history_bytes)
        self.assertEqual([json.loads(line)["pipeline"] for line in history_bytes.splitlines()], [old] * 3)


class CapabilityDispatchContract(unittest.TestCase):
    def test_capabilities_require_dispatch_access_and_fresh_evidence(self) -> None:
        declaration = section(current(PHASE_CONTRACT), "## Capabilities").partition("| Behaviour |")[0]
        prose = " ".join(declaration.replace("`", "").lower().split())
        expectations = {
            "declaration source": r"\balways-on\b",
            "unavailable declarations": r"(?=[^.]*\bno\b)(?=[^.]*\bunknown\b)(?=[^.]*\babsent\b)[^.]*\bunavailable\b",
            "declared yes still needs access": r"(?=[^.]*\byes\b)(?=[^.]*\bsession\b)(?=[^.]*\btools?\b)[^.]*\bpermissions?\b",
            "dispatch timing": r"\bat dispatch\b",
            "no network probing": r"\b(?:without|avoid|no)\b[^.]*\bnetwork prob(?:e|es|ing)\b",
            "fresh evidence": r"(?=[^.]*\brecords?\b)(?=[^.]*\bchang(?:e|es|ed|ing)\b)[^.]*\bnew evidence\b",
        }
        for requirement, pattern in expectations.items():
            with self.subTest(requirement=requirement):
                self.assertRegex(prose, pattern)

        spec_run = current("workflows/spec-run.md")
        repository_mode = section(spec_run, "## Repository mode")
        self.assertLess(spec_run.index("\n## Guard\n"), spec_run.index("\n## Repository mode\n"))
        self.assertRegex(repository_mode, r"(?i)\b(?:after|once) (?:the )?(?:capability )?(?:guard|preflight)\b")
        self.assertNotIn("before anything else", repository_mode.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
