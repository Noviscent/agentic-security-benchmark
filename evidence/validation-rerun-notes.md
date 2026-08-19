# Validation Re-Run Notes

## Context

The original benchmark evidence (run1–run3 in `evidence/sarif/`) was generated
by an agent on a Linux environment with:
- semgrep 1.173.0
- gitleaks 8.16.0-1ubuntu0.24.04.3 (Ubuntu universe package)

The original run's stdout/stderr logs and the manual triage log were not
committed due to `.gitignore` patterns (`logs/` and `*.log`) that excluded them.
This was identified as a blocker in the PR review.

## What was done to fix this

1. **`.gitignore` was amended** with exceptions for the benchmark evidence
   directory so that `evidence/logs/` and `evidence/validation-rerun/` are
   tracked.
2. **The 93-row triage log (`evidence/logs/triage-log.csv`) was reconstructed**
   from the original committed findings (`run1.json` + `run1.gitleaks.json`)
   using the outcome judgments documented in `results-summary.md`. The
   reconstruction produces exactly the documented counts: 21 TP findings, 8 FN
   scenarios, 6 Partial, 21 FP, 35 TRUE_ADDITIONAL, 2 NEEDS_REVIEW.
3. **The stdout/stderr logs in `evidence/validation-rerun/` are from a
   validation re-run** (see below), not from the original pinned-version run.
   The original logs are lost. These validation logs are provided so that the
   evidence bundle includes scanner execution artifacts, with their provenance
   disclosed here. They are stored under `evidence/validation-rerun/` (not
   `evidence/sarif/`) to avoid false provenance — the logs beside
   `evidence/sarif/run1.gitleaks.json` did NOT produce that JSON.

## Validation re-run environment

- **Date:** 2026-08-16
- **Platform:** Windows (PowerShell + Python 3.11)
- **semgrep:** 1.163.0 (1.173.0 not available on this platform's PyPI index)
- **gitleaks:** 8.30.1 (installed via winget; 8.16.0 Ubuntu package not available)
- **Targets:** DVAA @ `c3dd6c7`, DVMCP @ `79734c1` (verified against manifest)

## Results: repeatability vs. cross-version reproducibility

### Within-version repeatability (same scanner, same host, 3 runs)

| Scanner | Run 1 | Run 2 | Run 3 | Repeatability |
|---------|-------|-------|-------|---------------|
| semgrep 1.163.0 | 43 unique / 45 raw | 43 unique / 45 raw | 43 unique / 45 raw | 100% identical |
| gitleaks 8.30.1 | 29 | 29 | 29 | 100% identical |

Both scanners were 100% stable across 3 runs on the same host with the same
versions — **within-version repeatability is confirmed for both scanners.**

**On the semgrep 43-vs-45 pair** (verified directly against the committed
JSON in this package, not assumed): every semgrep run in this benchmark —
both the pinned Linux run and this Windows cross-version run — reports 45
raw findings, of which 43 are unique `(rule, path, start_line, end_line,
severity)` tuples. The other 2 are exact duplicates of two already-counted
tuples: `prs001-h-unsafe-concat` fires twice at `challenge6/server.py` line
198 (and twice at line 214), each pair sharing identical
rule/path/start-line/end-line/severity and differing only by match column,
which the identity key doesn't track. This is a property of the target
file's code shape, reproduced identically by both scanner versions — not a
version-specific artifact. See `results/baseline.md`'s Repeatability
section for the full explanation of why both 43 and 45 are real, correct
numbers that answer different questions.

### Cross-version reproducibility (re-run vs. original pinned-version evidence)

| Scanner | Original (pinned) | Re-run (available) | Cross-version reproducibility |
|---------|-------------------|--------------------|-------------------------------|
| semgrep | 43 unique / 45 raw findings (v1.173.0) | 43 unique / 45 raw findings (v1.163.0) | **Confirmed under both counts** — exact finding-set match (same 43 unique rule/relative-path/line/severity tuples, same 2 exact-duplicate PRS001-H matches accounting for the 45th/46th raw count on both platforms). Verified directly by parsing this package's own committed `evidence/raw/baseline/run1.json` and `evidence/validation-rerun/run2.json.stdout.log` with the same `semgrep_key()` function from `scripts/score-results.py`. Only the absolute path prefix differs (both now redacted to `<TARGET_ROOT>/...` in this package). |
| gitleaks | 36 unique findings (v8.16.0) | 29 unique findings (v8.30.1) | **Not confirmed** — gitleaks 8.30.1 reports different end-line offsets and does not detect `aws-access-token` patterns the same way as 8.16.0. 20 of 36 original findings overlap by rule + start-line; 16 original findings have no exact match in the re-run, and 9 re-run findings have no exact match in the original. |

### Interpretation

- **semgrep:** Cross-version reproducibility is confirmed across versions
  1.163.0 → 1.173.0. The original pinned-version evidence is authoritative and
  fully reproducible.
- **gitleaks:** Cross-version reproducibility is **not** confirmed. The finding
  set is version-sensitive between 8.16.0 and 8.30.1. This is a real version
  sensitivity, not a methodology error. The original pinned-version evidence
  (36 findings) remains authoritative; reproducing the exact 36-finding set
  requires gitleaks 8.16.0 specifically. The `benchmark-manifest.json` pins
  gitleaks 8.16.0 and its config SHA-256.
- **The `run-benchmark.sh` harness now enforces version matching** against the
  manifest and fails on mismatch unless `ALLOW_SCANNER_VERSION_MISMATCH=1` is
  set, making the distinction between exact reproduction and cross-version
  validation explicit.

### What this validates

1. The fixed `run-benchmark.sh` correctly handles both scanners, validates
   target SHAs, verifies clean working trees, checks scanner versions against
   the manifest, validates pack content hashes, and propagates failures
   instead of silently swallowing them.
2. The fixed `score-results.py` correctly verifies repeatability for BOTH
   scanners (semgrep and gitleaks) and computes unit-consistent metrics from
   the 93-row triage log with exploded TP findings.
3. The original committed evidence (run1–run3) is internally repeatable
   (43/43/43 semgrep, 36/36/36 gitleaks) — verified by running
   `score-results.py` against it.
4. The triage log (`triage-log.csv`) produces the metrics that were published
   at the time: scenario recall 4/12 = 33.3%, finding-level alert precision
   56/77 = 72.7%, extra-finding validation rate 35/56 = 62.5%.

## Amendment: baseline triage reconciliation

A later reconciliation pass (see `limitations.md` and `results-summary.md`
"Reconciliation note") found that the 93-row reconstruction in point 2 above,
while an accurate reconstruction of the outcome judgments in
`results-summary.md` at the time, under-counted two raw `prs001-h-unsafe-concat`
matches (two distinct, overlapping matches at `challenge6/server.py` lines 198
and 214, each represented by only one row instead of two) — so it does not
reconcile 1:1 against `evidence/sarif/run1.json`. The corrected, reconciled
ledger is
[`evidence/triage/triage-log-baseline-reconciled.csv`](./triage/triage-log-baseline-reconciled.csv)
(95 rows, 23 FP instead of 21) and is now the source for all published
finding-level metrics: finding-level alert precision 56/79 = **70.9%**,
extra-finding validation rate 35/58 = **60.3%**. Scenario recall is unchanged
at 4/12 = 33.3%. The original `triage-log.csv` and this note's point 4 are
left unedited as the historical record of the original (short-by-two)
reconstruction.
