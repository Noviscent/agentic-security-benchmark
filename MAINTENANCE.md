# Maintenance

This file documents the CI, branch-protection, release process, and
change-management policy for this repository.

## CI (`.github/workflows/publication-checks.yml`)

The workflow runs four checks on every push and pull request against `main`,
all read-only against committed content, none requiring the private Noviscent
scanner:

1. `scripts/syntax-check.py` — every tracked `.json`/`.csv` file parses.
2. `scripts/verify-integrity.py verify` — every hash in
   `evidence/hashes/file-hashes.txt` matches the bytes actually committed
   to git (not a filesystem copy), the bundle checksum matches, and no
   in-scope committed file is missing from the manifest.
3. `scripts/golden-metrics-check.py` — re-running `score-results.py`
   against the committed baseline and v0.1.1 evidence reproduces the exact
   numbers published in `results/baseline.md` and
   `results/remediation-v0.1.1.md`. Guards against a future edit to a
   triage CSV or raw JSON silently drifting the published numbers.
4. `scripts/publication-hygiene-check.py` — no unresolved year placeholder,
   no unremoved pre-publication note marker, no publication-blocker marker,
   no link placeholder, no TODO/TBD-before-publication marker, no
   `/home/`, `/Users/`, `C:\Users\`, `/tmp/claude-`, or `scratchpad` path
   fragment, no internal `app.`/`dev.noviscent.ca` or `@noviscent.*` domain
   reference, no ClickUp URL, no private key header, and no AWS account
   ID/access key outside the two disclosed DVAA/DVMCP demo fixtures.

None of these four scripts touch, run, or require Noviscent's detection
rule source. All are read-only against the repository's own committed
content.

**What this CI is not:** a legal review, a security review, or a
substitute for human judgment. A green run means "no known pattern-matched
problem was found," not "this repository has been reviewed by a human and
is perfect."

## Branch protection

The `main` branch is protected:

- Force-pushes to `main` are disallowed.
- Branch deletion for `main` is disallowed.
- Pull requests are required for changes to `main` (no direct pushes).
- The `Publication checks` workflow must pass before merge.

## Release process

1. Ensure all CI checks pass on `main`.
2. Create an annotated tag (`v0.1.1`, `v0.2.0`, etc.) pointing at the
   exact commit to release.
3. Create a GitHub Release referencing the tag, including:
   - the exact commit SHA;
   - the bundle checksum from `evidence/hashes/bundle-checksum.txt`;
   - a plain-language summary that does not overclaim.
4. If a future release uses a signed tag or Sigstore/cosign attestation,
   state that explicitly in the release notes. Do not claim a signature
   that does not exist.

## Evidence correction policy

This repository is specifically about evidence discipline. If a published
metric, artifact, or provenance statement is later found wrong:

1. **Preserve** the previous public Git history — do not force-push or
   rewrite.
2. **Commit the correction** in a new commit.
3. **Document** what changed and why, in the commit message and in the
   relevant results/limitations file.
4. **Recompute** affected metrics using `scripts/score-results.py`.
5. **Regenerate** `evidence/hashes/file-hashes.txt` and
   `evidence/hashes/bundle-checksum.txt` against the new committed state.
6. **Cut a patch release** if the correction affects a published release.
7. **Never** silently overwrite an unfavorable result. The retained
   baseline is the trust signal this repository exists to send.

This is a Noviscent research norm, not just a repository rule.

## Adding new evidence

If a future benchmark round adds new evidence:

1. Add raw output under `evidence/raw/<round>/`.
2. Add a triage log under `evidence/triage/`.
3. Add or update manifests under `evidence/manifests/`.
4. Run `python3 scripts/verify-integrity.py regenerate` to generate
   hashes from committed git bytes.
5. Commit the hash files.
6. Run `python3 scripts/verify-integrity.py verify` to confirm.
7. Update `results/` and `scripts/golden-metrics-check.py` with the new
   golden metrics.
8. Ensure all four CI checks pass before merging.
