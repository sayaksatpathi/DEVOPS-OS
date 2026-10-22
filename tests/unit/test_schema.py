"""Unit tests for the profile/lockfile validators. Stdlib unittest only."""

import unittest

from devos import schema


def _valid_profile():
    return {
        "schemaVersion": "0.1.0",
        "name": "core",
        "description": "essential tools",
        "tools": [{"name": "git", "source": "apt"}],
    }


class TestProfileValidation(unittest.TestCase):
    def test_valid_profile_has_no_errors(self):
        self.assertEqual(schema.validate_profile(_valid_profile()), [])

    def test_non_object_rejected(self):
        self.assertTrue(schema.validate_profile(["not", "an", "object"]))

    def test_unsupported_schema_version(self):
        p = _valid_profile()
        p["schemaVersion"] = "9.9.9"
        errs = schema.validate_profile(p)
        self.assertTrue(any("schemaVersion" in e for e in errs))

    def test_bad_name_not_kebab(self):
        p = _valid_profile()
        p["name"] = "Core Profile"
        errs = schema.validate_profile(p)
        self.assertTrue(any("kebab-case" in e for e in errs))

    def test_empty_tools_rejected(self):
        p = _valid_profile()
        p["tools"] = []
        self.assertTrue(schema.validate_profile(p))

    def test_unknown_top_level_field_rejected(self):
        p = _valid_profile()
        p["surprise"] = True
        errs = schema.validate_profile(p)
        self.assertTrue(any("unknown top-level field" in e for e in errs))

    def test_dollar_prefixed_field_allowed(self):
        p = _valid_profile()
        p["$comment"] = "fine"
        self.assertEqual(schema.validate_profile(p), [])

    def test_duplicate_tool_rejected(self):
        p = _valid_profile()
        p["tools"] = [{"name": "git", "source": "apt"},
                      {"name": "git", "source": "apt"}]
        errs = schema.validate_profile(p)
        self.assertTrue(any("duplicate" in e for e in errs))

    def test_bad_source_rejected(self):
        p = _valid_profile()
        p["tools"] = [{"name": "git", "source": "wget-from-somewhere"}]
        errs = schema.validate_profile(p)
        self.assertTrue(any("source" in e for e in errs))

    def test_binary_without_verification_rejected(self):
        p = _valid_profile()
        p["tools"] = [{"name": "opentofu", "source": "binary"}]
        errs = schema.validate_profile(p)
        self.assertTrue(any("verification" in e for e in errs))

    def test_binary_with_signature_and_checksum_ok(self):
        p = _valid_profile()
        p["tools"] = [{
            "name": "opentofu", "source": "binary",
            "verification": {"method": "upstream-signature", "checksum": "sha256:abc"},
        }]
        self.assertEqual(schema.validate_profile(p), [])

    def test_fallback_requires_explicit_approval_and_risk(self):
        p = _valid_profile()
        p["tools"] = [{
            "name": "sometool", "source": "binary",
            "verification": {"method": "fallback", "checksum": "sha256:abc"},
        }]
        errs = schema.validate_profile(p)
        self.assertTrue(any("fallbackApproved" in e for e in errs))
        self.assertTrue(any("residualRisk" in e for e in errs))


class TestLockfileValidation(unittest.TestCase):
    def test_locked_tool_must_pin_version(self):
        lock = {
            "lockfileVersion": "0.1.0",
            "profile": "core",
            "profileRevision": "0.1.0",
            "tools": [{"name": "git"}],  # no version
        }
        errs = schema.validate_lockfile(lock)
        self.assertTrue(any("version" in e for e in errs))

    def test_valid_lockfile(self):
        lock = {
            "lockfileVersion": "0.1.0",
            "profile": "core",
            "profileRevision": "0.1.0",
            "tools": [{"name": "git", "version": "1:2.0"}],
        }
        self.assertEqual(schema.validate_lockfile(lock), [])


if __name__ == "__main__":
    unittest.main()
