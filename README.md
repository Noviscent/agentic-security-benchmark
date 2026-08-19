# Noviscent Agentic AI Security Benchmark

**We kept the failed result.**

Noviscent evaluated its own agentic-AI security scanner against known weaknesses
documented before the scored benchmark. The first scored baseline exposed
material detection gaps. We retained that result, remediated the gaps, and
reran the same frozen corpus. Both rounds — the weak one and the fixed one —
are published here, side by side.

**Baseline**

4 / 12 statically in-scope scenarios detected

70.9% finding-level alert precision

**Same-corpus regression after remediation**

12 / 12 scenarios detected

95.7% finding-level alert precision

> **Important:** the second result is performance on the same corpus used to
> identify and remediate the gaps. It demonstrates regression closure, not
> independent holdout validation or universal scanner accuracy.

**On chronology:** the freeze-before-scanning discipline happened inside
Noviscent's private source repository, before this public package existed.
This package is where that already-completed record is published, not where it
was originally pre-registered in public. See `provenance.md` and
`REPRODUCIBILITY.md` for exactly what an external reader can and can't
independently verify about that timeline from public history alone — and for
why a future round done as a truly public pre-registration would be a stronger
claim than this one.

The next step — an unseen external corpus and independent execution by someone
who isn't us — is described in `REPRODUCIBILITY.md` and is not yet done.

---

## Technical methodology (short version)

- **Targets:** two deliberately-vulnerable, publicly available agentic-AI/MCP
  codebases — Damn Vulnerable AI Agent (DVAA) and Damn Vulnerable MCP Server
  (DVMCP) — pinned at specific commit SHAs. See `provenance.md` for licensing
  and attribution.
- **Ground truth first:** 18 known vulnerabilities (12 statically in-scope, 6
  partial/runtime-dependent) were catalogued from target documentation and source
  review and committed *before* any scan ran. See
  [`methodology/ground-truth.csv`](./methodology/ground-truth.csv) and
  [`methodology/protocol-current.md`](./methodology/protocol-current.md) (the amended methodology matching the published results; see [`methodology/protocol-pre-scan.md`](./methodology/protocol-pre-scan.md) for the true pre-scan original and [`methodology/protocol-amendments.md`](./methodology/protocol-amendments.md) for what changed and why).
- **Two frozen rounds:** a baseline run (Noviscent Engine A at a pinned commit)
  and, after root-causing every gap the baseline exposed, a remediation re-run
  against the *same unchanged corpus and ground truth* — not a new or easier test.
- **Every finding manually triaged** against ground truth: true positive, false
  positive, true-but-off-target additional finding, or needs-review — with a
  written rationale per row. See [`evidence/triage/`](./evidence/triage/).
- **Repeatability measured, not assumed:** each round was run 3 times with
  pinned scanner versions; the normalized finding set was compared run-to-run.
  (This is within-version repeatability — same scanner, same host. Cross-version
  reproducibility, a different and stronger claim, is checked separately; see
  [`evidence/validation-rerun-notes.md`](./evidence/validation-rerun-notes.md).)
- **Every artifact pinned and hashed:** target commit SHAs, Noviscent pack
  content hashes, scanner versions, and a sha256 checksum over the whole
  evidence bundle. See [`evidence/hashes/`](./evidence/hashes/) and
  [`REPRODUCIBILITY.md`](./REPRODUCIBILITY.md) for exactly what that checksum
  does and does not prove.
- **What this repository does not include:** the Noviscent detection rule source
  (the actual Semgrep pattern/AST match files). What it does include, in the
  raw scanner output under `evidence/raw/`: each rule's own emitted message,
  title, remediation text, CWE/OWASP mapping, and confidence level — that's
  legitimate scanner-produced metadata, not withheld. What's withheld is the
  underlying pattern logic that decides *when* a rule fires — the part that
  would let someone construct code specifically to evade it. See
  [`SECURITY.md`](./SECURITY.md) and the note at the bottom of this file.

