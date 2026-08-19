#!/usr/bin/env python3
"""Verify (or regenerate) this package's evidence hashes against bytes
actually committed to git -- not the working-tree filesystem.

Why this exists: an earlier round of this package computed hashes by
sha256-ing the filesystem copy of each file. That missed that several
files (everything under evidence/raw/*/*.log and evidence/validation-rerun/)
were silently skipped by `git add` due to a repo-wide `*.log` .gitignore
rule, so the published hash manifest referenced files that were never
actually committed. `sha256sum` on disk cannot catch that class of bug --
only checking against `git ls-tree` / `git show HEAD:<path>` can.

A second round found `verify` itself had two more bugs of the same shape:
it read its OWN hash-index files (file-hashes.txt, bundle-checksum.txt)
from the filesystem rather than from the committed HEAD blob, so a dirty
local edit to either file could pass `verify` without anything being
committed; and the bundle-checksum comparison had a logic bug (see
`git_tracked_paths` / `verify_bundle_checksum` below) that meant it never
actually ran. Both are fixed here, and `selftest` proves it with mutation
tests run against a disposable scratch git repo -- never against this
package's own real files.

Usage (run from this directory, i.e. the package root):
    python3 scripts/verify-integrity.py verify      # fail closed on any drift, reads only committed HEAD bytes
    python3 scripts/verify-integrity.py regenerate  # rewrite the hash files from committed HEAD bytes (writes to disk; you must then commit)
    python3 scripts/verify-integrity.py selftest    # proves verify() actually catches each failure mode, using a scratch repo

`verify` reads file-hashes.txt and bundle-checksum.txt from `git show
HEAD:<path>`, not from disk -- a working-tree edit to either file, or to
any hashed file, cannot change what `verify` reports unless it's committed.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], cwd=PACKAGE_ROOT,
    capture_output=True, text=True, check=True,
).stdout.strip()
REPO_ROOT = Path(REPO_ROOT)
PACKAGE_REL = PACKAGE_ROOT.relative_to(REPO_ROOT)

HASH_FILE_REL = "evidence/hashes/file-hashes.txt"
CHECKSUM_FILE_REL = "evidence/hashes/bundle-checksum.txt"
HASH_FILE = PACKAGE_ROOT / HASH_FILE_REL
CHECKSUM_FILE = PACKAGE_ROOT / CHECKSUM_FILE_REL

# Every committed file is in scope for hashing -- this is simpler and
# less fragile than maintaining an allowlist every time a top-level
# artifact (e.g. CITATION.cff, CONTRIBUTING.md) is added. The two
# hash-index files are deliberately excluded from hashing themselves
# (see HASH_INDEX_FILES) but ARE tracked/verified paths in their own
# right.
HASH_INDEX_FILES = {HASH_FILE_REL, CHECKSUM_FILE_REL}


def run_git(args, cwd, check=True):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, check=check)


def git_tracked_paths(repo_root: Path, package_rel: Path) -> list[str]:
    """Every path git actually has committed under this package at HEAD,
    relative to the package root. Includes the hash-index files themselves
    -- callers that want to exclude them from hashing do so explicitly via
    HASH_INDEX_FILES, not by filtering them out of "tracked"."""
    out = run_git(["ls-tree", "-r", "--name-only", "HEAD", "--", str(package_rel)], cwd=repo_root).stdout.decode()
    rel = [Path(p).relative_to(package_rel).as_posix() for p in out.splitlines()]
    return sorted(rel)


def git_blob_sha256(repo_root: Path, package_rel: Path, rel_path: str) -> str:
    """sha256 of the committed blob content -- NOT the filesystem copy."""
    full_git_path = (package_rel / rel_path).as_posix()
    result = run_git(["show", f"HEAD:{full_git_path}"], cwd=repo_root)
    return hashlib.sha256(result.stdout).hexdigest()


def git_blob_text(repo_root: Path, package_rel: Path, rel_path: str) -> str:
    full_git_path = (package_rel / rel_path).as_posix()
    result = run_git(["show", f"HEAD:{full_git_path}"], cwd=repo_root)
    return result.stdout.decode()


def expected_in_scope(tracked: list[str]) -> list[str]:
    # Every committed file except the hash-index files themselves.
    return sorted(p for p in tracked if p not in HASH_INDEX_FILES)


def cmd_regenerate():
    tracked = git_tracked_paths(REPO_ROOT, PACKAGE_REL)
    in_scope = expected_in_scope(tracked)
    if not in_scope:
        print("ERROR: no in-scope committed files found -- did you forget to `git add`/commit first?", file=sys.stderr)
        sys.exit(1)
    lines = []
    for rel_path in in_scope:
        digest = git_blob_sha256(REPO_ROOT, PACKAGE_REL, rel_path)
        lines.append(f"{digest}  {rel_path}")
    HASH_FILE.write_text("\n".join(lines) + "\n")
    checksum = hashlib.sha256(HASH_FILE.read_bytes()).hexdigest()
    CHECKSUM_FILE.write_text(checksum + "\n")
    print(f"Regenerated {HASH_FILE} ({len(in_scope)} files) from committed git bytes.")
    print(f"Bundle checksum: {checksum}")
    print("NOTE: these hash files must themselves be committed, then `verify` re-run against the new HEAD, for the manifest to be valid.")


def verify(repo_root: Path, package_rel: Path) -> list[str]:
    """Core verification logic, parameterized so `selftest` can point it at
    a scratch repo instead of the real package. Returns a list of failure
    strings; empty list means clean. Reads file-hashes.txt and
    bundle-checksum.txt from the COMMITTED HEAD blob, never from disk --
    a working-tree-only edit to either file cannot change the result."""
    tracked = set(git_tracked_paths(repo_root, package_rel))

    if HASH_FILE_REL not in tracked:
        return [f"MISSING FROM GIT: {HASH_FILE_REL} itself is not committed at HEAD."]

    declared_text = git_blob_text(repo_root, package_rel, HASH_FILE_REL)
    declared = {}
    for line in declared_text.splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        declared[path] = digest

    in_scope = set(expected_in_scope(sorted(tracked)))
    failures = []

    # 1. Every declared path must actually be committed to git.
    for path in declared:
        if path not in tracked:
            failures.append(f"MISSING FROM GIT: {path} is in file-hashes.txt but `git ls-tree` does not have it at HEAD (404 if fetched from GitHub)")

    # 2. Every declared path's hash must match the committed blob.
    for path in declared:
        if path in tracked:
            actual = git_blob_sha256(repo_root, package_rel, path)
            if actual != declared[path]:
                failures.append(f"HASH MISMATCH: {path}\n  declared: {declared[path]}\n  actual (git blob): {actual}")

    # 3. Every in-scope committed file must be declared (nothing silently un-hashed).
    for path in sorted(in_scope):
        if path not in declared:
            failures.append(f"UNHASHED IN-SCOPE FILE: {path} is committed under an in-scope directory but missing from file-hashes.txt")

    # 4. The bundle checksum (read from its OWN committed blob) must equal
    #    sha256 of file-hashes.txt's committed blob. Both sides read from
    #    git, not disk -- this is the check round 2 said it ran but
    #    couldn't, because file-hashes.txt had been filtered out of
    #    `tracked` before this comparison ran.
    if CHECKSUM_FILE_REL in tracked:
        declared_bundle = git_blob_text(repo_root, package_rel, CHECKSUM_FILE_REL).strip()
        actual_bundle = hashlib.sha256(declared_text.encode()).hexdigest()
        if declared_bundle != actual_bundle:
            failures.append(f"BUNDLE CHECKSUM MISMATCH: committed bundle-checksum.txt says {declared_bundle}, sha256 of committed file-hashes.txt is {actual_bundle}")
    else:
        failures.append(f"MISSING FROM GIT: {CHECKSUM_FILE_REL} itself is not committed at HEAD.")

    return failures


def cmd_verify():
    failures = verify(REPO_ROOT, PACKAGE_REL)
    if failures:
        print(f"FAILED: {len(failures)} integrity problem(s) found against committed git bytes:\n", file=sys.stderr)
        for f in failures:
            print(f"- {f}\n", file=sys.stderr)
        sys.exit(1)
    tracked = set(git_tracked_paths(REPO_ROOT, PACKAGE_REL))
    declared_count = len(git_blob_text(REPO_ROOT, PACKAGE_REL, HASH_FILE_REL).splitlines())
    print(f"OK: {declared_count} files verified against committed git bytes at HEAD. 0 mismatches, 0 missing, 0 unhashed in-scope files. Bundle checksum verified against committed file-hashes.txt blob.")


# ---------------------------------------------------------------------------
# selftest: proves `verify()` actually catches each failure mode, using a
# disposable scratch git repo. Never touches this package's real files.
# ---------------------------------------------------------------------------

def _scratch_repo(tmp: Path) -> Path:
    pkg = tmp / "pkg"
    (pkg / "methodology").mkdir(parents=True)
    (pkg / "evidence" / "hashes").mkdir(parents=True)
    run_git(["init", "-q"], cwd=tmp)
    run_git(["config", "user.email", "test@example.com"], cwd=tmp)
    run_git(["config", "user.name", "Test"], cwd=tmp)
    return pkg


def _commit_all(tmp: Path, message: str):
    run_git(["add", "-A"], cwd=tmp)
    run_git(["commit", "-q", "-m", message], cwd=tmp)


def _build_clean_scratch(tmp: Path) -> Path:
    pkg = _scratch_repo(tmp)
    (pkg / "methodology" / "a.md").write_text("hello\n")
    _commit_all(tmp, "add content")
    lines = [f"{git_blob_sha256(tmp, Path('pkg'), 'methodology/a.md')}  methodology/a.md"]
    (pkg / "evidence" / "hashes" / "file-hashes.txt").write_text("\n".join(lines) + "\n")
    _commit_all(tmp, "add file-hashes.txt")
    hf_hash = git_blob_sha256(tmp, Path("pkg"), HASH_FILE_REL)
    (pkg / "evidence" / "hashes" / "bundle-checksum.txt").write_text(hf_hash + "\n")
    _commit_all(tmp, "add bundle-checksum.txt")
    return pkg


def _case_clean_passes() -> str | None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        _build_clean_scratch(tmp)
        failures = verify(tmp, Path("pkg"))
        if failures:
            return f"clean scratch repo unexpectedly failed: {failures}"
    return None


def _case_missing_tracked_file_fails() -> str | None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pkg = _build_clean_scratch(tmp)
        # Declare a file that was never committed.
        hf = pkg / "evidence" / "hashes" / "file-hashes.txt"
        hf.write_text(hf.read_text() + "deadbeef" * 8 + "  methodology/never-committed.md\n")
        _commit_all(tmp, "declare a phantom file")
        cf = pkg / "evidence" / "hashes" / "bundle-checksum.txt"
        cf.write_text(git_blob_sha256(tmp, Path("pkg"), HASH_FILE_REL) + "\n")
        _commit_all(tmp, "fix checksum for phantom-file test")
        failures = verify(tmp, Path("pkg"))
        if not any("MISSING FROM GIT" in f and "never-committed.md" in f for f in failures):
            return f"expected a MISSING FROM GIT failure for the phantom file, got: {failures}"
    return None


def _case_wrong_committed_hash_fails() -> str | None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pkg = _build_clean_scratch(tmp)
        (pkg / "methodology" / "a.md").write_text("tampered content\n")
        _commit_all(tmp, "tamper with a.md after hashing")
        failures = verify(tmp, Path("pkg"))
        if not any("HASH MISMATCH" in f and "methodology/a.md" in f for f in failures):
            return f"expected a HASH MISMATCH failure, got: {failures}"
    return None


def _case_wrong_bundle_checksum_fails() -> str | None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pkg = _build_clean_scratch(tmp)
        (pkg / "evidence" / "hashes" / "bundle-checksum.txt").write_text("0" * 64 + "\n")
        _commit_all(tmp, "corrupt the committed bundle checksum")
        failures = verify(tmp, Path("pkg"))
        if not any("BUNDLE CHECKSUM MISMATCH" in f for f in failures):
            return f"expected a BUNDLE CHECKSUM MISMATCH failure, got: {failures}"
    return None


def _case_dirty_working_tree_hash_file_does_not_affect_verify() -> str | None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pkg = _build_clean_scratch(tmp)
        # Edit file-hashes.txt on disk WITHOUT committing.
        (pkg / "evidence" / "hashes" / "file-hashes.txt").write_text("garbage, not even a valid hash line\n")
        failures = verify(tmp, Path("pkg"))
        if failures:
            return f"an uncommitted (working-tree-only) edit to file-hashes.txt should not affect verify(), but got: {failures}"
    return None


def _case_unhashed_in_scope_file_fails() -> str | None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pkg = _build_clean_scratch(tmp)
        (pkg / "scripts").mkdir()
        (pkg / "scripts" / "new-script.py").write_text("print('hi')\n")
        _commit_all(tmp, "add an in-scope script without hashing it")
        failures = verify(tmp, Path("pkg"))
        if not any("UNHASHED IN-SCOPE FILE" in f and "scripts/new-script.py" in f for f in failures):
            return f"expected an UNHASHED IN-SCOPE FILE failure for scripts/new-script.py, got: {failures}"
    return None


def cmd_selftest():
    cases = [
        ("clean scratch repo passes", _case_clean_passes),
        ("declared-but-uncommitted file fails", _case_missing_tracked_file_fails),
        ("tampered committed content fails hash check", _case_wrong_committed_hash_fails),
        ("corrupted committed bundle checksum fails", _case_wrong_bundle_checksum_fails),
        ("uncommitted edit to file-hashes.txt cannot influence verify()", _case_dirty_working_tree_hash_file_does_not_affect_verify),
        ("an in-scope file (e.g. under scripts/) missing from the manifest fails", _case_unhashed_in_scope_file_fails),
    ]
    failed = 0
    for name, fn in cases:
        err = fn()
        if err is None:
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}\n  {err}", file=sys.stderr)
    if failed:
        print(f"\n{failed}/{len(cases)} selftest case(s) FAILED.", file=sys.stderr)
        sys.exit(1)
    print(f"\nAll {len(cases)} selftest cases passed.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("verify", "regenerate", "selftest"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "regenerate":
        cmd_regenerate()
    elif sys.argv[1] == "selftest":
        cmd_selftest()
    else:
        cmd_verify()
