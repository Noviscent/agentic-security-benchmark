# Protocol amendments — chronological ledger

This is the honest version of "methodology maturing" rather than a hidden
one. `protocol-pre-scan.md` is the exact, unedited methodology document as
it existed before the baseline benchmark ran. `protocol-current.md` is the
final, amended version — the one the published results actually match. This
file is the record of every change between the two, in order, with the
commit that made it, when, and why. Nothing here is presented as "the
original protocol" — that label belongs to `protocol-pre-scan.md` alone.

**Why this file exists:** an earlier version of this package labeled the
*final* amended protocol as "the frozen methodology, exactly as written
before any scan ran." That was wrong — the file it was describing contains
a note explicitly dated "round-3," which is post-baseline-scan by
definition. This ledger exists so that mistake can't recur: every change is
now dated, sourced, and separated from the pre-scan original rather than
blended into it.

**On chronology verifiability:** all of the commits below happened in
Noviscent's private source repository. An external reader can verify the
*sequence and content* of these amendments (this ledger, cross-checked
against `protocol-pre-scan.md` and `protocol-current.md`, both published
here), but not that the private repository's commit timestamps are
themselves trustworthy — that would require the freeze and each amendment
to have happened somewhere publicly observable, which they didn't. See
`provenance.md`, "On independently verifying this chronology."

## The freeze

| | |
|---|---|
| Commit | `e7b2ef7` |
| Timestamp | 2026-08-16T19:07:17Z |
| Message | "Freeze benchmark protocol, manifest, and ground truth before scanning" |

This is `protocol-pre-scan.md`, unedited. The baseline benchmark's three
scored runs happened after this commit, against this exact methodology.

## Amendments, in order

| # | Commit | Timing (relative to freeze/scan) | What changed | Why |
|---|---|---|---|---|
| 1 | `2a026cf` | After the baseline scan, during review | Replaced the original `Precision = TP/(TP+FP)`, `Recall = TP/(TP+FN)`, `F1` block (which mixed scenario-level TPs with individually-triaged finding-level FPs — different units) with two unit-consistent metrics: **scenario recall** (scenarios/scenarios) and **finding-level alert precision** (findings/findings). No combined F1 published going forward. The commit that introduced the mixed-unit metric (`ae87e49`, pre-dating this ledger's freeze commit) is referenced and its output withdrawn as a headline metric; raw counts unchanged. | A mixed-unit metric was misleading — see `results-summary.md`'s own historical note for the full story of the withdrawn `16%`/`0.216` figures. |
| 2 | `b6ee4cb` | Same review round | Section 2 wording: "primary precision/recall/F1 denominator" → "primary scenario-recall denominator," matching amendment 1's terminology. | Cleanup following amendment 1. |
| 3 | `d51325e` | After the baseline round was complete, ahead of the v0.1.1 remediation round | Split the single finding-level metric into two: **finding-level alert precision** (all valid alerts / all alerts) and **extra-finding validation rate** (true-additional / true-additional+FP) — the former is the headline number, the latter a narrower view of only the non-scenario alerts. Also added **Section 9, "Remediation re-runs,"** defining how a later remediation round (v0.1.1) must relate to the frozen baseline (same ground truth and targets, separate evidence directory, never overwrite baseline evidence). | The single finding-level metric conflated two different questions. Section 9 didn't exist at freeze time because the baseline round hadn't been scored yet — a remediation-round methodology couldn't be written before there was a baseline to remediate. |
| 4 | `2746b88` | v0.1.1 remediation round | Wording accuracy fix: v0.1.1's triage log described as "built independently from scratch" corrected to "manually rebuilt from scratch from the regenerated raw findings" — the original phrasing overstated independence (it was Noviscent re-triaging its own regenerated output, not a separately-sourced build). | Accuracy correction, not a methodology change. |
| 5 | `84f18ab` | v0.1.1 remediation round, "round-3" internal review pass | Added the **"Methodological clarification (round-3)"** callout explaining that the semgrep reproducibility key includes `severity` (per the section-7 definition) while the gitleaks key doesn't, because gitleaks JSON has no per-finding severity field — a property of the tool's output format, not a methodology change. | Disambiguates an implementation detail a reviewer had reasonably questioned; doesn't change what's measured. |

## What did NOT change across any amendment

- The 18 scenarios in `ground-truth.csv` and their in-scope/partial
  classification — unchanged since the freeze commit (same sha256, recorded
  in `evidence/manifests/`).
- The pinned DVAA/DVMCP target commits.
- The core principle that scenario recall and finding-level metrics are
  reported separately, never combined into a single score.

## Publication note

`README.md` and every other file in this package that previously said
"`protocol.md` (frozen, before any scan ran)" now points at
`protocol-pre-scan.md` for that specific claim, and at
`protocol-current.md` (via `publication-notes.md`) for the methodology that
actually matches the published numbers. Neither file is described as both
things at once.
