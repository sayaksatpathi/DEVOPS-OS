#!/usr/bin/env bash
# VM-level failure-injection suite (master-prompt §13.3, gap #13). Runs on a DISPOSABLE
# Ubuntu (a CI runner or a throwaway VM) — it mutates apt state, so never run on a machine
# you care about. Asserts that each injected failure produces a clear, non-zero failure with
# no false success. Cases that need mid-boot interruption (reboot during op, network loss
# mid-stream) remain out of scope here and are tracked in docs/testing-strategy.md.
set -uo pipefail   # intentionally NOT -e: we expect commands to fail

repo="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$repo"
export PYTHONPATH="$repo/packages/cli"
pass=0; fail=0
ok()   { echo "  PASS: $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL: $1"; fail=$((fail+1)); }

tmproot="$(mktemp -d)"
mkdir -p "$tmproot/profiles/definitions" "$tmproot/provision"
cp -r provision/ansible "$tmproot/provision/"
export DEVOS_ROOT="$tmproot"

echo "== Case 1: required artifact unavailable (nonexistent apt package) =="
cat > "$tmproot/profiles/definitions/badpkg.json" <<'J'
{"schemaVersion":"0.1.0","name":"badpkg","description":"nonexistent package",
 "tools":[{"name":"this-package-does-not-exist-devos-xyz","source":"apt"}]}
J
python3 -m devos profile apply badpkg --confirm > /tmp/c1.log 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then ok "nonexistent package -> apply failed (rc=$rc), no false success"; else bad "apply reported success for a missing package"; fi

echo "== Case 2: invalid checksum on a binary tool (download verification must fail) =="
cat > "$tmproot/profiles/definitions/badbin.json" <<'J'
{"schemaVersion":"0.1.0","name":"badbin","description":"bad checksum binary",
 "tools":[{"name":"opentofu","source":"binary","version":"1.13.2",
   "url":"https://github.com/opentofu/opentofu/releases/download/v1.13.2/tofu_1.13.2_linux_amd64.zip",
   "install":{"kind":"zip","binIn":"tofu","binOut":"tofu"},
   "verification":{"method":"upstream-signature","checksum":"sha256:0000000000000000000000000000000000000000000000000000000000000000"}}]}
J
python3 -m devos profile apply badbin --confirm > /tmp/c2.log 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then ok "bad checksum -> install failed (rc=$rc)"; else bad "installed a binary with a wrong checksum"; fi

echo "== Case 3: apt lock contention =="
if command -v flock >/dev/null 2>&1; then
  sudo flock -x /var/lib/dpkg/lock-frontend -c 'sleep 60' &
  lockpid=$!
  sleep 1
  timeout 90 python3 -m devos profile apply core --confirm > /tmp/c3.log 2>&1
  rc=$?
  sudo kill "$lockpid" 2>/dev/null || true
  if [ "$rc" -ne 0 ]; then ok "dpkg lock held -> apply failed cleanly (rc=$rc)"; else bad "apply succeeded despite held dpkg lock"; fi
else
  echo "  SKIP: flock unavailable"
fi

echo "== Case 4: malformed profile JSON =="
echo "{ not valid json" > "$tmproot/profiles/definitions/broken.json"
python3 -m devos profile validate broken > /tmp/c4.log 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then ok "malformed profile -> non-zero (rc=$rc)"; else bad "malformed profile validated OK"; fi

echo
echo "failure-injection: $pass passed, $fail failed"
rm -rf "$tmproot"
[ "$fail" -eq 0 ]
