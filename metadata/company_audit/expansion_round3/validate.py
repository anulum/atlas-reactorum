#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/expansion_round3/validate.py
"""Validate persisted expansion identities and their bounded evidence associations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATE = "2026-09-28"
CF = [
    "candidate_id",
    "organization",
    "aliases",
    "identity_class",
    "country",
    "founded",
    "normalized_status",
    "approach_family",
    "public_devices_projects",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "primary_url",
    "independent_urls",
    "source_ids",
    "source_dates",
    "audit_date",
    "confidence",
    "inclusion_rationale",
]
SF = [
    "source_id",
    "title",
    "publisher",
    "source_type",
    "source_date",
    "url",
    "scope_and_limitations",
    "accessed_on",
]
AUDIT_FIELDS = [
    "company",
    "aliases",
    "founded",
    "identity_class",
    "normalized_status",
    "country",
    "approach_family",
    "public_devices_projects",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "official_url",
    "independent_urls",
    "source_dates",
    "audit_date",
    "confidence",
]
FIRST_FIELDS = [
    "candidate_id",
    "organization",
    "aliases",
    "identity_class",
    "country",
    "founded",
    "normalized_status",
    "approach_family",
    "public_devices_projects",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "official_url",
    "independent_urls",
    "source_dates",
    "audit_date",
    "confidence",
    "inclusion_rationale",
]


def read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a nonempty source with its exact ordered producer schema.

    Parameters
    ----------
    path : pathlib.Path
        Candidate, registry or protected audit TSV.
    fields : list of str
        Selected producer's ordered columns.

    Returns
    -------
    list of dict
        Original rows without changing source wording or evidence levels.

    Raises
    ------
    ValueError
        If schema, row shape or table presence is invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: empty or malformed rows")
    return rows


def norm(value: str) -> str:
    """Normalize a declared identity solely for duplicate comparisons.

    Parameters
    ----------
    value : str
        Organization name or alias from an audited table.

    Returns
    -------
    str
        Case-folded alphanumeric comparison key, never a replacement identity.
    """
    return "".join(char for char in value.casefold() if char.isalnum())


def names(record: Mapping[str, str], column: str) -> list[str]:
    """Collect a declared organization identity and its original aliases.

    Parameters
    ----------
    record : mapping of str to str
        Actual audited row without modification of identity wording.
    column : str
        Company or organization column of the selected catalog.

    Returns
    -------
    list of str
        Primary identity followed by semicolon-separated recorded aliases.
    """
    return [record.get(column, ""), *record.get("aliases", "").split(";")]


def valid_url(value: str) -> bool:
    """Check recorded HTTPS authority without fetching evidence contents.

    Parameters
    ----------
    value : str
        Recorded primary, independent or registry URL.

    Returns
    -------
    bool
        Whether the URL has an HTTPS scheme and populated authority.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not any(char.isspace() for char in value)
    )


def main() -> None:
    """Check third-round identities against every earlier protected catalog."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=HERE)
    parser.add_argument("--audit-root", type=Path, default=HERE.parent)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    candidate_path, source_path = [
        args.directory / name for name in ("candidates.tsv", "source_registry.tsv")
    ]
    audit_path, first_path = [
        args.audit_root / name for name in ("audited_companies.tsv", "expansion_candidates.tsv")
    ]
    second_path = args.audit_root / "expansion_round2/candidates.tsv"
    report_path = args.report or args.directory / "validation.json"
    if report_path.resolve() in {
        path.resolve()
        for path in (candidate_path, source_path, audit_path, first_path, second_path)
    }:
        print("VALIDATION FAILED: report would replace an input")
        raise SystemExit(1)
    try:
        rows = read(candidate_path, CF)
        sources = read(source_path, SF)
        audits = [
            (read(audit_path, AUDIT_FIELDS), "company"),
            (read(first_path, FIRST_FIELDS), "organization"),
        ]
        audits.append((read(second_path, CF), "organization"))
        baseline_counts = dict(
            zip(
                (
                    "audited_companies.tsv",
                    "expansion_candidates.tsv",
                    "expansion_round2/candidates.tsv",
                ),
                (len(old) for old, _key in audits),
                strict=True,
            )
        )
        if list(baseline_counts.values()) != [51, 18, 15]:
            raise ValueError("expected baseline file counts 51/18/15 totaling84")
        hashes = [
            hashlib.sha256(path.read_bytes()).hexdigest() for path in (candidate_path, source_path)
        ]
        protected: set[str] = set()
        for old, key in audits:
            primary = [norm(row[key]) for row in old]
            if any(not value for value in primary) or len(set(primary)) != len(primary):
                raise ValueError("protected catalog has blank or duplicate primary identities")
            for row in old:
                for value in names(row, key):
                    if value.strip():
                        normalized = norm(value)
                        if not normalized:
                            raise ValueError("protected catalog has invalid alias")
                        protected.add(normalized)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"VALIDATION FAILED: {error}")
        raise SystemExit(1) from None
    errors: list[str] = []
    if len(rows) != 14:
        errors.append("expected 14 candidate records")
    source_by_id = {row["source_id"]: row for row in sources}
    if (
        len(sources) != 28
        or len(source_by_id) != 28
        or any(not key.strip() for key in source_by_id)
    ):
        errors.append("expected 28 unique nonempty sources")
    candidate_ids = [row["candidate_id"] for row in rows]
    if len(set(candidate_ids)) != len(candidate_ids):
        errors.append("duplicate candidate_id")
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        missing = [field for field in CF if not row[field].strip()]
        if missing:
            errors.append(f"line {line}: blank {missing}")
        if row["audit_date"] != DATE:
            errors.append(f"line {line}: wrong audit date")
        if row["confidence"] not in {"high", "medium", "low"}:
            errors.append(f"line {line}: invalid confidence")
        urls = [
            url.strip()
            for field in ("primary_url", "independent_urls")
            for url in row[field].split(";")
        ]
        if any(not valid_url(url) for url in urls):
            errors.append(f"line {line}: invalid URL")
        refs = [key.strip() for key in row["source_ids"].split(";")]
        if (
            len(refs) < 2
            or len(set(refs)) != len(refs)
            or any(key not in source_by_id for key in refs)
        ):
            errors.append(f"line {line}: invalid source references")
        elif {source_by_id[key]["url"] for key in refs} != set(urls):
            errors.append(f"line {line}: source URLs do not match candidate links")
        values = names(row, "organization")
        identities = {norm(value) for value in values if value.strip()}
        if "" in identities:
            errors.append(f"line {line}: invalid normalized identity")
        if identities & protected:
            errors.append(f"line {line}: protected identity collision")
        if identities & seen:
            errors.append(f"line {line}: duplicate candidate name or alias")
        seen.update(identities)
    for line, row in enumerate(sources, 2):
        if any(not row[field].strip() for field in SF):
            errors.append(f"source line {line}: blank field")
        if not valid_url(row["url"]) or row["accessed_on"] != DATE:
            errors.append(f"source line {line}: date or URL")
    result = {
        "audit_date": DATE,
        "baseline_records": sum(baseline_counts.values()),
        "baseline_files": baseline_counts,
        "candidate_records": len(rows),
        "combined_records_after_round3": sum(baseline_counts.values()) + len(rows),
        "source_records": len(sources),
        "candidate_sha256": hashes[0],
        "source_registry_sha256": hashes[1],
        "countries": dict(sorted(Counter(row["country"] for row in rows).items())),
        "identity_classes": dict(sorted(Counter(row["identity_class"] for row in rows).items())),
        "confidence": dict(sorted(Counter(row["confidence"] for row in rows).items())),
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
