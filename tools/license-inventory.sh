#!/usr/bin/env bash
# Generate a per-package license inventory (§15). Run on a DevOS system or against a
# packages list. Produces a TSV: package<TAB>version<TAB>license. The human license
# REVIEW/sign-off (docs/license-review-template.md) is a separate, non-automatable step.
set -euo pipefail
out="${1:-license-inventory.tsv}"
printf 'package\tversion\tlicense\n' > "$out"
if command -v dpkg-query >/dev/null 2>&1; then
  while IFS=$'\t' read -r pkg ver; do
    lic="unknown"
    cp="/usr/share/doc/${pkg}/copyright"
    if [ -r "$cp" ]; then
      lic="$(grep -m1 -iE '^License:' "$cp" | sed 's/^[Ll]icense:[[:space:]]*//' || true)"
      [ -z "$lic" ] && lic="see-copyright"
    fi
    printf '%s\t%s\t%s\n' "$pkg" "$ver" "$lic" >> "$out"
  done < <(dpkg-query -W -f='${Package}\t${Version}\n')
else
  echo "dpkg-query not found — run on a Debian/Ubuntu system, or feed a Trivy SBOM license scan." >&2
fi
echo "wrote $out ($(($(wc -l < "$out")-1)) packages). Review with docs/license-review-template.md."
