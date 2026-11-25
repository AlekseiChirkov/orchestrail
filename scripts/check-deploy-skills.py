#!/usr/bin/env python3
"""Check harness deployment contracts with isolated homes and project fixtures."""

import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]
REPORTER = SOURCE / "scripts/report-legacy-artifacts.sh"
CHECKER = SOURCE / "scripts/lint-instructions.py"


class LegacyArtifactReporterTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "fixture home"
        self.project = self.root / "project 'with spaces'\nand $dollars"
        self.config = self.root / "config"
        self.state = self.root / "state"
        for path in (self.home, self.project, self.config, self.state):
            path.mkdir()
        self.environment = {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.config),
            "XDG_STATE_HOME": str(self.state),
            "PATH": os.defpath,
            "LC_ALL": "C",
        }

    def snapshot(self) -> dict[Path, tuple[int, int, bytes | str | None]]:
        entries = {}
        for path in self.root.rglob("*"):
            info = path.lstat()
            payload = None
            if stat.S_ISLNK(info.st_mode):
                payload = os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                payload = path.read_bytes()
            entries[path.relative_to(self.root)] = (info.st_mode, info.st_mtime_ns, payload)
        return entries

    def run_reporter(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        self.assertTrue(REPORTER.is_file(), "The legacy reporter entry point is missing")
        return subprocess.run(
            ["bash", str(REPORTER), *arguments],
            cwd=self.root,
            env=self.environment,
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=15,
        )

    def expected_line(self, path: Path) -> str:
        quoted = subprocess.run(
            ["bash", "-c", 'printf "%q" "$1"', "bash", str(path)],
            cwd=self.root,
            env=self.environment,
            capture_output=True,
            encoding="utf-8",
            check=True,
            timeout=15,
        ).stdout
        return (
            f"legacy: {quoted} — created by an earlier Orchestrail version; "
            f"review it, then remove it manually if unused: rm -r -- {quoted}\n"
        )

    def assert_reports(self, paths: list[Path], *arguments: str) -> None:
        before = self.snapshot()
        result = self.run_reporter(*arguments)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, "".join(self.expected_line(path) for path in paths))

    def test_global_reports_only_registered_paths_in_order(self) -> None:
        integrations = self.home / ".codeium/windsurf"
        workflows = integrations / "global_workflows"
        rules = integrations / "global_rules"
        workflows.mkdir(parents=True)
        (workflows / "retained.md").write_bytes(b"Retained workflow")
        rules.write_bytes(b"Retained rules")
        (integrations / "unrelated").mkdir()
        (self.project / ".devin").mkdir()

        self.assert_reports([workflows, rules], "global")

    def test_project_reports_shell_sensitive_paths_without_writes(self) -> None:
        windsurf = self.project / ".windsurf"
        devin = self.project / ".devin"
        (windsurf / "rules").mkdir(parents=True)
        (windsurf / "rules/tdd.md").write_bytes(b"Retained project rule")
        devin.mkdir()
        (devin / "settings.json").write_bytes(b"{}\n")

        for _ in range(2):
            self.assert_reports([windsurf, devin], "project", str(self.project))

    def test_missing_objects_emit_nothing_and_dangling_symlinks_are_reported(self) -> None:
        self.assert_reports([], "global")
        self.assert_reports([], "project", str(self.project))

        windsurf = self.project / ".windsurf"
        windsurf.symlink_to(self.root / "absent target")
        workflows = self.home / ".codeium/windsurf/global_workflows"
        workflows.parent.mkdir(parents=True)
        workflows.symlink_to(self.root / "absent global target")

        self.assert_reports([windsurf], "project", str(self.project))
        self.assert_reports([workflows], "global")

    def test_invalid_invocations_return_usage_status_without_writes(self) -> None:
        before = self.snapshot()
        arguments = ((), ("other",), ("global", "extra"), ("project",), ("project", ""),
                     ("project", str(self.project), "extra"))
        for command in arguments:
            with self.subTest(arguments=command):
                result = self.run_reporter(*command)
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")

    def test_removed_integrations_section_is_exempt_from_legacy_lint(self) -> None:
        usage = (SOURCE / "docs/USAGE.md").read_text(encoding="utf-8")
        heading = "## Removed integrations"
        _, found, remainder = usage.partition(f"\n{heading}\n")
        self.assertTrue(found, "The usage guide is missing the Removed integrations heading")
        section = remainder.partition("\n## ")[0]
        for integration in ("windsurf", "codeium", "devin"):
            self.assertIn(integration, section.casefold())

        docs = self.root / "docs"
        docs.mkdir()
        (docs / "USAGE.md").write_text(f"{heading}\n{section}\n", encoding="utf-8")
        rules = self.root / "rules"
        rules.mkdir()
        (rules / "contract-demo.md").write_text(
            "---\ndescription: An example rule\nload: on-demand\n---\n\n# Rule\nWindsurf\n",
            encoding="utf-8",
        )
        scripts = self.root / "scripts"
        scripts.mkdir()
        self.assertTrue(REPORTER.is_file(), "The legacy reporter entry point is missing")
        (scripts / REPORTER.name).write_bytes(REPORTER.read_bytes())

        result = subprocess.run(
            [sys.executable, "-I", str(CHECKER), "--root", str(self.root)],
            cwd=self.root,
            env=self.environment,
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=15,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "legacy-mention rules/contract-demo.md:7 Legacy integration mention: Windsurf.",
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
