#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment_round3/validate_enrichment_round3.py
"""Validate the exact-ID round-3 overlay and regenerate completeness reports."""

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
PATCH = HERE / "enrichment_round3.tsv"
REGISTRY = HERE / "source_registry.tsv"
DATE = "2026-09-28"
BASE_SHA = "6ce4b68d1904d0785a67a15891963496002c6671e52c95e2ffd6247827cbaab3"
FROZEN_SHA256 = "5ad43c86982c9aa0514c5bb0e6c7ece2b5f5e35a064ac2282899bba003bd7c16"
HEADER = [
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
    expected_base_sha = BASE_SHA if args.base_selection == "public" else FROZEN_SHA256
    root = args.fusion_root
    here = root / "enrichment_round3"
    report_here = args.report_root if args.report_root is not None else here
    base_path = root / "fusion_facilities.tsv"
    try:
        errors: list[str] = []
        if hashlib.sha256(base_path.read_bytes()).hexdigest() != expected_base_sha:
            errors.append("base checksum changed")
        base_header, base = read(base_path)
        new_header, new = read(root / "enrichment" / "new_facilities.tsv")
        patch_header, patches = read(here / "enrichment_round3.tsv")
        if base_header != HEADER or new_header != HEADER or patch_header != HEADER:
            errors.append("unexpected facility schema")
        valid_ids = {row["stable_id"] for row in base + new}
        seen: set[str] = set()
        for line, row in enumerate(patches, 2):
            stable_id = row["stable_id"]
            if stable_id in seen or not stable_id:
                errors.append(f"line {line}: duplicate or blank stable_id")
            seen.add(stable_id)
            if stable_id not in valid_ids:
                errors.append(f"line {line}: non-integrated stable_id {stable_id}")
            if row["retrieved_date"] != DATE:
                errors.append(f"line {line}: wrong retrieval date")
            if any(
                not row[field].strip()
                for field in ["source_url", "source_role", "license", "verification_evidence_notes"]
            ):
                errors.append(f"line {line}: incomplete provenance")
            if any(not valid_https_url(url.strip()) for url in row["source_url"].split("|")):
                errors.append(f"line {line}: invalid HTTPS source URL")
            if row["latitude"] or row["longitude"]:
                errors.append(f"line {line}: round 3 must not add coordinates")
            for field in ["first_operation_date", "last_operation_date"]:
                if not valid_date(row[field]):
                    errors.append(f"line {line}: invalid {field}")

        _, sources = read(here / "source_registry.tsv")
        if not any(row["source_id"] == "excluded-iaea-fusdis" for row in sources):
            errors.append("missing FusDIS exclusion")
        if any(row["retrieved_date"] != DATE for row in sources):
            errors.append("wrong source-registry retrieval date")
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
        expected = {
            "coordinates": {"public": ("155", "155"), "frozen": ("141", "141")}[
                args.base_selection
            ],
            "configuration": ("0", "0"),
            "device_subtype": ("0", "0"),
            "status": ("0", "0"),
            "organization": ("1", "1"),
            "first_operation_date": {"public": ("131", "120"), "frozen": ("128", "117")}[
                args.base_selection
            ],
            "last_operation_date": ("146", "143"),
        }
        for row in summary:
            pair = (row["missing_before_round3"], row["missing_after_round3"])
            if pair != expected[row["field"]]:
                errors.append(f"unexpected coverage for {row['field']}: {pair}")
        if len(valid_ids) != 157:
            errors.append(f"effective ID count {len(valid_ids)} is not 157")
        if errors:
            print("FAIL")
            for error in errors:
                print(f"- {error}")
            raise SystemExit(1)
        print(f"PASS: {len(patches)} exact-ID overlays; 157 effective records; reports regenerated")

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
