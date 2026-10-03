#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tools/rebuild.py

"""Rebuild the published presentation and library inventory in a fresh source tree.

The contract is the offline release build in Makefile: taxonomy export, retained
evidence history, layer integration, coverage report and library inventory. Source acquisition and
historical editorial audits are inputs to this build, not implicit refreshes.
The dataset step decodes the pinned FFDB visible-data selection and requires both cached
catalogue products to match it before emitting presentation records.
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
import subprocess  # nosec B404 # Import creates no process; calls have scoped reviews.
import sys
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".pytest-scratch",
        "__pycache__",
        "agentic_project_memory",
    }
)
DATA = "04_interactive_presentation/data"
PRODUCTS = tuple(
    Path(path)
    for path in (
        f"{DATA}/taxonomy-expanded.sources.tsv",
        f"{DATA}/taxonomy-audit.json",
        f"{DATA}/taxonomy-audit.js",
        f"{DATA}/taxonomy-evidence-profiles.json",
        f"{DATA}/taxonomy-evidence-profiles.js",
        f"{DATA}/evidence-history.json",
        f"{DATA}/evidence-history.js",
        f"{DATA}/global_reactors.sample.json",
        f"{DATA}/global_reactors.sample.js",
        f"{DATA}/fusion_companies.sample.json",
        f"{DATA}/fusion_companies.sample.js",
        f"{DATA}/dataset-inventory.json",
        "metadata/coverage_audit/coverage.json",
        "metadata/coverage_audit/COVERAGE.md",
        "metadata/all_sources.tsv",
        "metadata/library_inventory.tsv",
        "metadata/duplicate_files.tsv",
        "metadata/validation_report.txt",
        "metadata/SHA256SUMS",
        "01_nuclear/SHA256SUMS",
        "02_chemical_biochemical/SHA256SUMS",
        "03_hybrid_emerging/SHA256SUMS",
    )
)


def repository_files(root: Path) -> Iterator[Path]:
    """Yield owned regular files without entering environments or private trees.

    Parameters
    ----------
    root : pathlib.Path
        Source directory. Symlinks are refused rather than followed into
        another checkout or writable external tree.

    Yields
    ------
    pathlib.Path
        Regular candidate files, in deterministic path order.

    Raises
    ------
    OSError
        A directory cannot be read or an owned entry is a symlink.
    """

    def unreadable(error: OSError) -> None:
        raise error

    for directory, names, files in os.walk(root, onerror=unreadable):
        base = Path(directory)
        excluded = SKIP_DIRS | ({"internal"} if base == root / "docs" else set())
        names[:] = sorted(name for name in names if name not in excluded)
        files = sorted(name for name in files if name not in excluded)
        for name in [*names, *files]:
            path = base / name
            if path.is_symlink():
                raise OSError("repository contains a symlink")
        for name in files:
            if not name.startswith(".coverage"):
                if not (base / name).is_file():
                    raise OSError("repository contains a nonregular file")
                yield base / name


def snapshot(root: Path) -> dict[Path, str]:
    """Hash the complete owned source and product set.

    Parameters
    ----------
    root : pathlib.Path
        Candidate source root.

    Returns
    -------
    dict of pathlib.Path to str
        Relative path and SHA-256 for each owned regular file.
    """
    return {
        path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in repository_files(root)
    }


def copy_source(root: Path, destination: Path) -> None:
    """Copy frozen release inputs and their directories into a new owned tree.

    Parameters
    ----------
    root : pathlib.Path
        Accepted candidate. Environments, private records and build products
        are omitted; owned symlinks are refused.
    destination : pathlib.Path
        Nonexistent source directory inside the caller's temporary workspace.
        Empty public directories are retained because catalogues can cite them.

    Raises
    ------
    OSError
        An owned symlink or unreadable source prevents copying. The caller
        owns cleanup of any partial temporary tree.
    """

    def omit(directory: str, names: list[str]) -> set[str]:
        base = Path(directory)
        excluded = SKIP_DIRS | ({"internal"} if base == root / "docs" else set())
        omitted = {
            name
            for name in names
            if name in excluded
            or (base / name).relative_to(root) in PRODUCTS
            or (name.startswith(".coverage") and not (base / name).is_dir())
        }
        if any((base / name).is_symlink() for name in set(names) - omitted):
            raise OSError("repository contains a symlink")
        return omitted

    shutil.copytree(root, destination, ignore=omit, symlinks=True)


def reproduce(root: Path, workspace: Path | None = None, *, timeout: float = 1800) -> list[str]:
    """Execute all five offline release build steps without writing the candidate.

    The taxonomy validator receives this process's interpreter by default.
    An explicitly supplied ATLAS_PYTHON selector retains its original semantics.

    Parameters
    ----------
    root : pathlib.Path
        Complete accepted candidate, including every expected product.
    workspace : pathlib.Path or None
        Existing parent for a newly owned temporary tree, outside the candidate.
        None uses the operating system temporary directory.
    timeout : float
        Maximum seconds allowed for each actual builder process.

    Returns
    -------
    list of str
        Missing products, failed processes, changed inputs or byte differences.
        No builder diagnostics or source contents are echoed.
    """
    failures: list[str] = []
    try:
        root = root.resolve(strict=True)
        workspace = (workspace or Path(tempfile.gettempdir())).resolve(strict=True)
        if workspace.is_relative_to(root):
            return ["reproducibility: workspace must be outside the candidate"]
        if not math.isfinite(timeout) or timeout <= 0:
            return ["reproducibility: timeout must be positive"]
        before = snapshot(root)
        missing = [path for path in PRODUCTS if path not in before]
        if missing:
            return [f"reproducibility: missing accepted product {path}" for path in missing]
        stamp = (
            (root / "metadata/validation_report.txt").read_text(encoding="utf-8").splitlines()[1]
        )
        recorded = datetime.strptime(stamp, "Generated (UTC): %Y-%m-%dT%H:%M:%SZ")
        epoch = str(int(recorded.replace(tzinfo=UTC).timestamp()))
        with tempfile.TemporaryDirectory(prefix="atlas-rebuild-", dir=workspace) as temporary:
            stage = Path(temporary) / "source"
            copy_source(root, stage)
            steps = (
                ("taxonomy", ["node", "04_interactive_presentation/scripts/export_taxonomy.cjs"]),
                (
                    "history",
                    [
                        "node",
                        "04_interactive_presentation/scripts/evidence_history.cjs",
                        "--build",
                        ".",
                    ],
                ),
                (
                    "datasets",
                    [sys.executable, "04_interactive_presentation/scripts/build_datasets.py"],
                ),
                ("coverage", [sys.executable, "metadata/coverage_audit/build_coverage.py"]),
                ("inventory", ["bash", "metadata/build_inventory.sh"]),
            )
            environment = {
                **os.environ,
                "SOURCE_DATE_EPOCH": epoch,
                "PYTHONDONTWRITEBYTECODE": "1",
                "ATLAS_PYTHON": os.environ.get("ATLAS_PYTHON", sys.executable),
            }
            for name, command in steps:
                # Fixed build argv in owned source copy; no shell; finite deadline.
                result = subprocess.run(  # nosec B603
                    command,
                    cwd=stage,
                    env=environment,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                )
                if result.returncode:
                    failures.append(f"reproducibility: {name} exited {result.returncode}")
                    break
            after = snapshot(stage)
            for relative in PRODUCTS:
                if relative not in after:
                    failures.append(f"reproducibility: product was not created {relative}")
                elif after[relative] != before[relative]:
                    failures.append(f"reproducibility: product changed {relative}")
            for relative in before.keys() - set(PRODUCTS):
                if after.get(relative) != before[relative]:
                    failures.append(f"reproducibility: staged input changed {relative}")
            for relative in after.keys() - before.keys():
                failures.append(f"reproducibility: undeclared build output {relative}")
        if snapshot(root) != before:
            failures.append("reproducibility: candidate changed during verification")
    except subprocess.TimeoutExpired:
        failures.append("reproducibility: builder timed out")
    except (OSError, ValueError, IndexError):
        failures.append("reproducibility: source, workspace or build receipt cannot be read")
    return sorted(failures)
