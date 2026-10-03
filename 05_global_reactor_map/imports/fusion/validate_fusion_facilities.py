#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/fusion/validate_fusion_facilities.py
"""Validate fusion_facilities.tsv without third-party dependencies."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "fusion_facilities.tsv"
REPORT = ROOT / "VALIDATION_REPORT.md"
EXPECTED = [
    "stable_id",
    "name",
    "aliases",
    "country",
    "latitude",
    "longitude",
    "coordinate_precision",
    "configuration",
    "device_subtype",
    "status",
    "organization",
    "first_operation_date",
    "last_operation_date",
    "source_url",
    "source_role",
    "retrieved_date",
    "license",
    "verification_evidence_notes",
]


def valid_date(value: str) -> bool:
    """Report whether a value is a valid date."""
    if not value:
        return True
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def main() -> int:
    """Read the tab-separated source into rows."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATA)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with args.dataset.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, dialect="excel-tab", strict=True)
            if reader.fieldnames != EXPECTED:
                raise ValueError(f"Header mismatch: {reader.fieldnames!r}")
            rows = list(reader)
        if not rows:
            raise ValueError("empty fusion catalogue")
        if any(None in row or None in row.values() for row in rows):
            raise ValueError("malformed fusion row")
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    ids = Counter(row["stable_id"] for row in rows)
    names = Counter((row["name"].casefold(), row["country"]) for row in rows)
    for number, row in enumerate(rows, 2):
        label = f"row {number} ({row.get('stable_id', '?')})"
        for required in (
            "stable_id",
            "name",
            "country",
            "configuration",
            "device_subtype",
            "status",
            "source_url",
            "source_role",
            "retrieved_date",
            "license",
        ):
            if not row.get(required):
                errors.append(f"{label}: missing {required}")
        lat, lon = row.get("latitude", ""), row.get("longitude", "")
        if bool(lat) != bool(lon):
            errors.append(f"{label}: latitude/longitude must be both present or both empty")
        if lat:
            try:
                if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <= 180:
                    errors.append(f"{label}: coordinates out of range")
            except ValueError:
                errors.append(f"{label}: non-numeric coordinates")
            if not row.get("coordinate_precision"):
                errors.append(f"{label}: coordinates present without precision note")
        for field in ("first_operation_date", "last_operation_date", "retrieved_date"):
            if not valid_date(row.get(field, "")):
                errors.append(f"{label}: invalid ISO date in {field}")
        urls = [part.strip() for part in row["source_url"].split("|")]
        roles = [part.strip() for part in row["source_role"].split("|")]
        if len(urls) != len(roles):
            errors.append(f"{label}: source URL/role counts differ")
        try:
            valid_urls = all(
                urlparse(url).scheme in {"http", "https"} and urlparse(url).netloc for url in urls
            )
        except ValueError:
            valid_urls = False
        if not valid_urls:
            errors.append(f"{label}: malformed source URL")
        if not row.get("organization"):
            warnings.append(f"{label}: organization unknown")
    for stable_id, count in ids.items():
        if count > 1:
            errors.append(f"duplicate stable_id {stable_id!r} ({count})")
    for key, count in names.items():
        if count > 1:
            warnings.append(f"possible same-name duplicate {key!r} ({count})")

    status_counts = Counter(row["status"] for row in rows)
    subtype_counts = Counter(row["device_subtype"] for row in rows)
    coordinate_count = sum(bool(row["latitude"]) for row in rows)
    date_count = sum(
        bool(row["first_operation_date"] or row["last_operation_date"]) for row in rows
    )
    report = [
        "# Fusion facilities validation report",
        "",
        f"Generated: {dt.date.today().isoformat()}",
        "",
        f"Result: **{'PASS' if not errors else 'FAIL'}**",
        "",
        f"Rows: {len(rows)}",
        f"Rows with coordinates: {coordinate_count}",
        f"Rows with at least one operation date: {date_count}",
        "",
        "## Status counts",
        "",
    ]
    report += [f"- {key}: {value}" for key, value in sorted(status_counts.items())]
    report += ["", "## Device subtype counts", ""]
    report += [f"- {key}: {value}" for key, value in sorted(subtype_counts.items())]
    report += ["", "## Errors", ""] + ([f"- {item}" for item in errors] or ["- None."])
    report += ["", "## Warnings", ""] + ([f"- {item}" for item in warnings] or ["- None."])
    try:
        args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"FAIL: cannot write report: {error}")
        return 1
    print(
        f"{'PASS' if not errors else 'FAIL'}: {len(rows)} rows, {len(errors)} errors, {len(warnings)} warnings"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
