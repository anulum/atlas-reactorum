#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round4/generate_completeness_report.py
"""Generate field-completeness reports after round 3 and after round 4."""

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
    HERE / "research_reactor_enrichment_round4.tsv",
]
FIELDS = [
    "status",
    "reactor_type",
    "thermal_power_mw",
    "operator",
    "purpose",
    "first_criticality",
    "shutdown_date",
]
REPORT_LABELS = {
    "status": "unknown_status",
    "reactor_type": "unknown_or_generic_reactor_type",
    "thermal_power_mw": "unknown_thermal_power_mw",
    "operator": "unknown_operator",
    "purpose": "unknown_purpose",
    "first_criticality": "unknown_first_criticality",
    "shutdown_date": "unpopulated_shutdown_date",
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


def missing(field: str, value: str) -> bool:
    """Classify missing facts and the generic research-reactor type.

    Parameters
    ----------
    field : str
        Catalogue field whose completeness is counted.
    value : str
        Recorded source value.

    Returns
    -------
    bool
        Whether the value is blank, unknown, or a generic reactor type.
    """
    normalized = value.strip().lower()
    if normalized in {"", "unknown"}:
        return True
    return field == "reactor_type" and normalized == "research reactor"


def effective(base_rows: list[dict[str, str]], patch_files: list[Path]) -> list[dict[str, str]]:
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
    overlays: dict[str, dict[str, str]] = {}
    for path in patch_files:
        for row in load(path):
            overlays.setdefault(row["stable_id"], {}).update(
                {key: value for key, value in row.items() if value and key in FIELDS}
            )
    result = []
    for row in base_rows:
        merged = row.copy()
        merged.update(overlays.get(row["stable_id"], {}))
        result.append(merged)
    return result


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
        lambda: {"records": 0, **{REPORT_LABELS[field]: 0 for field in FIELDS}}
    )
    for row in rows:
        country = row["country"] or "(unknown country)"
        result[country]["records"] += 1
        for field in FIELDS:
            if missing(field, row[field]):
                result[country][REPORT_LABELS[field]] += 1
    return dict(result)


def main() -> None:
    """Generate both completeness stages for the selected data and output directories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    base_rows = load(args.research_root / "research_reactors.tsv")
    patch_files = [args.research_root / path.relative_to(ROOT) for path in ROUND_FILES]
    stages = {
        "after_round3": effective(base_rows, patch_files[:3]),
        "after_round4": effective(base_rows, patch_files),
    }
    by_country_path = args.output_dir / "field_completeness_by_country.tsv"
    columns = ["stage", "country", "records", *REPORT_LABELS.values()]
    with by_country_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for stage, rows in stages.items():
            for country, values in sorted(aggregate(rows).items()):
                writer.writerow({"stage": stage, "country": country, **values})

    global_rows = []
    for stage, rows in stages.items():
        for field in FIELDS:
            unknown = sum(missing(field, row[field]) for row in rows)
            known = len(rows) - unknown
            global_rows.append(
                {
                    "stage": stage,
                    "field": REPORT_LABELS[field],
                    "records": len(rows),
                    "known": known,
                    "unknown_or_unpopulated": unknown,
                    "complete_percent": f"{known / len(rows) * 100:.1f}",
                }
            )
    summary_path = args.output_dir / "field_completeness_summary.tsv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", fieldnames=list(global_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(global_rows)

    before = {r["field"]: r for r in global_rows if r["stage"] == "after_round3"}
    after = {r["field"]: r for r in global_rows if r["stage"] == "after_round4"}
    report = [
        "# Research-reactor field completeness",
        "",
        "Generated 2026-09-28 from the 172-row base plus non-empty overlay values. The baseline is the effective state after rounds 1-3; the comparison includes round 4.",
        "",
        "`unknown_or_generic_reactor_type` counts blank, `unknown`, and the generic placeholder `research reactor` as incomplete. Other fields count only blank or `unknown`. An unpopulated shutdown date is not necessarily a defect for an operating reactor; it is reported as field population, not applicability.",
        "",
        "| Field | Unknown after round 3 | Unknown after round 4 | Reduction | Round-4 completeness |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in REPORT_LABELS.values():
        b = int(str(before[label]["unknown_or_unpopulated"]))
        a = int(str(after[label]["unknown_or_unpopulated"]))
        report.append(f"| `{label}` | {b} | {a} | {b - a} | {after[label]['complete_percent']}% |")
    report.extend(
        [
            "",
            "Country-level counts for both stages are in `field_completeness_by_country.tsv`; machine-readable global totals are in `field_completeness_summary.tsv`.",
            "",
        ]
    )
    (args.output_dir / "field_completeness_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
