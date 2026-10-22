"""Unit tests for supply-chain verification (checksum + install policy)."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from devos import verify


class TestChecksum(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "artifact.bin"
        self.path.write_bytes(b"devos-test-artifact")
        self.digest = hashlib.sha256(b"devos-test-artifact").hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def test_sha256_matches(self):
        self.assertEqual(verify.sha256_file(self.path), self.digest)

    def test_verify_checksum_true(self):
        self.assertTrue(verify.verify_checksum(self.path, self.digest))
        self.assertTrue(verify.verify_checksum(self.path, "sha256:" + self.digest))

    def test_verify_checksum_false_on_mismatch(self):
        self.assertFalse(verify.verify_checksum(self.path, "0" * 64))


class TestInstallPolicy(unittest.TestCase):
    def test_signature_label_without_material_is_refused(self):
        # A bare 'upstream-signature' label with no signature material is TOFU — refused.
        ok, reason = verify.install_allowed(
            {"method": "upstream-signature", "checksum": "sha256:abc"})
        self.assertFalse(ok)
        self.assertIn("missing material", reason)

    def test_signature_with_full_material_allowed(self):
        ok, _ = verify.install_allowed({
            "method": "upstream-signature", "checksum": "sha256:abc",
            "sumsUrl": "u", "sigUrl": "u", "certUrl": "u",
            "certIdentityRegexp": "r", "certOidcIssuer": "i",
        })
        self.assertTrue(ok)

    def test_checksum_only_without_method_rejected(self):
        ok, _ = verify.install_allowed({"checksum": "sha256:abc"})
        self.assertFalse(ok)

    def test_no_checksum_rejected(self):
        ok, _ = verify.install_allowed({"method": "upstream-signature"})
        self.assertFalse(ok)

    def test_fallback_requires_approval_and_risk(self):
        ok, _ = verify.install_allowed({"method": "fallback", "checksum": "x"})
        self.assertFalse(ok)
        ok2, _ = verify.install_allowed({
            "method": "fallback", "checksum": "x",
            "fallbackApproved": True, "residualRisk": "no upstream signature published",
        })
        self.assertTrue(ok2)


if __name__ == "__main__":
    unittest.main()
