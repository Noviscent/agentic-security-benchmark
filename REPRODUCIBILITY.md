# Reproducibility — read this before citing any number in this package

"Reproducible" is doing three different jobs in security-benchmark marketing,
and conflating them is how honest evidence turns into an overclaim. This
package supports two of the three. Here they are, kept separate on purpose.

## Layer 1 — Publicly inspectable evidence discipline

**What it means:** the methodology, ground truth, redacted raw scanner output, triage
log, and limitations are all here, in the open, for anyone to read and check
our arithmetic against.

**What this package supports:** yes, fully. You can read `methodology/`,
and re-derive every published number yourself by running
`scripts/score-results.py` against `evidence/triage/*.csv` and the raw JSON
in `evidence/raw/` — the scoring arithmetic is public and requires no access
to the private scanner.

**What this does NOT mean:** that the underlying scan was correct, that the
scanner would produce the same result today, or that anyone other than
Noviscent has run anything. It also does not mean the pre-scan chronology
(ground truth frozen before scanning) is independently verifiable — that
freeze happened in a private repository, so you're trusting Noviscent's
account of the order of events, not watching it happen. See `provenance.md`,
"On independently verifying this chronology."

## Layer 2 — Hash-indexed integrity evidence (not yet cryptographically anchored)

**What it means, precisely:** every file in this package has a recorded
sha256 hash (`evidence/hashes/file-hashes.txt`), and that hash file itself
has a checksum (`evidence/hashes/bundle-checksum.txt`). This lets anyone
detect an **uncoordinated** change — someone other than Noviscent editing a
published file, or a file getting corrupted in transit — because the edited
file's hash won't match the recorded one.

**What this package supports:** that, and only that. Run `python3
scripts/verify-integrity.py verify` (see `provenance.md`) to check every
declared hash against what's actually committed to this repository's git
history, not just a filesystem copy.

**What this explicitly does NOT mean, and where the phrase "tamper-evident"
oversells it:** a checksum stored *beside* the files it checks does not
protect against the **publisher** changing both together. If Noviscent
edits a result file, `file-hashes.txt`, and `bundle-checksum.txt` in the
same commit, every check above still passes — nothing here stops Noviscent
from updating its own record of itself. Git history is a partial mitigation
(old commits are still inspectable and diffable), but git history can
itself be force-pushed over in a repository Noviscent controls, so it isn't
a strong guarantee either. **This package currently gives you hash-indexed
integrity evidence: a way to detect uncoordinated tampering by a third
party, and a way to diff any two versions of this package against each
other.** It does not currently give you a cryptographically anchored
guarantee that the current published state matches what was true at
original publication time.

**A hash also proves nothing about correctness either way** — a matching
hash means the file is unchanged since it was hashed, not that the scan
behind it was accurate, complete, or representative. Two separate limits,
both real: (1) unchanged-since-hashed is not the same as
publisher-cannot-quietly-change-it, and (2) unchanged is not the same as
correct. We say **"hash-indexed integrity evidence"** here, not "verifiable
results" and not, without qualification, "tamper-evident" — those are
stronger claims than what's actually built today.

**What a real tamper-evident architecture would require** (not yet built —
listed here as the target, not as something this package claims to already
be):

```
evidence files
      ↓
file-hashes.txt
      ↓
bundle-checksum
      ↓
signed annotated git tag or signed GitHub release, over the exact publication commit
      ↓
a Sigstore/cosign signature or GitHub attestation over the bundle, ideally
      ↓
that immutable digest published somewhere OUTSIDE this mutable package
      (e.g. the noviscent.com research page, a release notes page a
      different system controls) — so a reader has an anchor Noviscent
      itself can't quietly move
```

Until that exists, prefer **"hash-indexed integrity evidence"** or
**"content checksums for detecting uncoordinated changes"** over
"tamper-evident evidence package" in any external-facing copy.

## Layer 3 — Independent reproduction

**What it means:** someone who is not Noviscent takes a frozen build of the
Noviscent scanner (not source access — a frozen, identified build), runs it
themselves against a defined protocol, and reports what they observed,
without Noviscent controlling the execution.

**What this package supports: no, not yet.** The Noviscent scanner (the
actual Semgrep rule source under `backend/packs/`) is proprietary and is not
included here. Nobody outside Noviscent can currently run this benchmark
themselves and get a scanner result, because they don't have the scanner. The
target checkouts, ground truth, and scoring methodology *are* independently
reproducible — but the detection step in the middle is not, today.

**This is the next step, not something already done.** See
`REPRODUCIBILITY.md` for what would need to be true before Layer 3 is real:
a frozen, identified Noviscent build; an evaluator who is not Noviscent;
a protocol written and frozen *before* that evaluator's first scored run;
and a result retained regardless of whether it's flattering.

## The rule this file exists to enforce

Do not describe this benchmark as "independently reproducible," "third-party
verified," or similar while Layer 3 isn't true. Do not describe the evidence
bundle as "tamper-evident" without the Layer 2 qualification above — it is
hash-indexed integrity evidence today, not a cryptographically anchored
guarantee. It is honest and still genuinely useful to say: "the methodology
and evidence are publicly inspectable, and hash-indexed so uncoordinated
changes are detectable; independent execution is the planned next step, not
yet complete." That sentence is accurate. Shortening it to
"reproducible" is not.
