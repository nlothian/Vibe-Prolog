#!/usr/bin/env python3
"""Measure xpath library load times with and without cached ASTs."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


def _repo_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parent.parent


def _short_commit_hash(repo_root: Path) -> str:
    """Return the current short git commit hash."""
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _run_xpath_load(repo_root: Path, clear_cache: bool) -> float:
    """Run xpath library load command and return elapsed seconds."""
    command = ["uv", "run", "vibeprolog.py"]
    if clear_cache:
        command.append("--clear-ast-cache")
    command.extend(["./library/xpath.pl", "-q", "true."])
    start = time.perf_counter()
    subprocess.run(command, cwd=repo_root, check=True)
    return time.perf_counter() - start


def _append_result(log_path: Path, commit_hash: str, elapsed: float) -> None:
    """Append measurement row to the provided CSV."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{commit_hash},{elapsed:.2f}\n")


def main() -> None:
    """Run timing measurement and append result."""
    repo_root = _repo_root()
    commit_hash = _short_commit_hash(repo_root)
    uncached_log = repo_root / "docs" / "uncached_xpath_library_load_times.csv"
    cached_log = repo_root / "docs" / "cached_xpath_library_load_times.csv"

    uncached_elapsed = _run_xpath_load(repo_root, clear_cache=True)
    _append_result(uncached_log, commit_hash, uncached_elapsed)
    print(f"Commit {commit_hash} uncached load time: {uncached_elapsed:.2f}s")

    cached_elapsed = _run_xpath_load(repo_root, clear_cache=False)
    _append_result(cached_log, commit_hash, cached_elapsed)
    print(f"Commit {commit_hash} cached load time: {cached_elapsed:.2f}s")


if __name__ == "__main__":
    main()
