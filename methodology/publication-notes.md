# Publication notes for the protocol documents

This package publishes the methodology as **three files**, not one, after a
provenance problem was found in an earlier version of this package (it
published a single file, labeled as "the frozen methodology, exactly as
written before any scan ran," that actually contained post-baseline-scan
amendments — including a note explicitly dated "round-3"). That was fixed
by separating the true pre-scan document from what it became:

- **`protocol-pre-scan.md`** — the exact blob committed to Noviscent's
  private repository before the baseline benchmark's first scored run
  (commit `e7b2ef7`). Published verbatim. Nothing in this file has been
  edited, including its now-stale internal path references (see below) —
  editing a frozen document after the fact, even to fix stale paths, is
  exactly the kind of silent rewrite this package's house style refuses to
  do (see `limitations.md`, "Baseline triage reconciliation," for the same
  principle applied to a triage log).
- **`protocol-current.md`** — the final, amended methodology, which is
  what the published results in `results/` actually match. Also published
  verbatim (unedited from its private-repository final state).
- **`protocol-amendments.md`** — the chronological ledger of every change
  between the two: which commit, when, and why. Read this if you want to
  know whether a specific published number reflects the pre-scan
  methodology or a later clarification.

Both protocol files were written against the private benchmark workspace's
directory layout, not this public package's layout — the path mapping below
applies to both.

## Why the paths don't match this package

| Referenced in the protocol documents | Actual location in this public package |
|---|---|
| `evidence/sarif/` | `evidence/raw/baseline/` |
| `evidence/sarif-v0.1.1/` | `evidence/raw/v0.1.1/` |
| `evidence/logs/` | `evidence/triage/` (triage logs) and `evidence/validation-rerun-notes.md` (everything else that lived in `evidence/logs/` in the private workspace) |
| `evidence/logs/triage-log.csv` | `evidence/triage/triage-log.csv` |
| `evidence/logs/triage-log-v0.1.1.csv` | `evidence/triage/triage-log-v0.1.1.csv` |
| `evidence/logs/ground-truth-corrections.md` | No corrections to `ground-truth.csv` have ever been needed (it has not changed since the freeze commit — same sha256 recorded in `evidence/manifests/` for both rounds), so this file has never existed. The protocol names it as a rule for *if* one were ever needed — it is still binding, it has simply never been triggered. |
| `scripts/score-results.py` | `scripts/score-results.py` (this public package) — see below |
| `results-summary.md` | `results/baseline.md` and `results/remediation-v0.1.1.md` |

## The "independent third party reproduction" claim needs a correction, not just a path fix

Both `protocol-pre-scan.md` and `protocol-current.md`, section 8 ("Evidence
retention"), say: *"Every artifact needed for an independent third party to
reproduce a published number is retained."*

That statement is true of the **internal, private** benchmark workspace,
where the scanner itself (the Semgrep rule source) sits alongside the
evidence. It is **not fully true of this public package**, because the
scanner is not included here — see `SECURITY.md` for why.

**Corrected statement for this public package:** this sentence, in both
protocol files, refers to the evidence bundle required by the internal
methodology, where the Noviscent scanner was also available to the person
reproducing a number. The Noviscent scanner itself remains private, so
**the detection step is not independently reproducible from this public
repository alone**. What *is* independently reproducible from this package
alone: the target checkouts (pinned commit SHAs), the scoring arithmetic
(given the raw scanner output and triage log already here,
`scripts/score-results.py` recomputes the exact published numbers — see
below), and the integrity of every published file (via `evidence/hashes/`,
checked against actual committed git bytes by `scripts/verify-integrity.py`).
See `REPRODUCIBILITY.md` for the full three-layer breakdown this package
holds itself to.

## Why `scripts/score-results.py` is published here

The scoring script is not detection logic — it doesn't decide what counts
as a vulnerability, it only computes reproducibility/precision/recall
arithmetic from already-triaged CSV rows and already-produced scanner JSON.
Publishing it lets any reader recompute every published number themselves
from the raw output and triage log already in this package, without needing
access to the private scanner at all. This is a meaningfully stronger
inspectability claim than "trust our arithmetic," and it exposes nothing
about how Noviscent's rules detect anything. It has been re-run against the
redacted evidence in this package (both baseline and v0.1.1) and confirmed
to reproduce every published metric exactly.
