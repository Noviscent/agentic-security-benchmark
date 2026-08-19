# Exploratory Run (NOT SCORED)

## What this is

Before the three scored runs (run1–run3) that include both semgrep and gitleaks,
an initial exploratory scan was performed using **semgrep only** (no gitleaks).
This directory documents that run's existence, purpose, observed result, and the
resulting methodology amendment.

## What happened

The exploratory semgrep-only run produced **43 findings** (the same 43 semgrep
findings as the scored runs) but **zero findings for SP001 (Hardcoded Secret
Detected)**. Inspection of the secrets-privacy pack configuration revealed
that SP001 is implemented via **gitleaks**, not semgrep — the semgrep-only run
was never going to detect hardcoded secrets.

This was the trigger for the pre-scoring execution amendment: all three scored
runs (run1–run3) include both scanners. The amendment is disclosed in the
manifest's `secondary_scanner.amendment_note` field rather than silently folded
in.

## What is and is not preserved

**The exploratory raw output was not retained.** Its observed count, purpose,
and resulting methodology amendment are documented here. Subsequent scored
Semgrep runs also produced 43 findings, but exact finding-set equivalence to
the unretained exploratory output cannot be independently verified. The
only known difference between the exploratory run and the scored runs is the
absence of gitleaks, which is the gap this directory documents.

## Why it is documented, not discarded

An earlier version of the benchmark documentation described this run as
"discarded." For an audit-style evidence artifact, documenting the messy history
makes the evidence stronger. This run is marked **NOT SCORED** — it is not
included in any metric, any triage count, or any repeatability check.
