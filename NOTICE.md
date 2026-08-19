# Third-party notices

This repository's raw evidence (`evidence/raw/`) contains scanner findings —
file paths, line numbers, and short code excerpts embedded in scanner
messages — produced by running third-party static analysis tools against
third-party target codebases. Those targets are not redistributed here in
full; only the specific findings (and, where a scanner's own output embeds
one, short surrounding context) are included as evidence of what the scanner
reported.

## Target codebases

### Damn Vulnerable AI Agent (DVAA)

- **Source:** https://github.com/opena2a-org/damn-vulnerable-ai-agent
- **License declared at the pinned commit:** `package.json`'s `license`
  field explicitly declares `"Apache-2.0"` (checked directly against
  `c3dd6c738cd5f225084867ff3d61b048515c4e3a` — this is package metadata the
  project author committed, not a rendered README badge). **No `LICENSE`
  file exists at the pinned commit**, however — checked directly and
  confirmed absent, not merely unlinked. Package metadata declaring a
  license is stronger evidence than a badge, but it is still not the same
  as a filed license grant. **License caveat:** no actual `LICENSE` file
  exists at the pinned commit. The `package.json` `license` field declaring
  `"Apache-2.0"` is package metadata the project author committed, not a
  filed license grant. This is noted here for provenance completeness; the
  target codebase is not redistributed in this repository (only scanner
  findings referencing it by path and line number are included).
- **Commit pinned for this benchmark:** `c3dd6c738cd5f225084867ff3d61b048515c4e3a`
- **Use in this repository:** referenced by relative path and line number in
  scanner findings and the ground-truth/triage tables; not copied in full.

### Damn Vulnerable MCP Server (DVMCP)

- **Source:** https://github.com/harishsg993010/damn-vulnerable-MCP-server
- **License declared at the pinned commit:** the project's `README.md`
  states, in prose (not a badge image), "This project is licensed under the
  MIT License - see the LICENSE file for details" (verified directly at
  `79734c19f5104cd11486c90926d245560f53befa`). **No `LICENSE` file actually
  exists at that commit** — checked directly and confirmed absent, so the
  README's own pointer to it is broken. **License caveat:** same as above
  — the README statement pointing at a missing LICENSE file is a signal,
  not a filed license grant. The target codebase is not redistributed in
  this repository.
- **Commit pinned for this benchmark:** `79734c19f5104cd11486c90926d245560f53befa`
- **Use in this repository:** referenced by relative path and line number in
  scanner findings and the ground-truth/triage tables; not copied in full.

Both projects are deliberately-vulnerable, intentionally-public educational
codebases built for exactly this kind of security-tool evaluation. The
fictional secrets, tokens, and credentials that appear in scanner findings
below (e.g. `AKIAIOSFODNN7EXAMPLE`, AWS's own published example access key
format; `sk_live_51NxEcT...`, a demo Stripe API key format) are demo
fixtures embedded in those target repositories as part of their intended
vulnerability scenarios — not real credentials, and not Noviscent's. The
literal Stripe key strings have been redacted in the published gitleaks
JSON to pass GitHub Push Protection; see `SECURITY.md` and
`evidence/redaction-manifest.json` (round 5).

## Scanners

- **Semgrep** (semgrep.dev) — used under its own license terms; not
  redistributed here. Only its JSON/SARIF *output* against the pinned
  targets, run through Noviscent's private detection packs, is included.
- **Gitleaks** (github.com/gitleaks/gitleaks) — used under its own license
  terms (MIT); not redistributed here. Only its JSON output against the
  pinned targets is included.

## Taxonomy references

Results are cross-referenced against the **OWASP Top 10 for Agentic
Applications (2026)**, published by the OWASP GenAI Security Project
(genai.owasp.org). This cross-reference is for legibility only. It is not an
OWASP-run validation, certification, or endorsement, and OWASP has not
reviewed or approved this repository's content.

## Noviscent's own content

Copyright 2026 Noviscent Inc.

Everything else in this repository — the protocol, ground truth, results
narratives, triage judgments and rationale, manifests, scripts, and this
notice — is Noviscent-authored and covered by the Apache License, Version 2.0
(see `LICENSE`). The license covers the Noviscent-authored content of this
repository. It does NOT cover third-party material referenced or reproduced
here — the target codebases, scanner outputs, and taxonomy references listed
above are governed by their respective licenses and terms.

**Not included:** Noviscent's detection rule source code (the Semgrep
pattern files under `backend/packs/` in Noviscent's private AI-SAST repository).
See `SECURITY.md` for why.
