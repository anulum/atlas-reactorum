#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/scripts/validate.py
"""Validate the standalone research-reactor TSV and print a coverage report."""

import argparse
import collections
import csv
import datetime as dt
import math
import re
from pathlib import Path
from urllib.parse import urlparse

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


def valid_date(value: str) -> bool:
    """Validate calendar dates while preserving source year/month precision."""
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
    """Read the tab-separated source into rows."""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="research_reactors.tsv")
    args = parser.parse_args()
    path = Path(args.path)
    errors = []
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", strict=True)
            if reader.fieldnames != FIELDS:
                raise ValueError(f"header differs from required schema: {reader.fieldnames!r}")
            rows = list(reader)
        if not rows:
            raise ValueError("empty research-reactor catalogue")
        if any(None in row or None in row.values() for row in rows):
            raise ValueError("malformed research-reactor row")
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"validation: FAIL: {read_error}")
        raise SystemExit(1) from None
    seen = set()
    for number, row in enumerate(rows, 2):
        prefix = f"row {number}"
        stable_id = row.get("stable_id", "")
        if not stable_id or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", stable_id):
            errors.append(f"{prefix}: invalid stable_id {stable_id!r}")
        if stable_id in seen:
            errors.append(f"{prefix}: duplicate stable_id {stable_id!r}")
        seen.add(stable_id)
        for required in (
            "name",
            "reactor_type",
            "status",
            "source_url",
            "source_role",
            "retrieved",
            "license",
            "verification_notes",
        ):
            if not row.get(required):
                errors.append(f"{prefix}: missing {required}")
        if row.get("status") not in STATUSES:
            errors.append(f"{prefix}: invalid status {row.get('status')!r}")
        lat, lon = row.get("lat", ""), row.get("lon", "")
        if bool(lat) != bool(lon):
            errors.append(f"{prefix}: latitude/longitude must be both present or both blank")
        if lat and lon:
            try:
                if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <= 180:
                    errors.append(f"{prefix}: coordinate out of range")
            except ValueError:
                errors.append(f"{prefix}: non-numeric coordinate")
        power = row.get("thermal_power_mw", "")
        if power:
            try:
                if not math.isfinite(float(power)) or float(power) < 0:
                    errors.append(f"{prefix}: invalid thermal power {power!r}")
            except ValueError:
                errors.append(f"{prefix}: invalid thermal power {power!r}")
        for field in ("first_criticality", "shutdown_date", "retrieved"):
            value = row.get(field, "")
            if not valid_date(value):
                errors.append(f"{prefix}: invalid {field} {value!r}")
        try:
            dt.date.fromisoformat(row.get("retrieved", ""))
        except ValueError:
            errors.append(f"{prefix}: retrieved must be a full ISO date")
        try:
            parsed = urlparse(row.get("source_url", ""))
            valid_url = parsed.scheme == "https" and bool(parsed.netloc)
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append(f"{prefix}: source_url must be an https URL")

    countries = {row["country"] for row in rows if row["country"]}
    status_counts = collections.Counter(row["status"] for row in rows)
    source_counts = collections.Counter(row["source_role"] for row in rows)
    print(f"records: {len(rows)}")
    print(f"named countries: {len(countries)}")
    print(f"with coordinates: {sum(bool(row['lat']) for row in rows)}")
    print(f"with operator: {sum(bool(row['operator']) for row in rows)}")
    print(f"with thermal power: {sum(bool(row['thermal_power_mw']) for row in rows)}")
    print(f"with first criticality: {sum(bool(row['first_criticality']) for row in rows)}")
    print(f"with shutdown date: {sum(bool(row['shutdown_date']) for row in rows)}")
    print("status: " + ", ".join(f"{key}={status_counts[key]}" for key in sorted(status_counts)))
    print(
        "source roles: " + ", ".join(f"{key}={source_counts[key]}" for key in sorted(source_counts))
    )
    if errors:
        print(f"validation: FAIL ({len(errors)} errors)")
        for error in errors:
            print("ERROR " + error)
        raise SystemExit(1)
    print("validation: PASS")


if __name__ == "__main__":
    main()
