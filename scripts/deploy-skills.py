#!/usr/bin/env python3
"""Deploy harness skills and instructions with ownership records and crash recovery."""

import argparse
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Literal


_HARNESS_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_PATH_SEGMENTS = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REVISION = re.compile(r"[0-9a-f]{40}")
_ACTIVE_PHASE_LINE = re.compile(r"- (discovery|execution|validation): in-progress[ \t]*")
_REQUIRED_ADAPTER_KEYS = frozenset({"skills_dir", "always_on_path"})
_PROJECT_LINK_KEY = "project_skills_link_dir"
_ADAPTER_KEYS = _REQUIRED_ADAPTER_KEYS | {_PROJECT_LINK_KEY}
_MANIFEST_KEYS = frozenset({
    "schema_version", "harness", "install_id", "skills_dir", "skills_dir_resolved",
    "always_on_path", "source_revision", "objects",
})
_OBJECT_KEYS = frozenset({"kind", "name", "path", "sha256"})
_JOURNAL_KEYS = frozenset({"schema_version", "entries"})
_JOURNAL_ENTRY_KEYS = frozenset({"path", "old_sha256", "new_sha256"})
_TEMPORARY_SUFFIX = ".orchestrail-tmp"
_JOURNAL_NAME = "journal.json"
_LOCK_NAME = "deploy.lock"
_REGISTRY_PATH = Path("orchestrail/projects")
_LEGACY_PROJECT_DIRS = frozenset({".windsurf", ".devin"})
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_NO_NATIVE_HOOK = '{"reason":"no-native-adapter","status":"unavailable"}'
_OWNERSHIP_RESOLUTION = (
    "changed since the last deployment; save your changes elsewhere, then delete the "
    "file or restore its deployed bytes, and rerun"
)


class _DeploymentError(Exception):
    exit_status: int = 1

    def __init__(self, code: str, detail: str, *, path: Path | None = None) -> None:
        self.code = code
        location = f" {path}" if path is not None else ""
        super().__init__(f"ERROR {code}{location}: {detail}")


@dataclass(frozen=True)
class _Adapter:
    directory: Path
    skills_dir: Path
    skills_dir_resolved: Path
    always_on_path: Path
    always_on_resolved: Path
    project_skills_link_dir: Path | None

    @property
    def name(self) -> str:
        return self.directory.name

    @property
    def install_id(self) -> str:
        identity = f"{self.name}\n{self.skills_dir_resolved}"
        return _digest(identity.encode("utf-8", errors="surrogateescape"))


@dataclass(frozen=True)
class _Manifest:
    contents: bytes
    objects: dict[Path, str]


@dataclass(frozen=True)
class _Action:
    kind: Literal["create", "replace", "adopt", "remove"]
    path: Path
    old_sha256: str | None
    new_sha256: str | None
    new_contents: bytes | None


@dataclass(frozen=True)
class _JournalEntry:
    old_sha256: str | None
    new_sha256: str | None

    def owns(self, sha256: str) -> bool:
        return sha256 in (self.old_sha256, self.new_sha256)


@dataclass(frozen=True)
class _Journal:
    entries: dict[Path, _JournalEntry]
    sha256: str | None


@dataclass(frozen=True)
class _DeploymentPaths:
    manifest_dir: Path
    lock: Path
    reserved: tuple[Path, ...]
    legacy: set[Path]
    registry: Path
    registry_addresses: set[Path]


@dataclass(frozen=True)
class _Plan:
    actions: tuple[_Action, ...]
    manifests: dict[Path, bytes]
    notices: tuple[str, ...]
    previous_manifests: dict[Path, str | None]
    adapters: list[_Adapter]
    journal: _Journal


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _mode(path: Path, error_code: str) -> int | None:
    try:
        return path.lstat().st_mode
    except FileNotFoundError:
        return None
    except OSError as error:
        raise _DeploymentError(error_code, f"cannot inspect {path}: {error.strerror}") from error


def _read_optional_file(path: Path, error_code: str) -> bytes | None:
    mode = _mode(path, error_code)
    if mode is None:
        return None
    if not stat.S_ISREG(mode):
        raise _DeploymentError(error_code, f"{path} must be a regular file")
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(path, flags), "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise _DeploymentError(error_code, f"{path} must be a regular file")
            return stream.read()
    except OSError as error:
        raise _DeploymentError(error_code, f"cannot read {path}: {error.strerror}") from error


def _read_source_file(path: Path, error_code: str) -> bytes:
    data = _read_optional_file(path, error_code)
    if data is None:
        raise _DeploymentError(error_code, f"missing file {path}")
    return data


@contextmanager
def _managed_directory(path: Path, *, create: bool = False) -> Iterator[int]:
    """Walk an absolute path without following links and anchor operations to the open directory."""
    descriptor = os.open(path.anchor, _DIRECTORY_FLAGS)
    try:
        for part in path.parts[1:]:
            try:
                child = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, dir_fd=descriptor)
                except FileExistsError:
                    pass
                os.fsync(descriptor)
                child = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def _read_at(directory: int, name: str) -> bytes | None:
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(errno.EINVAL, "expected a regular file", name)
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(name, flags, dir_fd=directory), "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise OSError(errno.EINVAL, "expected a regular file", name)
            return stream.read()
    except FileNotFoundError:
        return None


def _read_managed_file(path: Path, error_code: str) -> bytes | None:
    try:
        with _managed_directory(path.parent) as directory:
            return _read_at(directory, path.name)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise _DeploymentError(error_code, f"cannot read {path}: {error.strerror}") from error


