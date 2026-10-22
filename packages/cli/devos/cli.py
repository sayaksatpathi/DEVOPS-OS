"""The ``devos`` command-line interface (provisional, pre-Alpha).

Only commands with real, tested contracts are exposed. Provisioning commands
(``profile apply``/``install``/``remove``/``upgrade``, ``drift check``) are
deliberately NOT present yet: they require a target system and are tracked as
planned rather than shipped as empty stubs.

Exit codes:
  0  success / valid
  1  validation failure (one or more documents invalid)
  2  usage error (argparse)
  3  requested profile/resource not found
  4  engine/config error
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from . import engine
from . import schema

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_ENGINE = 4
EXIT_PROVISION = 5  # provisioning run failed


def _root() -> Path:
    return engine.find_root()


def cmd_doctor(_args: argparse.Namespace) -> int:
    """Report environment facts relevant to running the engine. Never mutates."""
    checks: list[tuple[str, bool, str]] = []

    py_ok = sys.version_info >= (3, 11)
    checks.append(("python >= 3.11", py_ok, platform.python_version()))

    is_linux = platform.system() == "Linux"
    checks.append((
        "host is Linux (needed for OS build/boot work)",
        is_linux,
        platform.system(),
    ))

    try:
        root = _root()
        checks.append(("repository root located", True, str(root)))
        n = len(engine.list_profiles(root))
        checks.append(("profiles discovered", n > 0, f"{n} profile(s)"))
    except engine.EngineError as e:
        checks.append(("repository root located", False, str(e)))

    print("devos doctor")
    all_ok = True
    for label, ok, detail in checks:
        mark = "ok  " if ok else "WARN"
        if not ok:
            all_ok = False
        print(f"  [{mark}] {label}: {detail}")

    if not is_linux:
        print(
            "\n  note: OS image build/boot/install is unsupported on this host; "
            "that work must run inside a disposable Linux VM. The engine itself "
            "(profiles, validation) runs fine here."
        )
    return EXIT_OK if all_ok else EXIT_VALIDATION


def cmd_profile_list(_args: argparse.Namespace) -> int:
    root = _root()
    names = engine.list_profiles(root)
    if not names:
        print("no profiles found")
        return EXIT_OK
    for n in names:
        doc = engine.load_profile(root, n)
        desc = doc.get("description", "")
        print(f"{n:16} {desc}")
    return EXIT_OK


def cmd_profile_inspect(args: argparse.Namespace) -> int:
    root = _root()
    try:
        doc = engine.load_profile(root, args.name)
    except engine.EngineError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_NOT_FOUND
    print(json.dumps(doc, indent=2))
    return EXIT_OK


def cmd_profile_validate(args: argparse.Namespace) -> int:
    root = _root()
    if args.all:
        names = engine.list_profiles(root)
        if not names:
            print("no profiles to validate")
            return EXIT_OK
    else:
        names = [args.name]

    failures = 0
    for name in names:
        try:
            doc = engine.load_profile(root, name)
        except engine.EngineError as e:
            print(f"{name}: NOT FOUND ({e})", file=sys.stderr)
            return EXIT_NOT_FOUND
        errors = schema.validate_profile(doc)
        if errors:
            failures += 1
            print(f"{name}: INVALID")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"{name}: valid")
    return EXIT_VALIDATION if failures else EXIT_OK


def build_apply_command(
    root: Path, profile_name: str, packages: list[str], *, check: bool,
    ask_become_pass: bool = False,
) -> tuple[list[str], Path, dict[str, str]]:
    """Build the (argv, cwd, env-overrides) for an ansible apply.

    Pure + unit-testable. Dry-run (check=True) adds ``--check`` so Ansible makes
    no changes. Roles path and safety settings are passed via environment rather
    than ansible.cfg, because a repo on a Windows mount (/mnt/*) is world-writable
    and Ansible will security-ignore an ansible.cfg found there.
    """
    extra_vars = json.dumps({"devos_core_apt_packages": packages})
    cmd = [
        "ansible-playbook", f"playbooks/{profile_name}.yml",
        "-i", "localhost,", "-c", "local",
        "-e", extra_vars,
    ]
    if check:
        cmd.append("--check")
    if ask_become_pass:
        cmd.append("--ask-become-pass")
    ansible_dir = engine.ansible_dir(root)
    env = {
        "ANSIBLE_ROLES_PATH": str(ansible_dir / "roles"),
        "ANSIBLE_HOST_KEY_CHECKING": "False",
        "ANSIBLE_RETRY_FILES_ENABLED": "False",
    }
    return cmd, ansible_dir, env


def cmd_profile_apply(args: argparse.Namespace) -> int:
    root = _root()
    try:
        profile = engine.load_profile(root, args.name)
    except engine.EngineError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_NOT_FOUND

    errors = schema.validate_profile(profile)
    if errors:
        print(f"{args.name}: INVALID — refusing to apply", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return EXIT_VALIDATION

    packages = engine.apt_packages(profile)
    check = not args.confirm  # dry-run unless explicitly confirmed
    cmd, cwd, env_overrides = build_apply_command(
        root, args.name, packages, check=check, ask_become_pass=args.ask_become_pass
    )

    mode = "DRY RUN (--check): no changes will be made" if check else "APPLY: will modify the system"
    print(f"profile: {args.name}")
    print(f"apt packages: {', '.join(packages) or '(none)'}")
    print(f"mode: {mode}")
    print(f"$ (cd {cwd}) {' '.join(cmd)}")

    if shutil.which("ansible-playbook") is None:
        print(
            "\nerror: ansible-playbook not found. Install ansible-core first, e.g.:\n"
            "  sudo apt install -y pipx && pipx install 'ansible-core'\n"
            "(pin the exact version per provision/ansible/requirements.yml before freezing).",
            file=sys.stderr,
        )
        return EXIT_ENGINE

    import os
    run_env = {**os.environ, **env_overrides}
    try:
        rc = subprocess.call(cmd, cwd=str(cwd), env=run_env)
    except OSError as e:
        print(f"error: failed to run ansible-playbook: {e}", file=sys.stderr)
        return EXIT_ENGINE
    return EXIT_OK if rc == 0 else EXIT_PROVISION


def build_lockfile(
    profile_name: str, profile_rev: str, packages: list[str],
    versions: dict[str, str], observed_base: str | None,
) -> dict:
    """Assemble a lockfile dict from resolved package versions. Pure."""
    tools = []
    for p in packages:
        v = versions.get(p)
        tools.append({
            "name": p,
            "source": "apt",
            "version": v if v else "UNRESOLVED",
            "verification": {
                "method": "dpkg-installed",
                "result": "resolved-from-running-system" if v else "unresolved",
            },
        })
    return {
        "$comment": "Generated by `devos profile lock` from the RUNNING system via "
                    "dpkg-query. Versions reflect this machine, not a pinned ISO, so "
                    "they are a reproducibility *baseline*, not a provenance guarantee. "
                    "A build-phase resolver must pin against the signed base image.",
        "lockfileVersion": "0.1.0",
        "profile": profile_name,
        "profileRevision": profile_rev,
        "generatedBy": "devos profile lock (dpkg-query)",
        "architecture": "amd64",
        "baseImage": {
            "id": observed_base or "unknown",
            "digest": "UNVERIFIED",
            "note": "observed from the running system; not a pinned artifact",
        },
        "tools": tools,
    }


def _observed_base() -> str | None:
    try:
        text = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("VERSION="):
            return "ubuntu " + line.split("=", 1)[1].strip().strip('"')
    return None


def cmd_profile_lock(args: argparse.Namespace) -> int:
    root = _root()
    try:
        profile = engine.load_profile(root, args.name)
    except engine.EngineError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_NOT_FOUND

    errors = schema.validate_profile(profile)
    if errors:
        print(f"{args.name}: INVALID — refusing to lock", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return EXIT_VALIDATION

    packages = engine.apt_packages(profile)
    if shutil.which("dpkg-query") is None:
        print("error: dpkg-query not found; run `devos profile lock` on the target "
              "Ubuntu system (e.g. inside WSL), not on Windows.", file=sys.stderr)
        return EXIT_ENGINE

    try:
        out = subprocess.run(
            ["dpkg-query", "-W", *packages],
            capture_output=True, text=True, check=False,
        ).stdout
    except OSError as e:
        print(f"error: failed to run dpkg-query: {e}", file=sys.stderr)
        return EXIT_ENGINE

    versions = engine.parse_dpkg_query(out)
    lock = build_lockfile(args.name, profile.get("revision", "0.1.0"),
                          packages, versions, _observed_base())

    lock_errors = schema.validate_lockfile(lock)
    if lock_errors:
        print(f"{args.name}: generated lockfile is INVALID", file=sys.stderr)
        for err in lock_errors:
            print(f"  - {err}", file=sys.stderr)
        return EXIT_VALIDATION

    path = engine.locks_dir(root) / f"{args.name}.lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")

    resolved = sum(1 for t in lock["tools"] if t["version"] != "UNRESOLVED")
    total = len(lock["tools"])
    print(f"wrote {path}  ({resolved}/{total} resolved)")
    for t in lock["tools"]:
        print(f"  {t['name']:20} {t['version']}")
    return EXIT_OK if resolved == total else EXIT_VALIDATION


def cmd_tools_list(args: argparse.Namespace) -> int:
    root = _root()
    name = args.profile
    lock = engine.load_lockfile(root, name)
    if lock is None:
        print(
            f"no lockfile for profile '{name}' (expected locks/{name}.lock.json); "
            "showing declared tools from the profile instead"
        )
        try:
            doc = engine.load_profile(root, name)
        except engine.EngineError as e:
            print(f"error: {e}", file=sys.stderr)
            return EXIT_NOT_FOUND
        for t in doc.get("tools", []):
            print(f"  {t.get('name','?'):20} (declared; source={t.get('source','?')})")
        return EXIT_OK

    for t in lock.get("tools", []):
        print(f"  {t.get('name','?'):20} {t.get('version','?'):16} "
              f"[{t.get('verification', {}).get('result', '?')}]")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="devos",
        description="DevOS reproducibility engine (pre-Alpha). Unprivileged; "
                    "performs no system changes.",
    )
    p.add_argument("--version", action="version", version=f"devos {__version__}")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("doctor", help="report environment facts (no changes)").set_defaults(
        func=cmd_doctor
    )

    pf = sub.add_parser("profile", help="inspect and validate profiles")
    pfsub = pf.add_subparsers(dest="subcommand")
    pfsub.add_parser("list", help="list available profiles").set_defaults(
        func=cmd_profile_list
    )
    insp = pfsub.add_parser("inspect", help="print a profile as JSON")
    insp.add_argument("name")
    insp.set_defaults(func=cmd_profile_inspect)
    valp = pfsub.add_parser("validate", help="validate profile(s) against the schema")
    valp.add_argument("name", nargs="?", help="profile name (omit with --all)")
    valp.add_argument("--all", action="store_true", help="validate every profile")
    valp.set_defaults(func=cmd_profile_validate)

    app = pfsub.add_parser(
        "apply", help="apply a profile via Ansible (dry-run unless --confirm)"
    )
    app.add_argument("name")
    app.add_argument("--confirm", action="store_true",
                     help="actually make changes (default is a --check dry run)")
    app.add_argument("--ask-become-pass", action="store_true",
                     help="prompt for the sudo/become password")
    app.set_defaults(func=cmd_profile_apply)

    lck = pfsub.add_parser(
        "lock", help="resolve installed versions into locks/<name>.lock.json (run on target)"
    )
    lck.add_argument("name")
    lck.set_defaults(func=cmd_profile_lock)

    pt = sub.add_parser("tools", help="inspect managed tools")
    ptsub = pt.add_subparsers(dest="subcommand")
    tl = ptsub.add_parser("list", help="list locked (or declared) tools for a profile")
    tl.add_argument("--profile", default="core", help="profile name (default: core)")
    tl.set_defaults(func=cmd_tools_list)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Bare `devos`, `devos profile`, `devos tools` -> show help, exit 0.
    if getattr(args, "func", None) is None:
        parser.parse_args((argv or []) + ["--help"]) if False else None
        parser.print_help()
        return EXIT_OK

    # Validate subcommand required a name unless --all was given.
    if args.func is cmd_profile_validate and not args.all and not args.name:
        parser.error("profile validate: provide a profile name or --all")

    try:
        return args.func(args)
    except engine.EngineError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_ENGINE


if __name__ == "__main__":
    raise SystemExit(main())
