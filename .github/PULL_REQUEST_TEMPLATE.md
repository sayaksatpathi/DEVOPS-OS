## What this changes

<!-- A short description of the change and why. -->

## Checklist

- [ ] Unit tests pass locally: `PYTHONPATH=packages/cli python3 -m unittest discover -s tests/unit`
- [ ] New/changed profiles validate: `devos profile validate --all`
- [ ] No secrets, keys, tokens, or machine identity added
- [ ] New tools are pinned; binary artifacts have a signature/attestation (not TOFU)
- [ ] `STATUS.md` / `CHANGELOG.md` updated (and `DECISIONS.md` for material choices)
- [ ] Status markers are honest (implemented / tested / partial / planned / experimental)
- [ ] Commits signed off (`git commit -s`) per the DCO in CONTRIBUTING.md

## Testing done

<!-- What you ran, on what OS, and the result. Note if anything is untested/blocked. -->