def _require_directory(path: Path, error_code: str = "unsafe-target") -> None:
    mode = _mode(path, error_code)
    if mode is not None and not stat.S_ISDIR(mode):
        raise _DeploymentError(error_code, f"{path} must be a directory")


def _require_parent_tree(path: Path, error_code: str = "unsafe-target") -> None:
    # Check the first existing component that could obstruct an otherwise absent target.
    for directory in reversed(path.parents):
        _require_directory(directory, error_code)
    _require_directory(path, error_code)


def _valid_relative_path(value: str) -> bool:
    return bool(_PATH_SEGMENTS.fullmatch(value)) and not {".", ".."}.intersection(value.split("/"))


def _read_adapter(directory: Path, home: Path, resolved_home: Path) -> _Adapter:
    path = directory / "deploy.env"
    data = _read_source_file(path, "deploy-env-invalid")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        line = data.count(b"\n", 0, error.start) + 1
        raise _DeploymentError("deploy-env-invalid", f"{path}:{line}: expected UTF-8") from error

    entries: dict[str, Path] = {}
    for number, line in enumerate(text.split("\n"), 1):
        if "\r" in line or "\x00" in line:
            raise _DeploymentError("deploy-env-invalid", f"{path}:{number}: invalid character")
        if not line or line.startswith("#"):
            continue
        key, equals, value = line.partition("=")
        required = key in _REQUIRED_ADAPTER_KEYS
        relative = value.removeprefix("$HOME/") if required else value
        if (not equals or key not in _ADAPTER_KEYS or key in entries
                or (required and not value.startswith("$HOME/")) or not _valid_relative_path(relative)):
            raise _DeploymentError("deploy-env-invalid", f"{path}:{number}: invalid adapter assignment")
        entries[key] = home / relative if required else Path(relative)

    missing = _REQUIRED_ADAPTER_KEYS - entries.keys()
    if missing:
        raise _DeploymentError("deploy-env-invalid", f"{path}: missing {', '.join(sorted(missing))}")
    skills_dir = entries["skills_dir"]
    always_on_path = entries["always_on_path"]
    return _Adapter(directory, skills_dir, Path(os.path.realpath(skills_dir)),
                    always_on_path, resolved_home / always_on_path.relative_to(home),
                    entries.get(_PROJECT_LINK_KEY))


def _load_adapters(source: Path, home: Path) -> list[_Adapter]:
    harness_dir = source / "harness"
    try:
        directories = sorted(harness_dir.iterdir())
    except OSError as error:
        raise _DeploymentError(
            "adapter-incomplete", f"cannot read {harness_dir}: {error.strerror}",
        ) from error

    resolved_home = Path(os.path.realpath(home))
    adapters = []
    for directory in directories:
        if not _HARNESS_NAME.fullmatch(directory.name):
            continue
        mode = _mode(directory, "adapter-incomplete")
        if mode is None or not stat.S_ISDIR(mode):
            continue
        files = {name: _mode(directory / name, "adapter-incomplete")
                 for name in ("deploy.env", "capabilities.md", "always-on.md")}
        if files["deploy.env"] is None and files["capabilities.md"] is None:
            continue
        for name, mode in files.items():
            if mode is None or not stat.S_ISREG(mode):
                raise _DeploymentError("adapter-incomplete", f"{directory / name} must be a regular file")
        adapters.append(_read_adapter(directory, home, resolved_home))
    return adapters


def _overlap(first: Path, second: Path) -> bool:
    return first.is_relative_to(second) or second.is_relative_to(first)


def _temporary_name(name: str) -> str:
    return f".{name}{_TEMPORARY_SUFFIX}"


def _temporary_path(target: Path) -> Path:
    return target.with_name(_temporary_name(target.name))


def _is_temporary_name(name: str) -> bool:
    return (name.startswith(".") and name.endswith(_TEMPORARY_SUFFIX)
            and len(name) > len(_TEMPORARY_SUFFIX) + 1)


def _path_addresses(path: Path) -> set[Path]:
    return {
        Path(os.path.abspath(path)),
        Path(os.path.realpath(path.parent)) / path.name,
        Path(os.path.realpath(path)),
    }


def _state_paths(home: Path, config: Path) -> _DeploymentPaths:
    legacy_paths = _path_addresses(home / ".codeium")
    registry = config / _REGISTRY_PATH
    registry_addresses = _path_addresses(registry)
    manifest_subdirectory = Path("orchestrail/deploy")
    manifest_dir = Path(os.path.realpath(config)) / manifest_subdirectory
    declared_manifest_dir = Path(os.path.abspath(config)) / manifest_subdirectory
    lock = manifest_dir.parent / _LOCK_NAME
    state_paths = (manifest_dir, declared_manifest_dir, lock, declared_manifest_dir.parent / _LOCK_NAME)
    if any(_overlap(path, legacy) for path in state_paths for legacy in legacy_paths):
        raise _DeploymentError("adapter-conflict", f"deployment state overlaps legacy paths: {manifest_dir}")
    if any(_overlap(path, address) for path in state_paths for address in registry_addresses):
        raise _DeploymentError("adapter-conflict", f"deployment state overlaps the project registry: {registry}")
    _require_parent_tree(manifest_dir, "manifest-invalid")
    return _DeploymentPaths(
        manifest_dir, lock, (*state_paths, *registry_addresses), legacy_paths, registry, registry_addresses,
    )


