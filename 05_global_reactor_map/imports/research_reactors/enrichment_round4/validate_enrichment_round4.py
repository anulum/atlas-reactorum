#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round4/validate_enrichment_round4.py
"""Validate round-4 overlay, provenance, and generated completeness reports."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import re
import subprocess  # nosec B404 # Import creates no process; calls have scoped reviews.
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
MAX_TIMEOUT_SECONDS = 3600
BASE = HERE.parent / "research_reactors.tsv"
PATCH = HERE / "research_reactor_enrichment_round4.tsv"
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
    "Creative Commons Attribution 4.0 International",
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
    """Check a source date without inventing a missing month or day.

    Parameters
    ----------
    value : str
        Source year, year-month or full ISO date.

    Returns
    -------
    bool
        Whether the date is possible at its supplied precision.
    """
    if not DATE.fullmatch(value):
        return False
    try:
        if len(value) == 4:
            return 1 <= int(value) <= 9999
        dt.date.fromisoformat(value if len(value) == 10 else value + "-01")
    except ValueError:
        return False
    return True


def main() -> None:
    """Validate source facts and bound the native completeness reporter lifetime.

    Raises
    ------
    SystemExit
        If CLI limits, source records or completeness reports are invalid.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, default=HERE.parent)
    parser.add_argument(
        "--check-reports",
        action="store_true",
        help="Validate existing completeness reports without regenerating them.",
    )
    parser.add_argument(
        "--report-timeout",
        type=float,
        default=30,
        help="Native reporter process wait limit in (0, 3600] seconds.",
    )
    args = parser.parse_args()
    if (
        not math.isfinite(args.report_timeout)
        or args.report_timeout <= 0
        or args.report_timeout > MAX_TIMEOUT_SECONDS
    ):
        parser.error("report timeout must be positive and finite and at most 3600 seconds")
    directory = args.research_root / "enrichment_round4"
    errors: list[str] = []
    try:
        _, base_rows = load(args.research_root / "research_reactors.tsv", FIELDS)
        _, rows = load(directory / "research_reactor_enrichment_round4.tsv", FIELDS)
        _, registry_rows = load(directory / "source_registry.tsv", REGISTRY_FIELDS)
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"validation: FAIL: {read_error}")
        raise SystemExit(1) from None

    base = {row["stable_id"]: row for row in base_rows}
    if len(base) != len(base_rows):
        errors.append("base contains duplicate stable_id")
    ids = Counter(row["stable_id"] for row in rows)
    included_urls = {
        row["url"] for row in registry_rows if row["use_decision"].startswith("Included")
    }
    excluded_urls = {row["url"] for row in registry_rows if row["use_decision"] == "Excluded"}
    for line, row in enumerate(rows, 2):
        label = f"line {line} ({row.get('stable_id') or '?'})"
        if row["stable_id"] not in base:
            errors.append(f"{label}: key absent from base")
            continue
        if ids[row["stable_id"]] != 1:
            errors.append(f"{label}: duplicate key")
        if row["country"] or row["lat"] or row["lon"] or row["precision"]:
            errors.append(f"{label}: round 4 must not alter country or coordinates")
        for field in (
            "source_url",
            "source_role",
            "retrieved",
            "license",
            "verification_notes",
        ):
            if not row[field]:
                errors.append(f"{label}: missing {field}")
        if not any(
            row[field] and row[field] != base[row["stable_id"]][field] for field in FACT_FIELDS
        ):
            errors.append(f"{label}: no factual change")
        if row["status"] and row["status"] not in STATUSES:
            errors.append(f"{label}: invalid status")
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
        if row["source_url"] not in included_urls:
            errors.append(f"{label}: primary source absent from included registry")
        if row["source_url"] in excluded_urls:
            errors.append(f"{label}: excluded source used")
        if row["license"] not in RIGHTS:
            errors.append(f"{label}: undeclared rights basis")

    registry_ids = Counter(row["source_id"] for row in registry_rows)
    for line, row in enumerate(registry_rows, 2):
        label = f"registry line {line} ({row.get('source_id') or '?'})"
        if not row["source_id"] or registry_ids[row["source_id"]] != 1:
            errors.append(f"{label}: missing or duplicate source_id")
        if not all(row[field] for field in REGISTRY_FIELDS):
            errors.append(f"{label}: blank required field")
        if not valid_https_url(row["url"]):
            errors.append(f"{label}: URL must be HTTPS")

    if not errors:
        try:
            if not args.check_reports:
                # Fixed sibling script; data paths are separate argv; no shell; finite deadline.
                subprocess.run(  # nosec B603
                    [
                        sys.executable,
                        str(HERE / "generate_completeness_report.py"),
                        "--research-root",
                        str(args.research_root),
                        "--output-dir",
                        str(directory),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=args.report_timeout,
                )
            expected_country_header = [
                "stage",
                "country",
                "records",
                "unknown_status",
                "unknown_or_generic_reactor_type",
                "unknown_thermal_power_mw",
                "unknown_operator",
                "unknown_purpose",
                "unknown_first_criticality",
                "unpopulated_shutdown_date",
            ]
            expected_summary_header = [
                "stage",
                "field",
                "records",
                "known",
                "unknown_or_unpopulated",
                "complete_percent",
            ]
            _, country_rows = load(
                directory / "field_completeness_by_country.tsv", expected_country_header
            )
            _, summary_rows = load(
                directory / "field_completeness_summary.tsv", expected_summary_header
            )
            if {row["stage"] for row in country_rows} != {
                "after_round3",
                "after_round4",
            }:
                errors.append("country report stages missing")
            if len(summary_rows) != 14:
                errors.append("summary report must contain seven fields for two stages")

        except subprocess.TimeoutExpired:
            errors.append("completeness reports: reporter timed out")
        except (
            OSError,
            UnicodeError,
            csv.Error,
            ValueError,
            subprocess.CalledProcessError,
        ) as report_error:
            errors.append(f"completeness reports: {report_error}")

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
        print(f"{field} patches: {sum(bool(row[field]) for row in rows)}")
    print(
        "countries: "
        + ", ".join(
            sorted({base[row["stable_id"]]["country"] for row in rows if row["stable_id"] in base})
        )
    )
    if errors:
        print(f"validation: FAIL ({len(errors)} errors)")
        for error in errors:
            print("ERROR " + error)
        raise SystemExit(1)
    print("validation: PASS")


if __name__ == "__main__":
    main()
