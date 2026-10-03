#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment/validate_enrichment.py
"""Validate the standalone research-reactor enrichment patch against its base."""

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
PATCH = HERE / "research_reactor_enrichment.tsv"
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
FACT_FIELDS = [
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
]
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
ALLOWED_LICENSES = {
    "U.S. Government work; public domain",
    "Open Government Licence - Canada 2.0",
}


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read the tab-separated source into rows."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path.name}: header does not match expected schema")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty table")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return FIELDS.copy(), rows


def valid_date(value: str) -> bool:
    """Validate an optional source date at its original year/month/day precision."""
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
    """Run this script's build and validation steps."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--patch", type=Path, default=PATCH)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        _, base_rows = read(args.base)
        _, patch_rows = read(args.patch)
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"validation: FAIL: {read_error}")
        raise SystemExit(1) from None
    base = {row["stable_id"]: row for row in base_rows}
    if len(base) != len(base_rows):
        errors.append("base contains duplicate stable_id")
    counts = Counter(row["stable_id"] for row in patch_rows)
    for line, row in enumerate(patch_rows, 2):
        prefix = f"line {line} ({row.get('stable_id') or '?'})"
        stable_id = row.get("stable_id", "")
        if stable_id not in base:
            errors.append(f"{prefix}: stable_id is absent from base")
            continue
        if counts[stable_id] != 1:
            errors.append(f"{prefix}: duplicate stable_id")
        for field in ("source_url", "source_role", "retrieved", "license", "verification_notes"):
            if not row.get(field):
                errors.append(f"{prefix}: missing provenance field {field}")
        if not any(
            row.get(field) and row[field] != base[stable_id].get(field, "") for field in FACT_FIELDS
        ):
            errors.append(f"{prefix}: patch changes no factual field")
        if row.get("status") and row["status"] not in STATUSES:
            errors.append(f"{prefix}: invalid status {row['status']!r}")
        if bool(row.get("lat")) != bool(row.get("lon")):
            errors.append(f"{prefix}: latitude/longitude must be paired")
        if row.get("lat"):
            try:
                if not -90 <= float(row["lat"]) <= 90 or not -180 <= float(row["lon"]) <= 180:
                    errors.append(f"{prefix}: coordinates out of range")
            except ValueError:
                errors.append(f"{prefix}: non-numeric coordinates")
        if row.get("thermal_power_mw"):
            try:
                power = float(row["thermal_power_mw"])
                if not math.isfinite(power) or power < 0:
                    errors.append(f"{prefix}: invalid thermal power")
            except ValueError:
                errors.append(f"{prefix}: non-numeric thermal power")
        for field in ("first_criticality", "shutdown_date", "retrieved"):
            value = row.get(field, "")
            if not valid_date(value):
                errors.append(f"{prefix}: invalid {field} {value!r}")
        try:
            dt.date.fromisoformat(row.get("retrieved", ""))
        except ValueError:
            errors.append(f"{prefix}: retrieved is not a full ISO date")
        try:
            parsed = urlparse(row.get("source_url", ""))
            valid_url = parsed.scheme == "https" and bool(parsed.netloc)
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append(f"{prefix}: source URL is not HTTPS")
        if row.get("license") not in ALLOWED_LICENSES:
            errors.append(f"{prefix}: unapproved reuse statement {row.get('license')!r}")
    print(f"base records: {len(base_rows)}")
    print(f"patch records: {len(patch_rows)}")
    print(f"status patches: {sum(bool(r['status']) for r in patch_rows)}")
    print(f"type patches: {sum(bool(r['reactor_type']) for r in patch_rows)}")
    print(f"power patches: {sum(bool(r['thermal_power_mw']) for r in patch_rows)}")
    print(f"operator patches: {sum(bool(r['operator']) for r in patch_rows)}")
    print(f"purpose patches: {sum(bool(r['purpose']) for r in patch_rows)}")
    print(f"coordinate patches: {sum(bool(r['lat']) for r in patch_rows)}")
    if errors:
        print(f"validation: FAIL ({len(errors)} errors)")
        for error in errors:
            print("ERROR " + error)
        raise SystemExit(1)
    print("validation: PASS")


if __name__ == "__main__":
    main()
