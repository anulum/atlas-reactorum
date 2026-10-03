#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/power_units/scripts/validate.py
"""Validate the power-reactor unit discovery TSV and print release statistics."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

FIELDS = [
    "stable_id",
    "unit_name",
    "plant_name",
    "country",
    "lat",
    "lon",
    "precision",
    "reactor_type",
    "model",
    "status",
    "nameplate_mw",
    "net_mwe",
    "gross_mwe",
    "thermal_mw",
    "operator",
    "owner",
    "construction_start",
    "first_criticality",
    "grid_connection",
    "commercial_operation",
    "permanent_shutdown",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]
STATUSES = {
    "announced",
    "pre-construction",
    "construction",
    "operating",
    "shelved",
    "cancelled",
    "mothballed",
    "retired",
    "unknown",
}


def valid_date(value: str) -> bool:
    """Report whether a value is a valid date."""
    if not value:
        return True
    try:
        if len(value) == 4:
            dt.datetime.strptime(value, "%Y")
        elif len(value) == 7:
            dt.datetime.strptime(value, "%Y-%m")
        else:
            dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def main() -> None:
    """Read the tab-separated source into rows."""
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    errors = []
    try:
        with args.dataset.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", strict=True)
            if reader.fieldnames != FIELDS:
                print("VALIDATION FAILED")
                parser.exit(1, f"header mismatch: {reader.fieldnames!r}\n")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        print("VALIDATION FAILED")
        parser.exit(1, f"cannot read dataset: {error}\n")
    if not rows:
        errors.append("dataset is empty")
    ids = Counter(r["stable_id"] for r in rows)
    for n, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"line {n}: malformed row")
            continue
        label = f"line {n} ({row.get('stable_id') or '?'})"
        for field in (
            "stable_id",
            "plant_name",
            "country",
            "status",
            "source_url",
            "source_role",
            "retrieved",
            "license",
            "verification_notes",
        ):
            if not row.get(field):
                errors.append(f"{label}: missing {field}")
        if row.get("status") not in STATUSES:
            errors.append(f"{label}: invalid status {row.get('status')!r}")
        if row.get("reactor_type", "").lower() == "fusion":
            errors.append(f"{label}: fusion record in fission layer")
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                errors.append(f"{label}: coordinates out of range")
        except ValueError:
            errors.append(f"{label}: missing or non-numeric coordinates")
        for field in ("nameplate_mw", "net_mwe", "gross_mwe", "thermal_mw"):
            if row.get(field):
                try:
                    number = float(row[field])
                    if not math.isfinite(number):
                        errors.append(f"{label}: non-finite {field}")
                    elif number < 0:
                        errors.append(f"{label}: negative {field}")
                except ValueError:
                    errors.append(f"{label}: non-numeric {field}")
        for field in (
            "construction_start",
            "first_criticality",
            "grid_connection",
            "commercial_operation",
            "permanent_shutdown",
            "retrieved",
        ):
            if not valid_date(row.get(field, "")):
                errors.append(f"{label}: invalid date {field}={row.get(field)!r}")
        urls = row.get("source_url", "").split("|")
        roles = row.get("source_role", "").split("|")
        if len(urls) != len(roles):
            errors.append(f"{label}: source_url/source_role count mismatch")
        parsed_urls = [urlparse(url) for url in urls]
        if any(url.scheme != "https" for url in parsed_urls):
            errors.append(f"{label}: non-HTTPS source URL")
        if any(not url.netloc for url in parsed_urls):
            errors.append(f"{label}: malformed source URL")
    for stable_id, count in ids.items():
        if not stable_id or count != 1:
            errors.append(f"stable_id {stable_id!r} occurs {count} times")
    if errors:
        print("VALIDATION FAILED")
        print("\n".join(errors[:100]))
        raise SystemExit(1)
    print("VALIDATION PASSED")
    print(f"records\t{len(rows)}")
    print(f"countries_areas\t{len({r['country'] for r in rows})}")
    print(f"plants_projects\t{len({(r['country'], r['plant_name']) for r in rows})}")
    print(f"coordinates\t{sum(bool(r['lat'] and r['lon']) for r in rows)}")
    print(
        "statuses\t"
        + "; ".join(f"{k}={v}" for k, v in sorted(Counter(r["status"] for r in rows).items()))
    )
    print(f"unknown_reactor_type\t{sum(not r['reactor_type'] for r in rows)}")
    print(f"unit_designator_blank\t{sum(not r['unit_name'] for r in rows)}")
    print(f"operator_blank\t{sum(not r['operator'] for r in rows)}")
    print(f"owner_blank\t{sum(not r['owner'] for r in rows)}")


if __name__ == "__main__":
    main()
