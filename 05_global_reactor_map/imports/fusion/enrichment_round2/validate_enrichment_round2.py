#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment_round2/validate_enrichment_round2.py
"""Validate round-2 exact-ID fusion overlays and generated reports."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
import subprocess  # nosec B404 # Import creates no process; calls have scoped reviews.
import sys
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "fusion_facilities.tsv"
ROUND1_NEW = ROOT / "enrichment" / "new_facilities.tsv"
PATCH = HERE / "enrichment_round2.tsv"
REGISTRY = HERE / "source_registry.tsv"
EXPECTED_DATE = "2026-09-28"
BASE_SHA256 = "6ce4b68d1904d0785a67a15891963496002c6671e52c95e2ffd6247827cbaab3"
FROZEN_SHA256 = "5ad43c86982c9aa0514c5bb0e6c7ece2b5f5e35a064ac2282899bba003bd7c16"
EXPECTED_HEADER = [
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


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read the tab-separated source into rows."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name}: empty table")
        fields, rows = list(reader.fieldnames), list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return fields, rows


def valid_date(value: str) -> bool:
    """Validate calendar dates at the source's declared precision."""
    if not value:
        return True
    if not re.fullmatch(r"[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?", value):
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
    """Require HTTPS authority and refuse malformed source URL syntax."""
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    """Validate actual source layers and regenerate reports under an explicit root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fusion-root", type=Path, default=ROOT)
    parser.add_argument("--base-selection", choices=("public", "frozen"), default="public")
    parser.add_argument("--report-root", type=Path)
    args = parser.parse_args()
    expected_base_sha = BASE_SHA256 if args.base_selection == "public" else FROZEN_SHA256
    root = args.fusion_root
    here = root / "enrichment_round2"
    report_here = args.report_root if args.report_root is not None else here
    base_path = root / "fusion_facilities.tsv"
    try:
        errors: list[str] = []
        if hashlib.sha256(base_path.read_bytes()).hexdigest() != expected_base_sha:
            errors.append("base fusion_facilities.tsv SHA-256 changed")
        base_header, base_rows = read(base_path)
        new_header, new_rows = read(root / "enrichment/new_facilities.tsv")
        header, rows = read(here / "enrichment_round2.tsv")
        if (
            header != EXPECTED_HEADER
            or base_header != EXPECTED_HEADER
            or new_header != EXPECTED_HEADER
        ):
            errors.append("unexpected facility schema")
        integrated_ids = {row["stable_id"] for row in base_rows + new_rows}
        seen: set[str] = set()
        for line, row in enumerate(rows, 2):
            stable_id = row["stable_id"]
            if not stable_id or stable_id in seen:
                errors.append(f"line {line}: blank or duplicate stable_id {stable_id!r}")
            seen.add(stable_id)
            if stable_id not in integrated_ids:
                errors.append(
                    f"line {line}: stable_id is not in effective 157-record layer: {stable_id}"
                )
            if row["retrieved_date"] != EXPECTED_DATE:
                errors.append(f"line {line}: retrieved_date must be {EXPECTED_DATE}")
            if (
                not row["source_url"]
                or not row["source_role"]
                or not row["license"]
                or not row["verification_evidence_notes"]
            ):
                errors.append(f"line {line}: provenance fields are required")
            if any(not valid_https_url(url.strip()) for url in row["source_url"].split("|")):
                errors.append(f"line {line}: invalid HTTPS source URL")
            for field in ("first_operation_date", "last_operation_date"):
                value = row[field]
                if not valid_date(value):
                    errors.append(f"line {line}: invalid {field}: {value}")
            if bool(row["latitude"]) != bool(row["longitude"]):
                errors.append(f"line {line}: coordinate pair is incomplete")
            if row["latitude"]:
                try:
                    lat, lon = float(row["latitude"]), float(row["longitude"])
                    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                        errors.append(f"line {line}: coordinates out of range")
                except ValueError:
                    errors.append(f"line {line}: coordinates are not numeric")
                if (
                    not row["coordinate_precision"]
                    or "campus" not in row["coordinate_precision"].lower()
                ):
                    errors.append(
                        f"line {line}: coordinate precision must be explicitly campus-level"
                    )

        _, sources = read(here / "source_registry.tsv")
        if not any(row["source_id"] == "excluded-iaea-fusdis" for row in sources):
            errors.append("source registry must explicitly record FusDIS exclusion")
        for line, row in enumerate(sources, 2):
            if row["retrieved_date"] != EXPECTED_DATE:
                errors.append(f"registry line {line}: retrieved_date must be {EXPECTED_DATE}")
        if errors:
            print("FAIL")
            for error in errors:
                print(f"- {error}")
            raise SystemExit(1)
        command = [sys.executable, str(HERE / "generate_gap_report.py"), "--fusion-root", str(root)]
        if args.report_root is not None:
            command.extend(["--report-root", str(args.report_root)])
        # Fixed sibling script; explicit data/output argv; no shell; finite deadline.
        subprocess.run(  # nosec B603
            command,
            check=True,
            timeout=30,
            capture_output=True,
        )
        _, summary = read(report_here / "gap_report_summary.tsv")
        summary_by_field = {row["field"]: row for row in summary}
        if summary_by_field.get("coordinates", {}).get("missing_after_round2") != (
            "155" if args.base_selection == "public" else "141"
        ):
            errors.append(
                "unexpected incomplete coordinate count for the selected base after round 2"
            )
        if len(integrated_ids) != 157:
            errors.append(f"effective ID count is {len(integrated_ids)}, expected 157")
        if errors:
            print("FAIL")
            for error in errors:
                print(f"- {error}")
            raise SystemExit(1)
        print(
            f"PASS: {len(rows)} exact-ID overlays; 157 effective records; generated reports current"
        )

    except (
        OSError,
        UnicodeError,
        csv.Error,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
    ):
        print("FAIL: source inputs or report outputs are invalid or unavailable")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
