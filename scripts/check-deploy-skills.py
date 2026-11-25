#!/usr/bin/env python3
"""Check harness deployment contracts with isolated homes and project fixtures."""

from contextlib import chdir
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


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


ENGINE = SOURCE / "scripts/deploy-skills.py"
HOOK_RESULT = '{"status":"unavailable","reason":"fixture"}'
NO_NATIVE_HOOK = b'{"reason":"no-native-adapter","status":"unavailable"}'
SKILL_BYTES = b"---\ndescription: Current skill\n---\n\n# Current skill\n"
OWNERSHIP_RESOLUTION = (
    "changed since the last deployment; save your changes elsewhere, then delete the "
    "file or restore its deployed bytes, and rerun"
)


class PlannerFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.home = root / "fixture home"
        self.config = root / "config"
        self.state = root / "state"
        self.source = root / "source"
        self.environment = {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.config),
            "XDG_STATE_HOME": str(self.state),
            "PATH": str(root / "bin"),
            "LC_ALL": "C",
        }
        for path in (self.home, self.config, self.state, root / "bin"):
            path.mkdir()
        for directory in ("workflows", "rules", "principles"):
            (self.source / directory).mkdir(parents=True)
        self.write(self.source / "workflows/current.md", SKILL_BYTES)
        self.make_harness("alpha")
        self.make_harness("omega")

    def make_harness(self, name: str) -> None:
        adapter = self.source / "harness" / name
        always_on = f"$HOME/.{name}/AGENTS.md"
        settings = f"skills_dir=$HOME/.{name}/skills\nalways_on_path={always_on}\n"
        self.write(adapter / "deploy.env", settings.encode())
        self.write(adapter / "always-on.md", f"# {name} instructions\n".encode())
        capabilities = (SOURCE / "harness/codex/capabilities.md").read_bytes()
        self.write(adapter / "capabilities.md", capabilities.replace(
            b"$HOME/.codex/AGENTS.md", always_on.encode(),
        ))

    @staticmethod
    def write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def adapter(self, name: str = "alpha") -> Path:
        return self.source / "harness" / name / "deploy.env"

    def skills_dir(self, name: str = "alpha") -> Path:
        return self.home / f".{name}" / "skills"

    def skill(self, name: str, harness: str = "alpha") -> Path:
        return self.skills_dir(harness) / name / "SKILL.md"

    def always_on(self, name: str = "alpha") -> Path:
        return self.home / f".{name}" / "AGENTS.md"

    def assembled_always_on(self, name: str) -> bytes:
        adapter = self.adapter(name).parent
        return (
            (adapter / "always-on.md").read_bytes() + b"\n<!-- Logging capabilities -->\n"
            + (adapter / "capabilities.md").read_bytes()
            + b"\n## Current hook installation\n\ninstallation-result: " + NO_NATIVE_HOOK + b"\n"
        )

    def manifest_path(self, name: str = "alpha") -> Path:
        return self.config / "orchestrail" / "deploy" / f"{name}.json"

    @staticmethod
    def manifest_object(path: Path, payload: bytes, name: str | None = None) -> dict:
        return {
            "kind": "always-on" if name is None else "skill",
            "name": name,
            "path": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def manifest(self, name: str, *objects: dict) -> dict:
        root = self.skills_dir(name)
        resolved = root.resolve()
        return {
            "schema_version": 1,
            "harness": name,
            "install_id": hashlib.sha256(f"{name}\n{resolved}".encode()).hexdigest(),
            "skills_dir": str(root),
            "skills_dir_resolved": str(resolved),
            "always_on_path": str(self.always_on(name)),
            "source_revision": None,
            "objects": sorted(objects, key=lambda item: item["path"]),
        }

    @staticmethod
    def manifest_bytes(manifest: dict) -> bytes:
        return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

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


class DeploymentPlanningTests(unittest.TestCase):
    def fixture(self) -> PlannerFixture:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return PlannerFixture(Path(temporary.name))

    def plan(self, fixture: PlannerFixture, *, refusal: str | None = None):
        self.assertTrue(ENGINE.is_file(), "The side-effect-free deployment planner is missing")
        before = fixture.snapshot()
        try:
            with chdir(fixture.root), patch.dict(os.environ, fixture.environment, clear=True):
                engine = runpy.run_path(str(ENGINE))
                planner = engine.get("_plan_deployment")
                self.assertTrue(callable(planner), "The side-effect-free deployment planner is missing")
                if refusal is None:
                    return planner(fixture.source, HOOK_RESULT)
                with self.assertRaises(engine["_DeploymentError"]) as caught:
                    planner(fixture.source, HOOK_RESULT)
                error = caught.exception
                self.assertEqual(error.exit_status, 1)
                self.assertEqual(error.code, refusal)
                separator = " " if refusal == "ownership-conflict" else ": "
                self.assertTrue(str(error).startswith(f"ERROR {refusal}{separator}"), str(error))
                return str(error)
        finally:
            self.assertEqual(fixture.snapshot(), before)

    def test_first_plan_adopts_existing_targets_and_keeps_unowned_files(self) -> None:
        fixture = self.fixture()
        fixture.write(fixture.skill("current"), b"Earlier deployment bytes")
        fixture.write(fixture.skill("obsolete"), b"Unowned bytes")
        fixture.write(fixture.source / "harness/orphan/always-on.md", b"Orphaned body")
        fixture.write(fixture.skill("current", "omega"), SKILL_BYTES)

        plan = self.plan(fixture)

        self.assertCountEqual([(action.kind, action.path) for action in plan.actions], [
            ("adopt", fixture.skill("current")),
            ("create", fixture.always_on()),
            ("create", fixture.always_on("omega")),
        ])
        for harness in ("alpha", "omega"):
            expected = fixture.manifest(
                harness,
                fixture.manifest_object(fixture.skill("current", harness), SKILL_BYTES, "current"),
                fixture.manifest_object(fixture.always_on(harness), fixture.assembled_always_on(harness)),
            )
            self.assertEqual(
                plan.manifests[fixture.manifest_path(harness)], fixture.manifest_bytes(expected),
            )

    def test_plan_removes_only_unchanged_obsolete_owned_files(self) -> None:
        fixture = self.fixture()
        old = fixture.skill("old")
        edited = fixture.skill("edited")
        missing = fixture.skill("missing")
        foreign = fixture.skill("foreign")
        current = fixture.skill("current")
        fixture.write(old, b"Owned old bytes")
        fixture.write(old.parent / "personal.md", b"Keep the directory and this foreign file")
        fixture.write(edited, b"Edited after deployment")
        fixture.write(foreign, b"Never owned")
        fixture.write(current, b"Owned previous bytes")
        always_on = fixture.assembled_always_on("alpha")
        fixture.write(fixture.always_on(), always_on)
        before = fixture.manifest(
            "alpha",
            fixture.manifest_object(old, b"Owned old bytes", "old"),
            fixture.manifest_object(edited, b"Before user edit", "edited"),
            fixture.manifest_object(missing, b"Before deletion", "missing"),
            fixture.manifest_object(current, b"Owned previous bytes", "current"),
            fixture.manifest_object(fixture.always_on(), always_on),
        )
        fixture.write(fixture.manifest_path(), fixture.manifest_bytes(before))
        fixture.write(
            fixture.source / "workflows/new.md", b"---\ndescription: New skill\n---\n\n# New skill\n",
        )

        plan = self.plan(fixture)

        actions = [(action.kind, action.path) for action in plan.actions]
        self.assertCountEqual([path for kind, path in actions if kind == "remove"], [old])
        self.assertIn(("create", fixture.skill("new")), actions)
        self.assertIn(("replace", current), actions)
        self.assertIn(f"release-modified {edited}", plan.notices)
        self.assertIn(f"keep-nonempty {old.parent}", plan.notices)
        desired = json.loads(plan.manifests[fixture.manifest_path()])
        self.assertCountEqual([obj["path"] for obj in desired["objects"]], [
            str(fixture.always_on()), str(current), str(fixture.skill("new")),
        ])

    def test_rejects_unsafe_target_types(self) -> None:
        for target, file_type in (
            ("skill", "symlink"), ("skill-directory", "symlink"), ("always-on", "symlink"),
            ("skill", "directory"), ("always-on", "directory"),
            ("skills-root", "file"), ("skill-directory", "file"), ("always-on-parent", "file"),
        ):
            with self.subTest(target=target, file_type=file_type):
                fixture = self.fixture()
                skill = fixture.skill("current", "omega")
                always_on = fixture.always_on("omega")
                path = {
                    "skill": skill, "skill-directory": skill.parent,
                    "skills-root": fixture.skills_dir("omega"),
                    "always-on": always_on, "always-on-parent": always_on.parent,
                }[target]
                path.parent.mkdir(parents=True, exist_ok=True)
                if file_type == "symlink":
                    protected = fixture.root / "foreign target"
                    if target == "skill-directory":
                        fixture.write(protected / "SKILL.md", b"Foreign target bytes")
                    else:
                        protected.write_bytes(b"Foreign target bytes")
                    path.symlink_to(protected, target_is_directory=target == "skill-directory")
                elif file_type == "directory":
                    path.mkdir()
                else:
                    path.write_bytes(b"Foreign target bytes")

                self.assertIn(str(path), self.plan(fixture, refusal="unsafe-target"))

    def test_rejects_manifest_skill_outside_resolved_root(self) -> None:
        fixture = self.fixture()
        outside = fixture.root / "foreign/SKILL.md"
        fixture.write(outside, b"Do not remove")
        obj = fixture.manifest_object(outside, b"Do not remove", "obsolete")
        fixture.write(fixture.manifest_path(), fixture.manifest_bytes(fixture.manifest("alpha", obj)))

        self.plan(fixture, refusal="unsafe-target")

    def test_rejects_invalid_manifests(self) -> None:
        fixture = self.fixture()
        obj = fixture.manifest_object(fixture.skill("current"), SKILL_BYTES, "current")
        manifest = fixture.manifest("alpha", obj)
        manifest_bytes = fixture.manifest_bytes(manifest)
        cases = {
            "unknown key": fixture.manifest_bytes(manifest | {"unexpected": True}),
            "unsupported version": fixture.manifest_bytes(manifest | {"schema_version": 2}),
            "wrong version type": fixture.manifest_bytes(manifest | {"schema_version": True}),
            "duplicate key": manifest_bytes.replace(
                b'"harness": "alpha",', b'"harness": "alpha", "harness": "alpha",',
            ),
            "duplicate object key": manifest_bytes.replace(
                b'"kind": "skill",', b'"kind": "skill", "kind": "skill",',
            ),
            "duplicate object identity": fixture.manifest_bytes(manifest | {"objects": [obj, obj]}),
            "unknown object key": fixture.manifest_bytes(manifest | {"objects": [obj | {"extra": 1}]}),
            "wrong revision type": fixture.manifest_bytes(manifest | {"source_revision": []}),
            "invalid JSON": b"{\n",
        }

        for reason, payload in cases.items():
            with self.subTest(reason=reason):
                fixture.write(fixture.manifest_path(), payload)
                self.plan(fixture, refusal="manifest-invalid")

    def test_rejects_invalid_adapter_values(self) -> None:
        fixture = self.fixture()
        good = fixture.adapter().read_bytes()
        for invalid, line in (
            (good.replace(b"$HOME/.alpha/skills", b"$HOME/$(id)"), 1),
            (good.replace(b"$HOME/.alpha/skills", b'"$HOME/x"'), 1),
            (good.replace(b"$HOME/.alpha/skills", b"$HOME/../outside"), 1),
            (good.replace(b"$HOME/.alpha/skills", b"$HOME/.alpha/skills "), 1),
            (good + b"unknown=ignored\n", 3),
            (good + b"skills_dir=$HOME/repeated\n", 3),
            (good + b"project_skills_link_dir=$HOME/project/skills\n", 3),
        ):
            with self.subTest(payload=invalid):
                fixture.adapter().write_bytes(invalid)
                diagnostic = self.plan(fixture, refusal="deploy-env-invalid")
                self.assertRegex(
                    diagnostic, rf"{re.escape(str(fixture.adapter()))}(?::|[^\n]*\bline ){line}\b",
                )

    def test_rejects_incomplete_adapters(self) -> None:
        for missing in ("always-on.md", "capabilities.md", "deploy.env"):
            with self.subTest(missing=missing):
                fixture = self.fixture()
                (fixture.adapter("omega").parent / missing).unlink()
                self.plan(fixture, refusal="adapter-incomplete")

    def test_rejects_owned_edits_and_foreign_new_skill(self) -> None:
        for scenario in ("skill edited", "always-on edited", "new skill occupied"):
            with self.subTest(scenario=scenario):
                fixture = self.fixture()
                if scenario == "always-on edited":
                    target = fixture.always_on()
                    objects = [fixture.manifest_object(target, b"Owned content")]
                else:
                    target = fixture.skill("current")
                    always_on = fixture.assembled_always_on("alpha")
                    fixture.write(fixture.always_on(), always_on)
                    objects = [fixture.manifest_object(fixture.always_on(), always_on)]
                    if scenario == "skill edited":
                        objects.append(fixture.manifest_object(target, b"Owned content", "current"))
                fixture.write(target, b"Bytes that must survive")
                manifest = fixture.manifest("alpha", *objects)
                fixture.write(fixture.manifest_path(), fixture.manifest_bytes(manifest))

                self.assertEqual(self.plan(fixture, refusal="ownership-conflict"),
                                 f"ERROR ownership-conflict {target}: {OWNERSHIP_RESOLUTION}")

    def test_rejects_second_harness_before_any_first_harness_write(self) -> None:
        fixture = self.fixture()
        first_skill = fixture.skill("current")
        fixture.write(first_skill, b"Old first-harness bytes")
        obj = fixture.manifest_object(first_skill, b"Old first-harness bytes", "current")
        fixture.write(fixture.manifest_path(), fixture.manifest_bytes(fixture.manifest("alpha", obj)))
        fixture.write(fixture.always_on("omega"), b"Old second-harness bytes")
        invalid = fixture.adapter("omega")
        invalid.write_bytes(invalid.read_bytes() + b"unsupported=ignored\n")

        self.assertIn(str(invalid), self.plan(fixture, refusal="deploy-env-invalid"))

    def test_rejects_invalid_home_and_conflicting_adapters(self) -> None:
        fixture = self.fixture()
        absolute_home = fixture.environment["HOME"]
        for home in ("relative/home", ""):
            with self.subTest(home=home):
                fixture.environment["HOME"] = home
                self.plan(fixture, refusal="home-invalid")
        fixture.environment["HOME"] = absolute_home

        for skills, always_on in (
            (b"$HOME/.alpha/skills/demo", b"$HOME/.omega/AGENTS.md"),
            (b"$HOME/.alpha/skills", b"$HOME/.omega/AGENTS.md"),
            (b"$HOME/.omega/skills", b"$HOME/.alpha/AGENTS.md"),
            (b"$HOME/.omega/skills", b"$HOME/.alpha/skills/always-on.md"),
        ):
            with self.subTest(skills=skills, always_on=always_on):
                fixture.adapter("omega").write_bytes(
                    b"skills_dir=" + skills + b"\nalways_on_path=" + always_on + b"\n",
                )
                self.plan(fixture, refusal="adapter-conflict")

    @staticmethod
    def link_skill_root(fixture: PlannerFixture) -> Path:
        root = fixture.skills_dir()
        root.parent.mkdir()
        real_root = fixture.home / "original skills"
        real_root.mkdir()
        root.symlink_to(real_root, target_is_directory=True)
        return real_root

    def test_plans_for_resolved_linked_skill_root(self) -> None:
        fixture = self.fixture()
        real_root = self.link_skill_root(fixture)
        path = real_root / "current/SKILL.md"
        obj = fixture.manifest_object(path, SKILL_BYTES, "current")
        manifest = fixture.manifest("alpha", obj)

        plan = self.plan(fixture)

        self.assertIn(("create", path), [(action.kind, action.path) for action in plan.actions])
        desired = json.loads(plan.manifests[fixture.manifest_path()])
        self.assertEqual(desired["skills_dir_resolved"], str(real_root))
        self.assertEqual(desired["install_id"], manifest["install_id"])

    def test_rejects_moved_installation(self) -> None:
        fixture = self.fixture()
        real_root = self.link_skill_root(fixture)
        path = real_root / "current/SKILL.md"
        obj = fixture.manifest_object(path, SKILL_BYTES, "current")
        manifest = fixture.manifest("alpha", obj)

        with self.subTest(reason="incorrect installation identity"):
            fixture.write(
                fixture.manifest_path(), fixture.manifest_bytes(manifest | {"install_id": "0" * 64}),
            )
            self.plan(fixture, refusal="target-moved")

        with self.subTest(reason="changed target resolution"):
            fixture.write(fixture.manifest_path(), fixture.manifest_bytes(manifest))
            new_root = fixture.home / "different skills"
            new_root.mkdir()
            root = fixture.skills_dir()
            root.unlink()
            root.symlink_to(new_root, target_is_directory=True)
            self.plan(fixture, refusal="target-moved")


if __name__ == "__main__":
    unittest.main(verbosity=2)
