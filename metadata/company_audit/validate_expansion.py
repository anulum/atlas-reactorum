#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/validate_expansion.py
"""Validate reviewed expansion identities, provenance and deterministic audit counts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
P = HERE / "expansion_candidates.tsv"
A = HERE / "audited_companies.tsv"
EXPECTED = [
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


def norm(value: str) -> str:
    """Normalize an identity using the expansion register's comparison rule.

    Parameters
    ----------
    value : str
        Company name or recorded alias.

    Returns
    -------
    str
        Case-folded alphanumeric identity, with punctuation and spaces removed.
    """
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def load(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a nonempty source table using its producer's exact schema.

    Parameters
    ----------
    path : pathlib.Path
        Expansion or protected company-audit table.
    fields : list of str
        Required source column order.

    Returns
    -------
    list of dict
        Unmodified source records.

    Raises
    ------
    ValueError
        If the schema, row shape or source table is invalid or empty.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"schema mismatch: {path.name}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"empty source table: {path.name}")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"malformed source row: {path.name}")
    return rows


def valid_source_url(value: str) -> bool:
    """Check an individual provenance link without following remote content.

    Parameters
    ----------
    value : str
        Official or independent source URL.

    Returns
    -------
    bool
        Whether a valid HTTPS authority is present.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    """Validate the selected expansion and write its counts without rebuilding source data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=P)
    parser.add_argument("--audit", type=Path, default=A)
    parser.add_argument("--report", type=Path, default=HERE / "expansion_validation.json")
    args = parser.parse_args()
    try:
        if args.report.resolve() in {args.input.resolve(), args.audit.resolve()}:
            raise ValueError("report path must differ from source inputs")
        rows = load(args.input, EXPECTED)
        audited = load(args.audit, AUDIT_FIELDS)
        audit_names = [norm(record["company"]) for record in audited]
        if not all(audit_names) or len(set(audit_names)) != len(audit_names):
            raise ValueError("empty or duplicate normalized audited identity")
        old = set()
        for record in audited:
            for value in [record["company"], *record["aliases"].split(";")]:
                if value.strip():
                    old.add(norm(value.strip()))
        errors: list[str] = []
        ids = Counter(row["candidate_id"] for row in rows)
        seen: dict[str, str] = {}
        organizations = []
        for line, row in enumerate(rows, 2):
            missing = [field for field in EXPECTED if not row[field].strip()]
            if missing:
                errors.append(f"line {line}: blank fields {missing}")
            if ids[row["candidate_id"]] != 1:
                errors.append(f"line {line}: duplicate candidate_id")
            if row["audit_date"] != "2026-09-27":
                errors.append(f"line {line}: wrong audit date")
            if row["confidence"] not in {"high", "medium", "low"}:
                errors.append(f"line {line}: invalid confidence")
            for field in ("official_url", "independent_urls"):
                for url in row[field].split(";"):
                    if not valid_source_url(url.strip()):
                        errors.append(f"line {line}: invalid {field} URL {url!r}")
            aliases = [row["organization"], *row["aliases"].split(";")]
            keys = {norm(value.strip()) for value in aliases if value.strip()}
            if not norm(row["organization"]) or "" in keys:
                errors.append(f"line {line}: blank normalized identity")
            if old & keys:
                errors.append(f"line {line}: collides with audited identity")
            for key in sorted(keys):
                if key in seen:
                    errors.append(f"line {line}: alias identity collides with {seen[key]}")
                seen[key] = row["organization"]
            organizations.append(norm(row["organization"]))
        if len(organizations) != len(set(organizations)):
            errors.append("duplicate normalized organization in expansion")
        counts = {
            "records": len(rows),
            "sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "identity_classes": Counter(row["identity_class"] for row in rows),
            "evidence_tiers": Counter(row["evidence_tier"] for row in rows),
            "confidence": Counter(row["confidence"] for row in rows),
            "errors": errors,
        }
        payload = json.dumps(counts, indent=2, ensure_ascii=False, default=dict) + "\n"
        args.report.write_text(payload, encoding="utf-8")
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"VALIDATION FAILED\n{read_error}")
        raise SystemExit(1) from None
    print(payload.rstrip())
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
