# Security

## Reporting a vulnerability found via this benchmark

This repository documents vulnerabilities in **third-party** deliberately
vulnerable demo applications (DVAA, DVMCP) that exist specifically to be
found — there is nothing to responsibly disclose about them. If you believe
you've found an issue in Noviscent's own product or infrastructure while
reading this repository, do not open a public issue here. Email
**hello@noviscent.ai** with details, and we will respond within 72 hours.

## What this repository deliberately does not include, and why

- **Noviscent's detection rule source.** This package reports *what class of
  vulnerability was or wasn't detected, by which rule ID, with what measured
  result* — not the exact Semgrep pattern logic that implements detection.
  Publishing exact matching patterns would let anyone construct code that
  evades them, with no corresponding benefit to a reader trying to evaluate
  whether Noviscent's methodology is honest. The methodology, the ground
  truth, the raw findings, and the triage reasoning are all public. To be
  precise about what "raw findings" actually contains: each finding in
  `evidence/raw/` includes not just a bare rule ID, but the rule's own
  emitted message, title, remediation text, CWE/OWASP mapping, and
  confidence level — this is scanner-produced metadata, disclosed
  intentionally, not an accidental leak. What is withheld is narrower and
  specific: the Semgrep pattern/AST match logic that decides when a rule
  fires — the part someone could use to construct evasive code.
- **Fictional secrets in scanner output.** Raw findings under `evidence/raw/`
  include gitleaks matches like `AKIAIOSFODNN7EXAMPLE` — this is AWS's own
  publicly documented example access-key format, embedded in DVAA/DVMCP as
  intentional demo fixtures. Gitleaks also matched demo Stripe API key
  values (`sk_live_51NxEcT...`) embedded in the same targets — these too
  are fictional demo fixtures, not real credentials. The literal Stripe key
  strings have been redacted to `sk_live_<REDACTED_DEMO_STRIPE_KEY>` in the
  published gitleaks JSON to pass GitHub Push Protection; the finding
  structure, rule IDs, paths, and line numbers are preserved. See
  `NOTICE.md` and `evidence/redaction-manifest.json` (round 5).
- **Local file paths and machine/user identifiers.** Raw evidence was swept
  and redacted for absolute local filesystem paths across four rounds (see
  below) before staging. If you find another instance, treat it as a bug in
  this package and report it as a bug in this repository.

## Redaction pass performed before staging

Before this package was assembled, every file under `evidence/` and
`methodology/` was checked for: AWS-format credentials outside the
known-fixture set, private key headers, `noviscent.ca`/`@noviscent.*`
internal references, ClickUp URLs, AWS ARNs/account IDs, and absolute local
filesystem paths. This happened across four rounds — each round's sweep
was incomplete in a way the next round's review or tooling caught, not
self-discovered ahead of time; all four rounds are disclosed here rather
than only the clean end state:

- **Round 1** found and fixed WSL/Linux local paths under a developer's
  home directory, but only in the v0.1.1 raw evidence subset — the sweep
  had not actually been run against the baseline or validation-rerun
  subsets yet, despite this file at the time claiming the general sweep was
  complete.
- **Round 2** (after review) found that gap and fixed two further leaks:
  the baseline raw evidence subset embedded an ephemeral AI-agent session's
  UUID-scoped scratch-directory path (`/tmp/claude-0/.../scratchpad/...`),
  and four validation-rerun `.json.stdout.log`/`.sarif.stdout.log` files
  embedded a developer's personal Windows/OneDrive folder path
  (`C:\Users\<name>\OneDrive\Desktop\...`). Round 2 closed by claiming "a
  full re-sweep of the entire package... found zero remaining matches" —
  that claim was itself wrong (see round 3).
- **Round 3** built an automated pattern-match gate,
  `scripts/publication-hygiene-check.py` (see below), instead of relying on
  manual re-sweeps, and ran it across every tracked file in the package
  rather than just the file types a prior round had just fixed. It
  immediately found the same Windows/OneDrive path still present,
  unredacted, in three files round 2 never checked:
  `evidence/validation-rerun/run{1,2,3}.gitleaks.log`. Those were fixed.
- **Round 4** ran the same gate once more as part of final pre-commit
  verification and it crashed with a `UnicodeDecodeError` on two more
  files: `run1.json.stdout.log` and `run1.sarif.stdout.log`. Those turned
  out to be UTF-16-encoded (a PowerShell stdout-redirect artifact), unlike
  every other text file in this package — meaning nothing, manual or
  automated, had ever actually scanned their content since staging began.
  Decoded directly, they contained the identical unredacted OneDrive path
  found in rounds 2 and 3 — 64 and 45 occurrences respectively, matching
  their already-fixed `run2`/`run3` counterparts exactly. Both are now
  fixed, and the gate itself was fixed to fall back to UTF-16 decoding
  instead of crashing, so a file of this shape can no longer silently go
  unscanned. All instances across all evidence subsets (baseline, v0.1.1,
  validation-rerun) are now normalized to `<TARGET_ROOT>/...` (or
  `<TARGET_ROOT>\...` for the Windows-path files).

Full before/after hash chain of custody for every transformed file (39
total across all four rounds): `evidence/redaction-manifest.json`. After
each redaction, `scripts/score-results.py` was re-run against the redacted
evidence and confirmed to reproduce the exact published metrics — the
redaction only touches path strings inside finding metadata, never the
findings themselves.

**Re-run `scripts/publication-hygiene-check.py` (not a manual grep) before
any future evidence regeneration lands in this package** — round 2's own
"full re-sweep" claim above is the concrete example of why a manual re-check
is exactly the kind of check that's easy to believe is complete when it
isn't; an automated gate that runs the same way every time is the fix.
