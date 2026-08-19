#!/usr/bin/env python3
"""
Parses every tracked .json and .csv file in this package and fails loudly
on the first one that doesn't parse. Catches a hand-edited JSON manifest or
a malformed CSV before it reaches CI's other gates (which assume valid
input and may fail with a confusing error, or silently skip a broken file).

Usage (run from this directory, i.e. the package root):
    python3 scripts/syntax-check.py
"""
import csv
import json
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


def git_tracked_files():
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", str(PACKAGE_REL)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return sorted(
        Path(p).relative_to(PACKAGE_REL).as_posix()
        for p in out.stdout.splitlines() if p
    )


def main():
    failures = []
    checked = 0
    for rel_path in git_tracked_files():
        full = PACKAGE_ROOT / rel_path
        if rel_path.endswith(".json"):
            checked += 1
            try:
                json.loads(full.read_text())
            except json.JSONDecodeError as e:
                failures.append(f"{rel_path}: invalid JSON -- {e}")
        elif rel_path.endswith(".csv"):
            checked += 1
            try:
                with open(full, newline="") as f:
                    rows = list(csv.reader(f))
                if not rows:
                    failures.append(f"{rel_path}: empty CSV")
                else:
                    width = len(rows[0])
                    for i, row in enumerate(rows[1:], start=2):
                        if len(row) != width:
                            failures.append(
                                f"{rel_path}:{i}: row has {len(row)} columns, header has {width}"
                            )
            except csv.Error as e:
                failures.append(f"{rel_path}: invalid CSV -- {e}")

    print(f"Checked {checked} JSON/CSV files.")
    if failures:
        print("\nSyntax check FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)
    print("Syntax check PASSED.")


if __name__ == "__main__":
    main()
