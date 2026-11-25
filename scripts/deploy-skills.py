#!/usr/bin/env python3
"""Prepare a complete deployment plan without changing the installation."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Literal


_HARNESS_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_PATH_SEGMENTS = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REVISION = re.compile(r"[0-9a-f]{40}")
_REQUIRED_ADAPTER_KEYS = frozenset({"skills_dir", "always_on_path"})
_PROJECT_LINK_KEY = "project_skills_link_dir"
_ADAPTER_KEYS = _REQUIRED_ADAPTER_KEYS | {_PROJECT_LINK_KEY}
_MANIFEST_KEYS = frozenset({
    "schema_version", "harness", "install_id", "skills_dir", "skills_dir_resolved",
    "always_on_path", "source_revision", "objects",
})
_OBJECT_KEYS = frozenset({"kind", "name", "path", "sha256"})
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
class _Plan:
    actions: tuple[_Action, ...]
    manifests: dict[Path, bytes]
    notices: tuple[str, ...]


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


def _read_adapter(directory: Path, home: Path) -> _Adapter:
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
    return _Adapter(directory, skills_dir, Path(os.path.realpath(skills_dir)),
                    entries["always_on_path"], entries.get(_PROJECT_LINK_KEY))


def _load_adapters(source: Path, home: Path) -> list[_Adapter]:
    harness_dir = source / "harness"
    try:
        directories = sorted(harness_dir.iterdir())
    except OSError as error:
        raise _DeploymentError(
            "adapter-incomplete", f"cannot read {harness_dir}: {error.strerror}",
        ) from error

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
        adapters.append(_read_adapter(directory, home))
    return adapters


def _overlap(first: Path, second: Path) -> bool:
    return first.is_relative_to(second) or second.is_relative_to(first)


def _validate_targets(adapters: list[_Adapter], home: Path, config: Path) -> Path:
    home_resolved = Path(os.path.realpath(home))
    retired = home / ".codeium"
    legacy_paths = {
        Path(os.path.abspath(retired)), home_resolved / retired.name, Path(os.path.realpath(retired)),
    }
    manifest_subdirectory = Path("orchestrail/deploy")
    manifest_dir = Path(os.path.realpath(config)) / manifest_subdirectory
    declared_manifest_dir = Path(os.path.abspath(config)) / manifest_subdirectory
    if any(_overlap(path, legacy) for path in (manifest_dir, declared_manifest_dir)
           for legacy in legacy_paths):
        raise _DeploymentError("adapter-conflict", f"deployment manifests overlap legacy paths: {manifest_dir}")
    _require_parent_tree(manifest_dir, "manifest-invalid")

    roots: list[Path] = []
    # Use physical paths for overlap checks while retaining the adapter's expanded path in the manifest.
    always_on_files: list[Path] = []
    for adapter in adapters:
        skills = adapter.skills_dir_resolved
        always_on = home_resolved / adapter.always_on_path.relative_to(home)
        resolved_always_on = Path(os.path.realpath(always_on.parent)) / always_on.name
        if any(_overlap(path, legacy) for path in (
            Path(os.path.abspath(adapter.skills_dir)), skills,
            Path(os.path.abspath(adapter.always_on_path)), always_on, resolved_always_on,
        ) for legacy in legacy_paths):
            raise _DeploymentError(
                "adapter-conflict", f"deployment paths overlap legacy paths for {adapter.name}",
            )
        if _overlap(skills, manifest_dir) or _overlap(resolved_always_on, manifest_dir):
            raise _DeploymentError(
                "adapter-conflict", f"deployment paths overlap manifests for {adapter.name}",
            )
        if (any(_overlap(skills, root) or _overlap(always_on, root) for root in roots)
                or _overlap(skills, always_on)
                or any(_overlap(skills, path) or _overlap(always_on, path) for path in always_on_files)):
            raise _DeploymentError("adapter-conflict", f"conflicting deployment paths for {adapter.name}")
        _require_parent_tree(skills)
        _require_parent_tree(always_on.parent)
        roots.append(skills)
        always_on_files.append(always_on)
    return manifest_dir


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
    contents = _read_optional_file(path, "manifest-invalid")
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


def _read_target_digest(path: Path, adapter: _Adapter) -> str | None:
    if path != adapter.always_on_path:
        # Manifest objects and desired skills were already bound to this exact location.
        _require_directory(path.parent)
    data = _read_optional_file(path, "unsafe-target")
    return None if data is None else _digest(data)


def _plan_harness(
    adapter: _Adapter, skills: dict[str, bytes], hook_result: str, manifest: _Manifest | None,
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
        objects.append({"kind": "always-on" if name is None else "skill", "name": name,
                        "path": str(path), "sha256": new_digest})
        if old_digest is None:
            actions.append(_Action("create", path, None, new_digest, payload))
        elif path in owned and owned[path] != old_digest:
            raise _DeploymentError("ownership-conflict", _OWNERSHIP_RESOLUTION, path=path)
        elif old_digest == new_digest:
            continue
        elif path in owned:
            actions.append(_Action("replace", path, old_digest, new_digest, payload))
        elif manifest is None:
            actions.append(_Action("adopt", path, old_digest, new_digest, payload))
        else:
            raise _DeploymentError("ownership-conflict", _OWNERSHIP_RESOLUTION, path=path)

    for path in sorted(owned.keys() - desired.keys()):
        digest = _read_target_digest(path, adapter)
        if digest is None:
            continue
        if digest != owned[path]:
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
        "always_on_path": str(adapter.always_on_path), "source_revision": None, "objects": objects,
    }
    return actions, (json.dumps(data, indent=2, sort_keys=True) + "\n").encode(), notices


def _plan_deployment(source: Path, hook_result: str) -> _Plan:
    """Read all harness inputs and return actions and changed manifests for a later transaction."""
    home_value = os.environ.get("HOME", "")
    if not os.path.isabs(home_value):
        raise _DeploymentError("home-invalid", "HOME must be a non-empty absolute path")
    home = Path(home_value)
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    adapters = _load_adapters(source, home)
    manifest_dir = _validate_targets(adapters, home, config)
    skills = _load_skill_sources(source)

    actions: list[_Action] = []
    notices: list[str] = []
    manifests: dict[Path, bytes] = {}
    for adapter in adapters:
        path = manifest_dir / f"{adapter.name}.json"
        manifest = _read_manifest(path, adapter)
        changes, updated, messages = _plan_harness(adapter, skills, hook_result, manifest)
        actions.extend(changes)
        notices.extend(messages)
        if manifest is None or manifest.contents != updated:
            manifests[path] = updated
    return _Plan(tuple(actions), manifests, tuple(notices))
