#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round5/generate_gap_report.py
"""Generate deterministic research-reactor gaps before and after round 5."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "research_reactors.tsv"
ROUND_FILES = [
    ROOT / "enrichment" / "research_reactor_enrichment.tsv",
    ROOT / "enrichment_round2" / "research_reactor_enrichment_round2.tsv",
    ROOT / "enrichment_round3" / "research_reactor_enrichment_round3.tsv",
    ROOT / "enrichment_round4" / "research_reactor_enrichment_round4.tsv",
    HERE / "research_reactor_enrichment_round5.tsv",
]
FIELDS = [
    "coordinates",
    "status",
    "reactor_type",
    "thermal_power_mw",
    "operator",
    "purpose",
    "first_criticality",
    "shutdown_date",
]
LABELS = {
    "coordinates": "unknown_coordinates",
    "status": "unknown_status",
    "reactor_type": "unknown_or_generic_reactor_type",
    "thermal_power_mw": "unknown_thermal_power_mw",
    "operator": "unknown_operator",
    "purpose": "unknown_purpose",
    "first_criticality": "unknown_first_criticality",
    "shutdown_date": "unpopulated_shutdown_date",
}
MERGE_FIELDS = {
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
}


def load(path: Path) -> list[dict[str, str]]:
    """Read catalogue rows without altering their recorded source values.

    Parameters
    ----------
    path : pathlib.Path
        Base catalogue or enrichment TSV.

    Returns
    -------
    list of dict
        Source rows in file order.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def missing(field: str, row: dict[str, str]) -> bool:
    """Classify incomplete coordinates and recorded source facts.

    Parameters
    ----------
    field : str
        Report field, including the latitude/longitude coordinate pair.
    row : dict
        Effective catalogue row.

    Returns
    -------
    bool
        Whether either coordinate is absent or the fact lacks a specific value.
    """
    if field == "coordinates":
        return not row["lat"].strip() or not row["lon"].strip()
    value = row[field].strip().lower()
    if value in {"", "unknown"}:
        return True
    return field == "reactor_type" and value == "research reactor"


def effective(base_rows: list[dict[str, str]], patches: list[Path]) -> list[dict[str, str]]:
    """Apply nonempty fact overlays in their chronological order.

    Parameters
    ----------
    base_rows : list of dict
        Base catalogue, retained without mutation.
    patch_files : list of pathlib.Path
        Accepted enrichment layers, oldest first.

    Returns
    -------
    list of dict
        Copies of base rows with later nonempty facts applied.
    """
    by_id = {row["stable_id"]: row.copy() for row in base_rows}
    for path in patches:
        for patch in load(path):
            target = by_id[patch["stable_id"]]
            for field in MERGE_FIELDS:
                if patch.get(field):
                    target[field] = patch[field]
    return list(by_id.values())


def aggregate(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    """Count records and incomplete fields by recorded country.

    Parameters
    ----------
    rows : list of dict
        Effective catalogue after the selected overlays.

    Returns
    -------
    dict
        Per-country record and incomplete-field totals. Blank countries
        are counted under ``(unknown country)``.
    """
    result: dict[str, dict[str, int]] = defaultdict(
        lambda: {"records": 0, **{LABELS[field]: 0 for field in FIELDS}}
    )
    for row in rows:
        country = row["country"] or "(unknown country)"
        result[country]["records"] += 1
        for field in FIELDS:
            if missing(field, row):
                result[country][LABELS[field]] += 1
    return dict(result)


def main() -> None:
    """Generate both round5 gap stages for the selected data and output directories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    base = load(args.research_root / "research_reactors.tsv")
    patch_files = [args.research_root / path.relative_to(ROOT) for path in ROUND_FILES]
    stages = {
        "before_round5": effective(base, patch_files[:4]),
        "after_round5": effective(base, patch_files),
    }
    country_columns = ["stage", "country", "records", *LABELS.values()]
    with (args.output_dir / "field_completeness_by_country.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", fieldnames=country_columns, lineterminator="\n"
        )
        writer.writeheader()
        for stage, rows in stages.items():
            for country, counts in sorted(aggregate(rows).items()):
                writer.writerow({"stage": stage, "country": country, **counts})

    summary = []
    for stage, rows in stages.items():
        for field in FIELDS:
            unknown = sum(missing(field, row) for row in rows)
            known = len(rows) - unknown
            summary.append(
                {
                    "stage": stage,
                    "field": LABELS[field],
                    "records": len(rows),
                    "known": known,
                    "unknown_or_unpopulated": unknown,
                    "complete_percent": f"{known / len(rows) * 100:.1f}",
                }
            )
    with (args.output_dir / "field_completeness_summary.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", fieldnames=list(summary[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(summary)

    before = {row["field"]: row for row in summary if row["stage"] == "before_round5"}
    after = {row["field"]: row for row in summary if row["stage"] == "after_round5"}
    report = [
        "# Research-reactor round-5 gap report",
        "",
        "Generated 2026-09-28 from all 172 base IDs. The baseline applies rounds 1-4; the comparison then applies round 5.",
        "",
        "Coordinates are complete only when both latitude and longitude are populated. No round-5 coordinates were added because none of the selected official records published a numeric pair. Generic `research reactor` is counted as an incomplete type. Shutdown-date population is reported without implying that the field applies to operating reactors.",
        "",
        "| Field | Unknown before | Unknown after | Reduction | After completeness |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in LABELS.values():
        b = int(str(before[label]["unknown_or_unpopulated"]))
        a = int(str(after[label]["unknown_or_unpopulated"]))
        report.append(f"| `{label}` | {b} | {a} | {b - a} | {after[label]['complete_percent']}% |")
    report += [
        "",
        "Country-level before/after counts are in `field_completeness_by_country.tsv`; global machine-readable counts are in `field_completeness_summary.tsv`.",
        "",
    ]
    (args.output_dir / "field_completeness_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
