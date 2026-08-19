# Contributing

This repository is an evidence package, not a general-purpose software
project. Contributions are welcome but scoped.

## Reporting errors

If you find an arithmetic, methodology, or provenance error:

1. Open a GitHub issue describing the error with specific file paths and
   line numbers.
2. If you can re-derive the correct number using
   `scripts/score-results.py`, include the expected vs. actual result.
3. Do not open a pull request that silently overwrites a published result —
   see `MAINTENANCE.md` for the evidence correction policy.

## Suggesting improvements

Non-sensitive improvements to documentation, scripts, or methodology
exposition are welcome via pull request. All pull requests must pass the
`Publication checks` CI workflow before merge.

## Security disclosures

Do not open a public issue for security vulnerabilities in Noviscent's
product or infrastructure. See `SECURITY.md` for the disclosure process.

## What this repository does not accept

- Changes to published evidence artifacts (raw scanner output, triage
  logs) without a documented correction commit.
- Addition of Noviscent's proprietary detection rule source.
- Marketing material or external outreach drafts.
- Changes that weaken or remove disclosed limitations.
