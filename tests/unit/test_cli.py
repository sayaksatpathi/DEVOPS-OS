"""Unit tests for the devos CLI: real exit codes against the shipped profiles."""

import io
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from devos import cli

REPO_ROOT = Path(__file__).resolve().parents[2]


def run(argv):
    """Run the CLI with the repo as DEVOS_ROOT; return (exit_code, stdout)."""
    os.environ["DEVOS_ROOT"] = str(REPO_ROOT)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue() + err.getvalue()


class TestCli(unittest.TestCase):
    def test_bare_invocation_shows_help_exit_0(self):
        code, text = run([])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("usage", text.lower())

    def test_profile_list_includes_core(self):
        code, text = run(["profile", "list"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("core", text)

    def test_profile_inspect_core(self):
        code, text = run(["profile", "inspect", "core"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn('"name": "core"', text)

    def test_profile_inspect_missing_is_not_found(self):
        code, _ = run(["profile", "inspect", "does-not-exist"])
        self.assertEqual(code, cli.EXIT_NOT_FOUND)

    def test_validate_all_passes_on_shipped_profiles(self):
        code, text = run(["profile", "validate", "--all"])
        self.assertEqual(code, cli.EXIT_OK, msg=text)
        self.assertIn("core: valid", text)

    def test_validate_missing_profile_not_found(self):
        code, _ = run(["profile", "validate", "nope"])
        self.assertEqual(code, cli.EXIT_NOT_FOUND)

    def test_tools_list_core_reads_lockfile(self):
        code, text = run(["tools", "list", "--profile", "core"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("git", text)

    def test_doctor_runs(self):
        code, text = run(["doctor"])
        # On a non-Linux host doctor returns EXIT_VALIDATION (a warning), which
        # is expected and correct; either way it must produce its report.
        self.assertIn("devos doctor", text)
        self.assertIn(code, (cli.EXIT_OK, cli.EXIT_VALIDATION))


if __name__ == "__main__":
    unittest.main()