Full protocol: [`methodology/protocol-current.md`](./methodology/protocol-current.md).
Full results and discussion: [`results/baseline.md`](./results/baseline.md) and
[`results/remediation-v0.1.1.md`](./results/remediation-v0.1.1.md).
Known limitations: [`limitations.md`](./limitations.md) — read this before citing
any number from this repository.

---

## Evidence navigation

```
README.md                      — this file
LICENSE                        — Apache 2.0, covers Noviscent-authored content
NOTICE.md                      — third-party attribution (DVAA, DVMCP, scanners)
provenance.md                  — where every input artifact came from, and its license
limitations.md                 — what these numbers do and do not mean
REPRODUCIBILITY.md             — the three trust layers, and which one each artifact supports
SECURITY.md                    — vulnerability disclosure, and what's deliberately excluded
MAINTENANCE.md                 — CI, integrity workflow, change-management, and correction policy
.github/workflows/publication-checks.yml — CI: syntax, integrity, golden metrics, hygiene
methodology/
  protocol-pre-scan.md         — the exact frozen methodology, unedited, as it existed before any scan ran
  protocol-current.md          — the final, amended methodology that the published results actually match
  protocol-amendments.md       — chronological ledger of every change between the two, with commit refs and reasons
  publication-notes.md         — path mapping + a correction to the current protocol's reproducibility claim, for this package's layout
  ground-truth.csv             — the 18 pre-scan scenario predictions
  coverage-matrix.csv          — baseline: rule/category coverage vs. OWASP Top 10 for Agentic Applications (2026)
  coverage-matrix-v0.1.1.csv   — same, after remediation
results/
  baseline.md                  — first-scored-baseline result: 4/12 scenario recall, 70.9% finding-level precision
  remediation-v0.1.1.md        — same-corpus re-run after fixes: 12/12 scenario recall, 95.7% precision
scripts/
  score-results.py             — recomputes every published number from the raw output + triage log in this repo (no detection logic)
  verify-integrity.py          — verifies (or regenerates) evidence/hashes/ against bytes actually committed to git
  golden-metrics-check.py      — asserts score-results.py reproduces the exact numbers published in results/ (CI regression gate)
  syntax-check.py              — parses every tracked .json/.csv file (CI gate)
  publication-hygiene-check.py — scans every tracked file for unresolved placeholders, internal paths/domains, and credential patterns (CI gate)
evidence/
  manifests/                   — redacted, capability-level manifest per round: commit SHAs, pack hashes, scanner versions
  raw/baseline/                — redacted copies of raw scanner output, 3 runs, both scanners
  raw/v0.1.1/                  — redacted copies of raw scanner output after remediation, 3 runs, both scanners
  redaction-manifest.json      — chain of custody for every redacted file: original hash → transform → published hash
  triage/                      — row-by-row manual triage log with rationale, for both rounds
  validation-rerun/            — cross-scanner-version repeatability check (see limitations.md)
  exploratory/                 — the one exploratory pre-scoring run, marked NOT SCORED, disclosed rather than hidden
  hashes/                      — sha256 of every file above (verified against committed git bytes), and a checksum over that file list
```

**Reproducing the scoring yourself:** [`REPRODUCIBILITY.md`](./REPRODUCIBILITY.md)
draws a hard line between three different things this repository supports —
publicly inspectable evidence, hash-indexed integrity evidence (not yet a
cryptographically anchored "tamper-evident" guarantee — the file explains
exactly why), and independent reproduction — and is explicit that this
package alone supports the first two, not the third, while the Noviscent
scanner remains private. Read it before describing any result from this
repository as "reproducible" or "tamper-evident" without qualification.

---

*This is a Noviscent-run benchmark. It is not an OWASP-run validation,
certification, or endorsement. Results are cross-referenced against the OWASP
Top 10 for Agentic Applications (2026) taxonomy for legibility only.*
