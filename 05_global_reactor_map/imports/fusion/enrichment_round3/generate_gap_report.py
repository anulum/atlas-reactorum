#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment_round3/generate_gap_report.py
"""Build round-3 fusion completeness reports from immutable inputs and overlays."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCHEMA_FIELDS = [
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


def read(path: Path) -> list[dict[str, str]]:
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


def apply(rows: dict[str, dict[str, str]], patches: list[dict[str, str]]) -> None:
    """Apply exact-identifier enrichment patches to the base rows."""
    for patch in patches:
        target = rows[patch["stable_id"]]
        for key, value in patch.items():
            if key != "stable_id" and value.strip():
                target[key] = value


def absent(value: str | None) -> bool:
    """Report whether a field is absent from the row."""
    return not value or value.strip().lower() in {"", "unknown", "n/a", "na"}


def gap(row: dict[str, str], field: str) -> bool:
    """Describe the remaining gap for a field."""
    if field == "coordinates":
        return absent(row.get("latitude")) or absent(row.get("longitude"))
    return absent(row.get(field))


def main() -> None:
    """Generate reports from an explicit native fusion directory without import side effects."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fusion-root", type=Path, default=ROOT)
    parser.add_argument("--report-root", type=Path)
    args = parser.parse_args()
    root = args.fusion_root
    here = root / "enrichment_round3"
    output = args.report_root if args.report_root is not None else here
    try:
        base = read(root / "fusion_facilities.tsv")
        if not base:
            raise ValueError("empty base catalogue")
        rows = {row["stable_id"]: dict(row) for row in base}
        apply(rows, read(root / "enrichment" / "enrichment.tsv"))
        new_rows = read(root / "enrichment" / "new_facilities.tsv")
        for row in new_rows:
            if row["stable_id"] in rows:
                raise ValueError(f"duplicate integrated ID: {row['stable_id']}")
            rows[row["stable_id"]] = dict(row)
        apply(rows, read(root / "enrichment_round2" / "enrichment_round2.tsv"))
        before = {stable_id: dict(row) for stable_id, row in rows.items()}
        apply(rows, read(here / "enrichment_round3.tsv"))
        after = rows

        output.mkdir(parents=True, exist_ok=True)
        with (output / "gap_report_summary.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "field",
                    "missing_before_round3",
                    "missing_after_round3",
                    "filled_by_round3",
                ],
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            for field in SCHEMA_FIELDS:
                old = sum(gap(row, field) for row in before.values())
                new = sum(gap(row, field) for row in after.values())
                writer.writerow(
                    {
                        "field": field,
                        "missing_before_round3": old,
                        "missing_after_round3": new,
                        "filled_by_round3": old - new,
                    }
                )

        countries: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in after.values():
            countries[(row.get("country") or "unknown").strip() or "unknown"].append(row)
        with (output / "gap_report_by_country.tsv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            fields = ["country", "records"] + [f"missing_{field}" for field in SCHEMA_FIELDS]
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for country in sorted(countries):
                group = countries[country]
                out = {"country": country, "records": len(group)}
                out.update(
                    {
                        f"missing_{field}": sum(gap(row, field) for row in group)
                        for field in SCHEMA_FIELDS
                    }
                )
                writer.writerow(out)

        with (output / "GAP_REPORT.md").open("w", encoding="utf-8") as handle:
            handle.write(
                "# Fusion facility enrichment round 3: completeness report\n\nSource-layer date: 2026-09-28\n\n"
            )
            handle.write(
                f"Effective records: **{len(after)}** ({len(base)} base plus {len(new_rows)} round-1 additions).\n\n"
            )
            handle.write(
                "| Field | Missing before | Missing after | Filled |\n|---|---:|---:|---:|\n"
            )
            for field in SCHEMA_FIELDS:
                old = sum(gap(row, field) for row in before.values())
                new = sum(gap(row, field) for row in after.values())
                handle.write(f"| {field} | {old} | {new} | {old - new} |\n")
            handle.write(
                "\nRound 3 found no additional official numeric coordinate pair that passed the non-inference rule. Coordinates therefore remain unchanged. Addresses, map pins, city centroids, and third-party geocoding were not converted into coordinates.\n\n"
            )
            handle.write(
                "The remaining organization gap is T-3. Official Kurchatov/Rosatom material reviewed did not state an exact T-3 ownership or operating relationship clearly enough for an overlay, so the field remains unknown.\n\n"
            )
            handle.write(
                "Raw missing end dates are not equivalent to defects: active and unbuilt records normally have no last-operation date. First-operation dates are likewise inapplicable to planned devices and programmes. Configuration, subtype, and status remain complete.\n\n"
            )
            handle.write(
                "No IAEA FusDIS content was accessed, scraped, or redistributed. Country-level raw counts are in `gap_report_by_country.tsv`.\n"
            )

    except (OSError, UnicodeError, csv.Error, ValueError, KeyError) as error:
        print(f"FAIL: {error}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
