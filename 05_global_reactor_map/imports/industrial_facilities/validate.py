#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/validate.py
"""Validate reported industrial sites without inferring individual reactor vessels."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

PATH = Path(__file__).with_name("industrial_facilities.tsv")
FIELDS = [
    "stable_id",
    "facility_name",
    "country",
    "lat",
    "lon",
    "precision",
    "sector",
    "process_or_activity",
    "reactor_type_if_explicit",
    "status",
    "operator",
    "capacity",
    "pollutant_or_product_context",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]
REQUIRED = (
    "stable_id",
    "facility_name",
    "country",
    "lat",
    "lon",
    "precision",
    "sector",
    "status",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a nonempty TSV with the exact industrial discovery column order.

    Ragged rows and invalid quoting are rejected before any record validation.
    The input is opened read-only and never rewritten by this module.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError("industrial table header differs from the required schema")
        rows: list[dict[str, str]] = []
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"line {line}: industrial table row has the wrong width")
            row = {field: raw[field] for field in FIELDS}
            rows.append(row)
    if not rows:
        raise ValueError("industrial table contains no records")
    return rows


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    """Return errors for complete parsed records, including provenance and site scope.

    Coordinates must be finite WGS84 values; retrieval dates must be exact ISO
    calendar dates. An EEA site never establishes an explicit reactor type.
    """
    if not rows:
        return ["industrial table contains no records"]
    errors: list[str] = []
    ids: Counter[str] = Counter()
    for line, row in enumerate(rows, 2):
        if set(row) != set(FIELDS) or any(not isinstance(v, str) for v in row.values()):
            errors.append(f"line {line}: record differs from the industrial string schema")
            continue
        ids[row["stable_id"]] += 1
        label = f"line {line} ({row['stable_id']})"
        for field in REQUIRED:
            if not row[field].strip():
                errors.append(f"{label}: missing {field}")
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                errors.append(f"{label}: coordinate out of range")
        except ValueError:
            errors.append(f"{label}: invalid coordinate")
        try:
            url = urlsplit(row["source_url"])
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username is not None
                or url.port == 0
                or any(c.isspace() for c in row["source_url"])
            ):
                raise ValueError("invalid HTTPS source")
        except ValueError:
            errors.append(f"{label}: source must be a valid anonymous HTTPS URL")
        try:
            if date.fromisoformat(row["retrieved"]).isoformat() != row["retrieved"]:
                raise ValueError("noncanonical date")
        except ValueError:
            errors.append(f"{label}: invalid ISO retrieval date")
        if row["stable_id"].startswith("eea-") and row["reactor_type_if_explicit"].strip():
            errors.append(f"{label}: EEA site must not imply an explicit reactor type")
    for stable_id, count in ids.items():
        if not stable_id or count != 1:
            errors.append(f"stable_id {stable_id!r} occurs {count} times")
    return errors


def coverage_statistics(rows: list[dict[str, str]]) -> str:
    """Format the original coverage metrics for records that passed validation."""
    counts = Counter(row["stable_id"].split(":")[0] for row in rows)
    return "\n".join(
        [
            f"records\t{len(rows)}",
            f"countries\t{len({row['country'] for row in rows})}",
            f"coordinates\t{sum(bool(row['lat'] and row['lon']) for row in rows)}",
            "sources\t" + "; ".join(f"{key}={value}" for key, value in sorted(counts.items())),
            f"explicit_reactor_type\t{sum(bool(row['reactor_type_if_explicit']) for row in rows)}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    """Validate the requested read-only dataset and print trace-free diagnostics.

    Returns zero only after table and record validation. The first hundred
    errors retain the original bounded console report; no report file is written.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=PATH)
    args = parser.parse_args(argv)
    try:
        rows = read_rows(args.dataset)
        errors = validate_rows(rows)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print("VALIDATION FAILED\n" + "\n".join(errors[:100]))
        return 1
    print("VALIDATION PASSED")
    print(coverage_statistics(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
