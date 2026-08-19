#!/usr/bin/env python3
"""
Golden-metrics check for CI: re-runs scripts/score-results.py for both the
baseline and v0.1.1 rounds and asserts the computed metrics exactly match
the numbers published in results/baseline.md and results/remediation-v0.1.1.md.

This is a regression gate for the published package itself -- it does not
re-run any scanner and does not touch scanner rules. It exists so that a
future edit to a triage CSV, a raw JSON file, or score-results.py's own
arithmetic cannot silently drift the published numbers without CI noticing.

Usage (run from this directory, i.e. the package root):
    python3 scripts/golden-metrics-check.py
"""
import json
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

# The exact published numbers, as they appear in results/baseline.md and
# results/remediation-v0.1.1.md at the time this gate was written. If a
# future, deliberate re-scoring changes a published number, update this
# dict in the same commit that updates the .md files -- never the other
# way around.
GOLDEN = {
    "baseline": {
        "sarif_dir": "evidence/raw/baseline",
        "triage": "evidence/triage/triage-log-baseline-reconciled.csv",
        "expected": {
            "TP_findings": 21,
            "FP_findings": 23,
            "TrueAdditional_findings": 35,
            "NeedsReview_findings": 2,
            "ScenarioRecall_str": "4/12 = 33.3%",
            "FindingLevelAlertPrecision_str": "56/79 = 70.9%",
            "ExtraFindingValidationRate_str": "35/58 = 60.3%",
        },
    },
    "v0.1.1": {
        "sarif_dir": "evidence/raw/v0.1.1",
        "triage": "evidence/triage/triage-log-v0.1.1.csv",
        "expected": {
            "TP_findings": 44,
            "FP_findings": 4,
            "TrueAdditional_findings": 45,
            "NeedsReview_findings": 5,
            "ScenarioRecall_str": "12/12 = 100.0%",
            "FindingLevelAlertPrecision_str": "89/93 = 95.7%",
            "ExtraFindingValidationRate_str": "45/49 = 91.8%",
        },
    },
}


def run_scorer(sarif_dir: str, triage: str):
    proc = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "scripts" / "score-results.py"),
         "--sarif-dir", str(PACKAGE_ROOT / sarif_dir),
         "--triage", str(PACKAGE_ROOT / triage),
         "--score"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"score-results.py exited {proc.returncode} for {sarif_dir}")
    # The scorer prints several JSON blocks under "=== ... ===" headers;
    # the scoring block is the last one.
    blocks = proc.stdout.split("=== Scoring ===")
    if len(blocks) != 2:
        print(proc.stdout)
        raise SystemExit(f"could not find '=== Scoring ===' block in scorer output for {sarif_dir}")
    return json.loads(blocks[1])


def main():
    failures = []
    for round_name, cfg in GOLDEN.items():
        actual = run_scorer(cfg["sarif_dir"], cfg["triage"])
        for key, expected_value in cfg["expected"].items():
            actual_value = actual.get(key)
            if actual_value != expected_value:
                failures.append(
                    f"{round_name}.{key}: expected {expected_value!r}, got {actual_value!r}"
                )
        print(f"{round_name}: {json.dumps({k: actual.get(k) for k in cfg['expected']}, indent=2)}")

    if failures:
        print("\nGolden-metrics check FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)

    print("\nGolden-metrics check PASSED -- computed metrics match the published numbers exactly.")


if __name__ == "__main__":
    main()
