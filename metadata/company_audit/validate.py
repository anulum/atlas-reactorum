#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/validate.py
"""Validate the company identity/evidence audit without promoting its claims."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

PATH = Path(__file__).with_name("audited_companies.tsv")
FIELDS = [
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
REQUIRED = {
    "company",
    "identity_class",
    "normalized_status",
    "country",
    "approach_family",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "source_dates",
    "audit_date",
    "confidence",
}


def load(path: Path) -> list[dict[str, str]]:
    """Read a nonempty audit without changing its identity or evidence values.

    Parameters
    ----------
    path : pathlib.Path
        Published company-audit TSV or an explicit local copy.

    Returns
    -------
    list of dict
        Original audit rows in file order.

    Raises
    ------
    ValueError
        If the exact audit schema or row structure is invalid or empty.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError("audit header differs from expected schema")
        rows = list(reader)
    if not rows:
        raise ValueError("empty company audit")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("audit contains a malformed row")
    return rows


def valid_source_url(value: str) -> bool:
    """Check a source URL's HTTPS authority without following the link.

    Parameters
    ----------
    value : str
        Official or independent source URL recorded by the audit.

    Returns
    -------
    bool
        Whether the URL has an HTTPS scheme and a populated authority.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    """Check audit structure and provenance while keeping source claims unchanged."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PATH)
    args = parser.parse_args()
    try:
        rows = load(args.input)
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        print(f"VALIDATION FAILED\n{read_error}")
        raise SystemExit(1) from None
    errors: list[str] = []
    names = Counter(row["company"] for row in rows)
    for line, row in enumerate(rows, 2):
        for field in REQUIRED:
            if not row[field].strip():
                errors.append(f"line {line} ({row['company']}): missing {field}")
        urls = ([row["official_url"]] if row["official_url"] else []) + [
            u.strip() for u in row["independent_urls"].split(";") if u.strip()
        ]
        if not urls:
            errors.append(f"line {line} ({row['company']}): no source URL")
        for url in urls:
            if not valid_source_url(url):
                errors.append(f"line {line} ({row['company']}): invalid source URL {url}")
        if row["confidence"] not in {"high", "medium", "low"}:
            errors.append(f"line {line}: invalid confidence")
        try:
            dt.date.fromisoformat(row["audit_date"])
        except ValueError:
            errors.append(f"line {line}: audit_date must be a full ISO date")
    for name, count in names.items():
        if not name.strip() or count != 1:
            errors.append(f"company {name!r} occurs {count} times")
    if errors:
        print("VALIDATION FAILED\n" + "\n".join(errors[:100]))
        raise SystemExit(1)
    print("VALIDATION PASSED")
    print(f"records\t{len(rows)}")
    print(
        "confidence\t"
        + "; ".join(f"{k}={v}" for k, v in sorted(Counter(r["confidence"] for r in rows).items()))
    )
    tiers = Counter(r["evidence_tier"].split(" — ")[0] for r in rows)
    print("evidence_tiers\t" + "; ".join(f"{k}={v}" for k, v in sorted(tiers.items())))


if __name__ == "__main__":
    main()
