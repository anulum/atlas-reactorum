#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round5/validate.py
"""Validate persisted round-5 company overlays without rebuilding or promoting them."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATE = "2026-09-28"
EXPECTED = {
    "Alpha Ring",
    "MIFTI",
    "Electric Fusion Systems",
    "Crossfield Fusion",
    "Astral Systems",
    "Deutelio",
}
GAP_MAPPING = {
    "status": "normalized_status",
    "source_date": "source_dates",
    "milestone": "highest_independently_supported_milestone",
}
OVERLAY_FIELDS = [
    "organization",
    "match_rule",
    "source_record_id",
    "fields_enriched",
    "enriched_identity_class",
    "enriched_status",
    "enriched_country",
    "enriched_approach_configuration",
    "enriched_named_devices_projects",
    "enriched_fuel_cycle",
    "enriched_highest_independently_supported_milestone",
    "enriched_unsupported_or_ambiguous_claims",
    "enriched_official_url",
    "enriched_independent_urls",
    "source_ids",
    "source_dates",
    "audit_date",
    "confidence",
    "overlay_note",
]
SOURCE_FIELDS = [
    "source_id",
    "organization",
    "title",
    "publisher",
    "source_type",
    "source_date",
    "url",
    "supports",
    "limitations",
    "accessed_on",
]
CLOSURE_FIELDS = [
    "organization",
    "source_record_id",
    "round4_gap_fields",
    "fields_closed",
    "remaining_explicit_limitations",
    "round5_disposition",
    "audit_date",
]
GAP_FIELDS = [
    "record_id",
    "source_catalog",
    "source_row",
    "organization",
    "country",
    "identity_class",
    "normalized_status",
    "approach_configuration",
    "named_devices_projects",
    "fuel_cycle",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "official_url",
    "independent_sources",
    "source_dates",
    "confidence",
    "evidence_tier",
    "status_completeness",
    "identity_completeness",
    "approach_completeness",
    "device_completeness",
    "fuel_cycle_completeness",
    "milestone_completeness",
    "unsupported_claims_completeness",
    "official_url_completeness",
    "independent_source_completeness",
    "source_date_completeness",
    "country_completeness",
    "confidence_completeness",
    "gap_count",
    "priority_score",
    "priority_band",
    "gap_fields",
]


def read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a persisted table with its exact producer schema.

    Parameters
    ----------
    path : pathlib.Path
        Overlay, source, closure or previous gap-matrix TSV.
    fields : list of str
        Ordered schema of the selected producer table.

    Returns
    -------
    list of dict
        Original nonempty rows without changing their claim or evidence text.

    Raises
    ------
    ValueError
        If the header, row shape or record count is structurally invalid.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty table")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return rows


def valid_url(value: str) -> bool:
    """Check HTTPS syntax without fetching or validating remote source contents.

    Parameters
    ----------
    value : str
        Recorded official or independent evidence link.

    Returns
    -------
    bool
        Whether the link has an HTTPS scheme and a populated authority.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    """Check persisted identity, provenance and gap closure through the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=HERE)
    parser.add_argument(
        "--gap-matrix", type=Path, default=HERE.parent / "depth_round4/gap_matrix.tsv"
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report_path = args.report or args.directory / "validation.json"
    paths = [
        args.directory / name
        for name in ("enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv")
    ]
    if report_path.resolve() in {p.resolve() for p in [*paths, args.gap_matrix]}:
        print("VALIDATION FAILED: report would replace a source input")
        raise SystemExit(1)
    try:
        overlays = read(paths[0], OVERLAY_FIELDS)
        sources = read(paths[1], SOURCE_FIELDS)
        closures = read(paths[2], CLOSURE_FIELDS)
        gaps = read(args.gap_matrix, GAP_FIELDS)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"VALIDATION FAILED: {error}")
        raise SystemExit(1) from None
    errors: list[str] = []
    old = {row["organization"]: row for row in gaps}
    if len(old) != len(gaps) or any(not name.strip() for name in old):
        errors.append("previous gap matrix has duplicate or blank identities")
    overlay_by_name = {row["organization"]: row for row in overlays}
    closure_by_name = {row["organization"]: row for row in closures}
    if set(overlay_by_name) != EXPECTED or len(overlays) != 6:
        errors.append("expected six unique overlay targets")
    if set(closure_by_name) != EXPECTED or len(closures) != 6:
        errors.append("expected six unique closure targets")
    source_by_id = {row["source_id"]: row for row in sources}
    if (
        len(sources) != 18
        or len(source_by_id) != 18
        or any(not key.strip() for key in source_by_id)
    ):
        errors.append("expected 18 unique nonempty sources")
    if Counter(row["organization"] for row in sources) != Counter(dict.fromkeys(EXPECTED, 3)):
        errors.append("expected three sources per target")
    for row in overlays:
        name = row["organization"]
        if row["match_rule"] != "exact normalized organization name":
            errors.append(f"non-exact match: {name}")
        if row["audit_date"] != DATE:
            errors.append(f"bad audit date: {name}")
        for field in (
            "enriched_status",
            "enriched_named_devices_projects",
            "enriched_fuel_cycle",
            "enriched_highest_independently_supported_milestone",
            "enriched_unsupported_or_ambiguous_claims",
            "source_dates",
            "source_record_id",
            "fields_enriched",
            "overlay_note",
        ):
            if not row[field].strip():
                errors.append(f"blank {field}: {name}")
        urls = [
            row["enriched_official_url"],
            *[u.strip() for u in row["enriched_independent_urls"].split(";") if u.strip()],
        ]
        for url in urls:
            if not valid_url(url):
                errors.append(f"bad overlay URL: {name}")
        ids = row["source_ids"].split(";")
        if (
            len(ids) != 3
            or len(set(ids)) != len(ids)
            or any(
                key not in source_by_id or source_by_id[key]["organization"] != name for key in ids
            )
        ):
            errors.append(f"invalid source association: {name}")
        if name not in old:
            errors.append(f"missing previous target: {name}")
            continue
        previous = old[name]
        if previous["priority_band"] != "high" or previous["record_id"] != row["source_record_id"]:
            errors.append(f"previous high-priority identity mismatch: {name}")
        if name not in closure_by_name:
            errors.append(f"missing closure: {name}")
            continue
        closure = closure_by_name[name]
        before = previous["gap_fields"].split(";")
        enriched = set(row["fields_enriched"].split(";"))
        closed = [field for field in before if GAP_MAPPING.get(field, field) in enriched]
        disposition = (
            "closed with bounded evidence"
            if len(closed) == len(before)
            else "partially closed; explicit negative finding retained"
        )
        expected = {
            "source_record_id": row["source_record_id"],
            "round4_gap_fields": previous["gap_fields"],
            "fields_closed": ";".join(closed),
            "remaining_explicit_limitations": row["overlay_note"],
            "round5_disposition": disposition,
            "audit_date": DATE,
        }
        if any(closure[field] != value for field, value in expected.items()):
            errors.append(f"closure differs from bounded overlay and previous gaps: {name}")
    for row in sources:
        if not valid_url(row["url"]):
            errors.append(f"bad source URL: {row['source_id']}")
        if not row["limitations"].strip():
            errors.append(f"missing source limitation: {row['source_id']}")
        if row["accessed_on"] != DATE:
            errors.append(f"bad source access date: {row['source_id']}")
    report = {
        "audit_date": DATE,
        "valid": not errors,
        "overlay_count": len(overlays),
        "source_count": len(sources),
        "gap_closure_count": len(closures),
        "errors": errors,
    }
    try:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"VALIDATION FAILED: cannot write report: {error}")
        raise SystemExit(1) from None
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
