"""Verify the pinned archival relocation for read-only journal inspection."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat

from finalization_archive import journal_files, validate_journal_document
from finalization_evidence import ancestor, commit, git, git_blob
from finalization_support import Refusal, digest, pairs_unique, reject_constant, require, safe_path

TASK_OLD = '.ai/tasks/completed/task-25-spec-driven-pr-review-p1'
TASK_NEW = '.ai/tasks/completed/task-026-spec-driven-pr-review-p1'
SPEC_OLD = '.ai/specs/25-spec-driven-pr-review.md'
SPEC_ARCHIVED = '.ai/specs/completed/25-spec-driven-pr-review.md'
SPEC_NEW = '.ai/specs/completed/026-spec-driven-pr-review.md'
RELOCATION_COMMIT = '32a608fc1f0d40929eb04df93c166a8173607432'
ARCHIVAL_COMMIT = '42325d2dc40c0b20bb333e1b7c7fdf5e5ce14117'
RENUMBERING_COMMIT = 'bda0f3e928c119da5a7d8d108c6daf89a4777b0f'
ALIASES = (TASK_OLD, TASK_NEW, SPEC_OLD, SPEC_NEW)
EVIDENCE_LIMIT = 1024 * 1024
JOURNAL_LIMIT = 4 * 1024 * 1024
INVALID = 'relocation-evidence-invalid'


def matches_alias(root: Path, selected: Path) -> bool:
    return (root / selected) in {root / alias for alias in ALIASES}


def read_regular(path: Path, limit: int, root: Path | None = None) -> bytes:
    path = safe_path(path, root)
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as handle:
        info = os.fstat(handle.fileno())
        require(stat.S_ISREG(info.st_mode), INVALID, f'Expected a regular file: {path}')
        require(info.st_size <= limit, INVALID, f'File exceeds {limit} bytes: {path}')
        data = handle.read(limit + 1)
        require(len(data) <= limit, INVALID, f'File exceeds {limit} bytes: {path}')
        return data


def json_object(data: bytes) -> dict:
    try:
        document = json.loads(data.decode('utf-8'), object_pairs_hook=pairs_unique, parse_constant=reject_constant)
    except RecursionError as error:
        raise Refusal(INVALID, 'Relocation JSON nesting exceeds the parser limit') from error
    require(isinstance(document, dict), INVALID, 'Expected a JSON object')
    return document


def read_evidence(path: Path) -> dict:
    evidence = json_object(read_regular(path, EVIDENCE_LIMIT))
    fixed_fields = {'schema_version': '1', 'task_old': TASK_OLD, 'task_new': TASK_NEW,
                    'spec_old': SPEC_OLD, 'spec_new': SPEC_NEW, 'evidence_commit': RELOCATION_COMMIT}
    identity_fields = {'journal_id', 'journal_sha256'}
    require(evidence.keys() == fixed_fields.keys() | identity_fields, INVALID, 'Relocation evidence fields differ')
    require(all(isinstance(value, str) for value in evidence.values()), INVALID, 'Relocation fields must be strings')
    require(all(evidence[key] == value for key, value in fixed_fields.items()), INVALID, 'Relocation paths or provenance differ')
    require(all(re.fullmatch(r'[0-9a-f]{64}', evidence[key]) for key in identity_fields), INVALID, 'Expected lowercase SHA-256 values')
    return evidence


def bound_journal(root: Path, evidence: dict) -> tuple[Path, dict, str]:
    locations = {root / path for path in ALIASES}
    matches = []
    for path in journal_files(root):
        data = read_regular(path, JOURNAL_LIMIT, root)
        journal = json_object(data)
        validate_journal_document(root, path, journal)
        claims = {Path(os.path.abspath(journal[key]))
                  for key in ('task_original', 'task_current', 'spec_original', 'spec_current')}
        if claims & locations:
            matches.append((path, journal, digest(data)))
    require(len(matches) == 1, INVALID, 'Relocation must identify exactly one journal')
    path, journal, revision = matches[0]
    require(journal['task_current'] == str(root / TASK_OLD) and journal['spec_current'] == str(root / SPEC_OLD),
            INVALID, 'Recorded journal locations differ')
    require(evidence['journal_id'] == journal['id'] and evidence['journal_sha256'] == revision,
            INVALID, 'Journal identity or byte digest differs')
    return path, journal, revision


def tree_files(root: Path, revision: str, *paths: str) -> dict[str, tuple[str, str]]:
    listing = git(root, 'ls-tree', '-r', '-z', '--full-tree', revision, '--', *paths)
    files = {}
    for row in listing.split('\0')[:-1]:
        details, name = row.split('\t', 1)
        mode, kind, object_id = details.split()
        require(kind == 'blob' and mode in {'100644', '100755'}, INVALID, f'Git tracks a non-regular entry: {name}')
        files[name] = (mode, object_id)
    return files


def spec_blob(root: Path, revision: str, path: str) -> str:
    files = tree_files(root, revision, path)
    require(files.keys() == {path}, INVALID, f'Expected a tracked specification at {revision}:{path}')
    return files[path][1]


def verify_git_history(root: Path) -> tuple[str, str]:
    require(safe_path(Path(git(root, 'rev-parse', '--show-toplevel'))) == root,
            INVALID, 'Relocation proof requires the physical project Git root')
    grafts = safe_path(Path(git(root, 'rev-parse', '--path-format=absolute', '--git-path', 'info/grafts')))
    require(not grafts.exists(), INVALID, 'Git ancestry is overridden by a graft file')
    head = commit(root, 'HEAD')
    require(bool(head) and commit(root, RELOCATION_COMMIT) == RELOCATION_COMMIT,
            INVALID, 'Relocation commit or repository HEAD is missing')
    require(head is not None and ancestor(root, RELOCATION_COMMIT, head),
            INVALID, 'Relocation commit is not an ancestor of HEAD')
    for revision in (ARCHIVAL_COMMIT, RENUMBERING_COMMIT):
        require(commit(root, revision) == revision and ancestor(root, revision, RELOCATION_COMMIT),
                INVALID, f'Historical specification provenance is missing: {revision}')
    before = git(root, 'rev-parse', '--verify', f'{RELOCATION_COMMIT}^:{TASK_OLD}')
    after = git(root, 'rev-parse', '--verify', f'{RELOCATION_COMMIT}:{TASK_NEW}')
    require(before == after, INVALID, 'Git trees at the recorded old and new task locations differ')
    spec_blob(root, ARCHIVAL_COMMIT, SPEC_ARCHIVED)
    spec_blob(root, RENUMBERING_COMMIT, SPEC_NEW)
    return head, spec_blob(root, ARCHIVAL_COMMIT + '^', SPEC_OLD)


def verify_live_paths(root: Path) -> None:
    task = root / TASK_NEW
    files = tree_files(root, RELOCATION_COMMIT, TASK_NEW, SPEC_NEW)
    require(SPEC_NEW in files and len(files) > 1, INVALID, 'Relocated task or specification is missing from Git')
    expected = {root / name for name in files if name != SPEC_NEW}
    directories = {parent for path in expected for parent in path.parents if parent.is_relative_to(task)}
    require(task.is_dir(), INVALID, 'Relocated task directory is unavailable')
    actual = set()
    for path in task.rglob('*'):
        safe_path(path, root)
        if path.is_dir():
            require(path in directories, INVALID, f'Unexpected task directory: {path}')
        else:
            actual.add(path)
    require(actual == expected, INVALID, 'Live task file inventory differs from the Git tree')
    tracked = git(root, 'ls-files', '--stage', '-z', '--', TASK_NEW, SPEC_NEW).split('\0')[:-1]
    expected_index = {f'{mode} {object_id} 0\t{name}' for name, (mode, object_id) in files.items()}
    require(len(tracked) == len(expected_index) and set(tracked) == expected_index,
            INVALID, 'Relocated files are untracked or their index entries differ')
    for name, (_, object_id) in files.items():
        expected_bytes = git_blob(root, object_id)
        require(read_regular(root / name, len(expected_bytes), root) == expected_bytes,
                INVALID, f'Live bytes differ from the Git blob: {name}')


def inspect_relocation(root: Path, selected: Path, evidence_path: Path) -> dict:
    try:
        require(matches_alias(root, selected), INVALID, 'Selector is outside the recorded relocation')
        paths = {name: safe_path(root / name, root) for name in ALIASES}
        require(not paths[TASK_OLD].exists() and not paths[SPEC_OLD].exists(), INVALID, 'A former location still exists')
        evidence = read_evidence(evidence_path)
        path, journal, revision = bound_journal(root, evidence)
        head, original_spec = verify_git_history(root)
        verify_live_paths(root)
        snapshot = path.parent / 'snapshot'
        require(Path(journal['snapshot_path']) == snapshot, INVALID, 'Recorded snapshot location differs')
        expected = git_blob(root, original_spec)
        require(read_regular(snapshot / 'spec.md', len(expected), root) == expected
                and journal['manifest']['spec_sha256'] == digest(expected),
                INVALID, 'Saved specification differs from its original Git blob')
        require(commit(root, 'HEAD') == head and digest(read_regular(path, JOURNAL_LIMIT, root)) == revision,
                INVALID, 'Repository HEAD or journal changed during inspection')
    except (Refusal, OSError, ValueError, TypeError, KeyError) as error:
        reason = error.reason if isinstance(error, Refusal) else str(error)
        raise Refusal(INVALID, reason) from error
    return {'schema_version': 1, 'command': 'inspect', 'status': 'ready', 'failures': [],
            'resolution': {'task_path': str(paths[TASK_NEW]), 'spec_path': str(paths[SPEC_NEW]),
                           'original_task_path': journal['task_original']},
            'id': journal['id'], 'journal_path': str(path), 'revision': revision,
            'relocation': 'verified-read-only', 'complete': False}
