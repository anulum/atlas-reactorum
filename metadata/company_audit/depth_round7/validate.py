#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round7/validate.py
"""Validate persisted round-7 company overlays without rebuilding or promoting them."""

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
    "Princeton Fusion Systems",
    "Proxima Fusion",
    "Renaissance Fusion",
    "First Light Fusion",
    "OpenStar Technologies",
    "Lockheed Martin Compact Fusion Reactor program",
    "Gauss Fusion",
    "Avalanche Energy",
    "EMC2 Fusion Development Corporation",
    "Marvel Fusion",
}
OVERLAY_FIELDS = [
    "organization",
    "match_rule",
    "source_record_id",
    "fields_enriched",
    "enriched_status",
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
    "scope_and_limitations",
    "accessed_on",
]
CLOSURE_FIELDS = [
    "organization",
    "source_record_id",
    "round4_gap_fields",
    "gap_instances_before",
    "fields_closed_or_resolved",
    "gap_instances_resolved",
    "remaining_explicit_negative_findings",
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

GAP_MAPPING = {
    "status": "normalized_status",
    "source_date": "source_dates",
    "milestone": "highest_independently_supported_milestone",
}
HISTORY_FIELDS = {
    "depth_round4": [
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
    ],
    "depth_round5": [
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
    ],
    "depth_round6": [
        "organization",
        "match_rule",
        "source_record_id",
        "fields_enriched",
        "enriched_status",
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
    ],
}


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
    parser.add_argument("--history-directory", type=Path, default=HERE.parent)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report_path = args.report or args.directory / "validation.json"
    paths = [
        args.directory / name
        for name in ("enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv")
    ]
    history_paths = [
        args.history_directory / name / "enrichment_overlays.tsv" for name in HISTORY_FIELDS
    ]
    if report_path.resolve() in {p.resolve() for p in [*paths, args.gap_matrix, *history_paths]}:
        print("VALIDATION FAILED: report would replace a source input")
        raise SystemExit(1)
    try:
        overlays = read(paths[0], OVERLAY_FIELDS)
        sources = read(paths[1], SOURCE_FIELDS)
        closures = read(paths[2], CLOSURE_FIELDS)
        gaps = read(args.gap_matrix, GAP_FIELDS)
        excluded: set[str] = set()
        for name, path in zip(HISTORY_FIELDS, history_paths, strict=True):
            prior = read(path, HISTORY_FIELDS[name])
            names = [row["organization"] for row in prior]
            if len(set(names)) != len(names) or any(not value.strip() for value in names):
                raise ValueError("historical overlays contain duplicate or blank identities")
            excluded.update(names)
        eligible = [
            row
            for row in gaps
            if row["organization"] not in excluded
            and {"fuel_cycle", "status"} & set(row["gap_fields"].split(";"))
        ]
        for row in gaps:
            if int(row["priority_score"]) < 0 or int(row["source_row"]) < 1:
                raise ValueError("invalid previous matrix ranking")
        eligible.sort(key=lambda row: (-int(row["priority_score"]), int(row["source_row"])))
        before_count = sum(int(row["gap_instances_before"]) for row in closures)
        resolved_count = sum(int(row["gap_instances_resolved"]) for row in closures)
        if any(
            int(row[field]) < 0
            for row in closures
            for field in ("gap_instances_before", "gap_instances_resolved")
        ):
            raise ValueError("negative gap accounting")
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"VALIDATION FAILED: {error}")
        raise SystemExit(1) from None
    errors: list[str] = []
    old = {row["organization"]: row for row in gaps}
    if len(old) != len(gaps) or any(not name.strip() for name in old):
        errors.append("previous gap matrix has duplicate or blank identities")
    if [row["organization"] for row in overlays] != [row["organization"] for row in eligible[:10]]:
        errors.append("overlay order/selection does not match deterministic rule")
    if (before_count, resolved_count) != (24, 24):
        errors.append(f"coverage expected 24/24 got {resolved_count}/{before_count}")
    overlay_by_name = {row["organization"]: row for row in overlays}
    closure_by_name = {row["organization"]: row for row in closures}
    if set(overlay_by_name) != EXPECTED or len(overlays) != 10:
        errors.append("expected ten unique overlay targets")
    if set(closure_by_name) != EXPECTED or len(closures) != 10:
        errors.append("expected ten unique closure targets")
    source_by_id = {row["source_id"]: row for row in sources}
    if (
        len(sources) != 30
        or len(source_by_id) != 30
        or any(not key.strip() for key in source_by_id)
    ):
        errors.append("expected 30 unique nonempty sources")
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
        if previous["record_id"] != row["source_record_id"]:
            errors.append(f"previous record identity mismatch: {name}")
        if name not in closure_by_name:
            errors.append(f"missing closure: {name}")
            continue
        closure = closure_by_name[name]
        before = previous["gap_fields"].split(";")
        enriched = set(row["fields_enriched"].split(";"))
        closed = [field for field in before if GAP_MAPPING.get(field, field) in enriched]
        if len(closed) != len(before):
            errors.append(f"incomplete bounded closure: {name}")
        expected = {
            "source_record_id": row["source_record_id"],
            "round4_gap_fields": previous["gap_fields"],
            "gap_instances_before": str(len(before)),
            "fields_closed_or_resolved": ";".join(closed),
            "gap_instances_resolved": str(len(closed)),
            "remaining_explicit_negative_findings": row["overlay_note"],
            "audit_date": DATE,
        }
        if any(closure[field] != value for field, value in expected.items()):
            errors.append(f"closure differs from bounded overlay and previous gaps: {name}")
    for row in sources:
        if not valid_url(row["url"]):
            errors.append(f"bad source URL: {row['source_id']}")
        if not row["scope_and_limitations"].strip():
            errors.append(f"missing source limitation: {row['source_id']}")
        if row["accessed_on"] != DATE:
            errors.append(f"bad source access date: {row['source_id']}")
    report = {
        "audit_date": DATE,
        "valid": not errors,
        "overlay_count": len(overlays),
        "source_count": len(sources),
        "gap_closure_count": len(closures),
        "gap_instances_before": before_count,
        "gap_instances_resolved": resolved_count,
        "project_bounded_fuel_before": "0/10",
        "project_bounded_fuel_after": "10/10" if not errors else "not verified",
        "record_specific_dates_before": "0/10",
        "record_specific_dates_after": "10/10" if not errors else "not verified",
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