def _validate_targets(adapters: list[_Adapter], state: _DeploymentPaths) -> None:
    if any(f"{adapter.name}.json" == _JOURNAL_NAME for adapter in adapters):
        journal = state.manifest_dir / _JOURNAL_NAME
        raise _DeploymentError("adapter-conflict", f"a manifest would occupy {journal}")

    roots: list[Path] = []
    # Use physical paths for overlap checks while retaining the adapter's expanded path in the manifest.
    always_on_files: list[Path] = []
    always_on_addresses = {
        path
        for adapter in adapters
        for path in (
            Path(os.path.abspath(adapter.always_on_path)), adapter.always_on_resolved,
            Path(os.path.realpath(adapter.always_on_resolved.parent)) / adapter.always_on_resolved.name,
        )
    }
    always_on_temporaries = {_temporary_path(path) for path in always_on_addresses}
    reserved_addresses = always_on_addresses | set(state.reserved) | state.legacy
    if any(_overlap(temporary, reserved) for temporary in always_on_temporaries
           for reserved in reserved_addresses):
        raise _DeploymentError("adapter-conflict", "an always-on temporary overlaps a reserved deployment path")
    for adapter in adapters:
        skills = adapter.skills_dir_resolved
        skill_paths = (
            Path(os.path.abspath(adapter.skills_dir)), skills,
            Path(os.path.realpath(adapter.skills_dir.parent)) / adapter.skills_dir.name,
        )
        if any(_overlap(root, temporary) for root in skill_paths for temporary in always_on_temporaries):
            raise _DeploymentError(
                "adapter-conflict", f"skill root for {adapter.name} overlaps an always-on temporary path",
            )
        always_on = adapter.always_on_resolved
        resolved_always_on = Path(os.path.realpath(always_on.parent)) / always_on.name
        locations = (
            Path(os.path.abspath(adapter.skills_dir)), skills,
            Path(os.path.abspath(adapter.always_on_path)), always_on, resolved_always_on,
        )
        if any(_overlap(path, legacy) for path in locations for legacy in state.legacy):
            raise _DeploymentError(
                "adapter-conflict", f"deployment paths overlap legacy paths for {adapter.name}",
            )
        if any(_overlap(path, reserved) for path in locations for reserved in state.reserved):
            raise _DeploymentError(
                "adapter-conflict", f"deployment paths overlap state files for {adapter.name}",
            )
        if _is_temporary_name(always_on.name):
            raise _DeploymentError("adapter-conflict", f"reserved temporary filename: {always_on}")
        if (any(_overlap(skills, root) or _overlap(always_on, root) for root in roots)
                or _overlap(skills, always_on)
                or any(_overlap(skills, path) or _overlap(always_on, path) for path in always_on_files)):
            raise _DeploymentError("adapter-conflict", f"conflicting deployment paths for {adapter.name}")
        _require_parent_tree(skills)
        _require_parent_tree(always_on.parent)
        roots.append(skills)
        always_on_files.append(always_on)


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _valid_absolute_path(value: object) -> bool:
    return isinstance(value, str) and "\x00" not in value and os.path.isabs(value)


def _valid_skill_name(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and value not in {".", ".."}
            and not any(character in value for character in "/\x00\r\n"))


