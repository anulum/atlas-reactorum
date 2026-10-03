#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment_round2/generate_gap_report.py
"""Rebuild completeness reports for the effective fusion dataset and round-2 overlay."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "fusion_facilities.tsv"
ROUND1_PATCH = ROOT / "enrichment" / "enrichment.tsv"
ROUND1_NEW = ROOT / "enrichment" / "new_facilities.tsv"
ROUND2 = HERE / "enrichment_round2.tsv"
TRACKED = [
    "coordinates",
    "configuration",
    "device_subtype",
    "status",
    "organization",
    "first_operation_date",
    "last_operation_date",
]


FIELDS = [
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


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Read the tab-separated source into rows."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    ids = [row["stable_id"] for row in rows]
    if any(not identity for identity in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"{path.name}: blank or duplicate stable_id")
    return rows


def missing(value: str | None) -> bool:
    """Report whether a field was not supplied by its source."""
    return not value or value.strip().lower() in {"", "unknown", "n/a", "na"}


def field_missing(row: dict[str, str], field: str) -> bool:
    """Report whether a row's field was not supplied by its source."""
    return (
        (missing(row.get("latitude")) or missing(row.get("longitude")))
        if field == "coordinates"
        else missing(row.get(field))
    )


def overlay(records: dict[str, dict[str, str]], rows: list[dict[str, str]]) -> None:
    """Build one overlay row for the gap report."""
    for patch in rows:
        target = records[patch["stable_id"]]
        for key, value in patch.items():
            if key != "stable_id" and value.strip():
                target[key] = value


def main() -> None:
    """Generate reports from an explicit native fusion directory without import side effects."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fusion-root", type=Path, default=ROOT)
    parser.add_argument("--report-root", type=Path)
    args = parser.parse_args()
    root = args.fusion_root
    here = root / "enrichment_round2"
    output = args.report_root if args.report_root is not None else here
    try:
        base_rows = read_tsv(root / "fusion_facilities.tsv")
        if not base_rows:
            raise ValueError("empty base catalogue")
        round1_new = read_tsv(root / "enrichment/new_facilities.tsv")
        records = {row["stable_id"]: dict(row) for row in base_rows}
        overlay(records, read_tsv(root / "enrichment/enrichment.tsv"))
        for row in round1_new:
            if row["stable_id"] in records:
                raise ValueError(f"duplicate round-1 new ID: {row['stable_id']}")
            records[row["stable_id"]] = dict(row)
        before = {stable_id: dict(row) for stable_id, row in records.items()}
        overlay(records, read_tsv(here / "enrichment_round2.tsv"))
        after = records

        by_country: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in after.values():
            by_country[(row.get("country") or "unknown").strip() or "unknown"].append(row)

        output.mkdir(parents=True, exist_ok=True)
        with (output / "gap_report_by_country.tsv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            fields = ["country", "records"] + [f"missing_{field}" for field in TRACKED]
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for country in sorted(by_country):
                rows = by_country[country]
                out = {"country": country, "records": len(rows)}
                out.update(
                    {
                        f"missing_{field}": sum(field_missing(row, field) for row in rows)
                        for field in TRACKED
                    }
                )
                writer.writerow(out)

        with (output / "gap_report_summary.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "field",
                    "missing_before_round2",
                    "missing_after_round2",
                    "filled_by_round2",
                ],
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            for field in TRACKED:
                prior = sum(field_missing(row, field) for row in before.values())
                current = sum(field_missing(row, field) for row in after.values())
                writer.writerow(
                    {
                        "field": field,
                        "missing_before_round2": prior,
                        "missing_after_round2": current,
                        "filled_by_round2": prior - current,
                    }
                )

        statuses = Counter(row.get("status", "") for row in after.values())
        with (output / "GAP_REPORT.md").open("w", encoding="utf-8") as handle:
            handle.write(
                "# Fusion facility round-2 gap report\n\nSource-layer date: 2026-09-28\n\n"
            )
            handle.write(
                f"Effective records: **{len(after)}** ({len(base_rows)} base plus {len(round1_new)} round-1 additions).\n\n"
            )
            handle.write(
                "Counts are calculated from the explicitly selected inputs. The public compilation selection omits the separately unqualified original Wikidata positions and dates; the complete frozen input route preserves them. The two round-2 coordinate additions remain explicitly attributed CEA host-campus points, not machine surveys.\n\n"
            )
            handle.write(
                "| Field | Missing before | Missing after | Filled |\n|---|---:|---:|---:|\n"
            )
            for field in TRACKED:
                prior = sum(field_missing(row, field) for row in before.values())
                current = sum(field_missing(row, field) for row in after.values())
                handle.write(f"| {field} | {prior} | {current} | {prior - current} |\n")
            handle.write(
                "\n`last_operation_date` is intentionally blank for most operating, planned, and under-construction records. Its raw missing count is not a defect count; applicability is lifecycle-dependent. Likewise, first-operation dates are not expected for unbuilt programmes.\n\n"
            )
            handle.write(
                "Configuration, subtype, and status were complete before this pass. The status overlay for JT-60SA is a current, source-stated upgrade phase. No generalized vocabulary normalisation is attempted here.\n\n"
            )
            handle.write(
                "Coordinate policy: only source-published coordinates tied to an unambiguous host facility are allowed. The two new coordinate pairs are the CEA-published GPS point for the Cadarache centre hosting WEST and its Tore Supra predecessor. They are marked campus-level and are not building surveys. No city centroid, geocoder, map click, or inferred coordinate is used.\n\n"
            )
            handle.write(
                "IAEA FusDIS was not accessed or redistributed.\n\n## Status distribution after round 2\n\n"
            )
            for status, count in sorted(statuses.items()):
                handle.write(f"- {status}: {count}\n")
            handle.write("\nCountry-level raw gap counts are in `gap_report_by_country.tsv`.\n")

    except (OSError, UnicodeError, csv.Error, ValueError, KeyError) as error:
        print(f"FAIL: {error}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
