#!/usr/bin/env python3
"""Exercise knowledge inventory resolution in isolated Git repositories."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = "test_public_identity_matches_exact_ledger_and_preserves_knowledge"
TASK_MOVES = (
    ("00", "001", "sensitive-data-scrub"),
    ("01", "002", "git-source-of-truth"),
    ("02", "003", "run-log-vocabulary-validation"),
    ("03", "004", "hook-based-logging"),
    ("04", "005", "model-catalog-cache"),
    ("05", "006", "cost-and-duration-telemetry"),
    ("06", "007", "harness-git-rails"),
    ("06-1", "008", "test-suite-runtime"),
    ("07", "009", "state-tool"),
    ("08", "010", "rules-workflows-audit"),
    ("24", "025", "task-finalization"),
    ("25", "026", "spec-driven-pr-review-p1"),
)


def identity_check() -> str:
    source = (ROOT / "scripts/validate-contracts.sh").read_text(encoding="utf-8")
    start = source.index(f"{CHECK}() (")
    end = source.index("\n)\n\ncheck ", start) + 3
    return source[start:end]


def task_path(status: str, number: str, slug: str) -> str:
    return f".ai/tasks/{status}/task-{number}-{slug}/nested notes/state.md"


class KnowledgeInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.home = self.workspace / "home"
        self.home.mkdir()
        self.template = self.workspace / "template"
        self.template.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(
            HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / "config"),
            XDG_STATE_HOME=str(self.home / "state"), LC_ALL="C",
            GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null",
            GIT_TEMPLATE_DIR=str(self.template), GIT_AUTHOR_NAME="Fixture",
            GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="Fixture",
            GIT_COMMITTER_EMAIL="fixture@example.invalid",
        )

    def git(self, repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false", *args],
            cwd=repo, env=self.env, check=True, capture_output=True, text=True, timeout=8,
        ).stdout.strip()

    def write(self, repo: Path, name: str, data: str = "Knowledge fixture\n") -> None:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")

    def repository(self, label: str, originals: list[str]) -> tuple[Path, str]:
        repo = self.workspace / label
        repo.mkdir()
        self.git(repo, "init", "-q")
        for name in originals:
            self.write(repo, name)
        self.git(repo, "add", "--", *originals)
        self.git(repo, "commit", "-qm", "Record baseline knowledge")
        baseline = self.git(repo, "rev-parse", "HEAD")
        token = "agentic" + "-workflows"
        heading = "### Exact Identity " + "Match Ledger"
        self.write(repo, "example.txt", token + "\n")
        self.write(repo, ".ai/ledger.md", f"  base_commit: {baseline}\n{heading}\n"
                   "| Path | Line | Expected token counts |\n|---|---:|---|\n"
                   f"| `example.txt` | 1 | `{token}` × 1 |\n")
        return repo, baseline

    def check(self, repo: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-c", f"{identity_check()}\n{CHECK}"], cwd=repo,
            env=self.env, capture_output=True, text=True, timeout=15,
        )

    def test_source_checkout_matches_public_identity_ledger(self) -> None:
        result = self.check(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_exact_recorded_relocations_and_existing_fallbacks(self) -> None:
        moves = {
            task_path("todo" if old == "24" else "completed", old, slug):
            task_path("completed", new, slug)
            for old, new, slug in TASK_MOVES
        }
        moves[".ai/tasks/todo/task-example/state.md"] = ".ai/tasks/completed/task-example/state.md"
        moves[".ai/specs/example.md"] = ".ai/specs/completed/example.md"
        original = ".ai/memory/current.md"
        preferred = task_path("todo", "00", "sensitive-data-scrub")
        repo, baseline = self.repository("verified", [original, preferred, *moves])
        for old, new in moves.items():
            (repo / old).unlink()
            self.write(repo, new)
            self.git(repo, "add", "--", old, new)
        # The still-tracked original must take precedence even when an alternative exists.
        self.write(repo, task_path("todo", "001", "sensitive-data-scrub"))

        result = self.check(repo)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"  base_commit: {baseline}\n", (repo / ".ai/ledger.md").read_text())

    def test_rejects_missing_ambiguous_and_untracked_paths(self) -> None:
        old = task_path("todo", "24", "task-finalization")
        archived = task_path("completed", "24", "task-finalization")
        mapped = task_path("completed", "025", "task-finalization")
        unsupported = task_path("completed", "025", "unrelated-task")
        cases = {
            "missing": (old, ()),
            "unsupported-numbering": (
                task_path("completed", "24", "unrelated-task"), ((unsupported, True),),
            ),
            "ambiguous": (old, ((archived, True), (mapped, True))),
            "untracked": (old, ((archived, True), (mapped, False))),
        }
        for case, (original, candidates) in cases.items():
            with self.subTest(case=case):
                repo, _ = self.repository(case, [original])
                (repo / original).unlink()
                self.git(repo, "add", "--", original)
                for path, tracked in candidates:
                    self.write(repo, path)
                    if tracked:
                        self.git(repo, "add", "--", path)

                result = self.check(repo)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
