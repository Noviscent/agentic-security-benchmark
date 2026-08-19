# Baseline result

**This is a Noviscent-run benchmark. It is not an OWASP-run validation,
certification, or endorsement.**

## Headline

> Noviscent detected **4 of 12 (33.3%)** known in-scope weaknesses (scenario
> recall). Finding-level alert precision was **56/79 = 70.9%** among the 79
> adjudicated findings included in the precision denominator (21
> scenario-matching true positives + 35 true-but-off-target additional
> findings + 23 false positives). Two additional findings were marked
> needs-review and excluded from that denominator. The canonical scored run
> (run1) contained 81 raw findings; three runs total were executed to
> measure repeatability, not to inflate the finding count — see
> "Repeatability" below for what the 3-run figures actually measure.
> Extra-finding validation rate was **35/58 = 60.3%** — of the 58 alerts that
> fell outside the pre-declared scenario matches, 35 were still real
> vulnerabilities. Finding-set repeatability was **100% across 3 runs under
> identical configuration** for both the semgrep and gitleaks components —
> the normalized finding sets were identical; the raw files themselves are
> not byte-identical (they embed run timestamps).

This is a modest result and it is published as measured, not adjusted. It
surfaced real, actionable, fixable gaps (see "Important false negatives"
below) alongside evidence of what already worked (see "What worked").

A single heuristic rule accounted for 19 of the 23 false positives; excluding
it, the false-positive count drops to 4 — both numbers are reported so the
effect is visible rather than asserted.

## Primary detection matrix (12 in-scope scenarios)

| Scenario | OWASP category | Result |
|---|---|---|
| DVMCP-02 Tool Poisoning | ASI02 | **FN** — no rule for docstring-embedded instructions at the time |
| DVMCP-03 Excessive Permission Scope | ASI03 | **FN** |
| DVMCP-05 Tool Shadowing (eval sink) | ASI02 | **FN** |
| DVMCP-07 Token Theft | ASI03 | **TP** |
| DVMCP-08 Malicious Code Execution | ASI05 | **FN** |
| DVMCP-09 Remote Access Control | ASI05 | **FN** |
| DVMCP-10 Multi-Vector (secrets component) | ASI08 | **TP** |
| DVAA-01 Pickle Deserialization | ASI05 | **TP** |
| DVAA-02 API Keys in Web-Served Files | ASI03 | **TP** |
| DVAA-03 Command Injection (exec template) | ASI05 | **FN** |
| DVAA-04 Insecure Install (curl\|sh) | ASI04 | **FN** — narrow bash rule coverage at the time |
| DVAA-08 Delegation Privilege Escalation | ASI03 | **FN** |

**TP = 4, FN = 8 → Recall = 4/12 = 33.3%**

6 additional scenarios were classified partial/out-of-primary-scope
(runtime- or call-count-gated mechanisms); see `methodology/ground-truth.csv`
and `methodology/protocol-current.md` (the amended methodology matching published results; see `methodology/protocol-amendments.md` for what changed since the pre-scan original in `methodology/protocol-pre-scan.md`) section 7.

## Most actionable finding

The single most actionable miss: the command-injection detection class
caught **0 of 6** textbook command-injection sinks across the corpus (Python
and TypeScript) — the kind of pattern a human reviewer flags on sight. This
is a strong, reproducible signal independent of language.

Other notable gaps (root cause classes only — see `limitations.md` and
`SECURITY.md` for why exact rule logic isn't published):
- A code-execution detection class missed two direct dynamic-eval calls and a
  temp-file-then-execute pattern.
- An agent-delegation detection class missed a scenario that was, on paper
  before scanning, the closest textual match to an existing rule description
  in the entire benchmark.
- A path-traversal detection class missed an unvalidated read with no
  validation at all.
- No rule at the time targeted MCP tool-description/docstring content for
  embedded imperative instructions ("tool poisoning") — a genuine, novel
  detection surface with no coverage, not an existing rule failing to match.
- A narrow gap in piped-installer coverage missed a generic `curl | sh`
  pattern.

## Most actionable false-positive source

One heuristic rule, explicitly documented in its own metadata as heuristic,
fired 19 times across 5 files on generic string construction with no
relationship to the vulnerability class it targets, and did not fire at any
of the scenarios' actual vulnerable lines. This is the single largest driver
of the baseline's low precision number.

A second, smaller source: two tool-routing heuristics misfired on a *safe*
reference implementation in one file while missing the real vulnerable sink
in the same file.

## What worked

- A deserialization-safety rule matched the pickle-load scenario at the
  exact predicted line.
- The secret-scanning component correctly caught every clean
  hardcoded-secret scenario tested, plus 15 additional real secrets
  scattered through scenarios whose primary declared vulnerability was
  something else.
- An MCP-authentication rule correctly and consistently fired on all 10
  DVMCP servers, none of which implement MCP auth middleware — accurate
  every time it fired, just not any scenario's declared primary root cause,
  so it shows up as a true additional finding rather than a primary TP.
- Both scanners were 100% stable across 3 runs with zero nondeterministic
  findings.

## Repeatability

3 runs under identical configuration, scored separately for each scanner component by comparing
the normalized finding set across runs:

- semgrep: **45 raw findings per run** (with duplicates counted — see below),
  **100% identical across all 3 runs**.
- gitleaks: 36/36/36 unique findings, **100% identical across all 3 runs**.

**A precision note on the semgrep count, because an earlier version of this
page mislabeled it:** 45 is the *raw* per-run finding count (every match
semgrep reported, including exact duplicates), not the count of *unique*
`(rule, path, start_line, end_line, severity)` tuples. The true unique-tuple
count for this run is **43** — two pairs of PRS001-H matches at
`challenge6/server.py` lines 198 and 214 each fire twice with the same
rule/path/start-line/end-line/severity, differing only by match column
(which isn't part of the identity key), so each pair collapses to one
tuple. Both numbers are real and both matter for different reasons: **45**
is what feeds the finding-level precision/recall arithmetic in
`evidence/triage/` (every raw finding, including the column-differing
duplicates, gets its own triage row — see "Full triage" below), while
**43** is the number to cite if you're asking "how many distinct locations
did semgrep flag." Neither number is wrong; they answer different
questions, and this package previously called 45 "unique" when it isn't.
See `evidence/validation-rerun-notes.md` for confirmation that this same
43-vs-45 relationship holds identically on the independent cross-version
validation run.

Redacted copies of the raw output for all 3 runs (see `evidence/redaction-manifest.json` for what was transformed and why): `evidence/raw/baseline/`.

## Full triage

`evidence/triage/triage-log-baseline-reconciled.csv` (95 rows: 21 individual
TP findings, 8 FN scenarios, 6 partial scenarios, 60 extra findings) is the
corrected, fully-reconciled ledger this result is computed from. The
originally-published triage log is preserved unedited at
`evidence/triage/triage-log.csv` as the historical record — see
`limitations.md`, "Baseline triage reconciliation."
