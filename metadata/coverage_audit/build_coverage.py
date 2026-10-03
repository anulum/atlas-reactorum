#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/coverage_audit/build_coverage.py
"""Generate a deterministic field-completeness snapshot for the integrated atlas.

The snapshot date identifies the local integration revision. Original source
check dates remain attached to each record and are not refreshed by this build.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "04_interactive_presentation/data"
OUT = Path(__file__).resolve().parent


def records_of(document: Any) -> list[dict[str, Any]]:
    """Return the record list from a dataset document.

    Parameters
    ----------
    document : Any
        A parsed dataset, either the wrapped object form or a bare array.

    Returns
    -------
    list of dict
        The records it carries.
    """
    if isinstance(document, dict):
        wrapped: list[dict[str, Any]] = document["records"]
        return wrapped
    bare: list[dict[str, Any]] = document
    return bare


def missing(value: object) -> bool:
    """Report whether a field was not supplied by its source.

    Parameters
    ----------
    value : object
        The raw field value.

    Returns
    -------
    bool
        True when the source supplied nothing. Whitespace counts as absent;
        a field present but empty is not evidence of a value.
    """
    return value is None or str(value).strip() == ""


def counter(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    """Tally how many rows carry each value of a field.

    Parameters
    ----------
    rows : iterable of mapping
        The records to tally.
    key : str
        The field to group by.

    Returns
    -------
    dict
        Value to count, ordered by value so the output is deterministic.
    """
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def main(argv: list[str] | None = None) -> None:
    """Write the coverage snapshot as JSON and as a readable report.

    Parameters
    ----------
    argv : list of str or None
        Command-line arguments. ``--data-dir`` and ``--out-dir`` let a caller
        read and write elsewhere, which is how the tests run this as a real
        process instead of substituting module state.

    Notes
    -----
    The Markdown report retains the repository provenance in a hidden HTML
    comment. Counts and original source-check dates remain unchanged.
    """
    global DATA, OUT
    parser = argparse.ArgumentParser(description="Build the coverage snapshot.")
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    arguments = parser.parse_args(argv)
    DATA = arguments.data_dir
    OUT = arguments.out_dir
    OUT.mkdir(parents=True, exist_ok=True)
    facilities = records_of(
        json.loads((DATA / "global_reactors.sample.json").read_text(encoding="utf-8"))
    )
    companies = records_of(
        json.loads((DATA / "fusion_companies.sample.json").read_text(encoding="utf-8"))
    )
    repositories = records_of(
        json.loads((DATA / "anulum_reactor_repos.json").read_text(encoding="utf-8"))
    )
    with (DATA / "taxonomy-expanded.sources.tsv").open(encoding="utf-8", newline="") as handle:
        taxonomy = list(csv.DictReader(handle, delimiter="\t"))

    fields: dict[str, Callable[[Mapping[str, Any]], bool]] = {
        "coordinates": lambda row: missing(row.get("lat")) or missing(row.get("lon")),
        "type": lambda row: missing(row.get("type")),
        "operator_or_organization": lambda row: (
            missing(row.get("operator")) and missing(row.get("organization"))
        ),
        "purpose": lambda row: missing(row.get("purpose")),
        "fuel_or_feed": lambda row: missing(row.get("fuel_or_feed")),
        "start_or_criticality_date": lambda row: all(
            missing(row.get(k)) for k in ("start_date", "first_criticality", "first_operation")
        ),
        "source_checked": lambda row: missing(row.get("source_checked")),
    }
    missing_totals = {name: sum(test(row) for row in facilities) for name, test in fields.items()}
    by_kind: defaultdict[str, dict[str, int]] = defaultdict(dict)
    for kind in sorted({row.get("record_kind") or "unknown" for row in facilities}):
        subset = [row for row in facilities if (row.get("record_kind") or "unknown") == kind]
        by_kind[kind] = {
            "records": len(subset),
            **{name: sum(test(row) for row in subset) for name, test in fields.items()},
        }

    unknown_status = sum(
        missing(row.get("status"))
        or str(row.get("status")).lower() in {"unknown", "status uncertain"}
        or "not asserted" in str(row.get("status")).lower()
        for row in facilities
    )
    report: dict[str, Any] = {
        "snapshot_date": "2026-10-02",
        "count_definition": "Overlapping discovery records; not unique physical reactor vessels.",
        "taxonomy": {
            "records": len(taxonomy),
            "audited_records": sum(
                not str(row.get("source_audit", "")).startswith("Introductory") for row in taxonomy
            ),
            "pending_records": sum(
                str(row.get("source_audit", "")).startswith("Introductory") for row in taxonomy
            ),
            "by_domain": counter(taxonomy, "domain"),
            "by_kind": counter(taxonomy, "kind"),
            "source_audit_labels": counter(taxonomy, "source_audit"),
        },
        "facilities": {
            "field_semantics": {
                "purpose": "Published purpose or end use; not independently verified operation.",
                "fuel_or_feed": "Published feedstock or publisher whole-plant fuel classification; not reactor fuel composition.",
            },
            "records": len(facilities),
            "mapped": sum(
                not missing(row.get("lat")) and not missing(row.get("lon")) for row in facilities
            ),
            "by_domain": counter(facilities, "domain"),
            "by_record_kind": counter(facilities, "record_kind"),
            "by_dataset": counter(facilities, "dataset_source"),
            "by_country": counter(facilities, "country"),
            "unknown_or_nonasserted_status": unknown_status,
            "missing_fields": missing_totals,
            "missing_fields_by_record_kind": dict(by_kind),
        },
        "companies_and_programmes": {
            "records": len(companies),
            "by_country": counter(companies, "country"),
            "by_identity_class": counter(companies, "identity_class"),
            "by_evidence_tier": counter(companies, "evidence"),
            "by_confidence": counter(companies, "confidence"),
            "missing_independent_evidence": sum(
                missing(row.get("independent_evidence")) for row in companies
            ),
            "missing_named_device_or_project": sum(
                missing(row.get("public_devices_projects")) and missing(row.get("devices/projects"))
                for row in companies
            ),
            "explicit_fuel_cycle": sum(not missing(row.get("fuel_cycle")) for row in companies),
            "missing_explicit_fuel_cycle": sum(missing(row.get("fuel_cycle")) for row in companies),
        },
        "anulum_repositories": {
            "records": len(repositories),
            "by_category": counter(repositories, "category"),
            "missing_license_label": sum(missing(row.get("license")) for row in repositories),
        },
        "limitations": [
            "A missing-field count is a research backlog, not proof that the fact is unavailable.",
            "Industrial registries describe sites and activities; they usually do not enumerate reactor vessels.",
            "Company inclusion documents an organization or claim and does not validate performance.",
            "Current-status facts can change after the stated source-check date.",
        ],
    }
    (OUT / "coverage.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "<!--",
        "SPDX-License-"  # Keep the generated tag separate from this file licence.
        "Identifier: AGPL-3.0-or-later",
        "Commercial license available",
        "\N{COPYRIGHT SIGN} Concepts 1996–2026 Miroslav Šotek. All rights reserved.",
        "\N{COPYRIGHT SIGN} Code 2020–2026 Miroslav Šotek. All rights reserved.",
        "ORCID: 0009-0009-3560-0851",
        "Contact: www.anulum.li | protoscience@anulum.li",
        "Atlas Reactorum — metadata/coverage_audit/COVERAGE.md",
        "-->",
        "",
        "# Atlas coverage audit",
        "",
        f"Snapshot: {report['snapshot_date']}",
        "",
        f"- Taxonomy entries: {len(taxonomy):,}",
        f"- Taxonomy entries with first-pass scientific/editorial audit: {report['taxonomy']['audited_records']:,}",
        f"- Taxonomy entries pending first-pass audit: {report['taxonomy']['pending_records']:,}",
        f"- Facility/project records: {len(facilities):,}",
        f"- Mapped facility/project records: {report['facilities']['mapped']:,}",
        f"- Company/programme records: {len(companies):,}",
        f"- ANULUM repositories: {len(repositories):,}",
        "",
        "## Facility field backlog",
        "",
        "Fuel/feed availability includes publisher classifications; it does not establish reactor fuel composition or current operation.",
        "",
        "| Field | Missing records |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name.replace('_', ' ')} | {count:,} |" for name, count in missing_totals.items()
    )
    lines.extend(
        [
            f"| unknown or explicitly non-asserted status | {unknown_status:,} |",
            "",
            "## Facility records by domain",
            "",
            "| Domain | Records |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {domain} | {count:,} |" for domain, count in report["facilities"]["by_domain"].items()
    )
    lines.extend(
        [
            "",
            "## Company and programme field backlog",
            "",
            "| Field | Records |",
            "|---|---:|",
            f"| explicit project-bounded fuel cycle | {report['companies_and_programmes']['explicit_fuel_cycle']:,} |",
            f"| missing explicit project-bounded fuel cycle | {report['companies_and_programmes']['missing_explicit_fuel_cycle']:,} |",
            f"| missing independent-evidence summary | {report['companies_and_programmes']['missing_independent_evidence']:,} |",
            f"| missing named device or project | {report['companies_and_programmes']['missing_named_device_or_project']:,} |",
            "",
            "See `coverage.json` for breakdowns by record kind, dataset, country, evidence tier and identity class.",
            "",
            "Counts measure the current snapshot and expose research gaps. They do not establish global completeness or unique physical-reactor totals.",
        ]
    )
    (OUT / "COVERAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "facilities": len(facilities),
                "mapped": report["facilities"]["mapped"],
                "companies": len(companies),
                "taxonomy": len(taxonomy),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
