"""Pure-Python validators for DevOS profiles and lockfiles.

Dependency-free on purpose (no jsonschema/pyyaml): the engine must validate
and run in a minimal environment and inside a builder VM without network.

Each validator returns a list of human-readable error strings. An empty list
means the document is valid. Validators never raise on bad *content* (they
report); they raise only on a programming error (e.g. non-dict input).
"""

from __future__ import annotations

import re
from typing import Any

from . import SUPPORTED_SCHEMA_VERSIONS

_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_SOURCES = {"apt", "snap", "binary"}
ALLOWED_VERIFICATION_METHODS = {"upstream-signature", "attestation", "fallback"}


def _is_str(v: Any) -> bool:
    return isinstance(v, str) and v != ""


def validate_profile(doc: Any) -> list[str]:
    """Validate a profile document. Returns a list of error strings."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["profile: expected a JSON object at the top level"]

    allowed_top = {"schemaVersion", "name", "description", "tools"}
    for key in doc:
        if key not in allowed_top and not key.startswith("$"):
            errors.append(f"profile: unknown top-level field '{key}'")

    sv = doc.get("schemaVersion")
    if not _is_str(sv):
        errors.append("profile.schemaVersion: required non-empty string")
    elif sv not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"profile.schemaVersion: '{sv}' is not supported "
            f"(supported: {', '.join(SUPPORTED_SCHEMA_VERSIONS)})"
        )

    name = doc.get("name")
    if not _is_str(name):
        errors.append("profile.name: required non-empty string")
    elif not _KEBAB.match(name):
        errors.append(f"profile.name: '{name}' must be kebab-case (e.g. 'core')")

    if not _is_str(doc.get("description")):
        errors.append("profile.description: required non-empty string")

    tools = doc.get("tools")
    if not isinstance(tools, list) or len(tools) == 0:
        errors.append("profile.tools: required non-empty array")
    else:
        seen: set[str] = set()
        for i, tool in enumerate(tools):
            errors.extend(_validate_tool(tool, i, seen))
    return errors


def _validate_tool(tool: Any, i: int, seen: set[str]) -> list[str]:
    errs: list[str] = []
    where = f"profile.tools[{i}]"
    if not isinstance(tool, dict):
        return [f"{where}: expected an object"]

    name = tool.get("name")
    if not _is_str(name):
        errs.append(f"{where}.name: required non-empty string")
    else:
        if name in seen:
            errs.append(f"{where}.name: duplicate tool '{name}'")
        seen.add(name)

    source = tool.get("source")
    if not _is_str(source):
        errs.append(f"{where}.source: required non-empty string")
    elif source not in ALLOWED_SOURCES:
        errs.append(
            f"{where}.source: '{source}' invalid (allowed: {', '.join(sorted(ALLOWED_SOURCES))})"
        )

    # Binary artifacts must carry independently-authenticated verification.
    if source == "binary":
        errs.extend(_validate_binary_verification(tool.get("verification"), where))
    return errs


def _validate_binary_verification(ver: Any, where: str) -> list[str]:
    errs: list[str] = []
    if not isinstance(ver, dict):
        return [f"{where}.verification: required object when source == 'binary'"]
    method = ver.get("method")
    if method not in ALLOWED_VERIFICATION_METHODS:
        errs.append(
            f"{where}.verification.method: must be one of "
            f"{', '.join(sorted(ALLOWED_VERIFICATION_METHODS))}"
        )
    if not _is_str(ver.get("checksum")):
        errs.append(f"{where}.verification.checksum: required non-empty string")
    # A pure checksum from the same download page is trust-on-first-use and is
    # rejected unless an explicit, documented fallback is approved (prompt §9.1).
    if method == "fallback":
        if ver.get("fallbackApproved") is not True:
            errs.append(
                f"{where}.verification: method 'fallback' requires fallbackApproved=true "
                "(no silent trust-on-first-use)"
            )
        if not _is_str(ver.get("residualRisk")):
            errs.append(
                f"{where}.verification.residualRisk: required text when method == 'fallback'"
            )
    return errs


def validate_lockfile(doc: Any) -> list[str]:
    """Validate a lockfile document. Returns a list of error strings."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["lockfile: expected a JSON object at the top level"]
    for field in ("lockfileVersion", "profile", "profileRevision"):
        if not _is_str(doc.get(field)):
            errors.append(f"lockfile.{field}: required non-empty string")
    tools = doc.get("tools")
    if not isinstance(tools, list) or len(tools) == 0:
        errors.append("lockfile.tools: required non-empty array")
    else:
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                errors.append(f"lockfile.tools[{i}]: expected an object")
                continue
            if not _is_str(tool.get("name")):
                errors.append(f"lockfile.tools[{i}].name: required non-empty string")
            if not _is_str(tool.get("version")):
                errors.append(
                    f"lockfile.tools[{i}].version: required non-empty string "
                    "(every locked tool must pin a version)"
                )
    return errors
