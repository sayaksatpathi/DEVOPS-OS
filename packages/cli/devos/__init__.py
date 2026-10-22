"""DevOS reproducibility-engine CLI (provisional, pre-Alpha).

This package is the environment-independent core of DevOS: profile/lockfile
loading, validation, and the ``devos`` command surface. It builds and tests on
any host with Python 3.11+ and does NOT build or boot an operating system.

Status: partially implemented. Only the commands with real, tested contracts
are exposed (see cli.py). Provisioning/apply against a live system is NOT
implemented here and is deliberately absent rather than stubbed.
"""

__version__ = "0.1.0"
SUPPORTED_SCHEMA_VERSIONS = ("0.1.0",)
