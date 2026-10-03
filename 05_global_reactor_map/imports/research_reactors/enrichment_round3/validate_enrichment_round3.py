#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round3/validate_enrichment_round3.py
"""Validate research-reactor enrichment round 3 against the current base TSV."""

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
PATCH = HERE / "research_reactor_enrichment_round3.tsv"
REGISTRY = HERE / "source_registry.tsv"
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
REGISTRY_FIELDS = [
    "source_id",
    "source_name",
    "publisher",
    "url",
    "role",
    "countries",
    "retrieved",
    "rights_basis",
    "use_decision",
    "notes",
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
    "Individual factual assertions; source copyright retained",
    "CC0 1.0",
}


def load(path: Path, fields: list[str] | None = None) -> tuple[list[str], list[dict[str, str]]]:
    """Read a nonempty source table, optionally enforcing its exact schema.

    Parameters
    ----------
    path : pathlib.Path
        Source TSV to read.
    fields : list of str, optional
        Required column order for the base, patch or source registry.

    Returns
    -------
    tuple
        Column names and unmodified source rows.

    Raises
    ------
    ValueError
        If the source schema or row structure is invalid or empty.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames is None or (fields is not None and reader.fieldnames != fields):
            raise ValueError(f"{path.name}: header differs from expected schema")
        header, rows = list(reader.fieldnames), list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty table")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return header, rows


def valid_https_url(value: str) -> bool:
    """Check a source URL's HTTPS authority without propagating parse errors.

    Parameters
    ----------
    value : str
        URL from a source row or registry.

    Returns
    -------
    bool
        Whether the URL has a valid HTTPS authority.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def valid_partial_date(value: str) -> bool:
    """Report whether a value is a valid full or partial date."""
    if not DATE.fullmatch(value):
        return False
    try:
        if len(value) == 4:
            return 1 <= int(value) <= 9999
        if len(value) == 7:
            dt.date.fromisoformat(value + "-01")
        else:
            dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def main() -> None:
    """Validate selected round-3 inputs and their included/excluded source registry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--patch", type=Path, default=PATCH)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        _, base_rows = load(args.base, FIELDS)
        _, rows = load(args.patch, FIELDS)
        _, registry_rows = load(args.registry, REGISTRY_FIELDS)
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"validation: FAIL: {read_error}")
        raise SystemExit(1) from None

    base = {r["stable_id"]: r for r in base_rows}
    if len(base) != len(base_rows):
        errors.append("base contains duplicate stable_id")
    ids = Counter(r["stable_id"] for r in rows)
    registry_urls = {r["url"] for r in registry_rows if r["use_decision"].startswith("Included")}
    excluded_urls = {r["url"] for r in registry_rows if r["use_decision"] == "Excluded"}

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
        for field in ("first_criticality", "shutdown_date"):
            if row[field] and not valid_partial_date(row[field]):
                errors.append(f"{label}: invalid {field}")
        try:
            dt.date.fromisoformat(row["retrieved"])
        except ValueError:
            errors.append(f"{label}: retrieved must be a full ISO date")
        if not valid_https_url(row["source_url"]):
            errors.append(f"{label}: source URL must be HTTPS")
        if row["source_url"] not in registry_urls:
            errors.append(f"{label}: source URL absent from included registry entries")
        if row["source_url"] in excluded_urls:
            errors.append(f"{label}: excluded source used in patch")
        if row["license"] not in RIGHTS:
            errors.append(f"{label}: undeclared rights basis {row['license']!r}")

    registry_ids = Counter(r["source_id"] for r in registry_rows)
    for line, row in enumerate(registry_rows, 2):
        label = f"registry line {line} ({row.get('source_id') or '?'})"
        if not row["source_id"] or registry_ids[row["source_id"]] != 1:
            errors.append(f"{label}: missing or duplicate source_id")
        if not all(row[f] for f in REGISTRY_FIELDS):
            errors.append(f"{label}: blank required field")
        if not valid_https_url(row["url"]):
            errors.append(f"{label}: URL must be HTTPS")

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
