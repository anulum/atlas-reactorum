#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/anulum_github/validate.py
"""Validate the frozen 30-record public ANULUM reactor-repository snapshot."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

PATH = Path(__file__).with_name("reactor_repositories.tsv")
FIELDS = [
    "name",
    "url",
    "description",
    "category",
    "language",
    "license",
    "updated_at",
    "archived",
    "fork",
    "topics",
    "evidence_boundary",
    "source_url",
    "retrieved",
]
REQUIRED = {
    "name",
    "url",
    "description",
    "category",
    "updated_at",
    "evidence_boundary",
    "source_url",
    "retrieved",
}
CATEGORIES = {
    "device-family architecture",
    "shared physics / kernels",
    "control / integration",
    "supporting hardware / compute",
}


def load(path: Path) -> list[dict[str, str]]:
    """Read the released public snapshot using its exact column order.

    Parameters
    ----------
    path : pathlib.Path
        Frozen public GitHub snapshot TSV.

    Returns
    -------
    list of dict
        Unmodified snapshot records in their source order.

    Raises
    ------
    ValueError
        If the snapshot header or row structure is invalid.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError("snapshot header differs from expected schema")
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("snapshot contains a malformed row")
    return rows


def valid_source_url(value: str, host: str) -> bool:
    """Check a source URL's exact HTTPS authority without propagating parse failures.

    Parameters
    ----------
    value : str
        Repository or API source URL from the released snapshot.
    host : str
        Expected GitHub or GitHub API authority.

    Returns
    -------
    bool
        Whether the URL uses HTTPS with the required exact authority.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and parsed.netloc == host


def main() -> None:
    """Check the released public snapshot without changing source or portfolio records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PATH)
    args = parser.parse_args()
    try:
        rows = load(args.input)
    except (OSError, UnicodeError, csv.Error, ValueError) as read_error:
        parser.exit(1, f"VALIDATION FAILED: {read_error}\n")
    errors: list[str] = []
    if len(rows) != 30:
        errors.append(f"expected 30 rows, found {len(rows)}")
    if len({row["name"] for row in rows}) != len(rows):
        errors.append("duplicate repository name")
    for line, row in enumerate(rows, 2):
        if not all(row[field] for field in REQUIRED):
            errors.append(f"line {line}: blank required field")
        if not valid_source_url(row["url"], "github.com"):
            errors.append(f"line {line}: repository URL must be HTTPS on github.com")
        if not valid_source_url(row["source_url"], "api.github.com"):
            errors.append(f"line {line}: source URL must be HTTPS on api.github.com")
        if row["archived"] != "False":
            errors.append(f"line {line}: archived repository unexpectedly included")
        if row["fork"] not in {"True", "False"}:
            errors.append(f"line {line}: invalid fork flag")
        if row["category"] not in CATEGORIES:
            errors.append(f"line {line}: unknown repository category")
        try:
            updated = dt.datetime.fromisoformat(row["updated_at"])
            if updated.tzinfo is None:
                raise ValueError("timestamp requires a timezone")
        except ValueError:
            errors.append(f"line {line}: updated_at must be an ISO timestamp with timezone")
        try:
            dt.date.fromisoformat(row["retrieved"])
        except ValueError:
            errors.append(f"line {line}: retrieved must be a full ISO date")
    if errors:
        parser.exit(1, "VALIDATION FAILED: " + "; ".join(errors) + "\n")
    print("VALIDATION PASSED")
    print(f"records\t{len(rows)}")
    print(
        "categories\t"
        + "; ".join(f"{k}={v}" for k, v in sorted(Counter(row["category"] for row in rows).items()))
    )


if __name__ == "__main__":
    main()
