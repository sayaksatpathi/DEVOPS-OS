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
from . import verify

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_ENGINE = 4
EXIT_PROVISION = 5  # provisioning run failed


def _root() -> Path:
    return engine.find_root()


def _as_name(args: argparse.Namespace) -> argparse.Namespace:
    """Adapt commands that take --profile to the shared handlers that read .name."""
    args.name = args.profile
    return args


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
    state: str = "present", ask_become_pass: bool = False,
) -> tuple[list[str], Path, dict[str, str]]:
    """Build the (argv, cwd, env-overrides) for an ansible apply/remove.

    Pure + unit-testable. Dry-run (check=True) adds ``--check`` so Ansible makes
    no changes. ``state`` is 'present' (install) or 'absent' (remove). Roles path
    and safety settings are passed via environment rather than ansible.cfg, because
    a repo on a Windows mount (/mnt/*) is world-writable and Ansible will
    security-ignore an ansible.cfg found there.
    """
    extra_vars = json.dumps({
        "devos_profile": profile_name,
        "devos_apt_packages": packages,
        "devos_apt_state": state,
    })
    cmd = [
        "ansible-playbook", "playbooks/apply.yml",
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


def _run_profile_ansible(root: Path, name: str, packages: list[str], *,
                         state: str, check: bool, ask_become_pass: bool,
                         verb: str) -> int:
    changing = "APPLY" if state == "present" else "REMOVE"
    mode = (f"DRY RUN (--check): no changes will be made"
            if check else f"{changing}: will modify the system")
    print(f"profile: {name}")
    print(f"apt packages ({state}): {', '.join(packages) or '(none)'}")
    print(f"mode: {mode}")
    cmd, cwd, env_overrides = build_apply_command(
        root, name, packages, check=check, state=state, ask_become_pass=ask_become_pass
    )
    print(f"$ (cd {cwd}) {' '.join(cmd)}")
    if shutil.which("ansible-playbook") is None:
        print("\nerror: ansible-playbook not found. Install it on the target, e.g. "
              "`sudo apt install -y ansible-core`.", file=sys.stderr)
        return EXIT_ENGINE
    import os
    run_env = {**os.environ, **env_overrides}
    try:
        rc = subprocess.call(cmd, cwd=str(cwd), env=run_env)
    except OSError as e:
        print(f"error: failed to run ansible-playbook: {e}", file=sys.stderr)
        return EXIT_ENGINE
    return EXIT_OK if rc == 0 else EXIT_PROVISION


def _load_valid_profile(root: Path, name: str, action: str):
    """Return (profile, None) or (None, exit_code) if missing/invalid."""
    try:
        profile = engine.load_profile(root, name)
    except engine.EngineError as e:
        print(f"error: {e}", file=sys.stderr)
        return None, EXIT_NOT_FOUND
    errors = schema.validate_profile(profile)
    if errors:
        print(f"{name}: INVALID — refusing to {action}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return None, EXIT_VALIDATION
    return profile, None


def gate_binary_tools(profile: dict) -> tuple[list[dict], list[tuple[str, str]]]:
    """Split binary tools into (allowed specs, [(name, reason) skipped]).

    A tool is allowed only if its verification block passes the §9.1 policy gate
    (signature/attestation, or an explicitly approved fallback). Allowed tools are
    turned into install specs for the devos_binary role.
    """
    allowed: list[dict] = []
    skipped: list[tuple[str, str]] = []
    for t in engine.binary_tools(profile):
        name = t.get("name", "?")
        ok, reason = verify.install_allowed(t.get("verification"))
        if not ok:
            skipped.append((name, reason))
            continue
        inst = t.get("install", {})
        ver = t.get("verification", {})
        allowed.append({
            "name": name,
            "version": t.get("version", ""),
            "url": t.get("url", ""),
            "checksum": ver.get("checksum", ""),
            "kind": inst.get("kind", "raw"),
            "binIn": inst.get("binIn", name),
            "binOut": inst.get("binOut", name),
            # cosign signature-verification material (real verification, not a label)
            "sumsUrl": ver.get("sumsUrl", ""),
            "sigUrl": ver.get("sigUrl", ""),
            "certUrl": ver.get("certUrl", ""),
            "certIdentityRegexp": ver.get("certIdentityRegexp", ""),
            "certOidcIssuer": ver.get("certOidcIssuer", ""),
            "sumEntry": ver.get("sumEntry", ""),
        })
    return allowed, skipped


def build_binary_command(
    root: Path, profile_name: str, specs: list[dict], *, check: bool,
    ask_become_pass: bool = False,
) -> tuple[list[str], Path, dict[str, str]]:
    """Build the (argv, cwd, env) for the verified-binary install playbook. Pure."""
    extra_vars = json.dumps({"devos_profile": profile_name, "devos_binary_specs": specs})
    cmd = ["ansible-playbook", "playbooks/binary.yml",
           "-i", "localhost,", "-c", "local", "-e", extra_vars]
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
    profile, err = _load_valid_profile(root, args.name, "apply")
    if err is not None:
        return err

    # 1) apt-sourced tools — pin to the lockfile when available (reproducible).
    apt_list, pinned = engine.apt_packages_enforced(root, args.name, profile)
    if apt_list:
        print(f"apt version pinning: {'ENFORCED from lockfile' if pinned else 'NOT pinned (no lockfile; installs latest)'}")
    rc = _run_profile_ansible(
        root, args.name, apt_list,
        state="present", check=not args.confirm,
        ask_become_pass=args.ask_become_pass, verb="apply",
    ) if apt_list else EXIT_OK
    if rc not in (EXIT_OK,):
        return rc

    # 2) verified binary tools (gate first — refuse trust-on-first-use)
    allowed, skipped = gate_binary_tools(profile)
    for name, reason in skipped:
        print(f"skip binary '{name}': {reason}")
    if not allowed:
        return rc
    names = ', '.join(s['name'] + ' ' + s['version'] for s in allowed)
    if not args.confirm:
        # Download+extract can't be meaningfully simulated in Ansible check mode; report intent.
        print(f"binary tools (dry-run, verified, would install): {names}")
        print("  run with --confirm to download (checksum-verified) and install to /usr/local/bin")
        return rc
    print(f"binary tools (install, verified): {names}")
    cmd, cwd, env = build_binary_command(
        root, args.name, allowed, check=False, ask_become_pass=args.ask_become_pass)
    print(f"$ (cd {cwd}) {' '.join(cmd[:6])} …")
    if shutil.which("ansible-playbook") is None:
        print("error: ansible-playbook not found (install ansible-core on the target).",
              file=sys.stderr)
        return EXIT_ENGINE
    import os
    try:
        brc = subprocess.call(cmd, cwd=str(cwd), env={**os.environ, **env})
    except OSError as e:
        print(f"error: failed to run ansible-playbook: {e}", file=sys.stderr)
        return EXIT_ENGINE
    return EXIT_OK if brc == 0 else EXIT_PROVISION


def cmd_profile_remove(args: argparse.Namespace) -> int:
    root = _root()
    profile, err = _load_valid_profile(root, args.name, "remove")
    if err is not None:
        return err
    # Preserve user data: remove only this profile's apt packages, never autoremove/purge.
    return _run_profile_ansible(
        root, args.name, engine.apt_packages(profile),
        state="absent", check=not args.confirm,
        ask_become_pass=args.ask_become_pass, verb="remove",
    )


def pinned_packages_from_lock(lock: dict) -> list[str]:
    """Build apt 'name=version' specs from a lockfile, skipping unresolved versions."""
    out: list[str] = []
    for t in lock.get("tools", []):
        if not isinstance(t, dict) or t.get("source") != "apt":
            continue
        name, ver = t.get("name"), t.get("version")
        if name and ver and ver not in ("PLACEHOLDER", "UNRESOLVED"):
            out.append(f"{name}={ver}")
    return out


def cmd_profile_rollback(args: argparse.Namespace) -> int:
    """Reinstall the exact versions recorded in a lockfile (profile/tool rollback).

    Honest scope: this rolls back apt-managed tool *versions* where those versions are
    still available in the archive; it is NOT atomic full-system rollback (ext4).
    """
    root = _root()
    lock_path = Path(args.to) if args.to else engine.locks_dir(root) / f"{args.name}.lock.json"
    lock = engine.load_lockfile(root, args.name) if not args.to else None
    if args.to:
        try:
            import json as _j
            lock = _j.loads(lock_path.read_text(encoding="utf-8"))
        except OSError as e:
            print(f"error: cannot read lockfile {lock_path}: {e}", file=sys.stderr)
            return EXIT_NOT_FOUND
    if lock is None:
        print(f"error: no lockfile for '{args.name}' at {lock_path}", file=sys.stderr)
        return EXIT_NOT_FOUND
    pkgs = pinned_packages_from_lock(lock)
    if not pkgs:
        print("no resolved pinned versions in lockfile; run `devos profile lock` on the target first")
        return EXIT_VALIDATION
    return _run_profile_ansible(
        root, args.name, pkgs, state="present", check=not args.confirm,
        ask_become_pass=args.ask_become_pass, verb="rollback",
    )


def cmd_drift_check(args: argparse.Namespace) -> int:
    """Compare declared profile packages against what is installed. Never changes state."""
    root = _root()
    profile, err = _load_valid_profile(root, args.name, "drift check")
    if err is not None:
        return err
    packages = engine.apt_packages(profile)
    if shutil.which("dpkg-query") is None:
        print("error: dpkg-query not found; run `devos drift check` on the target system.",
              file=sys.stderr)
        return EXIT_ENGINE
    out = subprocess.run(["dpkg-query", "-W", *packages],
                         capture_output=True, text=True, check=False).stdout
    installed = engine.parse_dpkg_query(out)
    missing = [p for p in packages if p not in installed]
    print(f"drift check: profile '{args.name}' ({len(packages)} declared apt tools)")
    for p in packages:
        state = installed.get(p)
        print(f"  {p:20} {'installed ' + state if state else 'MISSING'}")
    if missing:
        print(f"\ndrift detected: {len(missing)} missing — run "
              f"`devos profile apply {args.name} --confirm` to converge (no auto-correction).")
        return EXIT_VALIDATION
    print("\nno drift: all declared tools are installed.")
    return EXIT_OK


def cmd_update_check(args: argparse.Namespace) -> int:
    """Report available apt updates. Read-only (simulated). --system covers the whole OS."""
    root = _root()
    if shutil.which("apt-get") is None:
        print("error: apt-get not found; run `devos update` on the target system.",
              file=sys.stderr)
        return EXIT_ENGINE

    if getattr(args, "system", False):
        # Whole-OS update preview: kernel, base, security — read-only simulation.
        sim = subprocess.run(["apt-get", "-s", "dist-upgrade"],
                             capture_output=True, text=True, check=False).stdout
        upgrades = [ln for ln in sim.splitlines() if ln.startswith("Inst ")]
        print("system update check (simulated; no changes)")
        if not upgrades:
            print("  system is up to date.")
            return EXIT_OK
        kernel = [u for u in upgrades if "linux-image" in u or "linux-generic" in u]
        print(f"  {len(upgrades)} package update(s) available"
              + (f", including {len(kernel)} kernel update(s)" if kernel else ""))
        for u in upgrades[:40]:
            print(f"  {u}")
        print("\napply with your OS tooling (apt full-upgrade); DevOS does not auto-upgrade.")
        return EXIT_OK

    profile, err = _load_valid_profile(root, args.name, "update check")
    if err is not None:
        return err
    packages = engine.apt_packages(profile)
    sim = subprocess.run(["apt-get", "-s", "install", *packages],
                         capture_output=True, text=True, check=False).stdout
    upgrades = [ln for ln in sim.splitlines() if ln.startswith("Inst ")]
    print(f"update check: profile '{args.name}' (simulated; no changes)")
    if not upgrades:
        print("  all managed tools are at the latest available version (or already current).")
        return EXIT_OK
    for ln in upgrades:
        print(f"  {ln}")
    print("\nupdates available. Review, then re-lock with `devos profile lock` after applying.")
    return EXIT_OK


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


def cmd_diag(args: argparse.Namespace) -> int:
    """Collect a secret-redacted diagnostic bundle (§6.14). Read-only."""
    import platform, os
    root = _root()
    sections = []
    sections.append(("devos", f"version {__version__}\nroot {root}"))
    sections.append(("system", f"{platform.platform()}\npython {platform.python_version()}"))
    try:
        sections.append(("os-release", Path("/etc/os-release").read_text(encoding="utf-8")))
    except OSError:
        pass
    sections.append(("profiles", "\n".join(engine.list_profiles(root)) or "(none)"))
    for cmd, label in ((["df", "-h"], "disk"), (["free", "-h"], "memory")):
        if shutil.which(cmd[0]):
            try:
                sections.append((label, subprocess.run(cmd, capture_output=True, text=True,
                                                       check=False).stdout))
            except OSError:
                pass
    if shutil.which("journalctl"):
        try:
            jl = subprocess.run(["journalctl", "-b", "-p", "err", "--no-pager", "-n", "50"],
                                capture_output=True, text=True, check=False).stdout
            sections.append(("journal-errors", jl))
        except OSError:
            pass
    bundle = "\n".join(f"===== {name} =====\n{engine.redact_secrets(body)}"
                       for name, body in sections)
    if args.out:
        Path(args.out).write_text(bundle + "\n", encoding="utf-8")
        print(f"wrote redacted diagnostic bundle to {args.out}")
    else:
        print(bundle)
    return EXIT_OK


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

    rmp = pfsub.add_parser(
        "remove", help="remove a profile's apt packages (dry-run unless --confirm; preserves data)"
    )
    rmp.add_argument("name")
    rmp.add_argument("--confirm", action="store_true",
                     help="actually remove (default is a --check dry run)")
    rmp.add_argument("--ask-become-pass", action="store_true",
                     help="prompt for the sudo/become password")
    rmp.set_defaults(func=cmd_profile_remove)

    lck = pfsub.add_parser(
        "lock", help="resolve installed versions into locks/<name>.lock.json (run on target)"
    )
    lck.add_argument("name")
    lck.set_defaults(func=cmd_profile_lock)

    rb = pfsub.add_parser(
        "rollback", help="reinstall the exact versions from a lockfile (dry-run unless --confirm)"
    )
    rb.add_argument("name")
    rb.add_argument("--to", help="lockfile path to roll back to (default: locks/<name>.lock.json)")
    rb.add_argument("--confirm", action="store_true", help="actually install the pinned versions")
    rb.add_argument("--ask-become-pass", action="store_true", help="prompt for sudo password")
    rb.set_defaults(func=cmd_profile_rollback)

    dr = sub.add_parser("drift", help="check declared vs installed state")
    drsub = dr.add_subparsers(dest="subcommand")
    drc = drsub.add_parser("check", help="report missing tools for a profile (no changes)")
    drc.add_argument("--profile", default="core", help="profile name (default: core)")
    drc.set_defaults(func=lambda a: cmd_drift_check(_as_name(a)))

    dg = sub.add_parser("diag", help="collect a secret-redacted diagnostic bundle (read-only)")
    dg.add_argument("--out", help="write the bundle to a file instead of stdout")
    dg.set_defaults(func=cmd_diag)

    upd = sub.add_parser("update", help="check for available updates (read-only)")
    upd.add_argument("--profile", default="core", help="profile name (default: core)")
    upd.add_argument("--check", action="store_true", help="simulate only (default behavior)")
    upd.add_argument("--system", action="store_true",
                     help="check whole-OS updates (kernel/base/security), not just tools")
    upd.set_defaults(func=lambda a: cmd_update_check(_as_name(a)))

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
