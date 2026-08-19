#!/usr/bin/env python3
"""
Publication hygiene gate for the Noviscent Agentic AI Security Benchmark
public evidence package.

Scans every tracked file (as committed to git — same discipline as
verify-integrity.py) for markers that mean "not actually ready to publish":
unresolved placeholders, leftover internal paths, internal domains, AWS
credential/ARN patterns outside the one disclosed demo fixture, private key
headers, and ClickUp URLs.

This is a hygiene gate, not a legal or security review. A clean run means
"no known leftover placeholder or leaked internal detail was found by
pattern match" -- it does not mean the content has been reviewed by a
human, and does not substitute for human judgment.

Usage (run from this directory, i.e. the package root):
    python3 scripts/publication-hygiene-check.py

Exit code 0 = clean. Exit code 1 = one or more findings (printed to stdout).
"""
import re
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], cwd=PACKAGE_ROOT,
    capture_output=True, text=True, check=True,
).stdout.strip()
REPO_ROOT = Path(REPO_ROOT)
PACKAGE_REL = PACKAGE_ROOT.relative_to(REPO_ROOT)

# The disclosed, intentional demo credential fixtures (see NOTICE.md) --
# AWS-example-format access keys embedded in DVAA/DVMCP as deliberate
# vulnerability scenarios. Not real credentials. Verified directly against
# every AKIA-prefixed string actually present in evidence/ before adding
# either entry here.
KNOWN_FIXTURE_ALLOWLIST = {"AKIAIOSFODNN7EXAMPLE", "AKIA5EXAMPLE12345678"}

# (label, compiled regex, narrative_exempt_eligible). Regexes are matched
# per-line so a finding can be reported with a line number;
# KNOWN_FIXTURE_ALLOWLIST is checked separately for the AWS-key-format
# pattern only. narrative_exempt_eligible marks the subset of patterns that
# NARRATIVE_EXEMPT_FILES is allowed to mention in disclosed, documented
# prose (see that constant below) -- every other pattern (unresolved
# placeholders, ClickUp URLs, private key headers, AWS account IDs) applies
# unconditionally to every file, including those two.
PATTERNS = [
    ("unresolved [YEAR] placeholder", re.compile(r"\[YEAR\]"), False),
    ("unremoved 'NOTE (remove before publication)' marker",
     re.compile(r"NOTE \(remove before publication\)", re.IGNORECASE), False),
    ("unresolved security-contact placeholder",
     re.compile(r"insert real disclosure address", re.IGNORECASE), False),
    ("unresolved PUBLICATION BLOCKER marker",
     re.compile(r"PUBLICATION BLOCKER"), False),
    ("unresolved [link ...] placeholder",
     re.compile(r"\[link[,\s]", re.IGNORECASE), False),
    ("TODO/TBD publication placeholder",
     re.compile(r"\b(TODO|TBD)\b.*(publish|before submitting|before publication)", re.IGNORECASE), False),
    ("absolute filesystem path (/home/)", re.compile(r"/home/[A-Za-z0-9_.\-]+"), True),
    ("absolute filesystem path (/Users/)", re.compile(r"/Users/[A-Za-z0-9_.\-]+"), True),
    ("absolute filesystem path (C:\\Users\\)", re.compile(r"C:\\\\?Users\\\\?", re.IGNORECASE), True),
    ("ephemeral agent scratch path (/tmp/claude-)", re.compile(r"/tmp/claude-"), True),
    ("leftover 'scratchpad' path fragment", re.compile(r"scratchpad"), True),
    ("internal Noviscent domain reference",
     re.compile(r"(?<![\w.-])(app|dev)\.noviscent\.ca\b|@noviscent\.(?!com\b)", re.IGNORECASE), True),
    ("ClickUp URL", re.compile(r"app\.clickup\.com|clickup\.com/t/", re.IGNORECASE), False),
    ("private key header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), False),
    # The bare-12-digit alternative is deliberately bounded against adjacent
    # hex letters too (not just digits) -- this package is full of sha256
    # hashes and git commit SHAs, which are long runs of [0-9a-f] that can
    # coincidentally contain 12 consecutive decimal digits. A real AWS
    # account ID appears in prose or an ARN, not embedded in a hex string.
    ("AWS account ID / ARN", re.compile(r"arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:|(?<![0-9a-fA-F])\d{12}(?![0-9a-fA-F])"), False),
]

AWS_ACCESS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")

# Files this gate does not scan: its own source (the patterns above would
# trip on themselves) and anything git-ignores already excludes.
SELF_EXCLUDE = {"scripts/publication-hygiene-check.py"}

# These two files intentionally, disclosedly narrate the redaction
# incidents in prose -- SECURITY.md's "Redaction pass performed before
# staging" section and redaction-manifest.json's descriptions both quote
# the actual leaked-path/domain patterns as part of documenting what was
# found and fixed (see git history for this package). That is the point of
# disclosing a mistake honestly rather than only showing the clean end
# state -- it is not itself a live leak, since the evidence files those
# incidents affected were separately transformed. Only the
# narrative_exempt_eligible patterns are exempted here, and only for these
# two files; every other pattern, and every other file (including all of
# evidence/raw/ and evidence/validation-rerun/), is still scanned
# unconditionally.
NARRATIVE_EXEMPT_FILES = {"SECURITY.md", "evidence/redaction-manifest.json"}


def git_tracked_files(repo_root: Path, package_rel: Path):
    """Every path git actually has committed under this package at HEAD,
    relative to the package root -- scoped the same way verify-integrity.py
    scopes its own git ls-tree call, so this never accidentally scans the
    whole AI-SAST superproject."""
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", str(package_rel)],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return sorted(
        Path(p).relative_to(package_rel).as_posix()
        for p in out.stdout.splitlines() if p
    )


