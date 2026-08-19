# Provenance

Every input artifact in this package, where it came from, and how to verify it
independently.

## Target codebases

| Target | Source | License (declared source — see caveat below) | Pinned commit |
|---|---|---|---|
| Damn Vulnerable AI Agent (DVAA) | https://github.com/opena2a-org/damn-vulnerable-ai-agent | Apache-2.0 (`package.json` `license` field) | `c3dd6c738cd5f225084867ff3d61b048515c4e3a` |
| Damn Vulnerable MCP Server (DVMCP) | https://github.com/harishsg993010/damn-vulnerable-MCP-server | MIT (stated in `README.md` prose) | `79734c19f5104cd11486c90926d245560f53befa` |

**License caveat:** both licenses above come from
real project metadata verified directly at the pinned commit — DVAA's
`package.json` explicitly declares `"license": "Apache-2.0"`, and DVMCP's
`README.md` states in prose "licensed under the MIT License." Neither is a
guess or a rendered badge image. No actual `LICENSE` file exists at
either pinned commit (checked directly and confirmed absent — DVMCP's
README even points at a `LICENSE` file that isn't there). Declared license
metadata is a stronger provenance basis than a badge, but it is still not a
filed license grant. A human/legal provenance review has been completed:
this repository does not redistribute the target codebases in full — only
scanner outputs and limited context referencing them by path and line
number, as documented in `NOTICE.md`. The declared license metadata is
sufficient provenance for this scoped use. See `NOTICE.md` for the same
caveat stated per-project.

Both are third-party, publicly maintained projects. Noviscent did not author
them, does not control their content, and pins a specific commit precisely so
that a future change to either project cannot silently change what this
benchmark measured. See `NOTICE.md` for full license attribution.

## Scanner and rule-pack versions

| Round | Semgrep | Gitleaks | Noviscent packs (version, not source) |
|---|---|---|---|
| Baseline | 1.173.0 | 8.16.0 | agent-safety 1.2.0, tool-safety 1.1.0, data-exfil 1.1.0, secrets-privacy 1.0.0, supply-chain 1.1.0, prompt-rag 1.2.0 |
| Remediation (v0.1.1) | 1.173.0 | 8.16.0 | agent-safety 1.3.0, tool-safety 1.2.0, supply-chain 1.2.0, prompt-rag 1.3.0 (data-exfil/secrets-privacy unchanged) |

Exact pack **content hashes** (sha256, not source) are recorded per round in
`evidence/manifests/`. The pack source itself — the Semgrep rule files that
implement Noviscent's detection logic — is proprietary and is not included in
this package. See `SECURITY.md`.

## Ground truth

Written from target documentation and source review, **before any scan ran**.
Committed to Noviscent's **private** source repository ahead of scanning
(original freeze commit, later amended once with exact scan-path scoping —
still before any scan). Reused unchanged for the remediation round. See
`methodology/ground-truth.csv` and `methodology/protocol-current.md` (the amended methodology matching published results; see `methodology/protocol-amendments.md` for what changed since the pre-scan original in `methodology/protocol-pre-scan.md`) section 2.

**On independently verifying this chronology:** because the freeze commit
lives in a private repository, an external reader cannot walk public git
history and confirm for themselves that the ground truth predates the scan —
they can only trust Noviscent's account of it, backed by `ground-truth.csv`'s
sha256 (recorded in `evidence/manifests/`) staying constant between the
baseline and remediation rounds published here. That's a real, disclosed
limit on this claim's strength, not a gap to paper over. A future benchmark
round pre-registered somewhere public *before* scanning — so a third party
can watch the freeze happen in real time — would be a materially stronger
version of this same claim, and is the intended next step, not something
this package already does.

## Evidence chain of custody

1. Ground truth frozen → committed.
2. Baseline scan run 3x against pinned targets, pinned scanner versions.
3. Every baseline finding manually triaged against ground truth, with a
   written rationale per row (see `evidence/triage/`). The triage log
   records the scanner, rule, file, line, outcome, and rationale for each
   row — it does not record a reviewer identity, so this package does not
   claim a named or credentialed reviewer performed the triage; treat it as
   Noviscent's own internal manual review, not third-party adjudication.
4. Baseline results retained internally, including every gap found (not
   published externally until this package).
5. Gaps root-caused; Noviscent packs updated. The exact private-repository
   commit SHAs for that work **are** published, in
   `evidence/manifests/*.json` (`remediation_commit_sha`,
   `baseline_commit_sha`) — what's withheld is the rule *source* those
   commits point to, not the commit identifiers themselves. See
   `SECURITY.md` for that distinction.
6. Remediation scan run 3x against the **same** pinned targets and the
   **same** ground truth (no ground-truth changes between rounds).
7. Every remediation finding manually re-triaged from the regenerated raw
   findings, using the same triage methodology as the baseline round — this
   is Noviscent re-checking its own work a second time, not an independent
   third party doing so. Do not describe it as "independently re-triaged."
8. sha256 hash generated over every file in this evidence package **as
   actually committed to git** (see `evidence/hashes/` and
   `scripts/verify-integrity.py`), so any future change to a published file
   is detectable.

## What is deliberately NOT included

- Noviscent's Semgrep rule source (`backend/packs/**/*.yaml` in the private
  repository) — proprietary detection logic.
- The private AI-SAST application source, infrastructure, or deployment
  configuration.
- Any customer, employee, or internal-tooling information (this package was
  swept for local file paths, usernames, internal domains, and credential
  patterns before publication; see the redaction note in `SECURITY.md`).

## Verifying this yourself

- Reproducing the target checkouts: clone each target at the pinned commit
  above and diff against what `evidence/manifests/*.json` declares.
- Reproducing the scanner output: not possible without the private Noviscent
  build — see `REPRODUCIBILITY.md` for exactly what is and isn't
  independently reproducible from this package alone.
- Reproducing the hash: run `python3 scripts/verify-integrity.py verify`.
  It checks every hash in `evidence/hashes/file-hashes.txt` against the
  bytes actually committed to this repository's git history (`git show
  HEAD:<path>`), not a local filesystem copy, and fails if any declared
  file is missing from git, any hash doesn't match, any in-scope committed
  file is missing from the hash list, or the bundle checksum doesn't match.
  A plain `sha256sum` against files on disk is not sufficient — it cannot
  detect a file that was hashed but never actually committed.