def _read_manifest(path: Path, adapter: _Adapter) -> _Manifest | None:
    contents = _read_managed_file(path, "manifest-invalid")
    if contents is None:
        return None
    try:
        data = json.loads(contents.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (ValueError, RecursionError) as error:
        raise _DeploymentError("manifest-invalid", f"{path}: invalid JSON ({error})") from error

    if (not isinstance(data, dict) or data.keys() != _MANIFEST_KEYS
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["harness"] != adapter.name
            or not isinstance(data["install_id"], str) or not _SHA256.fullmatch(data["install_id"])
            or not all(_valid_absolute_path(data[key]) for key in (
                "skills_dir", "skills_dir_resolved", "always_on_path"))
            or not isinstance(data["objects"], list)):
        raise _DeploymentError("manifest-invalid", f"{path}: invalid manifest fields")
    revision = data["source_revision"]
    if revision is not None and (not isinstance(revision, str) or not _REVISION.fullmatch(revision)):
        raise _DeploymentError("manifest-invalid", f"{path}: invalid source revision")
    if (data["skills_dir_resolved"] != str(adapter.skills_dir_resolved)
            or data["install_id"] != adapter.install_id):
        raise _DeploymentError("target-moved", f"{path}: installation target differs from the manifest")
    if data["always_on_path"] != str(adapter.always_on_path):
        raise _DeploymentError("manifest-invalid", f"{path}: always-on path differs from the adapter")

    objects: dict[Path, str] = {}
    names: set[str | None] = set()
    previous = ""
    for item in data["objects"]:
        if (not isinstance(item, dict) or item.keys() != _OBJECT_KEYS
                or not _valid_absolute_path(item["path"])
                or not isinstance(item["sha256"], str) or not _SHA256.fullmatch(item["sha256"])):
            raise _DeploymentError("manifest-invalid", f"{path}: invalid object fields")
        name = item["name"]
        if item["kind"] == "always-on" and name is None:
            expected = adapter.always_on_path
        elif item["kind"] == "skill" and _valid_skill_name(name):
            root = adapter.skills_dir_resolved
            if not Path(os.path.abspath(item["path"])).is_relative_to(root):
                raise _DeploymentError("unsafe-target", f"{item['path']} is outside {root}")
            expected = root / name / "SKILL.md"
        else:
            raise _DeploymentError("manifest-invalid", f"{path}: invalid object identity")
        identity = name.casefold() if name is not None else None
        if item["path"] != str(expected) or item["path"] <= previous or identity in names:
            raise _DeploymentError("manifest-invalid", f"{path}: invalid, repeated or unsorted object path")
        previous = item["path"]
        names.add(identity)
        objects[expected] = item["sha256"]
    return _Manifest(contents, objects)


def _load_skill_sources(source: Path) -> dict[str, bytes]:
    skills: dict[str, bytes] = {}
    names: set[str] = set()
    for directory, prefix in (("workflows", ""), ("rules", "rule-"), ("principles", "principle-")):
        source_dir = source / directory
        try:
            paths = sorted(source_dir.iterdir())
        except OSError as error:
            raise _DeploymentError(
                "unsafe-target", f"cannot read skill sources in {source_dir}: {error.strerror}",
            ) from error
        for path in paths:
            if not path.name.endswith(".md"):
                continue
            mode = _mode(path, "unsafe-target")
            if mode is not None and stat.S_ISDIR(mode):
                continue
            name = prefix + path.stem
            if not _valid_skill_name(name) or name.casefold() in names:
                raise _DeploymentError(
                    "name-collision", f"invalid or repeated installed name {name!r} at {path}",
                )
            names.add(name.casefold())
            skills[name] = _read_source_file(path, "unsafe-target")
    return skills


def _assemble_always_on(adapter: _Adapter, hook_result: str) -> bytes:
    body = _read_source_file(adapter.directory / "always-on.md", "adapter-incomplete")
    capabilities = _read_source_file(adapter.directory / "capabilities.md", "adapter-incomplete")
    result = hook_result if (adapter.directory / "hooks.json").is_file() else _NO_NATIVE_HOOK
    return (body + b"\n<!-- Logging capabilities -->\n" + capabilities
            + b"\n## Current hook installation\n\ninstallation-result: " + result.encode() + b"\n")


def _adapter_target(adapter: _Adapter, path: Path) -> Path | None:
    if path == adapter.always_on_path:
        return adapter.always_on_resolved
    if (path.name == "SKILL.md" and path.parent.parent == adapter.skills_dir_resolved
            and _valid_skill_name(path.parent.name)):
        return path
    return None


def _valid_journal_digest(value: object) -> bool:
    return value is None or (isinstance(value, str) and _SHA256.fullmatch(value) is not None)


def _read_journal(path: Path, adapters: list[_Adapter]) -> _Journal:
    contents = _read_managed_file(path, "journal-invalid")
    if contents is None:
        return _Journal({}, None)
    try:
        data = json.loads(contents.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (ValueError, RecursionError) as error:
        raise _DeploymentError("journal-invalid", f"{path}: invalid JSON ({error})") from error
    if (not isinstance(data, dict) or data.keys() != _JOURNAL_KEYS
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or not isinstance(data["entries"], list)):
        raise _DeploymentError("journal-invalid", f"{path}: invalid journal fields")

    entries: dict[Path, _JournalEntry] = {}
    targets: dict[Path, Path] = {}
    previous = ""
    for item in data["entries"]:
        if (not isinstance(item, dict) or item.keys() != _JOURNAL_ENTRY_KEYS
                or not _valid_absolute_path(item["path"])
                or not _valid_journal_digest(item["old_sha256"])
                or not _valid_journal_digest(item["new_sha256"])
                or item["old_sha256"] == item["new_sha256"]):
            raise _DeploymentError("journal-invalid", f"{path}: invalid journal entry")
        name = item["path"]
        try:
            os.fsencode(name)
        except UnicodeEncodeError as error:
            raise _DeploymentError("journal-invalid", f"{path}: entry path cannot be encoded") from error
        managed = Path(name)
        if str(managed) != name or name <= previous:
            raise _DeploymentError("journal-invalid", f"{path}: invalid, repeated or unsorted entry path")
        for adapter in adapters:
            target = _adapter_target(adapter, managed)
            if target is not None:
                break
        else:
            raise _DeploymentError("journal-invalid", f"{path}: entry outside managed targets: {name}")
        previous = name
        entries[managed] = _JournalEntry(item["old_sha256"], item["new_sha256"])
        targets[managed] = target

    for managed, target in targets.items():
        current = _read_managed_file(target, "journal-mismatch")
        digest = None if current is None else _digest(current)
        _check_recovery_digest(managed, digest, entries[managed])
    return _Journal(entries, _digest(contents))


def _read_target_digest(path: Path, adapter: _Adapter) -> str | None:
    target = _adapter_target(adapter, path)
    if target is None:
        raise _DeploymentError("unsafe-target", f"{path} is outside the targets for {adapter.name}")
    data = _read_managed_file(target, "unsafe-target")
    return None if data is None else _digest(data)


def _check_recovery_digest(path: Path, digest: str | None, entry: _JournalEntry) -> None:
    if digest not in (entry.old_sha256, entry.new_sha256):
        raise _DeploymentError("journal-mismatch", f"{path} differs from both recorded digests")


def _plan_harness(
    adapter: _Adapter, skills: dict[str, bytes], hook_result: str, manifest: _Manifest | None,
    journal: dict[Path, _JournalEntry], *, source_revision: str | None,
) -> tuple[list[_Action], bytes, list[str]]:
    desired: dict[Path, tuple[str | None, bytes]] = {
        adapter.skills_dir_resolved / name / "SKILL.md": (name, data) for name, data in skills.items()
    }
    desired[adapter.always_on_path] = (None, _assemble_always_on(adapter, hook_result))
    owned = manifest.objects if manifest is not None else {}
    actions = []
    objects = []
    notices = []
    for path in sorted(desired, key=str):
        name, payload = desired[path]
        old_digest = _read_target_digest(path, adapter)
        new_digest = _digest(payload)
        entry = journal.get(path)
        if entry is not None:
            _check_recovery_digest(path, old_digest, entry)
        recovery_owned = old_digest is not None and entry is not None and entry.owns(old_digest)
        objects.append({"kind": "always-on" if name is None else "skill", "name": name,
                        "path": str(path), "sha256": new_digest})
        if old_digest is None:
            actions.append(_Action("create", path, None, new_digest, payload))
        elif path in owned and owned[path] != old_digest and not recovery_owned:
            raise _DeploymentError("ownership-conflict", _OWNERSHIP_RESOLUTION, path=path)
        elif old_digest == new_digest:
            continue
        elif path in owned or recovery_owned:
            actions.append(_Action("replace", path, old_digest, new_digest, payload))
        elif manifest is None:
            actions.append(_Action("adopt", path, old_digest, new_digest, payload))
        else:
            raise _DeploymentError("ownership-conflict", _OWNERSHIP_RESOLUTION, path=path)

    obsolete = (owned.keys() | journal.keys()) - desired.keys() if manifest is not None else set()
    for path in sorted(obsolete, key=str):
        digest = _read_target_digest(path, adapter)
        entry = journal.get(path)
        if entry is not None:
            _check_recovery_digest(path, digest, entry)
        if digest is None:
            continue
        if digest != owned.get(path) and (entry is None or not entry.owns(digest)):
            notices.append(f"release-modified {path}")
            continue
        actions.append(_Action("remove", path, digest, None, None))
        try:
            if any(entry != path for entry in path.parent.iterdir()):
                notices.append(f"keep-nonempty {path.parent}")
        except OSError as error:
            raise _DeploymentError(
                "unsafe-target", f"cannot read {path.parent}: {error.strerror}",
            ) from error

    data = {
        "schema_version": 1, "harness": adapter.name, "install_id": adapter.install_id,
        "skills_dir": str(adapter.skills_dir), "skills_dir_resolved": str(adapter.skills_dir_resolved),
        "always_on_path": str(adapter.always_on_path), "source_revision": source_revision,
        "objects": objects,
    }
    return actions, (json.dumps(data, indent=2, sort_keys=True) + "\n").encode(), notices


def _config_directory(home: Path) -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")


def _deployment_home() -> tuple[Path, Path]:
    home_value = os.environ.get("HOME", "")
    if not _valid_absolute_path(home_value):
        raise _DeploymentError("home-invalid", "HOME must be a non-empty absolute path")
    home = Path(home_value)
    return home, _config_directory(home)


def _source_revision(source: Path) -> str | None:
    environment = os.environ.copy()
    # A caller's Git repository overrides must not redirect the selected source query.
    for name in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_NAMESPACE"):
        environment.pop(name, None)
    try:
        result = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "--verify", "HEAD"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=environment, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    revision = result.stdout.removesuffix(b"\n").decode("ascii", errors="replace")
    return revision if _REVISION.fullmatch(revision) else None


def _build_plan(
    source: Path, hook_result: str, home: Path, state: _DeploymentPaths, *, recover: bool,
) -> _Plan:
    adapters = _load_adapters(source, home)
    _validate_targets(adapters, state)
    manifest_dir = state.manifest_dir
    journal = _read_journal(manifest_dir / _JOURNAL_NAME, adapters) if recover else _Journal({}, None)
    skills = _load_skill_sources(source)
    source_revision = _source_revision(source)

    actions: list[_Action] = []
    notices: list[str] = []
    manifests: dict[Path, bytes] = {}
    previous_manifests: dict[Path, str | None] = {}
    for adapter in adapters:
        path = manifest_dir / f"{adapter.name}.json"
        manifest = _read_manifest(path, adapter)
        adapter_journal = {key: entry for key, entry in journal.entries.items()
                           if _adapter_target(adapter, key) is not None}
        changes, updated, messages = _plan_harness(
            adapter, skills, hook_result, manifest, adapter_journal, source_revision=source_revision,
        )
        actions.extend(changes)
        notices.extend(messages)
        if manifest is None or manifest.contents != updated:
            manifests[path] = updated
            previous_manifests[path] = None if manifest is None else _digest(manifest.contents)
    return _Plan(tuple(actions), manifests, tuple(notices), previous_manifests, adapters, journal)


def _plan_deployment(source: Path, hook_result: str) -> _Plan:
    """Read harness inputs without opening a transaction or applying recovery evidence."""
    home, config = _deployment_home()
    return _build_plan(source, hook_result, home, _state_paths(home, config), recover=False)


@contextmanager
def _deployment_lock(path: Path) -> Iterator[None]:
    with _managed_directory(path.parent, create=True) as directory:
        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
        descriptor = os.open(path.name, flags, mode=0o600, dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise _DeploymentError("unsafe-target", f"{path} must be a regular lock file")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise _DeploymentError("deploy-locked", f"another deploy holds {path}") from error
            yield
        finally:
            os.close(descriptor)


def _matches_at(directory: int, path: Path, expected: str | None) -> None:
    contents = _read_at(directory, path.name)
    current = None if contents is None else _digest(contents)
    if current != expected:
        raise OSError(errno.EBUSY, "target changed after validation", str(path))


def _check_directory_identity(path: Path, descriptor: int) -> None:
    with _managed_directory(path) as current:
        if not os.path.samestat(os.fstat(descriptor), os.fstat(current)):
            raise OSError(errno.EBUSY, "directory changed after validation", str(path))


def _replace_file(path: Path, payload: bytes, expected: str | None) -> None:
    with _managed_directory(path.parent, create=True) as directory:
        _matches_at(directory, path, expected)
        temporary = _temporary_name(path.name)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open(temporary, flags, mode=0o666, dir_fd=directory)
        temporary_info: os.stat_result | None = None
        replaced = False
        try:
            with os.fdopen(descriptor, "wb") as stream:
                temporary_info = os.fstat(stream.fileno())
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _check_directory_identity(path.parent, directory)
            _matches_at(directory, path, expected)
            if not os.path.samestat(
                temporary_info, os.stat(temporary, dir_fd=directory, follow_symlinks=False),
            ):
                raise OSError(errno.EBUSY, "temporary file changed", str(path))
            # Keep both names anchored to the opened directory during replacement.
            previous_directory = os.open(".", _DIRECTORY_FLAGS)
            try:
                os.fchdir(directory)
                os.replace(temporary, path.name)
                replaced = True
            finally:
                try:
                    os.fchdir(previous_directory)
                finally:
                    os.close(previous_directory)
            os.fsync(directory)
        finally:
            if not replaced and temporary_info is not None:
                try:
                    current = os.stat(temporary, dir_fd=directory, follow_symlinks=False)
                    if os.path.samestat(temporary_info, current):
                        os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:
                    pass


def _unlink_file(path: Path, directory: int, expected: str | None) -> None:
    _check_directory_identity(path.parent, directory)
    _matches_at(directory, path, expected)
    os.unlink(path.name, dir_fd=directory)
    os.fsync(directory)


def _remove_skill(path: Path, expected: str | None) -> bool:
    parent = path.parent
    with _managed_directory(parent.parent) as root, _managed_directory(parent) as directory:
        _unlink_file(path, directory, expected)
        if not os.path.samestat(os.fstat(directory), os.stat(parent.name, dir_fd=root, follow_symlinks=False)):
            raise OSError(errno.EBUSY, "directory changed after validation", str(parent))
        try:
            os.rmdir(parent.name, dir_fd=root)
        except OSError as error:
            if error.errno in {errno.ENOTEMPTY, errno.EEXIST}:
                return False
            raise
        os.fsync(root)
    return True


def _clean_temporaries(directory: int, names: list[str]) -> None:
    for name in names:
        try:
            if _is_temporary_name(name) and stat.S_ISREG(
                os.stat(name, dir_fd=directory, follow_symlinks=False).st_mode,
            ):
                os.unlink(name, dir_fd=directory)
        except FileNotFoundError:
            continue


def _clean_target_temporaries(
    path: Path, *, visit_children: bool = False, preserve: set[str] | None = None,
) -> None:
    try:
        with _managed_directory(path) as directory:
            names = os.listdir(directory)
            if visit_children:
                for name in names:
                    try:
                        child = os.open(name, _DIRECTORY_FLAGS, dir_fd=directory)
                    except OSError as error:
                        if error.errno in {errno.ENOENT, errno.ENOTDIR, errno.ELOOP}:
                            continue
                        raise
                    try:
                        _clean_temporaries(child, os.listdir(child))
                    finally:
                        os.close(child)
            _clean_temporaries(directory, names if preserve is None else [name for name in names if name not in preserve])
    except FileNotFoundError:
        return


def _clean_deployment_temporaries(adapters: list[_Adapter], state: _DeploymentPaths) -> None:
    for adapter in adapters:
        _clean_target_temporaries(adapter.skills_dir_resolved, visit_children=True)
    for directory in {adapter.always_on_resolved.parent for adapter in adapters}:
        preserve = {path.name for path in state.registry_addresses if path.parent == directory}
        _clean_target_temporaries(directory, preserve=preserve)
    # An interrupted journal or manifest replacement can leave these exact state temporaries.
    try:
        with _managed_directory(state.manifest_dir) as directory:
            names = [_temporary_name(_JOURNAL_NAME)]
            names.extend(_temporary_name(f"{adapter.name}.json") for adapter in adapters)
            _clean_temporaries(directory, names)
    except FileNotFoundError:
        return


def _journal_payload(plan: _Plan) -> bytes:
    # Applied targets still need their previous entry until the manifests record the new digests.
    entries = plan.journal.entries | {
        action.path: _JournalEntry(action.old_sha256, action.new_sha256) for action in plan.actions
    }
    record = {"schema_version": 1, "entries": [
        {"path": str(path), "old_sha256": entry.old_sha256, "new_sha256": entry.new_sha256}
        for path, entry in sorted(entries.items(), key=lambda pair: str(pair[0]))
    ]}
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()


def _validate_pending_temporaries(targets: list[Path]) -> None:
    for target in targets:
        path = _temporary_path(target)
        try:
            with _managed_directory(path.parent) as directory:
                info = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as error:
            raise _DeploymentError("unsafe-target", f"cannot inspect {path}: {error.strerror}") from error
        if not stat.S_ISREG(info.st_mode):
            raise _DeploymentError("unsafe-target", f"{path} must be absent or a regular temporary file")


def _apply_plan(
    plan: _Plan, state: _DeploymentPaths, *, always_on_targets: dict[Path, Path], write_journal: bool,
) -> None:
    manifest_dir = state.manifest_dir
    journal_path = manifest_dir / _JOURNAL_NAME
    journal_digest = plan.journal.sha256
    _clean_deployment_temporaries(plan.adapters, state)
    if write_journal:
        journal_bytes = _journal_payload(plan)
        _replace_file(journal_path, journal_bytes, journal_digest)
        journal_digest = _digest(journal_bytes)

    kept = []
    for action in plan.actions:
        target = always_on_targets.get(action.path, action.path)
        if action.new_contents is None:
            if not _remove_skill(target, action.old_sha256):
                kept.append(f"keep-nonempty {target.parent}")
        else:
            _replace_file(target, action.new_contents, action.old_sha256)

    for path, payload in plan.manifests.items():
        _replace_file(path, payload, plan.previous_manifests[path])
    if journal_digest is not None:
        with _managed_directory(manifest_dir) as directory:
            _unlink_file(journal_path, directory, journal_digest)

    for action in plan.actions:
        print(f"{action.kind} {action.path}")
    for notice in kept:
        print(notice)
    for notice in plan.notices:
        if not notice.startswith("keep-nonempty "):
            print(notice)


def _read_project_registry(registry: Path) -> tuple[Path, ...] | None:
    """Read the registration format shared with the Git rails hook."""
    try:
        try:
            descriptor = os.open(registry, os.O_RDONLY | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise _DeploymentError("registry-invalid", f"{registry} must be a regular file")
            lines = stream.read().decode("utf-8").split("\n")
    except (OSError, UnicodeDecodeError) as error:
        raise _DeploymentError("registry-invalid", f"cannot read {registry}: {error}") from error

    if lines[-1] == "":
        lines.pop()
    roots: dict[str, Path] = {}
    for number, line in enumerate(lines, 1):
        if (not _valid_absolute_path(line) or "\r" in line or os.path.realpath(line) != line):
            raise _DeploymentError("registry-invalid", f"{registry}:{number}: expected a canonical absolute path")
        roots.setdefault(line, Path(line))
    return tuple(roots.values())


def _list_projects() -> None:
    home = os.environ.get("HOME")
    if not home and not os.environ.get("XDG_CONFIG_HOME"):
        return
    source = Path(__file__).resolve().parents[1]
    projects = _read_project_registry(_config_directory(Path(home or "")) / _REGISTRY_PATH)
    for project in projects or ():
        if project != source and project.is_dir():
            sys.stdout.buffer.write(os.fsencode(project) + b"\0")


def _task_state_is_active(path: Path) -> bool:
    """Read only regular task states, treating unreadable contents as active."""
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return False
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError:
        return True

    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(path, flags), "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return False
            text = stream.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return True

    in_phases = False
    for line in text.split("\n"):
        if line.startswith("## "):
            in_phases = line == "## Phases"
        elif in_phases and _ACTIVE_PHASE_LINE.fullmatch(line):
            return True
    return False


def _active_project_task(project: Path) -> Path | None:
    if not project.is_dir():
        return None
    for task in sorted((project / ".ai/tasks/todo").glob("*")):
        if _task_state_is_active(task / "state.md"):
            return task
    return None


def _add_project_links(
    adapter: _Adapter, destination: Path, directory: int, registry_addresses: set[Path],
) -> int:
    try:
        entries = os.scandir(adapter.skills_dir)
    except FileNotFoundError:
        return 0
    linked = 0
    with entries:
        for entry in entries:
            if destination / entry.name in registry_addresses:
                continue
            try:
                if not entry.is_dir():
                    continue
            except OSError as error:
                if error.errno == errno.ELOOP:
                    continue
                raise
            _check_directory_identity(destination, directory)
            try:
                os.symlink(f"{entry.path}/", entry.name, dir_fd=directory)
            except FileExistsError:
                continue
            linked += 1
    return linked


def _remove_broken_project_links(
    adapter: _Adapter, destination: Path, directory: int, registry_addresses: set[Path],
) -> int:
    prefixes = (f"{adapter.skills_dir}/", f"{adapter.skills_dir_resolved}/")
    unlinked = 0
    with os.scandir(directory) as entries:
        for entry in entries:
            if destination / entry.name in registry_addresses or not entry.is_symlink():
                continue
            try:
                original = entry.stat(follow_symlinks=False)
                if not os.readlink(entry.name, dir_fd=directory).startswith(prefixes):
                    continue
                try:
                    os.stat(entry.name, dir_fd=directory)
                except OSError as error:
                    if error.errno not in {errno.ENOENT, errno.ENOTDIR, errno.ELOOP}:
                        raise
                else:
                    continue
                _check_directory_identity(destination, directory)
                current = os.stat(entry.name, dir_fd=directory, follow_symlinks=False)
                if os.path.samestat(original, current):
                    os.unlink(entry.name, dir_fd=directory)
                    unlinked += 1
            except FileNotFoundError:
                continue
    return unlinked


def _is_legacy_project_path(path: Path, legacy: set[Path]) -> bool:
    return bool(_LEGACY_PROJECT_DIRS.intersection(path.parts)) or any(
        path.is_relative_to(address) for address in legacy
    )


def _project_links(
    project: Path, adapter: _Adapter, legacy: set[Path], registry_addresses: set[Path], *, refresh: bool,
) -> tuple[int, int]:
    relative = adapter.project_skills_link_dir
    if relative is None:
        return 0, 0
    destination = project / relative
    if (_is_legacy_project_path(destination, legacy)
            or any(destination.is_relative_to(address) for address in registry_addresses)):
        return 0, 0
    with ExitStack() as stack:
        try:
            directory = stack.enter_context(_managed_directory(destination, create=not refresh))
        except OSError as error:
            if refresh and error.errno in {errno.ENOENT, errno.ENOTDIR, errno.ELOOP}:
                return 0, 0
            raise
        unlinked = _remove_broken_project_links(adapter, destination, directory, registry_addresses) if refresh else 0
        return _add_project_links(adapter, destination, directory, registry_addresses), unlinked


def _link_project(source: Path, project: Path) -> None:
    home, config = _deployment_home()
    adapters = _load_adapters(source, home)
    legacy = _path_addresses(home / ".codeium")
    registry_addresses = _path_addresses(config / _REGISTRY_PATH)
    with _managed_directory(project):
        for adapter in adapters:
            _project_links(project, adapter, legacy, registry_addresses, refresh=False)


def _has_tracked_knowledge(project: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(project), "ls-files", "--", ".ai"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5,
        )
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired as error:
        raise OSError(errno.ETIMEDOUT, "cannot check tracked project knowledge", project) from error
    return bool(result.stdout)


def _has_knowledge_ignore(contents: bytes) -> bool:
    return bool({b".ai", b".ai/"}.intersection(contents.split(b"\n")))


def _is_registry_file(info: os.stat_result, registry: Path) -> bool:
    try:
        return os.path.samestat(info, registry.stat())
    except FileNotFoundError:
        return False


def _ignore_untracked_knowledge(project: Path, state: _DeploymentPaths) -> None:
    name = ".gitignore"
    if (_is_legacy_project_path(project, state.legacy) or project / name in state.registry_addresses
            or not (project / ".git").is_dir()
            or _has_tracked_knowledge(project)):
        return
    with _managed_directory(project) as directory:
        flags = os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
        try:
            previous = os.stat(name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            previous = None
            flags |= os.O_CREAT | os.O_EXCL
        # A linked ignore file may share its bytes with another project's file.
        if previous is not None and (not stat.S_ISREG(previous.st_mode) or previous.st_nlink != 1):
            return
        try:
            descriptor = os.open(name, flags, mode=0o666, dir_fd=directory)
        except PermissionError:
            if _has_knowledge_ignore(_read_at(directory, name) or b""):
                return
            raise
        with os.fdopen(descriptor, "r+b") as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or (previous is not None and not os.path.samestat(previous, info))):
                return
            contents = stream.read()
            if not _has_knowledge_ignore(contents) and not _is_registry_file(info, state.registry):
                _check_directory_identity(project, directory)
                separator = b"\n" if contents and not contents.endswith(b"\n") else b""
                stream.write(separator + b".ai/\n")


def _refresh_projects(
    source: Path, projects: tuple[Path, ...] | None, adapters: list[_Adapter], state: _DeploymentPaths,
    *, skip_active: set[Path],
) -> None:
    if projects is None:
        print("registry absent: no projects registered; run scripts/setup-new-project.sh in each project")
        return
    for project in projects:
        if not project.is_dir():
            print(f"project missing {project}")
        elif project == source:
            print(f"project skipped (source checkout) {project}")
        elif project in skip_active:
            print(f"project skipped (active task) {project}")
        else:
            linked = unlinked = 0
            for adapter in adapters:
                added, removed = _project_links(project, adapter, state.legacy, state.registry_addresses, refresh=True)
                linked += added
                unlinked += removed
            _ignore_untracked_knowledge(project, state)
            print(f"project updated {project} (linked {linked}, unlinked {unlinked})")


def _deploy(source: Path, hook_result: str, *, force: bool) -> int:
    home, config = _deployment_home()
    state = _state_paths(home, config)
    # Check reserved-path collisions before creating the lock. Plan only while holding it.
    lock_mode = _mode(state.lock, "unsafe-target")
    if lock_mode is None:
        _validate_targets(_load_adapters(source, home), state)
        # A malformed registry must not create the persistent lock on a first run.
        _read_project_registry(state.registry)
    elif not stat.S_ISREG(lock_mode):
        raise _DeploymentError("unsafe-target", f"{state.lock} must be a regular lock file")
    with _deployment_lock(state.lock):
        locked_state = _state_paths(home, config)
        if locked_state.lock != state.lock:
            raise _DeploymentError("unsafe-target", f"deployment configuration moved: {config}")
        projects = _read_project_registry(locked_state.registry)
        plan = _build_plan(source, hook_result, home, locked_state, recover=True)
        always_on_targets = {adapter.always_on_path: adapter.always_on_resolved for adapter in plan.adapters}
        write_journal = bool(plan.actions or (plan.manifests and plan.journal.sha256 is None))
        replacements = [
            always_on_targets.get(action.path, action.path) for action in plan.actions
            if action.new_contents is not None
        ]
        replacements.extend(plan.manifests)
        if write_journal:
            replacements.append(locked_state.manifest_dir / _JOURNAL_NAME)
        _validate_pending_temporaries(replacements)

        active: dict[Path, Path] = {}
        for project in projects or ():
            task = _active_project_task(project)
            if task is not None:
                active[project] = task
        if plan.actions and active and not force:
            print("deferred: active consumers")
            for project, task in active.items():
                print(f"active {project} {task}")
            return 3

        _apply_plan(plan, locked_state, always_on_targets=always_on_targets, write_journal=write_journal)
        _refresh_projects(
            source, projects, plan.adapters, locked_state, skip_active=set() if force else set(active),
        )
        if force:
            for project in active:
                print(f"forced {project}")
        print("note: task starts during deployment are not detected; run sync when no pipeline run is starting")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    deploy = commands.add_parser("deploy", allow_abbrev=False)
    deploy.add_argument("--from", dest="source", type=Path, required=True)
    deploy.add_argument("--hook-result", required=True)
    deploy.add_argument("--force", action="store_true")
    commands.add_parser("list-projects", allow_abbrev=False)
    link = commands.add_parser("link-project", allow_abbrev=False)
    link.add_argument("--from", dest="source", type=Path, required=True)
    link.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "deploy":
            if "\r" in args.hook_result or "\n" in args.hook_result:
                deploy.error("--hook-result must be a single line")
            return _deploy(Path(os.path.realpath(args.source)), args.hook_result, force=args.force)
        elif args.command == "list-projects":
            _list_projects()
        else:
            _link_project(Path(os.path.realpath(args.source)), Path(os.path.abspath(args.project)))
    except _DeploymentError as error:
        print(error, file=sys.stderr)
        return error.exit_status
    except OSError as error:
        print(f"ERROR io-error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
