#!/usr/bin/env python3
"""Check harness deployment contracts with isolated homes and project fixtures."""

from contextlib import chdir
import fcntl
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

    def test_rejects_direct_and_resolved_legacy_targets(self) -> None:
        for target in ("declared paths", "symlinked skill root"):
            with self.subTest(target=target):
                fixture = self.fixture()
                legacy = fixture.home / ".codeium/windsurf"
                fixture.write(legacy / "skills/current/SKILL.md", b"Retained legacy skill bytes")
                if target == "declared paths":
                    fixture.write(legacy / "AGENTS.md", b"Retained legacy instructions")
                    fixture.adapter().write_bytes(
                        b"skills_dir=$HOME/.codeium/windsurf/skills\n"
                        b"always_on_path=$HOME/.codeium/windsurf/AGENTS.md\n",
                    )
                else:
                    root = fixture.skills_dir()
                    root.parent.mkdir()
                    root.symlink_to(legacy / "skills", target_is_directory=True)

                self.plan(fixture, refusal="adapter-conflict")

    def test_rejects_target_inside_manifest_namespace(self) -> None:
        fixture = self.fixture()
        config = fixture.home / ".config"
        fixture.environment["XDG_CONFIG_HOME"] = str(config)
        retained = fixture.skill("current", "dormant")
        fixture.write(retained, SKILL_BYTES)
        obj = fixture.manifest_object(retained, SKILL_BYTES, "current")
        dormant = config / "orchestrail/deploy/dormant.json"
        fixture.write(dormant, fixture.manifest_bytes(fixture.manifest("dormant", obj)))
        fixture.adapter().write_bytes(
            b"skills_dir=$HOME/.alpha/skills\n"
            b"always_on_path=$HOME/.config/orchestrail/deploy/dormant.json\n",
        )

        self.plan(fixture, refusal="adapter-conflict")


