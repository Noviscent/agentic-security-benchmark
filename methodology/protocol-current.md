# Noviscent Agentic AI Security Benchmark v0.1 — Protocol

This document is the frozen methodology for the benchmark. It is written and committed
**before** any Noviscent scan is executed against the benchmark targets, per the quality
gate in Noviscent's internal quality tracking.

## 1. Scope

The benchmark measures how well Noviscent's Engine A (Semgrep-based) static analysis
detects known, intentionally-introduced vulnerabilities in two deliberately vulnerable
agentic-AI / MCP codebases:

- **DVAA** — Damn Vulnerable AI Agent (`opena2a-org/damn-vulnerable-ai-agent`)
- **DVMCP** — Damn Vulnerable MCP Server (`harishsg993010/damn-vulnerable-MCP-server`)

Both targets and their exact commit SHAs are pinned in
`evidence/manifests/benchmark-manifest.json`.

This is a **Noviscent-run benchmark**. It is not an OWASP-run validation, certification,
or endorsement. Results are mapped to the OWASP Top 10 for Agentic Applications (2026)
taxonomy for communicability only.

## 2. Static-scope classification

Every scenario in `ground-truth.csv` is classified, before scanning, as one of:

1. **in-scope** — a code/configuration pattern exists that a SAST-style scanner can
   reasonably inspect and, in principle, flag from source alone.
2. **partial** — static code exposes a relevant weakness, but exploitability depends
   materially on runtime state, external state (e.g. a public package registry), or
   LLM behavior.
3. **runtime-only** — the weakness cannot reasonably be judged from source/configuration
   alone.

Only category 1 (in-scope) scenarios are counted in the primary scenario-recall
denominator. Category 2 (partial) results are reported separately and are never counted
as a false negative. No scenario in v0.1 was classified runtime-only outright; several
partial scenarios share characteristics with what would be runtime-only classifications
in a larger corpus (see `limitations.md`).

## 3. Ground truth discipline

`ground-truth.csv` was built by reading each target's own documentation (READMEs,
`expected-checks.json` where present), source code, and maintainer commentary —
**without running Noviscent first**. The file was committed to git before the first
Noviscent scan of these targets, and that commit SHA is recorded in this benchmark's
evidence bundle. Any post-hoc correction to `ground-truth.csv` after seeing scanner
output must be recorded separately with rationale and reviewer name in
`evidence/logs/ground-truth-corrections.md` — silent edits are not permitted.

## 4. Execution

