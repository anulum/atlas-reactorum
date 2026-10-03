#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round4/validate.py
"""Validate persisted depth matrices against their source audits and summaries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import runpy
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATE = "2026-09-28"
# Only the canonical, import-safe sibling producer supplies schema/derivation.
# Data arguments cannot select executable code and no builder output is written.
_builder = runpy.run_path(str(HERE / "build.py"))
MATRIX_FIELDS = cast(list[str], _builder["MATRIX_FIELDS"])
OVERLAY_FIELDS = cast(list[str], _builder["OVERLAY_FIELDS"])
BUILD_MATRIX = cast(Callable[[Path], list[dict[str, str]]], _builder["build_matrix"])
KEYS = [
    "status",
    "identity",
    "approach",
    "device",
    "fuel_cycle",
    "milestone",
    "unsupported_claims",
    "official_url",
    "independent_source",
    "source_date",
    "country",
    "confidence",
]
SUMMARY_COLUMNS = [
    "records",
    "complete_records",
    "records_with_gaps",
    "high_priority",
    "medium_priority",
    "low_priority",
    "missing_fuel_cycle",
    "missing_official_url",
]
SUMMARIES = {
    "summary_by_country.tsv": "country",
    "summary_by_identity.tsv": "identity_class",
    "summary_by_evidence_tier.tsv": "evidence_tier",
}
FILES = ["gap_matrix.tsv", "enrichment_overlays.tsv", "overlay_sources.tsv", *SUMMARIES]
SOURCE_FIELDS = [
    "source_id",
    "title",
    "publisher",
    "source_type",
    "source_date",
    "url",
    "scope_and_limitations",
    "accessed_on",
]
CURATED_REFS = {
    row["organization"]: set(row["source_ids"].split(";"))
    for row in cast(list[dict[str, str]], _builder["OVERLAYS"])
}
EXPECTED_OVERLAYS = {"Neo Fusion", "China Fusion Energy Corporation", "Stellarex"}


def read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a persisted output using its exact producer schema.

    Parameters
    ----------
    path : pathlib.Path
        Selected output TSV.
    fields : list of str
        Ordered schema of the actual producer.

    Returns
    -------
    list of dict
        Original nonempty rows without claim normalization.

    Raises
    ------
    ValueError
        If header, row shape or record presence is invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: empty or malformed rows")
    return rows


def valid_url(value: str) -> bool:
    """Check a recorded link's HTTPS authority without fetching its contents.

    Parameters
    ----------
    value : str
        Official or independent evidence link.

    Returns
    -------
    bool
        Whether syntax includes an HTTPS scheme and populated authority.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    """Check persisted outputs without generating or modifying audit evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=HERE)
    parser.add_argument("--audit-root", type=Path, default=HERE.parent)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report_path = args.report or args.directory / "validation.json"
    inputs = [args.directory / name for name in FILES]
    audits = [
        args.audit_root / name
        for name in (
            "audited_companies.tsv",
            "expansion_candidates.tsv",
            "expansion_round2/candidates.tsv",
            "expansion_round3/candidates.tsv",
        )
    ]
    if report_path.resolve() in {path.resolve() for path in [*inputs, *audits]}:
        print("VALIDATION FAILED: report would replace an input")
        raise SystemExit(1)
    try:
        rows = read(inputs[0], MATRIX_FIELDS)
        overlays = read(inputs[1], OVERLAY_FIELDS)
        sources = read(inputs[2], SOURCE_FIELDS)
        summaries = {
            name: read(args.directory / name, [key, *SUMMARY_COLUMNS])
            for name, key in SUMMARIES.items()
        }
        derived = BUILD_MATRIX(args.audit_root)
        hashes = {
            name: hashlib.sha256((args.directory / name).read_bytes()).hexdigest() for name in FILES
        }
        for table in summaries.values():
            if any(int(row[field]) < 0 for row in table for field in SUMMARY_COLUMNS):
                raise ValueError("negative summary count")
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError) as error:
        print(f"VALIDATION FAILED: {error}")
        raise SystemExit(1) from None
    errors: list[str] = []
    if len(rows) != 98 or rows != derived:
        errors.append("matrix differs from source-derived 98-record audit")
    for line, row in enumerate(rows, 2):
        if any(
            not row[key].strip()
            for key in MATRIX_FIELDS
            if key not in {"official_url", "gap_fields"}
        ):
            errors.append(f"matrix line {line}: blank required field")
    ids = [row["record_id"] for row in rows]
    if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
        errors.append("duplicate or blank matrix record_id")
    lookup = {row["record_id"]: row for row in rows}
    if len(overlays) != 3 or {row["organization"] for row in overlays} != EXPECTED_OVERLAYS:
        errors.append("expected three exact overlay targets")
    source_ids = {row["source_id"] for row in sources}
    if len(sources) != 9 or len(source_ids) != 9 or any(not key.strip() for key in source_ids):
        errors.append("expected nine unique source IDs")
    for line, row in enumerate(overlays, 2):
        if any(not row[key].strip() for key in OVERLAY_FIELDS if key != "enriched_official_url"):
            errors.append(f"overlay line {line}: blank required field")
        if row["audit_date"] != DATE or row["match_rule"] != "exact normalized organization name":
            errors.append(f"overlay line {line}: date or match rule")
        base = lookup.get(row["source_record_id"])
        if base is None or base["organization"] != row["organization"]:
            errors.append(f"overlay line {line}: exact-name/record mismatch")
        refs = [key.strip() for key in row["source_ids"].split(";")]
        if (
            len(refs) < 2
            or len(set(refs)) != len(refs)
            or any(
                key not in source_ids or key not in CURATED_REFS.get(row["organization"], set())
                for key in refs
            )
        ):
            errors.append(f"overlay line {line}: source reference problem")
        urls = [url.strip() for url in row["enriched_independent_urls"].split(";")]
        if row["enriched_official_url"]:
            urls.append(row["enriched_official_url"])
        if any(not valid_url(url) for url in urls):
            errors.append(f"overlay line {line}: invalid source URL")
    for line, row in enumerate(sources, 2):
        if any(not row[key].strip() for key in SOURCE_FIELDS):
            errors.append(f"source line {line}: blank field")
        if row["accessed_on"] != DATE or not valid_url(row["url"]):
            errors.append(f"source line {line}: date or URL")
    for name, key in SUMMARIES.items():
        table = summaries[name]
        groups = {row[key] for row in rows}
        if len(table) != len(groups) or {row[key] for row in table} != groups:
            errors.append(f"{name}: duplicate, missing or foreign grouping")
        for row in table:
            items = [item for item in rows if item[key] == row[key]]
            expected = {
                "records": len(items),
                "complete_records": sum(item["gap_count"] == "0" for item in items),
                "records_with_gaps": sum(item["gap_count"] != "0" for item in items),
                **{
                    f"{band}_priority": sum(item["priority_band"] == band for item in items)
                    for band in ("high", "medium", "low")
                },
                **{
                    f"missing_{field}": sum(
                        item[f"{field}_completeness"].startswith("missing") for item in items
                    )
                    for field in ("fuel_cycle", "official_url")
                },
            }
            if any(int(row[field]) != count for field, count in expected.items()):
                errors.append(f"{name}: derived summary counts mismatch")
    result = {
        "audit_date": DATE,
        "records": len(rows),
        "overlays": len(overlays),
        "overlay_sources": len(sources),
        "priority_bands": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "field_completeness": {
            key: dict(
                sorted(Counter(row[f"{key}_completeness"].split(":", 1)[0] for row in rows).items())
            )
            for key in KEYS
        },
        "hashes": hashes,
        "errors": errors,
    }
    try:
        report_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError as error:
        print(f"VALIDATION FAILED: cannot write report: {error}")
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
