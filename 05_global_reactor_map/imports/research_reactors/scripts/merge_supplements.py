#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/scripts/merge_supplements.py
"""Append reviewed, openly licensed official records to a discovery snapshot."""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path

FIELDS = [
    "stable_id",
    "name",
    "aliases",
    "country",
    "lat",
    "lon",
    "precision",
    "reactor_type",
    "status",
    "purpose",
    "thermal_power_mw",
    "operator",
    "first_criticality",
    "shutdown_date",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a nonempty research catalogue with unique, populated source identities.

    Parameters
    ----------
    path : pathlib.Path
        Discovery snapshot or reviewed official supplement TSV.

    Returns
    -------
    tuple
        Original column order and unmodified source rows.

    Raises
    ------
    ValueError
        If the schema, row structure, or source identities are invalid.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames is None:
            raise ValueError(f"source file has no header row: {path}")
        if reader.fieldnames != FIELDS:
            raise ValueError(f"header mismatch: {path}")
        fields, rows = list(reader.fieldnames), list(reader)
    if not rows:
        raise ValueError(f"empty source table: {path}")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"malformed source row: {path}")
    seen: set[str] = set()
    for row in rows:
        if not row["stable_id"].strip():
            raise ValueError(f"blank stable_id: {path}")
        if row["stable_id"] in seen:
            raise ValueError(f"duplicate stable_id: {row['stable_id']}")
        seen.add(row["stable_id"])
    return fields, rows


def main() -> None:
    """Merge disjoint reviewed source rows and replace the output after a complete write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    parser.add_argument("supplements", nargs="+")
    parser.add_argument("--out", default="research_reactors.tsv")
    args = parser.parse_args()
    try:
        fields, rows = read(Path(args.base))
        seen = {row["stable_id"] for row in rows}
        for filename in args.supplements:
            _, supplement_rows = read(Path(filename))
            for row in supplement_rows:
                if row["stable_id"] in seen:
                    raise ValueError(f"duplicate stable_id: {row['stable_id']}")
                seen.add(row["stable_id"])
                rows.append(row)
        rows.sort(
            key=lambda row: (
                row["country"].casefold(),
                row["name"].casefold(),
                row["stable_id"],
            )
        )
        output = Path(args.out)
        with tempfile.TemporaryDirectory(
            dir=output.parent, prefix=f".{output.name}.", suffix=".tmp"
        ) as directory:
            temporary = Path(directory) / "merged.tsv"
            with temporary.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            temporary.replace(output)
    except (OSError, UnicodeError, csv.Error, ValueError) as merge_error:
        parser.exit(1, f"merge: FAIL: {merge_error}\n")
    print(f"wrote {len(rows)} records to {args.out}")


if __name__ == "__main__":
    main()
