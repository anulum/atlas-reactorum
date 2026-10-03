#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment/validate_enrichment.py
"""Validate the non-destructive fusion facility enrichment layer."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "fusion_facilities.tsv"
BASE_SHA256 = "6ce4b68d1904d0785a67a15891963496002c6671e52c95e2ffd6247827cbaab3"
FROZEN_SHA256 = "5ad43c86982c9aa0514c5bb0e6c7ece2b5f5e35a064ac2282899bba003bd7c16"
FILES = (ROOT / "enrichment.tsv", ROOT / "new_facilities.tsv")
REGISTRY = ROOT / "source_registry.tsv"
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
DATE = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2})?)?$")
REGISTRY_FIELDS = [
    "source_id",
    "title",
    "url",
    "publisher",
    "role",
    "license_or_terms",
    "retrieved_date",
    "notes",
]


def load(path: Path, fields: list[str] | None = None) -> list[dict[str, str]]:
    """Read the tab-separated source into rows."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != (EXPECTED if fields is None else fields):
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return rows


def valid_date(value: str) -> bool:
    """Validate optional calendar dates at their original source precision."""
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


def valid_https_url(value: str) -> bool:
    """Require an HTTPS source authority and refuse malformed bracketed hosts."""
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    """Run this script's build and validation steps."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--enrichment", type=Path, default=FILES[0])
    parser.add_argument("--new", type=Path, default=FILES[1])
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--base-selection", choices=("public", "frozen"), default="public")
    args = parser.parse_args()
    expected_base_sha = BASE_SHA256 if args.base_selection == "public" else FROZEN_SHA256
    errors: list[str] = []
    try:
        digest = hashlib.sha256(args.base.read_bytes()).hexdigest()
        base = load(args.base)
        enrichment, new = load(args.enrichment), load(args.new)
        registry = load(args.registry, REGISTRY_FIELDS)
        if not registry:
            raise ValueError("empty source registry")
        if not enrichment and not new:
            raise ValueError("empty enrichment layer")
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"FAIL: {read_error}")
        raise SystemExit(1) from None
    if digest != expected_base_sha:
        errors.append(f"base file hash changed: expected {expected_base_sha}, got {digest}")
    if len(base) != 146:
        errors.append(f"base row count changed: expected 146, got {len(base)}")
    base_ids = {row["stable_id"] for row in base}

    for row in enrichment:
        if row["stable_id"] not in base_ids:
            errors.append(f"enrichment key absent from base: {row['stable_id']}")
    for row in new:
        if row["stable_id"] in base_ids:
            errors.append(f"new facility collides with base: {row['stable_id']}")
        for required in (
            "name",
            "country",
            "configuration",
            "device_subtype",
            "status",
            "organization",
        ):
            if not row[required]:
                errors.append(f"{row['stable_id']}: missing {required}")

    all_rows = enrichment + new
    counts = Counter(row["stable_id"] for row in all_rows)
    for key, count in counts.items():
        if count != 1:
            errors.append(f"duplicate stable_id {key}: {count}")
    for row in all_rows:
        key = row["stable_id"]
        if row["retrieved_date"] != "2026-09-27":
            errors.append(f"{key}: retrieved_date must be 2026-09-27")
        if not row["source_role"] or not row["verification_evidence_notes"]:
            errors.append(f"{key}: provenance fields are required")
        urls = [part.strip() for part in row["source_url"].split("|") if part.strip()]
        if not urls:
            errors.append(f"{key}: source_url is required")
        for url in urls:
            if not valid_https_url(url):
                errors.append(f"{key}: invalid HTTPS URL {url}")
        for field in ("first_operation_date", "last_operation_date"):
            if not valid_date(row[field]):
                errors.append(f"{key}: invalid {field} {row[field]}")
        lat, lon = row["latitude"], row["longitude"]
        if bool(lat) != bool(lon):
            errors.append(f"{key}: coordinate pair is incomplete")
        if lat:
            try:
                if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <= 180:
                    errors.append(f"{key}: coordinate out of range")
            except ValueError:
                errors.append(f"{key}: non-numeric coordinate")
            if not row["coordinate_precision"]:
                errors.append(f"{key}: coordinate precision is required when coordinates exist")

    base_names = {row["name"].casefold() for row in base}
    for row in new:
        if row["name"].casefold() in base_names:
            errors.append(f"new facility duplicates a base display name: {row['name']}")

    registry_ids = Counter(row["source_id"] for row in registry)
    for source_id, count in registry_ids.items():
        if not source_id or count != 1:
            errors.append(f"source registry duplicate/empty ID {source_id!r}: {count}")
    for row in registry:
        if not valid_https_url(row["url"]):
            errors.append(f"source registry invalid URL: {row['url']}")
        if row["retrieved_date"] != "2026-09-27":
            errors.append(f"source registry wrong retrieval date: {row['source_id']}")

    if errors:
        print("FAIL")
        for error in errors:
            print("-", error)
        raise SystemExit(1)
    print(
        f"PASS: immutable base hash verified; {len(enrichment)} enrichments and {len(new)} new facilities valid"
    )


if __name__ == "__main__":
    main()