class DeploymentTransactionTests(unittest.TestCase):
    def fixture(self) -> PlannerFixture:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return PlannerFixture(Path(temporary.name).resolve())

    @staticmethod
    def lock_path(fixture: PlannerFixture) -> Path:
        return fixture.config / "orchestrail/deploy.lock"

    @staticmethod
    def journal_path(fixture: PlannerFixture) -> Path:
        return fixture.manifest_path("journal")

    def deploy(
        self, fixture: PlannerFixture, *, interrupt_after: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        launcher = []
        if interrupt_after is not None:
            # Kill only the fixture process just after a global atomic replacement completes.
            launcher = ["-c", """
import os
from pathlib import Path
import runpy
import sys

interrupt_after = Path(sys.argv[1])
sys.argv = sys.argv[2:]
replace = os.replace

def replace_then_interrupt(source, target, **kwargs):
    replace(source, target, **kwargs)
    if Path(target).absolute() == interrupt_after:
        os._exit(73)

os.replace = replace_then_interrupt
runpy.run_path(sys.argv[0], run_name="__main__")
""", str(interrupt_after)]
        return subprocess.run(
            [sys.executable, "-I", *launcher, str(ENGINE), "deploy", "--from", str(fixture.source),
             "--hook-result", HOOK_RESULT],
            cwd=fixture.root,
            env=fixture.environment,
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=15,
        )

    def assert_no_temporary_files(self, fixture: PlannerFixture) -> None:
        self.assertEqual(list(fixture.root.rglob(".*.orchestrail-tmp")), [])

    def assert_refused(self, fixture: PlannerFixture, code: str) -> None:
        before = fixture.snapshot()
        result = self.deploy(fixture)
        self.assertEqual(fixture.snapshot(), before)
        self.assert_no_temporary_files(fixture)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertRegex(result.stderr, rf"^ERROR {code}(?: [^\n]+)?: ")

    def assert_deployed(self, fixture: PlannerFixture) -> None:
        self.assertFalse(self.journal_path(fixture).exists(), "Completed journal still exists")
        self.assert_no_temporary_files(fixture)
        for harness in ("alpha", "omega"):
            with self.subTest(harness=harness):
                skill = fixture.skill("current", harness)
                always_on = fixture.always_on(harness)
                always_on_bytes = fixture.assembled_always_on(harness)
                self.assertEqual(skill.read_bytes(), SKILL_BYTES)
                self.assertEqual(always_on.read_bytes(), always_on_bytes)
                manifest = fixture.manifest(
                    harness,
                    fixture.manifest_object(skill, SKILL_BYTES, "current"),
                    fixture.manifest_object(always_on, always_on_bytes),
                )
                self.assertEqual(fixture.manifest_path(harness).read_bytes(),
                                 fixture.manifest_bytes(manifest))

    def half_applied_journal(self, fixture: PlannerFixture) -> dict:
        fixture.write(self.lock_path(fixture), b"")
        old_always_on = b"Previously deployed instructions\n"
        old_skill = b"Previously deployed skill\n"
        fixture.write(fixture.always_on(), fixture.assembled_always_on("alpha"))
        fixture.write(fixture.skill("current"), old_skill)
        previous_manifest = fixture.manifest(
            "alpha",
            fixture.manifest_object(fixture.always_on(), old_always_on),
            fixture.manifest_object(fixture.skill("current"), old_skill, "current"),
        )
        fixture.write(fixture.manifest_path(), fixture.manifest_bytes(previous_manifest))
        steady_skill = fixture.skill("current", "omega")
        steady_always_on = fixture.always_on("omega")
        steady_always_on_bytes = fixture.assembled_always_on("omega")
        fixture.write(steady_skill, SKILL_BYTES)
        fixture.write(steady_always_on, steady_always_on_bytes)
        steady_manifest = fixture.manifest(
            "omega",
            fixture.manifest_object(steady_skill, SKILL_BYTES, "current"),
            fixture.manifest_object(steady_always_on, steady_always_on_bytes),
        )
        fixture.write(fixture.manifest_path("omega"), fixture.manifest_bytes(steady_manifest))

        journal = {
            "schema_version": 1,
            "entries": [
                {"path": str(path), "old_sha256": hashlib.sha256(old).hexdigest(),
                 "new_sha256": hashlib.sha256(new).hexdigest()}
                for path, old, new in (
                    (fixture.always_on(), old_always_on, fixture.assembled_always_on("alpha")),
                    (fixture.skill("current"), old_skill, SKILL_BYTES),
                )
            ],
        }
        fixture.write(self.journal_path(fixture), fixture.manifest_bytes(journal))
        return journal

    def test_first_deploy_installs_and_records_targets_then_leaves_them_untouched(self) -> None:
        fixture = self.fixture()
        skill = fixture.skill("current")
        fixture.write(skill, b"Old non-manifest bytes\n")
        foreign = skill.parent / "personal.md"
        unrecorded = fixture.skill("unrecorded")
        fixture.write(foreign, b"Keep this foreign file\n")
        fixture.write(unrecorded, b"Earlier unrecorded skill\n")

        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"adopt {skill}", result.stdout.splitlines())
        self.assertTrue(self.lock_path(fixture).is_file())
        self.assert_deployed(fixture)
        self.assertEqual(foreign.read_bytes(), b"Keep this foreign file\n")
        self.assertEqual(unrecorded.read_bytes(), b"Earlier unrecorded skill\n")

        before = fixture.snapshot()
        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotRegex(result.stdout, r"(?m)^(?:adopt|create|remove|replace) ")
        self.assertEqual(fixture.snapshot(), before)

    def test_deploy_removes_unmodified_obsolete_skills_and_keeps_other_files(self) -> None:
        fixture = self.fixture()
        obsolete = fixture.skill("obsolete")
        edited = fixture.skill("edited")
        foreign = fixture.skill("foreign")
        old = b"Previously deployed skill\n"
        fixture.write(obsolete, old)
        fixture.write(edited, b"User-edited skill\n")
        fixture.write(foreign, b"Unowned skill\n")
        manifest = fixture.manifest(
            "alpha",
            fixture.manifest_object(obsolete, old, "obsolete"),
            fixture.manifest_object(edited, old, "edited"),
        )
        fixture.write(fixture.manifest_path(), fixture.manifest_bytes(manifest))

        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(obsolete.parent.exists())
        self.assertEqual(edited.read_bytes(), b"User-edited skill\n")
        self.assertEqual(foreign.read_bytes(), b"Unowned skill\n")
        self.assertIn(f"release-modified {edited}", result.stdout.splitlines())
        self.assert_deployed(fixture)

    def test_first_deploy_journals_global_changes_before_replacing_targets(self) -> None:
        fixture = self.fixture()
        skill = fixture.skill("current")
        old_skill = b"Old non-manifest bytes\n"
        fixture.write(skill, old_skill)

        interrupted = self.deploy(fixture, interrupt_after=fixture.always_on())

        self.assertEqual(interrupted.returncode, 73, interrupted.stdout + interrupted.stderr)
        self.assertFalse(fixture.manifest_path().exists())
        self.assert_no_temporary_files(fixture)
        retained = json.loads(self.journal_path(fixture).read_bytes())
        target_bytes = {
            skill: SKILL_BYTES,
            fixture.always_on(): fixture.assembled_always_on("alpha"),
            fixture.skill("current", "omega"): SKILL_BYTES,
            fixture.always_on("omega"): fixture.assembled_always_on("omega"),
        }
        expected = []
        for path, payload in sorted(target_bytes.items()):
            old = old_skill if path == skill else None
            current = path.read_bytes() if path.exists() else None
            self.assertIn(current, (old, payload), str(path))
            expected.append({"path": str(path), "new_sha256": hashlib.sha256(payload).hexdigest(),
                             "old_sha256": hashlib.sha256(old).hexdigest() if old else None})
        self.assertEqual(retained, {"schema_version": 1, "entries": expected})

        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_deployed(fixture)

    def test_deploy_with_held_lock_exits_without_writes(self) -> None:
        fixture = self.fixture()
        lock = self.lock_path(fixture)
        fixture.write(lock, b"Existing lock contents\n")

        with lock.open("rb") as descriptor:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assert_refused(fixture, "deploy-locked")

    def test_deploy_with_invalid_journal_exits_without_writes(self) -> None:
        fixture = self.fixture()
        journal = self.half_applied_journal(fixture)
        applied, pending = journal["entries"]
        invalid_entries = {
            "unknown entry key": [applied | {"unknown": False}, pending],
            "invalid digest": [applied, pending | {"old_sha256": "not-a-digest"}],
            "relative path": [applied, pending | {"path": "relative/SKILL.md"}],
            "duplicate path": [applied, applied],
        }
        cases = {
            "invalid JSON": b"{\n",
            "duplicate schema key": b'{"schema_version": 1, "schema_version": 1, "entries": []}\n',
        }
        cases.update({reason: fixture.manifest_bytes(journal | {"entries": entries})
                      for reason, entries in invalid_entries.items()})

        for reason, payload in cases.items():
            with self.subTest(reason=reason):
                fixture.write(self.journal_path(fixture), payload)
                self.assert_refused(fixture, "journal-invalid")

    def test_deploy_with_edited_recovery_target_exits_without_writes(self) -> None:
        fixture = self.fixture()
        self.half_applied_journal(fixture)
        fixture.write(fixture.always_on(), b"User change after the interruption\n")

        self.assert_refused(fixture, "journal-mismatch")

    def test_deploy_completes_a_half_applied_journal(self) -> None:
        fixture = self.fixture()
        self.half_applied_journal(fixture)

        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_deployed(fixture)

    def test_deploy_recovers_again_after_a_second_interruption(self) -> None:
        fixture = self.fixture()
        journal = self.half_applied_journal(fixture)
        previous_manifest = fixture.manifest_path().read_bytes()

        interrupted = self.deploy(fixture, interrupt_after=fixture.skill("current"))

        self.assertEqual(interrupted.returncode, 73, interrupted.stdout + interrupted.stderr)
        self.assert_no_temporary_files(fixture)
        self.assertEqual(fixture.manifest_path().read_bytes(), previous_manifest)
        retained = json.loads(self.journal_path(fixture).read_bytes())
        for entry in journal["entries"]:
            self.assertEqual(hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest(),
                             entry["new_sha256"])
            self.assertIn(entry, retained["entries"])

        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_deployed(fixture)

    def test_deploy_rejects_reserved_path_collisions_before_writing(self) -> None:
        paths = (
            ("always_on_path", ".config/orchestrail/deploy.lock"),
            ("skills_dir", ".config/orchestrail/deploy.lock/skills"),
            ("always_on_path", ".config/orchestrail/deploy/journal.json"),
            ("always_on_path", ".config/orchestrail/deploy/omega.json"),
        )
        for key, path in paths:
            with self.subTest(key=key, path=path):
                fixture = self.fixture()
                fixture.environment["XDG_CONFIG_HOME"] = str(fixture.home / ".config")
                adapter = fixture.adapter()
                settings = adapter.read_text(encoding="utf-8")
                updated = re.sub(rf"(?m)^{key}=.*$", f"{key}=$HOME/{path}", settings)
                adapter.write_text(updated, encoding="utf-8")
                if key == "always_on_path":
                    capabilities = adapter.with_name("capabilities.md")
                    capabilities.write_bytes(capabilities.read_bytes().replace(
                        b"$HOME/.alpha/AGENTS.md", f"$HOME/{path}".encode(),
                    ))

                self.assert_refused(fixture, "adapter-conflict")

    def test_deploy_rejects_harness_whose_manifest_path_is_the_journal(self) -> None:
        fixture = self.fixture()
        fixture.make_harness("journal")

        self.assert_refused(fixture, "adapter-conflict")

    def assert_prewrite_refusal(self, fixture: PlannerFixture, code: str) -> None:
        before = fixture.snapshot()
        result = self.deploy(fixture)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(self.journal_path(fixture).exists(), result.stderr)
        self.assertEqual(fixture.snapshot(), before)
        self.assertRegex(result.stderr, rf"^ERROR {code}(?: [^\n]+)?: ")

    def test_deploy_refuses_a_skill_root_at_another_targets_temporary_path(self) -> None:
        fixture = self.fixture()
        fixture.write(self.lock_path(fixture), b"Persistent lock\n")
        fixture.write(fixture.skill("current"), b"Previous first-harness skill\n")
        fixture.adapter().write_bytes(
            b"skills_dir=$HOME/.alpha/skills\nalways_on_path=$HOME/shared/AGENTS.md\n",
        )
        capabilities = fixture.adapter().with_name("capabilities.md")
        capabilities.write_bytes(capabilities.read_bytes().replace(
            b"$HOME/.alpha/AGENTS.md", b"$HOME/shared/AGENTS.md",
        ))
        fixture.adapter("omega").write_bytes(
            b"skills_dir=$HOME/shared/.AGENTS.md.orchestrail-tmp\n"
            b"always_on_path=$HOME/.omega/AGENTS.md\n",
        )
        root = fixture.home / "shared/.AGENTS.md.orchestrail-tmp"
        fixture.write(root / "personal.md", b"Unowned bytes in the skill root\n")

        self.assert_prewrite_refusal(fixture, "adapter-conflict")

    def test_deploy_refuses_a_symlink_at_a_pending_replacements_temporary_path(self) -> None:
        fixture = self.fixture()
        fixture.write(self.lock_path(fixture), b"Persistent lock\n")
        skill = fixture.skill("current", "omega")
        fixture.write(skill, b"Previous second-harness skill\n")
        foreign = fixture.home / "personal.md"
        fixture.write(foreign, b"Unowned bytes behind the link\n")
        skill.with_name(".SKILL.md.orchestrail-tmp").symlink_to(foreign)

        self.assert_prewrite_refusal(fixture, "unsafe-target")

    def test_deploy_refuses_an_unencodable_journal_path(self) -> None:
        fixture = self.fixture()
        fixture.write(self.lock_path(fixture), b"Persistent lock\n")
        fixture.skills_dir().mkdir(parents=True)
        entry = {
            "path": f"{fixture.skills_dir()}/\ud800/SKILL.md",
            "old_sha256": None,
            "new_sha256": hashlib.sha256(SKILL_BYTES).hexdigest(),
        }
        journal = {"schema_version": 1, "entries": [entry]}
        fixture.write(self.journal_path(fixture), fixture.manifest_bytes(journal))

        self.assert_refused(fixture, "journal-invalid")


class RegisteredProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture = PlannerFixture(Path(temporary.name).resolve())
        self.registry = self.fixture.config / "orchestrail/projects"

    def command(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-I", str(ENGINE), *arguments],
            cwd=self.fixture.root,
            env=self.fixture.environment,
            capture_output=True,
            timeout=15,
        )

    def deploy(self) -> subprocess.CompletedProcess[bytes]:
        return self.command(
            "deploy", "--from", str(self.fixture.source), "--hook-result", HOOK_RESULT,
        )

    def project(self, name: str) -> Path:
        project = self.fixture.root / name
        project.mkdir(parents=True)
        return project

    def include_links(self, harness: str, directory: str) -> None:
        adapter = self.fixture.adapter(harness)
        adapter.write_bytes(adapter.read_bytes() + f"project_skills_link_dir={directory}\n".encode())

    def assert_success(self, result: subprocess.CompletedProcess[bytes]) -> None:
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_link(self, link: Path, target: Path) -> None:
        self.assertTrue(link.is_symlink(), link)
        self.assertEqual(link.resolve(strict=True), target.resolve(strict=True))

    def project_entries(self, *roots: Path) -> dict[Path, tuple[int, int, bytes | str | None]]:
        relative = tuple(root.relative_to(self.fixture.root) for root in roots)
        return {path: entry for path, entry in self.fixture.snapshot().items()
                if any(path.is_relative_to(root) for root in relative)}

    def test_lists_existing_projects_in_registry_order_without_writes(self) -> None:
        parent = self.project("zéta project 'with spaces' ")
        nested = self.project(f"{parent.name}/child")
        first = self.project("alpha project")
        missing = self.fixture.root / "missing"
        file = self.fixture.root / "regular file"
        file.write_bytes(b"Not a project directory\n")
        roots = (parent, missing, first, SOURCE, parent, file, nested, first)
        self.fixture.write(self.registry, "\n".join(map(str, roots)).encode())
        self.fixture.write(self.fixture.home / ".config/orchestrail/projects", b"ignored/relative/path\n")
        before = self.fixture.snapshot()

        result = self.command("list-projects")

        self.assert_success(result)
        self.assertEqual(result.stdout, b"".join(os.fsencode(root) + b"\0" for root in (parent, first, nested)))
        self.assertEqual(self.fixture.snapshot(), before)

    def test_absent_registry_lists_nothing_and_deploy_does_not_discover_home_projects(self) -> None:
        fixture = self.fixture
        self.include_links("alpha", ".alpha/skills")
        unregistered = fixture.home / "unregistered project"
        fixture.write(unregistered / ".devin/workflows/local.md", b"Legacy bytes\n")
        (unregistered / ".alpha/skills").mkdir(parents=True)
        before = fixture.snapshot()
        project_before = self.project_entries(unregistered)

        with self.subTest(command="list-projects"):
            listed = self.command("list-projects")
            self.assert_success(listed)
            self.assertEqual(listed.stdout, b"")
            self.assertEqual(fixture.snapshot(), before)

        with self.subTest(command="deploy"):
            result = self.deploy()
            self.assert_success(result)
            self.assertIn(
                b"registry absent: no projects registered; run scripts/setup-new-project.sh in each project",
                result.stdout.splitlines(),
            )
            self.assertEqual(fixture.skill("current").read_bytes(), SKILL_BYTES)
            self.assertFalse(self.registry.exists())
            self.assertEqual(self.project_entries(unregistered), project_before)

    def test_links_declared_adapter_directories_and_preserves_existing_entries(self) -> None:
        fixture = self.fixture
        fixture.make_harness("gamma")
        self.include_links("alpha", ".providers/alpha/skills")
        self.include_links("omega", ".omega/custom")
        project = self.project("explicit project")
        alpha = project / ".providers/alpha/skills"
        local = alpha / "manual"
        fixture.write(local, b"Project-owned bytes\n")
        foreign_link = alpha / "private"
        foreign_link.symlink_to("../missing")
        for name in ("current", "manual", "private"):
            fixture.skill(name).parent.mkdir(parents=True)
        fixture.write(fixture.skills_dir() / "notes.md", b"Global loose file\n")
        fixture.skill("second", "omega").parent.mkdir(parents=True)
        fixture.skill("unconfigured", "gamma").parent.mkdir(parents=True)

        arguments = ("link-project", "--from", str(fixture.source), "--project", str(project))
        self.assert_success(self.command(*arguments))

        self.assert_link(alpha / "current", fixture.skills_dir() / "current")
        self.assert_link(project / ".omega/custom/second", fixture.skills_dir("omega") / "second")
        self.assertEqual(local.read_bytes(), b"Project-owned bytes\n")
        self.assertEqual(os.readlink(foreign_link), "../missing")
        self.assertEqual({path.name for path in alpha.iterdir()}, {"current", "manual", "private"})
        self.assertEqual({path.name for path in project.iterdir()}, {".providers", ".omega"})
        self.assertFalse(self.registry.exists())
        after = fixture.snapshot()
        self.assert_success(self.command(*arguments))
        self.assertEqual(fixture.snapshot(), after)

    def make_tracking_stub(self) -> None:
        git = self.fixture.root / "bin/git"
        git.write_text(r"""#!/bin/sh
if [ "$1" = -C ]; then
    cd -- "$2" || exit 1
    shift 2
fi
[ "$1" = ls-files ] || exit 1
if [ -f .git/tracked-knowledge ]; then
    printf '%s\n' '.ai/README.md'
fi
""", encoding="utf-8")
        git.chmod(0o755)

    def test_deployment_refreshes_each_root_and_changes_only_owned_links_and_ignore(self) -> None:
        fixture = self.fixture
        self.include_links("alpha", ".providers/skills")
        resolved = fixture.home / "resolved skills"
        resolved.mkdir()
        fixture.skills_dir().parent.mkdir()
        fixture.skills_dir().symlink_to(resolved, target_is_directory=True)
        self.assert_success(self.deploy())

        parent = self.project("parent")
        nested = self.project("parent/nested project")
        empty = self.project("no configured link directory")
        for project in (parent, nested):
            (project / ".providers/skills").mkdir(parents=True)
            (project / ".git").mkdir()
            fixture.write(project / ".gitignore", b"*.cache\n")
            fixture.write(project / ".ai/README.md", b"Existing knowledge\n")
        fixture.write(nested / ".git/tracked-knowledge", b"")
        self.make_tracking_stub()

        links = parent / ".providers/skills"
        owned = links / "stale-declared"
        owned.symlink_to(fixture.skills_dir() / "retired")
        resolved_owned = links / "stale-resolved"
        resolved_owned.symlink_to(resolved / "retired")
        live = links / "live"
        live.symlink_to(fixture.skills_dir() / "current")
        foreign = links / "foreign"
        foreign.symlink_to(f"{fixture.skills_dir()}-other/retired")
        relative_foreign = links / "relative-foreign"
        relative_foreign.symlink_to("../personal")
        missing = fixture.root / "missing project"
        roots = (parent, missing, fixture.source, nested, parent, empty)
        registry_bytes = "".join(f"{root}\n" for root in roots).encode()
        fixture.write(self.registry, registry_bytes)
        for name in (".devin/workflows/old.md", ".windsurf/rules/old.md", "AGENTS.md", "CLAUDE.md"):
            fixture.write(parent / name, f"Preserved {name}\n".encode())
        before = fixture.snapshot()

        result = self.deploy()

        self.assert_success(result)
        self.assertEqual(
            [line for line in result.stdout.splitlines() if line.startswith(b"project ")],
            [
                f"project updated {parent} (linked 1, unlinked 2)".encode(),
                f"project missing {missing}".encode(),
                f"project skipped (source checkout) {fixture.source}".encode(),
                f"project updated {nested} (linked 1, unlinked 0)".encode(),
                f"project updated {empty} (linked 0, unlinked 0)".encode(),
            ],
        )
        self.assertFalse(owned.is_symlink())
        self.assertFalse(resolved_owned.is_symlink())
        self.assert_link(links / "current", resolved / "current")
        self.assert_link(nested / ".providers/skills/current", resolved / "current")
        self.assertFalse((empty / ".providers").exists())
        self.assertEqual((parent / ".gitignore").read_bytes(), b"*.cache\n.ai/\n")
        after = fixture.snapshot()
        removed = {owned.relative_to(fixture.root), resolved_owned.relative_to(fixture.root)}
        added = {(project / ".providers/skills/current").relative_to(fixture.root)
                 for project in (parent, nested)}
        changed = {(project / ".providers/skills").relative_to(fixture.root)
                   for project in (parent, nested)}
        changed.add((parent / ".gitignore").relative_to(fixture.root))
        self.assertEqual(set(before) - set(after), removed)
        self.assertEqual(set(after) - set(before), added)
        preserved = (before.keys() & after.keys()) - changed
        self.assertEqual({path: before[path] for path in preserved}, {path: after[path] for path in preserved})

        retry = self.deploy()
        self.assert_success(retry)
        self.assertIn(f"project updated {parent} (linked 0, unlinked 0)".encode(), retry.stdout.splitlines())
        self.assertEqual(fixture.snapshot(), after)

    def test_deployment_skips_legacy_destinations_and_symlinked_project_parents(self) -> None:
        fixture = self.fixture
        self.include_links("alpha", ".windsurf/skills")
        self.include_links("omega", ".devin/skills")
        fixture.make_harness("gamma")
        self.include_links("gamma", ".redirected/skills")
        project = self.project("protected project")
        fixture.write(project / ".windsurf/skills/legacy.md", b"Retired editor bytes\n")
        fixture.write(project / ".devin/rules/legacy.md", b"Another retired editor's bytes\n")
        (project / ".windsurf/skills/owned").symlink_to(fixture.skills_dir() / "retired")
        external = self.project("outside project")
        (external / "skills").mkdir()
        (external / "skills/owned").symlink_to(fixture.skills_dir("gamma") / "retired")
        (project / ".redirected").symlink_to(external, target_is_directory=True)
        fresh = self.project("fresh project")
        fixture.write(self.registry, f"{project}\n{fresh}\n".encode())
        before = self.project_entries(project, fresh, external)

        result = self.deploy()

        self.assert_success(result)
        lines = result.stdout.splitlines()
        for root in (project, fresh):
            self.assertIn(f"project updated {root} (linked 0, unlinked 0)".encode(), lines)
        self.assertEqual(self.project_entries(project, fresh, external), before)

    def test_rejects_invalid_registry_before_global_or_project_writes(self) -> None:
        fixture = self.fixture
        self.include_links("alpha", ".alpha/skills")
        project = self.project("registered project")
        (project / ".alpha/skills").mkdir(parents=True)
        (project / ".git").mkdir()
        alias = fixture.root / "project alias"
        alias.symlink_to(project, target_is_directory=True)
        fixtures = {
            "relative path": b"relative/path",
            "noncanonical path": os.fsencode(alias),
            "carriage return": os.fsencode(project) + b"\r",
            "NUL": os.fsencode(project) + b"\0",
            "invalid UTF-8": b"/invalid-\xff",
            "empty line": b"\n",
            "nonregular registry": None,
        }
        for name, payload in fixtures.items():
            if payload is None:
                self.registry.unlink()
                self.registry.mkdir()
            else:
                fixture.write(self.registry, os.fsencode(project) + b"\n" + payload + b"\n")
            before = fixture.snapshot()

            for arguments in (("list-projects",),
                              ("deploy", "--from", str(fixture.source), "--hook-result", HOOK_RESULT)):
                with self.subTest(registry=name, command=arguments[0]):
                    result = self.command(*arguments)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(result.stdout, b"")
                    self.assertTrue(result.stderr.startswith(b"ERROR registry-invalid: "), result.stderr)
                    self.assertEqual(fixture.snapshot(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