def git_blob_text(repo_root: Path, package_rel: Path, rel_path: str):
    """Returns the committed blob's text, or None if the path doesn't
    exist at HEAD or its bytes don't decode as text under any encoding we
    try. Deliberately reads raw bytes (not subprocess text=True, which
    would raise on the first non-UTF-8 byte and abort the whole scan) --
    this package has already been caught once shipping a real leak inside
    a UTF-16 PowerShell transcript log that a UTF-8-only scan silently
    couldn't read. Tries UTF-8 first (the vast majority of this package),
    then UTF-16 (PowerShell's default stdout-redirect encoding on
    Windows, which is what run1's validation-rerun logs turned out to be)
    before giving up."""
    full_git_path = (package_rel / rel_path).as_posix()
    out = subprocess.run(
        ["git", "show", f"HEAD:{full_git_path}"],
        cwd=repo_root, capture_output=True,
    )
    if out.returncode != 0:
        return None
    for encoding in ("utf-8", "utf-16"):
        try:
            return out.stdout.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def _backtick_quoted(line: str, start: int, end: int) -> bool:
    """True if the matched span [start:end) is immediately wrapped in a
    single backtick on each side, e.g. the [YEAR] in `[YEAR]`. This is a
    deliberate Markdown authoring signal for "this is a literal pattern
    being described/quoted," not a live instance of it -- e.g. this very
    script's own documentation, or a doc explaining what a CI gate checks
    for, needs to be able to name its patterns without tripping itself.
    Does not apply to JSON files (no backtick convention there); those use
    NARRATIVE_EXEMPT_FILES instead."""
    return start > 0 and end < len(line) and line[start - 1] == "`" and line[end] == "`"


def scan_file(rel_path: str, text: str):
    exempt = rel_path in NARRATIVE_EXEMPT_FILES
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, pattern, narrative_exempt_eligible in PATTERNS:
            if exempt and narrative_exempt_eligible:
                continue
            m = pattern.search(line)
            if m and not _backtick_quoted(line, m.start(), m.end()):
                findings.append((rel_path, lineno, label, line.strip()[:160]))
        for m in AWS_ACCESS_KEY_RE.finditer(line):
            if m.group(0) not in KNOWN_FIXTURE_ALLOWLIST and not _backtick_quoted(line, m.start(), m.end()):
                findings.append((rel_path, lineno, "AWS access key ID (not the disclosed demo fixture)", line.strip()[:160]))
    return findings


def main():
    tracked = git_tracked_files(REPO_ROOT, PACKAGE_REL)
    all_findings = []
    undecodable = []
    for rel_path in tracked:
        if rel_path in SELF_EXCLUDE:
            continue
        text = git_blob_text(REPO_ROOT, PACKAGE_REL, rel_path)
        if text is None:
            undecodable.append(rel_path)
            continue
        all_findings.extend(scan_file(rel_path, text))

    if undecodable:
        print(
            f"WARNING: {len(undecodable)} tracked file(s) could not be decoded as "
            "UTF-8 or UTF-16 and were NOT scanned by this gate -- verify them by "
            "hand before publishing:"
        )
        for rel_path in undecodable:
            print(f"  {rel_path}")
        print()

    if all_findings:
        print(f"Publication hygiene check FAILED -- {len(all_findings)} finding(s):\n")
        for rel_path, lineno, label, snippet in all_findings:
            print(f"  {rel_path}:{lineno}: {label}\n    {snippet}")
        print(
            "\nThis is a pattern-match gate, not a legal or security review. "
            "A clean run does not substitute for human judgment."
        )
        sys.exit(1)

    print("Publication hygiene check PASSED -- no known placeholder/leak patterns found.")
    print(
        "Reminder: this is a pattern-match gate, not a legal or security review. "
        "Human review is still required for any substantive change."
    )


if __name__ == "__main__":
    main()
