#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility fields read-only native validator

"""Validate every field assertion against complete original sources without writing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "metadata.facility_fields"

from .build import REPOSITORY, payload_bytes


def validate(root: Path, dataset: Path) -> int:
    """Require exact complete parity with the original native source projection.

    Parameters
    ----------
    root : pathlib.Path
        Complete original research checkout.
    dataset : pathlib.Path
        Explicit field projection to verify; never rewritten.

    Returns
    -------
    int
        Complete count of verbatim source assertions.

    Raises
    ------
    ValueError
        A field, order, count, source binding or pin digest differs.
    OSError
        Complete source inputs or the explicit dataset cannot be read.
    """
    if dataset.read_bytes() != payload_bytes(root):
        raise ValueError("field projection differs from complete original sources")
    return 1631


def main() -> None:
    """Run original-cell validation with explicit input paths and fixed refusal text."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=REPOSITORY)
    parser.add_argument("--dataset", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        count = validate(arguments.source_root, arguments.dataset)
    except (ValueError, OSError, KeyError):
        print("FACILITY FIELD VALIDATION FAILED: original cells or source bindings differ")
        raise SystemExit(1) from None
    print(f"{count} assertions match complete original fields; no input rewritten")


if __name__ == "__main__":
    main()
