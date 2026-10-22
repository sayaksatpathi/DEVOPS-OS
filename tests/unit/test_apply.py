"""Unit tests for apply-command construction and package extraction.

These do NOT execute ansible; they verify the pure logic devos uses to build a
safe (dry-run-by-default) provisioning command from a profile.
"""

import unittest
from pathlib import Path

from devos import cli, engine

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestAptPackages(unittest.TestCase):
    def test_only_apt_sourced_tools(self):
        profile = {
            "tools": [
                {"name": "git", "source": "apt"},
                {"name": "opentofu", "source": "binary"},
                {"name": "code", "source": "snap"},
                {"name": "jq", "source": "apt"},
            ]
        }
        self.assertEqual(engine.apt_packages(profile), ["git", "jq"])

    def test_core_profile_packages(self):
        profile = engine.load_profile(REPO_ROOT, "core")
        pkgs = engine.apt_packages(profile)
        self.assertIn("git", pkgs)
        self.assertIn("jq", pkgs)
        self.assertEqual(len(pkgs), len(profile["tools"]))  # core is all-apt


class TestBuildApplyCommand(unittest.TestCase):
    def test_dry_run_adds_check(self):
        cmd, cwd, _env = cli.build_apply_command(
            REPO_ROOT, "core", ["git", "jq"], check=True
        )
        self.assertIn("--check", cmd)
        self.assertEqual(cmd[0], "ansible-playbook")
        self.assertTrue(str(cwd).endswith("provision/ansible")
                        or str(cwd).endswith("provision\\ansible"))

    def test_confirm_omits_check(self):
        cmd, _cwd, _env = cli.build_apply_command(
            REPO_ROOT, "core", ["git"], check=False
        )
        self.assertNotIn("--check", cmd)

    def test_uses_generic_apply_playbook(self):
        cmd, _cwd, _env = cli.build_apply_command(
            REPO_ROOT, "core", ["git"], check=True
        )
        self.assertIn("playbooks/apply.yml", cmd)

    def test_packages_passed_as_extra_vars(self):
        cmd, _cwd, _env = cli.build_apply_command(
            REPO_ROOT, "core", ["git", "jq"], check=True
        )
        joined = " ".join(cmd)
        self.assertIn("devos_apt_packages", joined)
        self.assertIn("devos_apt_state", joined)
        self.assertIn("git", joined)
        self.assertIn("jq", joined)

    def test_state_present_vs_absent(self):
        cmd_i, _, _ = cli.build_apply_command(REPO_ROOT, "core", ["git"], check=True,
                                              state="present")
        cmd_r, _, _ = cli.build_apply_command(REPO_ROOT, "core", ["git"], check=True,
                                              state="absent")
        self.assertIn("present", " ".join(cmd_i))
        self.assertIn("absent", " ".join(cmd_r))

    def test_ask_become_pass_flag(self):
        cmd, _cwd, _env = cli.build_apply_command(
            REPO_ROOT, "core", ["git"], check=True, ask_become_pass=True
        )
        self.assertIn("--ask-become-pass", cmd)

    def test_roles_path_env_points_at_roles_dir(self):
        _cmd, _cwd, env = cli.build_apply_command(
            REPO_ROOT, "core", ["git"], check=True
        )
        self.assertIn("ANSIBLE_ROLES_PATH", env)
        self.assertTrue(env["ANSIBLE_ROLES_PATH"].replace("\\", "/").endswith(
            "provision/ansible/roles"))


if __name__ == "__main__":
    unittest.main()
