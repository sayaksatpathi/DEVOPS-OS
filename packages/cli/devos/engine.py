"""Repository discovery and profile/lockfile loading for DevOS.

The engine locates the repository root, loads profile and lockfile JSON, and
reports structured results. It performs no privileged operations and writes
nothing — it is safe to run anywhere.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class EngineError(Exception):
    """Raised for unrecoverable engine/config problems (maps to exit code 4)."""


def find_root(start: Path | None = None) -> Path:
    """Locate the DevOS repository root.

    Order: $DEVOS_ROOT, then walk upward from ``start`` (or cwd) looking for a
    ``profiles`` directory. Raises EngineError if none is found.
    """
    env = os.environ.get("DEVOS_ROOT")
    if env:
        p = Path(env)
        if (p / "profiles").is_dir():
            return p
        raise EngineError(f"DEVOS_ROOT={env} has no 'profiles' directory")
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "profiles" / "definitions").is_dir():
            return candidate
    raise EngineError(
        "could not locate DevOS repo root (no profiles/definitions found); "
        "run from inside the repo or set DEVOS_ROOT"
    )


def profiles_dir(root: Path) -> Path:
    return root / "profiles" / "definitions"


def locks_dir(root: Path) -> Path:
    return root / "locks"


def list_profiles(root: Path) -> list[str]:
    d = profiles_dir(root)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise EngineError(f"{path}: invalid JSON: {e}") from e


def load_profile(root: Path, name: str) -> dict:
    path = profiles_dir(root) / f"{name}.json"
    try:
        doc = _load_json(path)
    except FileNotFoundError:
        raise EngineError(f"profile '{name}' not found at {path}") from None
    if not isinstance(doc, dict):
        raise EngineError(f"profile '{name}': top level is not an object")
    return doc


def apt_packages(profile: dict) -> list[str]:
    """Return the names of apt-sourced tools in a profile, in declared order."""
    out: list[str] = []
    for tool in profile.get("tools", []):
        if isinstance(tool, dict) and tool.get("source") == "apt":
            name = tool.get("name")
            if isinstance(name, str) and name:
                out.append(name)
    return out


def apt_packages_enforced(root: "Path", name: str, profile: dict) -> tuple[list[str], bool]:
    """Return the apt install list, PINNED to the lockfile's versions when available.

    Returns (packages, pinned). When a lockfile exists and has resolved versions for every
    apt tool, each entry is "name=version" (reproducible). Otherwise falls back to bare names
    and pinned=False — apply then reports that it installed latest, not locked, versions.
    """
    names = apt_packages(profile)
    try:
        lock = load_lockfile(root, name)
    except EngineError:
        lock = None
    if not lock:
        return names, False
    versions: dict[str, str] = {}
    for t in lock.get("tools", []):
        if isinstance(t, dict) and t.get("source") == "apt":
            v = t.get("version")
            if isinstance(v, str) and v and v not in ("PLACEHOLDER", "UNRESOLVED"):
                versions[t.get("name")] = v
    if names and all(n in versions for n in names):
        return [f"{n}={versions[n]}" for n in names], True
    return names, False


def ansible_dir(root: Path) -> Path:
    return root / "provision" / "ansible"


def binary_tools(profile: dict) -> list[dict]:
    """Return the binary-sourced tool dicts in a profile, in declared order."""
    return [t for t in profile.get("tools", [])
            if isinstance(t, dict) and t.get("source") == "binary"]


import re as _re

_SECRET_PATTERNS = [
    _re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key|bearer)\s*[:=]\s*\S+'),
    _re.compile(r'(?i)(aws_)?(secret_)?access_key_id?\s*[:=]\s*\S+'),
    _re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'),
    _re.compile(r'AKIA[0-9A-Z]{16}'),
    _re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    _re.compile(r'(?i)\beyJ[A-Za-z0-9_-]{10,}\b'),  # JWT-ish
]


def redact_secrets(text: str) -> str:
    """Redact obvious secrets from diagnostic text (§6.14). Best-effort, not a guarantee."""
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def parse_dpkg_query(output: str) -> dict[str, str]:
    """Parse `dpkg-query -W pkg...` output (``name\\tversion`` per line).

    Lines without a tab (e.g. 'no packages found') are ignored. Returns a map of
    package name -> version string.
    """
    versions: dict[str, str] = {}
    for line in output.splitlines():
        if "\t" not in line:
            continue
        name, _, ver = line.partition("\t")
        name, ver = name.strip(), ver.strip()
        if name and ver:
            versions[name] = ver
    return versions


def load_lockfile(root: Path, name: str) -> dict | None:
    path = locks_dir(root) / f"{name}.lock.json"
    try:
        doc = _load_json(path)
    except FileNotFoundError:
        return None
    if not isinstance(doc, dict):
        raise EngineError(f"lockfile '{name}': top level is not an object")
    return doc
