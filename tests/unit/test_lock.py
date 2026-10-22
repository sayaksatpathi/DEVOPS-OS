"""Unit tests for the lockfile resolver's pure logic (no dpkg needed)."""

import unittest

from devos import cli, engine, schema


class TestParseDpkgQuery(unittest.TestCase):
    def test_parses_tab_separated(self):
        out = "git\t1:2.53.0-1ubuntu1\njq\t1.8.1-4ubuntu2\n"
        self.assertEqual(
            engine.parse_dpkg_query(out),
            {"git": "1:2.53.0-1ubuntu1", "jq": "1.8.1-4ubuntu2"},
        )

    def test_ignores_non_tab_lines(self):
        out = "no packages found matching foo\ngit\t1:2.53.0-1ubuntu1\n"
        self.assertEqual(engine.parse_dpkg_query(out), {"git": "1:2.53.0-1ubuntu1"})

    def test_empty(self):
        self.assertEqual(engine.parse_dpkg_query(""), {})


class TestBuildLockfile(unittest.TestCase):
    def test_resolved_lockfile_is_schema_valid(self):
        lock = cli.build_lockfile(
            "core", "0.1.0", ["git", "jq"],
            {"git": "1:2.53.0-1ubuntu1", "jq": "1.8.1-4ubuntu2"},
            "ubuntu 26.04.1 LTS",
        )
        self.assertEqual(schema.validate_lockfile(lock), [])
        self.assertEqual(lock["tools"][0]["version"], "1:2.53.0-1ubuntu1")
        self.assertEqual(lock["profile"], "core")

    def test_unresolved_marked_but_still_structurally_present(self):
        lock = cli.build_lockfile(
            "core", "0.1.0", ["git", "ghost"],
            {"git": "1:2.53.0-1ubuntu1"}, None,
        )
        ghost = next(t for t in lock["tools"] if t["name"] == "ghost")
        self.assertEqual(ghost["version"], "UNRESOLVED")
        self.assertEqual(ghost["verification"]["result"], "unresolved")

    def test_order_follows_packages_argument(self):
        lock = cli.build_lockfile(
            "core", "0.1.0", ["curl", "git"],
            {"git": "x", "curl": "y"}, None,
        )
        self.assertEqual([t["name"] for t in lock["tools"]], ["curl", "git"])


if __name__ == "__main__":
    unittest.main()


class TestRollbackPinning(unittest.TestCase):
    def test_pinned_packages_skip_unresolved(self):
        lock = {"tools": [
            {"name": "git", "source": "apt", "version": "1:2.53.0-1ubuntu1"},
            {"name": "jq", "source": "apt", "version": "UNRESOLVED"},
            {"name": "tofu", "source": "binary", "version": "1.13.2"},
        ]}
        self.assertEqual(cli.pinned_packages_from_lock(lock), ["git=1:2.53.0-1ubuntu1"])
