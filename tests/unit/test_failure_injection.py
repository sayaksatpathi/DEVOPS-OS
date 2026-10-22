"""Failure-injection tests (engine level) — Alpha-1 criterion #18, testable subset.

These assert that bad inputs and missing prerequisites fail *clearly* (structured
errors, non-zero exit, no false success, no silent install) rather than crashing or
appearing to succeed. VM-level cases from master-prompt §13.3 (interrupted install,
disk-full during provisioning, repo unreachable mid-run, reboot during an operation)
require a disposable VM and are tracked separately in docs/testing-strategy.md.
"""

import io
import os
import random
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from devos import cli, engine, schema, verify

REPO_ROOT = Path(__file__).resolve().parents[2]


def run(argv):
    os.environ["DEVOS_ROOT"] = str(REPO_ROOT)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue() + err.getvalue()


class TestBadProfilesFailClearly(unittest.TestCase):
    def test_unknown_profile_is_not_found_not_crash(self):
        code, _ = run(["profile", "validate", "does-not-exist"])
        self.assertEqual(code, cli.EXIT_NOT_FOUND)

    def test_apply_unknown_profile_not_found(self):
        code, _ = run(["profile", "apply", "ghost"])
        self.assertEqual(code, cli.EXIT_NOT_FOUND)

    def test_malformed_profile_json_raises_engine_error(self, ):
        # engine.load_profile must surface a clear EngineError on broken JSON, not crash.
        import tempfile, json
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "profiles" / "definitions").mkdir(parents=True)
            (root / "profiles" / "definitions" / "broken.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(engine.EngineError):
                engine.load_profile(root, "broken")


class TestSupplyChainFailsClosed(unittest.TestCase):
    def test_binary_without_signature_is_refused_not_installed(self):
        profile = {"tools": [
            {"name": "evil", "source": "binary",
             "verification": {"checksum": "sha256:abc"}},  # checksum only = TOFU
        ]}
        allowed, skipped = cli.gate_binary_tools(profile)
        self.assertEqual(allowed, [], "unverified binary must never be installed")
        self.assertEqual(len(skipped), 1)

    def test_checksum_mismatch_detected(self):
        import tempfile, hashlib
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.bin"
            f.write_bytes(b"real-content")
            self.assertFalse(verify.verify_checksum(f, "sha256:" + "0" * 64))
            self.assertTrue(verify.verify_checksum(
                f, "sha256:" + hashlib.sha256(b"real-content").hexdigest()))

    def test_fallback_without_approval_refused(self):
        ok, _ = verify.install_allowed({"method": "fallback", "checksum": "x"})
        self.assertFalse(ok)


class TestMissingPrereqsFailClearly(unittest.TestCase):
    def test_lock_without_dpkg_is_engine_error(self):
        # On a host without dpkg-query (e.g. Windows), lock must fail with a clear message.
        import shutil
        if shutil.which("dpkg-query") is not None:
            self.skipTest("dpkg-query present; this path is exercised on non-Debian hosts")
        code, text = run(["profile", "lock", "core"])
        self.assertEqual(code, cli.EXIT_ENGINE)
        self.assertIn("dpkg-query", text)

    def test_parse_dpkg_query_tolerates_garbage(self):
        # Malformed resolver output must not crash; just yield what parses.
        self.assertEqual(engine.parse_dpkg_query("garbage\n\n\x00no-tab-here"), {})


class TestMalformedInputFuzz(unittest.TestCase):
    """Validators must never raise on arbitrary input — they report, not crash."""

    def _rand(self, depth=0):
        r = random.random()
        if depth > 4 or r < 0.2:
            return random.choice([None, 0, 1, -1, "", "x", True, 3.14, [], {}])
        if r < 0.5:
            return [self._rand(depth + 1) for _ in range(random.randint(0, 4))]
        if r < 0.8:
            return {random.choice(["name", "tools", "x", "schemaVersion", "source"]):
                    self._rand(depth + 1) for _ in range(random.randint(0, 4))}
        return random.choice(["apt", "binary", "snap", "sha256:z", "0.1.0", "core"])

    def test_validate_profile_never_raises(self):
        random.seed(1234)
        for _ in range(500):
            try:
                errs = schema.validate_profile(self._rand())
                self.assertIsInstance(errs, list)
            except Exception as e:  # noqa: BLE001
                self.fail(f"validate_profile raised on fuzz input: {e!r}")

    def test_validate_lockfile_never_raises(self):
        random.seed(5678)
        for _ in range(500):
            try:
                errs = schema.validate_lockfile(self._rand())
                self.assertIsInstance(errs, list)
            except Exception as e:  # noqa: BLE001
                self.fail(f"validate_lockfile raised on fuzz input: {e!r}")


if __name__ == "__main__":
    unittest.main()
