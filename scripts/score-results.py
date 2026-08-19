#!/usr/bin/env python3
"""
Scores Noviscent Engine A scanner output against ground-truth.csv for the
Noviscent Agentic AI Security Benchmark v0.1.

This script only *aggregates and computes*. TP/FN/Partial/OOS classification
per scenario, and FP/true-additional-finding triage for out-of-ground-truth
findings, is a human judgment call recorded in ground-truth.csv's
`static_scope` column and in evidence/triage/triage-log-baseline-reconciled.csv
(or the v0.1.1 equivalent) respectively.
This script's job is to (a) diff the three raw run outputs for finding-set
repeatability -- for BOTH scanner components (semgrep and gitleaks), and
(b) compute metrics from a completed triage log using unit-consistent
definitions (see methodology/protocol-current.md section 7).

Metric definitions (unit-consistent, see methodology/protocol-current.md):
  Scenario recall = unique TP scenario IDs / (unique TP scenario IDs + FN scenarios)
    -- both numerator and denominator are *scenarios*. Computed from the
       distinct scenario_id values among TP rows and the FN rows.
  Finding-level alert precision = (TP_findings + TrueAdditional) / (TP_findings + TrueAdditional + FP)
    -- all of TP_findings, TrueAdditional, and FP are *individual findings*.
       This is the conventional precision: of all alerts raised, what fraction
       pointed at a real vulnerability (whether it matched a scenario or was
       a true additional finding). NEEDS_REVIEW is reported separately and
       excluded from the denominator.
  Extra-finding validation rate = TrueAdditional / (TrueAdditional + FP)
    -- precision among alerts that fell *outside* the pre-declared scenario
       matches. A stricter view: of alerts that were NOT scenario TPs, what
       fraction was still a real vulnerability?
  No combined F1 is published: scenario recall and finding-level alert
  precision are computed over different populations (scenarios vs. findings),
  so a single F1 over mixed units would not be a defensible standard metric.

Usage:
    score-results.py --sarif-dir evidence/raw/baseline --triage evidence/triage/triage-log-baseline-reconciled.csv --score
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def load_semgrep_findings(path: Path):
    """Load semgrep JSON output ({"results": [...]} schema)."""
    data = json.loads(path.read_text())
    findings = []
    for r in data.get("results", []):
        findings.append(
            {
                "check_id": r.get("check_id"),
                "path": r.get("path"),
                "start_line": r.get("start", {}).get("line"),
                "end_line": r.get("end", {}).get("line"),
                "severity": r.get("extra", {}).get("severity"),
            }
        )
    return findings


def load_gitleaks_findings(path: Path):
    """Load gitleaks JSON output (a top-level JSON array of finding objects)."""
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array, got {type(data).__name__}")
    findings = []
    for r in data:
        findings.append(
            {
                "rule_id": r.get("RuleID"),
                "path": (r.get("File") or r.get("file") or r.get("path")),
                "start_line": r.get("StartLine"),
                "end_line": r.get("EndLine"),
            }
        )
    return findings


def semgrep_key(f):
    # Normalize check_id: semgrep may emit either a dotted path
    # (backend.packs.tool-safety...) or a flattened path
    # (e.g. a Windows-style flattened path) depending on how the
    # config was specified. The rule's short id (last segment) is stable.
    cid = f["check_id"]
    if "." in cid:
        cid = cid.rsplit(".", 1)[-1]
    # Include severity per methodology/protocol-current.md section 6: "same rule IDs, same
    # file:line locations, same severities". Gitleaks findings do not
    # carry a severity field, so severity is only included for semgrep.
    return (cid, f["path"], f["start_line"], f["end_line"], f.get("severity"))


def gitleaks_key(f):
    return (f["rule_id"], f["path"], f["start_line"], f["end_line"])


def normalize_rule_id(check_id: str) -> str:
    """'backend.packs.tool-safety.rules.semgrep.tools003-js-command-injection'
    -> 'tools003-js-command-injection'. Gitleaks RuleIDs already have no dots."""
    return check_id.rsplit(".", 1)[-1] if check_id else check_id


# Map all known target-root directory names to canonical probe names.
# Different run environments use different checkout directory names:
#   - Linux container run:  dvaa-probe/  dvmcp-probe/
#   - Windows local run:    damn-vulnerable-ai-agent/  damn-vulnerable-MCP-server/
#   - WSL run:              damn-vulnerable-ai-agent/  damn-vulnerable-MCP-server/
# The canonical form used in triage-log.csv is dvaa-probe/ and dvmcp-probe/.
PROBE_ROOT_MAP = {
    "dvaa-probe/": "dvaa-probe/",
    "dvmcp-probe/": "dvmcp-probe/",
    "damn-vulnerable-ai-agent/": "dvaa-probe/",
    "damn-vulnerable-MCP-server/": "dvmcp-probe/",
    "dvaa/": "dvaa-probe/",
    "dvmcp/": "dvmcp-probe/",
}


def normalize_path(path: str) -> str:
    """Strip a run's absolute/machine-specific prefix down to the
    probe-relative path (e.g. '<run-specific-prefix>/dvaa-probe/scenarios/x/y.py'
    -> 'dvaa-probe/scenarios/x/y.py'), matching triage-log.csv's `file`
    column. Raw scanner output paths are tied to whatever machine produced
    them; the canonical key must not depend on that prefix.
    Also maps alternative checkout directory names (damn-vulnerable-ai-agent,
    damn-vulnerable-MCP-server) to the canonical probe names (dvaa-probe,
    dvmcp-probe) so the same triage log reconciles regardless of which
    environment produced the raw output."""
    if not path:
        return path
    normalized = path.replace("\\", "/")
    for root, canonical in PROBE_ROOT_MAP.items():
        idx = normalized.find(root)
        if idx != -1:
            return canonical + normalized[idx + len(root):]
    return normalized


def canonical_key(scanner: str, rule_id: str, path: str, line):
    return (scanner, normalize_rule_id(rule_id), normalize_path(path), str(line) if line is not None else line)


def reconcile_triage_with_raw(sarif_dir: Path, triage_csv: Path):
    """Verify the triage ledger is a 1:1 mapping onto the raw scanner output:
    every triaged (tp_finding/extra) row corresponds to exactly one raw
    finding, no raw finding is triaged more than once, and no raw finding is
    left untriaged. Uses run1 as the canonical raw finding set (the
    repeatability check above already establishes run1/run2/run3 are
    identical finding sets; if they were not, repeatability would already
    have failed the benchmark before scoring is meaningful).

    Row types 'scenario' (FN/PARTIAL) are excluded: they represent an
    ABSENCE of a finding (a miss), so by definition they have no raw finding
    to reconcile against.
    """
    from collections import Counter

    raw_counter: Counter = Counter()
    for f in load_semgrep_findings(sarif_dir / "run1.json"):
        raw_counter[canonical_key("semgrep", f["check_id"], f["path"], f["start_line"])] += 1
    for f in load_gitleaks_findings(sarif_dir / "run1.gitleaks.json"):
        raw_counter[canonical_key("gitleaks", f["rule_id"], f["path"], f["start_line"])] += 1

    triage_counter: Counter = Counter()
    triage_rows_by_key = {}
    with open(triage_csv, newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if row.get("row_type", "").strip() not in ("tp_finding", "extra"):
                continue
            key = canonical_key(row.get("scanner", ""), row.get("rule_id", ""), row.get("file", ""), row.get("line", "").strip())
            triage_counter[key] += 1
            triage_rows_by_key.setdefault(key, []).append(i + 2)  # +2: header + 1-index

    untriaged = raw_counter - triage_counter  # raw findings with no (or too few) triage rows
    phantom = triage_counter - raw_counter  # triage rows with no (or too many) matching raw finding
    duplicated = {k: c for k, c in triage_counter.items() if c > 1 and raw_counter.get(k, 0) < c}

    ok = not untriaged and not phantom

    return {
        "raw_finding_count": sum(raw_counter.values()),
        "triaged_finding_count": sum(triage_counter.values()),
        "reconciled": ok,
        "untriaged_raw_findings": sorted(f"{k} x{c}" for k, c in untriaged.items()),
        "phantom_triage_rows": [
            {"key": str(k), "csv_lines": triage_rows_by_key.get(k, [])} for k in sorted(phantom, key=str)
        ],
        "duplicate_triage_of_same_finding": [
            {"key": str(k), "csv_lines": triage_rows_by_key.get(k, [])} for k in sorted(duplicated, key=str)
        ],
    }


def check_reproducibility(run_paths, loader, key_fn, label):
    from collections import Counter
    # Use Counter (not set) so an exact duplicate finding disappearing between
    # runs cannot be hidden by set deduplication. E.g. if run1 has finding X
    # twice and run2 has it once, a set would say "identical" but a Counter
    # correctly reports a mismatch.
    runs = [Counter(key_fn(f) for f in loader(p)) for p in run_paths]
    base = runs[0]
    all_equal = all(r == base for r in runs[1:])
    # Union = max count across runs for each key; intersection = min count.
    # Unstable findings = keys where the count differs across runs.
    union = Counter()
    intersection = Counter()
    for k in set().union(*[set(r) for r in runs]):
        counts = [r.get(k, 0) for r in runs]
        union[k] = max(counts)
        intersection[k] = min(counts)
    unstable = {k: union[k] - intersection[k] for k in union if union[k] != intersection[k]}
    return {
        "scanner": label,
        "runs": [sum(r.values()) for r in runs],
        "identical_across_runs": all_equal,
        "union_size": sum(union.values()),
        "intersection_size": sum(intersection.values()),
        "unstable_findings": sorted(f"{k} x{c}" for k, c in unstable.items()),
    }


def score_triage(triage_csv: Path):
    """Compute metrics from triage-log.csv.

    The triage log has three row types:
      - tp_finding: individual finding matching a scenario root cause (outcome=TP)
      - scenario:  scenario-level row for FN or PARTIAL (no individual finding)
      - extra:     individual finding outside all scenario root causes
                   (outcome=FP, TRUE_ADDITIONAL, or NEEDS_REVIEW)
    """
    tp_findings = 0
    fn_scenarios = 0
    partial = 0
    oos = 0
    fp = 0
    true_additional = 0
    needs_review = 0
    tp_scenario_ids = set()

    with open(triage_csv, newline="") as f:
        for row in csv.DictReader(f):
            outcome = row.get("outcome", "").strip().upper()
            row_type = row.get("row_type", "").strip()
            if outcome == "TP":
                tp_findings += 1
                sid = row.get("scenario_id", "").strip()
                if sid:
                    tp_scenario_ids.add(sid)
            elif outcome == "FN":
                fn_scenarios += 1
            elif outcome == "PARTIAL":
                partial += 1
            elif outcome == "OOS":
                oos += 1
            elif outcome == "FP":
                fp += 1
            elif outcome == "TRUE_ADDITIONAL":
                true_additional += 1
            elif outcome == "NEEDS_REVIEW":
                needs_review += 1

    tp_scenarios = len(tp_scenario_ids)

    # Scenario recall: scenario-level (unique TP scenario IDs / (TP + FN) scenarios)
    scenario_recall = tp_scenarios / (tp_scenarios + fn_scenarios) if (tp_scenarios + fn_scenarios) else float("nan")

    # Finding-level alert precision: finding-level (all valid alerts / all alerts)
    valid_alerts = tp_findings + true_additional
    all_alerts = valid_alerts + fp
    finding_precision = valid_alerts / all_alerts if all_alerts else float("nan")

    # Extra-finding validation rate: TrueAdditional / (TrueAdditional + FP)
    extra_denom = true_additional + fp
    extra_validation_rate = true_additional / extra_denom if extra_denom else float("nan")

    return {
        "TP_findings": tp_findings,
        "TP_scenario_ids": sorted(tp_scenario_ids),
        "TP_scenarios": tp_scenarios,
        "FN_scenarios": fn_scenarios,
        "Partial": partial,
        "OOS": oos,
        "FP_findings": fp,
        "TrueAdditional_findings": true_additional,
        "NeedsReview_findings": needs_review,
        "ScenarioRecall": scenario_recall,
        "ScenarioRecall_str": f"{tp_scenarios}/{tp_scenarios + fn_scenarios} = {scenario_recall:.1%}" if (tp_scenarios + fn_scenarios) else "n/a",
        "FindingLevelAlertPrecision": finding_precision,
        "FindingLevelAlertPrecision_str": f"{valid_alerts}/{all_alerts} = {finding_precision:.1%}" if all_alerts else "n/a",
        "ExtraFindingValidationRate": extra_validation_rate,
        "ExtraFindingValidationRate_str": f"{true_additional}/{extra_denom} = {extra_validation_rate:.1%}" if extra_denom else "n/a",
        "Note": (
            "No combined F1 is reported: scenario recall and finding-level alert "
            "precision are computed over different populations (scenarios vs. "
            "individual findings); a mixed-unit F1 would not be a defensible "
            "standard metric. See methodology/protocol-current.md section 7."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sarif-dir", type=Path, required=True,
                    help="dir containing run1.json, run2.json, run3.json (semgrep) "
                         "and run1.gitleaks.json, run2.gitleaks.json, run3.gitleaks.json")
    ap.add_argument("--triage", type=Path,
                    help="triage-log.csv with 'row_type' and 'outcome' columns. Required for scoring.")
    ap.add_argument("--score", action="store_true",
                    help="Require scoring. If set and --triage is missing/absent, exit non-zero.")
    args = ap.parse_args()

    semgrep_paths = [args.sarif_dir / f"run{i}.json" for i in (1, 2, 3)]
    gitleaks_paths = [args.sarif_dir / f"run{i}.gitleaks.json" for i in (1, 2, 3)]

    missing = [p for p in semgrep_paths if not p.exists()]
    if missing:
        print(f"Missing semgrep run files: {missing}", file=sys.stderr)
        sys.exit(1)
    missing_gl = [p for p in gitleaks_paths if not p.exists()]
    if missing_gl:
        print(f"Missing gitleaks run files: {missing_gl}", file=sys.stderr)
        sys.exit(1)

    print("=== Repeatability (3 runs, same scanner version, same host) ===")
    repro_sg = check_reproducibility(semgrep_paths, load_semgrep_findings, semgrep_key, "semgrep")
    print(json.dumps(repro_sg, indent=2))
    repro_gl = check_reproducibility(gitleaks_paths, load_gitleaks_findings, gitleaks_key, "gitleaks")
    print(json.dumps(repro_gl, indent=2))

    # Hard gate: scoring is meaningless if the scanner output is not
    # repeatable across runs. Fail loudly rather than computing metrics
    # from a non-deterministic finding set.
    if not repro_sg["identical_across_runs"] or not repro_gl["identical_across_runs"]:
        print(
            "\nERROR: repeatability check FAILED -- scanner output differs across "
            "runs. Metrics computed from non-repeatable output are not trustworthy. "
            "Scoring aborted.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.triage and args.triage.exists():
        print("\n=== Triage/raw-output reconciliation ===")
        reconciliation = reconcile_triage_with_raw(args.sarif_dir, args.triage)
        print(json.dumps(reconciliation, indent=2))
        if not reconciliation["reconciled"]:
            print(
                "\nERROR: triage-log.csv does not reconcile 1:1 against run1's raw scanner "
                "output (see untriaged_raw_findings / phantom_triage_rows above). Metrics "
                "below are NOT trustworthy until this is fixed -- scoring aborted.",
                file=sys.stderr,
            )
            sys.exit(1)

        print("\n=== Scoring ===")
        print(json.dumps(score_triage(args.triage), indent=2))
    elif args.score:
        print(f"\nERROR: --score requested but triage log not found at {args.triage}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n(No --triage supplied; skipping scoring. Repeatability check only.)")


if __name__ == "__main__":
    main()