Noviscent's Engine A packs were run as `semgrep --config <rule.yaml ...>` directly
against the pinned target checkouts (the proprietary rule files that ship in
Noviscent's private AI-SAST repository), three times, with identical configuration
and no changes to target code, scanner version, or rules between runs. Raw
JSON/SARIF-style output and logs for every run are retained under `evidence/raw/`.

Packs evaluated: `agent-safety`, `tool-safety`, `data-exfil`, `secrets-privacy`,
`supply-chain`, `prompt-rag`. SBOM/dependency-graph/compliance-baseline packs
(`deps-osv-sbom`, `ai-bom`, `sbom-cyclonedx`, `genai-enterprise-baseline`,
`auth-tenant`, `samd-starter`) are out of scope for v0.1 — they target concerns this
benchmark's targets do not exercise.

## 5. Classification of results

For every in-scope and partial scenario:

- **TP** — a Noviscent finding correctly identifies the expected vulnerable code /
  root cause described in `ground-truth.csv`.
- **FN** — the scenario is in-scope but Noviscent produced no defensible corresponding
  finding.
- **Partial** — Noviscent detects a related issue but not enough of the expected
  weakness to count as a full TP.
- **OOS** — explicitly out of static scope (excluded from the primary denominator).

Every Noviscent finding that falls **outside** a known ground-truth scenario location
is manually triaged as:

- **True additional finding** — a real, separate issue Noviscent correctly caught
  that was not part of the pre-declared ground truth (e.g. a second vulnerability in
  the same file).
- **False positive** — Noviscent flagged something that is not a real vulnerability
  in context.
- **Needs review / uncertain** — ambiguous; documented, not silently discarded.

## 6. Reproducibility

The three runs are compared for exact finding-set stability: same rule IDs, same
file:line locations, same severities. The target for deterministic static analysis is
100% finding-set stability across runs; any deviation is reported as the real number,
not rounded up, and investigated.

> **Methodological clarification (round-3):** `score-results.py`'s
> reproducibility key for semgrep is `(rule_id, path, start_line, end_line,
> severity)` — including severity per the definition above. Gitleaks findings
> do not carry a per-finding severity field in their JSON output, so the
> gitleaks reproducibility key is `(rule_id, path, start_line, end_line)`
> without severity. This is a property of the gitleaks output format, not a
> methodological deviation.

## 7. Metrics

Three unit-consistent metrics are reported, all computed mechanically by
`scripts/score-results.py` from the triage log (never by hand). A single
combined F1 is **not** published, because scenario recall and the two
finding-level metrics are computed over different populations (scenarios vs.
individual findings) and a mixed-unit F1 would not be a defensible standard
metric.

```
Scenario recall = TP_scenarios / (TP_scenarios + FN_scenarios)
  # both numerator and denominator are *scenarios* (in-scope only).
  # measures: of the scenarios a SAST scanner should be able to detect,
  #           what fraction did Noviscent flag?

Finding-level alert precision = (TP_findings + TrueAdditional) / (TP_findings + TrueAdditional + FP)
  # TP_findings, TrueAdditional, and FP are all *individual findings*.
  # measures: of every alert Noviscent raised across the whole run, what
  #           fraction pointed at a real vulnerability (whether it matched
  #           a declared scenario or was a true, off-target additional find)?
  # NEEDS_REVIEW is reported separately and excluded from the denominator.

Extra-finding validation rate = TrueAdditional / (TrueAdditional + FP)
  # both numerator and denominator are *individually reviewed findings*
  #   that fell outside the pre-declared ground-truth scenario set.
  # measures: of the alerts that were NOT a scenario TP, what fraction
  #           still pointed at a real (if off-target) vulnerability? A
  #           stricter, narrower view than finding-level alert precision.
```

Scenario recall is computed over the in-scope subset only; both finding-level
metrics are computed over the individually-triaged finding set (scenario-TP
findings plus extra findings). Partial detections, OOS scenarios, and
reproducibility are reported alongside, never folded into these ratios. Raw
counts are always shown alongside percentages (e.g. `4/12 (33.3%)`, not
`33.3%` alone).

The previous version of this protocol (commit `ae87e49`) defined a single
`Precision = TP / (TP + FP)` mixing scenario-TPs with individually-verified
finding-FPs, excluding true-additional findings from the numerator entirely.
That mixed-unit precision (and the F1 derived from it) is withdrawn as a
headline metric for the reasons above; the raw counts it was computed from
are unchanged. A subsequent revision of this document also briefly mislabeled
the extra-finding validation rate's formula as "finding-level alert
precision" -- both metrics are now defined correctly above, matching
`scripts/score-results.py`'s actual output exactly.

## 8. Evidence retention

Every artifact needed for an independent third party to reproduce a published number
is retained under `evidence/`: the manifest, raw scan output for all three runs, logs,
the manual triage log, and a checksum of the finished evidence bundle. See
`results-summary.md` for the final numbers and `evidence/hashes/` for the bundle
checksum.

## 9. Remediation re-runs (v0.1.1 and beyond)

When gaps surfaced by a scored run are fixed in the rules-under-test, the
benchmark may be re-run to measure the effect -- but never by editing the
baseline's ground truth, scanned paths, or scoring rules. A remediation
re-run:

- Re-uses `ground-truth.csv` and the pinned DVAA/DVMCP target commits
  **unchanged**. Only the Noviscent rule commit changes.
- Gets its own manifest (`benchmark-manifest-v0.1.1.json`, etc.), its own
  evidence directory (`evidence/sarif-v0.1.1/`, etc.), and its own triage log
  (`evidence/logs/triage-log-v0.1.1.csv`), manually rebuilt from scratch from the regenerated raw findings --
  every finding is re-verified against ground truth, not assumed fixed just
  because a code change targeted it.
- Never overwrites the baseline evidence (`evidence/sarif/`,
  `evidence/logs/triage-log.csv`, `benchmark-manifest.json`). Both are
  published side by side so a reader can see exactly what changed and verify
  either one independently.
- Follows the same 3-run reproducibility requirement and the same metric
  definitions (Section 7) as the baseline.

## 10. Non-negotiable rules carried over from the ticket

- Runtime-only vulnerabilities are never counted as false negatives for a static
  scanner.
- No scenario was selected because Noviscent was already known to detect it — the
  scenario set (`ground-truth.csv`) was frozen before any scan ran.
- No percentage is published without its numerator, denominator, and underlying
  evidence.
- No "OWASP certified/approved/endorsed/validated/verified" language is used anywhere
  in this benchmark's outputs.
