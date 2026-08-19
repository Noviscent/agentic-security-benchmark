# Remediation result (v0.1.1)

**This is still a Noviscent-run benchmark, not an OWASP-run validation,
certification, or endorsement — the same disclaimer applies to every number
below.**

**This is a same-corpus regression/remediation result, not independent
validation.** Every gap the baseline exposed was root-caused and the
detection logic updated (privately — see `SECURITY.md`); the benchmark was
then re-run against the **same frozen ground truth and the same target
commits** used for the baseline. Nothing about what counts as a hit changed
between rounds. This demonstrates that Noviscent closed the gaps it found in
itself — it does not demonstrate generalization to an unseen corpus or
independent confirmation by anyone outside Noviscent. See
`REPRODUCIBILITY.md`.

## Headline

> **Scenario recall: 12/12 (100%)**, up from 4/12 (33.3%) at baseline.
> **Finding-level alert precision: 89/93 = 95.7%**, up from 70.9%.
> **Extra-finding validation rate: 45/49 = 91.8%**, up from 60.3%.
> **100% finding-set repeatability** across 3 runs under identical configuration, both
> scanner components.

## What changed, at the class level

(Root cause and remediation class only — not exact rule logic; see
`SECURITY.md`.)

| Baseline gap | Root-cause class | Remediation class | Result |
|---|---|---|---|
| 0/6 command-injection sinks caught | Detection was scoped too narrowly to specific framework call shapes | Broadened the recognized input-source shape; added missing sink functions | 6/6 now caught |
| Missed a dynamic-eval call in an MCP tool | Decorator-shape recognition was framework-specific | Added a generic tool-decorator match; added a temp-file-execute sink | All previously-missed eval/exec sinks now caught |
| Missed an agent-delegation privilege-escalation pattern | Detection was single-framework, Python-only | Added a framework-agnostic pattern covering the actual language/transport used | Scenario now caught |
| Missed an unvalidated-read path-traversal pattern | Same input-source narrowness as the command-injection gap | Same fix | Scenario now caught, plus 6 new true-additional path-traversal findings elsewhere in the corpus |
| Heuristic rule caused 19 of 23 baseline false positives | Over-broad match condition | Added a narrowing constraint | 0 false positives from this rule in the full re-run |
| No detection for MCP tool-description "poisoning" | No rule existed | New rule added for this detection class | Scenario now caught, plus 4 new true-additional instances found elsewhere that weren't part of any declared scenario |
| No coverage for generic piped-install pattern | Existing bash-rule coverage was narrow | New rule added for this detection class | Scenario now caught |

## Repeatability (v0.1.1)

- semgrep: 62/62/62 unique findings, **100% identical across all 3 runs**.
- gitleaks: 36/36/36 unique findings, **100% identical across all 3 runs**
  (unchanged from baseline).

Redacted copies of the raw output for all 3 runs (see `evidence/redaction-manifest.json` for what was transformed and why): `evidence/raw/v0.1.1/`.

## Full triage

`evidence/triage/triage-log-v0.1.1.csv` — 98 raw findings, 98 triaged rows,
zero untriaged/phantom/duplicate (verified by reconciling the triage log
against raw scanner output 1:1).

## What is still not perfect

- 4 remaining false positives from a rule outside this remediation's scope.
- 5 findings deliberately marked needs-review rather than resolved either
  way, erring toward the conservative label.
- A separate, larger, pre-existing quality gap: auditing the full Noviscent
  rule-pack test suite (unrelated to this specific benchmark) found a number
  of rules with non-functional or missing positive test fixtures. This is
  real, disclosed, and tracked as follow-up work — not part of this
  benchmark's scope, and not hidden because it's inconvenient.

## What this result is not

- Not an unseen holdout corpus.
- Not independently executed by anyone outside Noviscent.
- Not evidence that the fixes generalize beyond DVAA/DVMCP.

The next validation step — an unseen external corpus and independent
execution — is described in `REPRODUCIBILITY.md` and has not yet happened.
