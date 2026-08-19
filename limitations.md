# Limitations

This benchmark is **not** an OWASP certification, OWASP-run validation, or
endorsement of Noviscent by OWASP. It is a Noviscent-run technical exercise
whose results are mapped to the OWASP Top 10 for Agentic Applications (2026)
taxonomy for communicability only. Noviscent has not been "OWASP certified,
approved, endorsed, validated, or verified," and no material produced from
this benchmark should say otherwise unless OWASP explicitly grants such a
status in writing.

- **Small, curated sample.** 18 scenarios (12 in-scope) is enough to surface
  real, actionable signal — and it did — but it is not a statistically
  representative sample of agentic/MCP vulnerability classes in the wild.
  Confidence intervals on a sample this size are wide; treat the point
  estimates (baseline: 33.3% scenario recall, 70.9% finding-level alert
  precision; v0.1.1 after remediation: 100% scenario recall, 95.7%
  finding-level alert precision) as directional, not as a precise population
  parameter. A 12-scenario denominator means each individual scenario is
  worth over 8 percentage points of recall.
- **Two target codebases, not a market survey.** DVAA and DVMCP were chosen
  because they are purpose-built, well-documented, and widely known in the AI
  red-team community — not because they are representative of production
  codebases in shape, size, or framework diversity.
- **Static scope only.** This benchmark intentionally excludes runtime-,
  behavior-, and LLM-dependent vulnerability classes from the primary metric
  calculation; it does not claim static analysis is sufficient for agentic AI
  security on its own. See `methodology/protocol-current.md` (the amended methodology matching published results; see `methodology/protocol-amendments.md` for what changed since the pre-scan original in `methodology/protocol-pre-scan.md`) section 7 for the exact
  in-scope/partial classification.
- **Public benchmark visibility.** DVAA and DVMCP are public, well-known
  repositories. As with any public benchmark, there is a standing risk that
  tool vendors — including Noviscent — could tune rules specifically to these
  fixtures over time, inflating future scores without a corresponding
  improvement in real-world detection. An unseen external corpus and
  independent execution (see `REPRODUCIBILITY.md`) exist specifically to
  guard against this, and are the planned next step, not yet done.
- **Version-pinned result.** Both the baseline and remediation numbers are
  tied to specific, pinned Noviscent pack versions and content hashes (see
  `evidence/manifests/`). Neither result automatically applies to earlier or
  later Noviscent versions.
- **Same-corpus remediation, not independent validation.** The v0.1.1 result
  is Noviscent re-scanning the *same* frozen ground truth and target commits
  used for the baseline, after fixing the gaps that baseline exposed. This is
  a legitimate, honestly-measured regression-closure result — it is not an
  unseen holdout, and it is not independently executed by anyone other than
  Noviscent. Do not describe it as either.
- **Manual triage judgment calls.** Classifying an extra finding as a false
  positive vs. a true-but-off-target additional finding vs. needs-review
  involved human judgment, documented per-row with rationale in
  `evidence/triage/`. A different reviewer might draw a small number of these
  boundaries differently; none of the calls change the scenario-level TP/FN
  counts that drive the headline recall number.
- **Baseline triage reconciliation.** The originally-published baseline
  triage log undercounted two raw findings (two overlapping-but-distinct
  Semgrep matches at the same rule/file/line, represented by one triage row
  instead of two). Rather than silently editing the frozen historical log,
  a separate, clearly-labeled corrected ledger was published alongside it,
  and every affected metric (finding-level alert precision, extra-finding
  validation rate) was recomputed from the corrected ledger and disclosed as
  a correction, not folded in unremarked. See `evidence/triage/` for both the
  original and the corrected file, and the commit history for the disclosure.
  This is called out here as an example of the standard this package holds
  itself to: corrections are visible, not silent.
- **Scanned-path scope.** Each DVMCP challenge ships both a primary server
  file and an alternate transport wrapper around identical vulnerable logic;
  only the primary file was scanned to avoid double-counting identical
  findings. This does not affect detection rate, only finding volume.
- **No claim beyond tested scope.** This benchmark says nothing, one way or
  the other, about Noviscent's detection of vulnerability classes not
  exercised by the scenarios in this package.
- **Not independently reproducible today.** The Noviscent scanner is
  proprietary; nobody outside Noviscent has independently executed this
  benchmark. See `REPRODUCIBILITY.md` for the precise distinction between
  what is and isn't true about "reproducibility" here.
