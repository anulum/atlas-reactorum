#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round2/validate_enrichment_round2.py
"""Validate research-reactor enrichment round 2 against the current base TSV."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "research_reactors.tsv"
PATCH = HERE / "research_reactor_enrichment_round2.tsv"
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
FACT_FIELDS = FIELDS[1:14]
STATUSES = {
    "unknown",
    "operational",
    "under_construction",
    "planned",
    "shutdown",
    "decommissioning",
    "decommissioned",
    "cancelled",
    "suspended",
}
DATE = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2})?)?$")
RIGHTS = {
    "Open Government Licence v3.0",
    "Individual factual assertions; ARPANSA source copyright retained",
    "Individual factual assertions; ANSTO source copyright retained",
    "Individual factual assertions; JAEA source copyright retained",
    "Individual factual assertions; Kyoto University source copyright retained",
    "Individual factual assertions; KAERI source copyright retained",
    "Individual factual assertions; TU Wien source copyright retained",
    "Individual factual assertions; NCBJ source copyright retained",
    "Individual factual assertions; Research Centre Rez source copyright retained",
}


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a complete source table with the required column order.

    Parameters
    ----------
    path : pathlib.Path
        Base or enrichment TSV to read.

    Returns
    -------
    tuple
        Column names and source rows, without modifying the input.

    Raises
    ------
    ValueError
        If the schema, row width or nonempty-table requirement fails.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path.name}: header differs from expected schema")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty table")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return FIELDS.copy(), rows


def valid_date(value: str) -> bool:
    """Check an optional source date at its stated calendar precision.

    Parameters
    ----------
    value : str
        Empty value or ISO year, month or full date.

    Returns
    -------
    bool
        Whether the value represents an allowed calendar date.
    """
    if not value:
        return True
    if not DATE.fullmatch(value):
        return False
    parts = value.split("-")
    try:
        dt.date(
            int(parts[0]),
            int(parts[1]) if len(parts) > 1 else 1,
            int(parts[2]) if len(parts) > 2 else 1,
        )
    except ValueError:
        return False
    return True


def main() -> None:
    """Validate the selected base and round-2 source patch through the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--patch", type=Path, default=PATCH)
    args = parser.parse_args()
    errors = []
    try:
        _, base_rows = load(args.base)
        _, rows = load(args.patch)
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"validation: FAIL: {read_error}")
        raise SystemExit(1) from None
    base = {r["stable_id"]: r for r in base_rows}
    if len(base) != len(base_rows):
        errors.append("base contains duplicate stable_id")
    ids = Counter(r["stable_id"] for r in rows)
    for line, row in enumerate(rows, 2):
        label = f"line {line} ({row.get('stable_id') or '?'})"
        if row["stable_id"] not in base:
            errors.append(f"{label}: key absent from base")
            continue
        if ids[row["stable_id"]] != 1:
            errors.append(f"{label}: duplicate key")
        for field in (
            "source_url",
            "source_role",
            "retrieved",
            "license",
            "verification_notes",
        ):
            if not row[field]:
                errors.append(f"{label}: missing {field}")
        if not any(row[f] and row[f] != base[row["stable_id"]][f] for f in FACT_FIELDS):
            errors.append(f"{label}: no factual change")
        if row["status"] and row["status"] not in STATUSES:
            errors.append(f"{label}: invalid status")
        if bool(row["lat"]) != bool(row["lon"]):
            errors.append(f"{label}: unpaired coordinates")
        if row["lat"]:
            try:
                if not -90 <= float(row["lat"]) <= 90 or not -180 <= float(row["lon"]) <= 180:
                    errors.append(f"{label}: coordinates out of range")
            except ValueError:
                errors.append(f"{label}: non-numeric coordinates")
        if row["thermal_power_mw"]:
            try:
                power = float(row["thermal_power_mw"])
                if not math.isfinite(power) or power < 0:
                    errors.append(f"{label}: invalid thermal power")
            except ValueError:
                errors.append(f"{label}: non-numeric power")
        for field in ("first_criticality", "shutdown_date", "retrieved"):
            if not valid_date(row[field]):
                errors.append(f"{label}: invalid {field}")
        try:
            dt.date.fromisoformat(row["retrieved"])
        except ValueError:
            errors.append(f"{label}: retrieved must be full ISO date")
        try:
            parsed = urlparse(row["source_url"])
            valid_url = parsed.scheme == "https" and bool(parsed.netloc)
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append(f"{label}: source URL must be HTTPS")
        if row["license"] not in RIGHTS:
            errors.append(f"{label}: undeclared rights basis {row['license']!r}")
    print(f"base records: {len(base_rows)}")
    print(f"patch records: {len(rows)}")
    for field in (
        "status",
        "reactor_type",
        "thermal_power_mw",
        "operator",
        "purpose",
        "first_criticality",
        "shutdown_date",
        "lat",
    ):
        print(f"{field} patches: {sum(bool(r[field]) for r in rows)}")
    countries = {base[r["stable_id"]]["country"] for r in rows if r["stable_id"] in base}
    print("countries: " + ", ".join(sorted(countries)))
    if errors:
        print(f"validation: FAIL ({len(errors)} errors)")
        for error in errors:
            print("ERROR " + error)
        raise SystemExit(1)
    print("validation: PASS")


if __name__ == "__main__":
    main()
