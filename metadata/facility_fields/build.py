#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility fields native protected producer

"""Prepare a separate complete source-bound field projection without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "metadata.facility_fields"

from .project import project

REPOSITORY = Path(__file__).resolve().parents[2]


def payload_bytes(root: Path) -> bytes:
    """Render every original assertion with its reviewed pin-ledger digest.

    Parameters
    ----------
    root : pathlib.Path
        Complete source checkout, kept intact.

    Returns
    -------
    bytes
        Deterministic UTF-8 JSON with every original field observation.

    Raises
    ------
    ValueError
        Complete source projection or its pin ledger changes during preparation.
    OSError
        A complete original input cannot be read.
    """
    pins = root / "metadata/facility_fields/source_pins.json"
    before = pins.read_bytes()
    records = project(root)
    if pins.read_bytes() != before:
        raise ValueError("source pins changed during projection")
    document = {
        "schema_version": "1.0.0",
        "source_pins_sha256": hashlib.sha256(before).hexdigest(),
        "record_count": len(records),
        "records": records,
        "limitations": [
            "Published end use, feedstock and whole-plant fuel classification are separate assertions.",
            "No reactor fuel composition, vessel design or present physical operation is established.",
            "Original capture dates are retained rather than refreshed by this offline projection.",
        ],
    }
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def checked_destination(path: Path, source_root: Path) -> Path:
    """Require a new external file beneath an existing nonsymlink directory.

    Parameters
    ----------
    path : pathlib.Path
        Explicit new output.
    source_root : pathlib.Path
        Original input tree protected against output writes.

    Returns
    -------
    pathlib.Path
        Absolute checked destination.

    Raises
    ------
    ValueError
        The destination is existing, symlinked or inside protected source trees.
    OSError
        Its parent does not exist.
    """
    absolute = path.absolute()
    if any(parent.is_symlink() for parent in (absolute, *absolute.parents)):
        raise ValueError("output symlinks are refused")
    target = absolute.parent.resolve(strict=True) / absolute.name
    if (
        target.exists()
        or target.is_relative_to(source_root.resolve())
        or target.is_relative_to(REPOSITORY)
    ):
        raise ValueError("output must be a new external file")
    return target


def build(root: Path, output: Path) -> int:
    """Publish complete validated bytes atomically without replacing any file.

    Parameters
    ----------
    root : pathlib.Path
        Complete reviewed original source checkout.
    output : pathlib.Path
        New external destination under an existing parent.

    Returns
    -------
    int
        Number of original assertions written.

    Raises
    ------
    ValueError
        Source or destination contract is incomplete.
    OSError
        The native write or protected hard link fails.
    """
    target = checked_destination(output, root)
    body = payload_bytes(root)
    with tempfile.TemporaryDirectory(prefix=".facility-fields-", dir=target.parent) as temporary:
        product = Path(temporary) / "observations.json"
        product.write_bytes(body)
        os.link(product, target)
    return 1631


def main() -> None:
    """Run the native producer with an explicit source root and separate output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=REPOSITORY)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        count = build(arguments.source_root, arguments.output)
    except (ValueError, OSError, KeyError):
        print("FACILITY FIELD BUILD FAILED: complete source or protected destination differs")
        raise SystemExit(1) from None
    print(
        f"{count} original field assertions written; physical verification and rights review remain separate"
    )


if __name__ == "__main__":
    main()
