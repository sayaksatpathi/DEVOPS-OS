#!/usr/bin/env bash
# Backup/restore recovery test (gap #3): prove an encrypted backup can be created and a
# deleted file restored from it. Uses restic on a disposable host (CI runner / throwaway VM).
set -euo pipefail

work="$(mktemp -d)"
export RESTIC_REPOSITORY="$work/repo"
export RESTIC_PASSWORD="devos-backup-test"
data="$work/data"
mkdir -p "$data"

command -v restic >/dev/null 2>&1 || { sudo apt-get update -qq && sudo apt-get install -y restic; }
restic version

echo "== create data, back it up =="
echo "important user config v1" > "$data/config.txt"
echo "a document" > "$data/doc.txt"
restic init
restic backup "$data"

echo "== simulate data loss =="
rm -f "$data/config.txt"
[ ! -f "$data/config.txt" ] || { echo "FAIL: file not deleted"; exit 1; }

echo "== restore from backup =="
restic restore latest --target "$work/restored"
restored="$(find "$work/restored" -name config.txt | head -1)"
if [ -n "$restored" ] && grep -q "important user config v1" "$restored"; then
  echo "BACKUP/RESTORE TEST PASSED: deleted file restored with correct contents from an encrypted backup."
else
  echo "BACKUP/RESTORE TEST FAILED: file not restored correctly."
  exit 1
fi
rm -rf "$work"
