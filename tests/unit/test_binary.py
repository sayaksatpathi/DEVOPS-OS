"""Unit tests for binary-tool gating and install-command construction."""

import unittest
from pathlib import Path

from devos import cli, engine

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestGateBinaryTools(unittest.TestCase):
    def test_signed_tool_allowed_and_spec_built(self):
        profile = {
            "tools": [
                {"name": "git", "source": "apt"},
                {"name": "opentofu", "source": "binary", "version": "1.13.2",
                 "url": "https://example/tofu.zip",
                 "install": {"kind": "zip", "binIn": "tofu", "binOut": "tofu"},
                 "verification": {"method": "upstream-signature", "checksum": "sha256:abc",
                                  "sumsUrl": "u", "sigUrl": "u", "certUrl": "u",
                                  "certIdentityRegexp": "r", "certOidcIssuer": "i"}},
            ]
        }
        allowed, skipped = cli.gate_binary_tools(profile)
        self.assertEqual(len(allowed), 1)
        self.assertEqual(skipped, [])
        spec = allowed[0]
        self.assertEqual(spec["name"], "opentofu")
        self.assertEqual(spec["kind"], "zip")
        self.assertEqual(spec["checksum"], "sha256:abc")
        self.assertEqual(spec["binOut"], "tofu")

    def test_unverified_tool_skipped_not_installed(self):
        profile = {"tools": [
            {"name": "sketchy", "source": "binary",
             "verification": {"checksum": "sha256:abc"}},  # no method → TOFU, rejected
        ]}
        allowed, skipped = cli.gate_binary_tools(profile)
        self.assertEqual(allowed, [])
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0][0], "sketchy")

    def test_real_infra_profile_opentofu_allowed(self):
        profile = engine.load_profile(REPO_ROOT, "infra")
        allowed, skipped = cli.gate_binary_tools(profile)
        self.assertEqual(skipped, [])
        self.assertEqual(allowed[0]["name"], "opentofu")
        self.assertTrue(allowed[0]["url"].startswith("https://github.com/opentofu/"))


class TestBuildBinaryCommand(unittest.TestCase):
    def test_check_flag_and_extra_vars(self):
        specs = [{"name": "opentofu", "version": "1.13.2", "url": "u",
                  "checksum": "sha256:abc", "kind": "zip", "binIn": "tofu", "binOut": "tofu"}]
        cmd, _cwd, _env = cli.build_binary_command(REPO_ROOT, "infra", specs, check=True)
        self.assertIn("playbooks/binary.yml", cmd)
        self.assertIn("--check", cmd)
        self.assertIn("devos_binary_specs", " ".join(cmd))


if __name__ == "__main__":
    unittest.main()
