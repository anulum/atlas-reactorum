# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — verified offline research comparison reader
"""Restore a downloaded comparison using explicit hashes and original public contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 # Only the fixed local Node reader is invoked with a finite deadline.
import sys
from pathlib import Path
from typing import cast

from metadata.evidence_profiles.validate import ProfileError, validate_profiles


class ComparisonError(ValueError):
    """Refuse a research import without changing accepted input or source data."""


def restore_comparison(
    root: Path, bundle: Path, profile_sha256: str, bundle_sha256: str
) -> dict[str, object]:
    """Restore an exact ordered export and its original claims and sources.

    Parameters
    ----------
    root : pathlib.Path
        Complete accepted repository snapshot with original taxonomy, citations and profiles.
    bundle : pathlib.Path
        Canonical JSON file downloaded from the comparison interface.
    profile_sha256 : str
        Expected whole-profile digest from a separately retained trusted snapshot manifest.
    bundle_sha256 : str
        Expected original downloaded-file digest from a separately retained trusted manifest.

    Returns
    -------
    dict of str to object
        Original comparison, unchanged, with source locators and explicit rights retained.

    Raises
    ------
    ComparisonError
        A source, file, digest, whole profile or native comparison contract is unavailable
        or inconsistent. Current data never replace an unavailable selected snapshot.
    """
    if not all(re.fullmatch(r"[a-f0-9]{64}", value) for value in (profile_sha256, bundle_sha256)):
        raise ComparisonError("Explicit lowercase SHA-256 digests are required.")
    executable = shutil.which("node")
    if executable is None:
        raise ComparisonError("Native Node comparison reader is unavailable.")
    try:
        root = root.resolve()
        bundle = bundle.resolve()
        data = bundle.read_bytes()
        if hashlib.sha256(data).hexdigest() != bundle_sha256:
            raise ComparisonError("Original comparison file digest does not match.")
        taxonomy = root / "04_interactive_presentation/data/taxonomy-expanded.js"
        validate_profiles(root, hashlib.sha256(taxonomy.read_bytes()).hexdigest())
        request = [
            "--restore",
            str(root / "metadata/evidence_profiles/profiles.json"),
            profile_sha256,
            str(bundle),
            bundle_sha256,
        ]
        result = subprocess.run(  # nosec B603 # Fixed literal argv; JSON stdin, trusted source cwd and 30-second deadline.
            ["/usr/bin/env", "node", "04_interactive_presentation/scripts/research_comparison.cjs"],
            input=json.dumps(request),
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise ComparisonError("Native comparison source binding was refused.")
        return cast(dict[str, object], json.loads(result.stdout))
    except (OSError, UnicodeError, ProfileError, subprocess.TimeoutExpired) as error:
        raise ComparisonError(
            "Comparison inputs or original source validation are unavailable."
        ) from error


def main(argv: list[str] | None = None) -> int:
    """Print a validated comparison through the bounded public CLI.

    Parameters
    ----------
    argv : list of str or None
        Explicit arguments, or native process arguments when None.

    Returns
    -------
    int
        Zero for the original restored bundle; two for a fixed safe refusal.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        restored = restore_comparison(args.root, args.bundle, args.snapshot, args.bundle_sha256)
    except ComparisonError:
        print("research comparison: input or source binding refused", file=sys.stderr)
        return 2
    print(json.dumps(restored, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
