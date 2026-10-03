#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/check_expansion_urls.py
"""Check source availability without treating a response as scientific validation."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import shutil
import subprocess  # nosec B404 # Import creates no process; calls have scoped reviews.
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
MAX_TIMEOUT_SECONDS = 3600
SOURCE_FIELDS = [
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

OUTPUT_FIELDS = ["url", "roles", "http_status", "reachable_or_access_controlled", "checked_on"]


def valid_url(value: str) -> bool:
    """Check an anonymous absolute HTTPS reference before invoking curl.

    Parameters
    ----------
    value : str
        Recorded source URL without embedded credentials.

    Returns
    -------
    bool
        Whether scheme, hostname and absence of whitespace/userinfo are valid.
    """
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and not any(char.isspace() for char in value)
    )


def collect_urls(path: Path) -> dict[str, set[str]]:
    """Read actual expansion references with their original deduplicated roles.

    Parameters
    ----------
    path : pathlib.Path
        Reviewed nineteen-column expansion TSV or an explicit local copy.

    Returns
    -------
    dict of str to sets of str
        Unique source links and the original official_url/independent labels.

    Raises
    ------
    ValueError
        If schema, rows or recorded HTTPS references are invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != SOURCE_FIELDS:
            raise ValueError("expansion header mismatch")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError("expansion table empty or malformed")
    urls: dict[str, set[str]] = {}
    for row in rows:
        for field, role in (("official_url", "official_url"), ("independent_urls", "independent")):
            for value in row[field].split(";"):
                url = value.strip()
                if not valid_url(url):
                    raise ValueError("invalid anonymous HTTPS source URL")
                urls.setdefault(url, set()).add(role)
    return urls


def check_url(
    url: str,
    roles: set[str],
    curl: str,
    *,
    timeout: float,
    checked_on: str,
    ca_certificate: Path | None = None,
) -> dict[str, str]:
    """Record a real bounded curl transfer while retaining access barriers.

    Parameters
    ----------
    url : str
        Valid anonymous HTTPS source reference.
    roles : set of str
        Recorded source-role labels.
    curl : str
        Resolved native curl executable selected by the caller.
    timeout : float
        Finite curl transfer limit in (0, 3600] seconds. The native process
        wait limit is one second longer, at most 3601 seconds.
    checked_on : str
        Run date already validated by the CLI.
    ca_certificate : pathlib.Path or None
        Optional trusted certificate bundle for an institutional HTTPS endpoint.

    Returns
    -------
    dict of str
        Original availability row; failed transfers never claim reachability.

    Raises
    ------
    ValueError
        If the source URL is not anonymous HTTPS or the timeout is outside
        the positive finite supported range (0, 3600].
    """
    if not math.isfinite(timeout) or timeout <= 0 or timeout > MAX_TIMEOUT_SECONDS:
        raise ValueError("timeout must be positive and finite and at most 3600 seconds")
    if not valid_url(url):
        raise ValueError("invalid anonymous HTTPS source URL")
    command = [
        curl,
        "--location",
        "--proto",
        "=https",
        "--proto-redir",
        "=https",
        "--user-agent",
        "Mozilla/5.0",
        "--silent",
        "--show-error",
        "--output",
        "/dev/null",
        "--max-time",
        str(timeout),
        "--write-out",
        "%{http_code}",
    ]
    if ca_certificate is not None:
        command.extend(["--cacert", str(ca_certificate)])
    command.extend(["--", url])
    try:
        # Resolved curl; HTTPS-only flags and -- URL separator; finite deadline.
        process = subprocess.run(  # nosec B603
            command, text=True, capture_output=True, check=False, timeout=timeout + 1
        )
        code = process.stdout.strip() or "000"
        acceptable = process.returncode == 0 and (
            code.startswith(("2", "3")) or code in {"401", "403", "406", "429"}
        )
    except (OSError, subprocess.TimeoutExpired):
        code, acceptable = "000", False
    return {
        "url": url,
        "roles": ";".join(sorted(roles)),
        "http_status": code,
        "reachable_or_access_controlled": "yes" if acceptable else "no",
        "checked_on": checked_on,
    }


def main() -> None:
    """Validate recorded references and write a dated real availability snapshot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "expansion_candidates.tsv")
    parser.add_argument("--output", type=Path, default=HERE / "expansion_url_checks.tsv")
    parser.add_argument(
        "--timeout",
        type=float,
        default=20,
        help="Curl transfer limit in (0, 3600] seconds; process wait is one second longer.",
    )
    parser.add_argument("--checked-on", default=dt.datetime.now(dt.UTC).date().isoformat())
    parser.add_argument("--ca-certificate", type=Path)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.timeout > MAX_TIMEOUT_SECONDS:
        parser.error("timeout must be positive and finite and at most 3600 seconds")
    try:
        if dt.date.fromisoformat(args.checked_on).isoformat() != args.checked_on:
            raise ValueError("checked-on must use YYYY-MM-DD")
        if args.input.resolve() == args.output.resolve():
            raise ValueError("output would replace expansion input")
        urls = collect_urls(args.input)
        curl = shutil.which("curl")
        if curl is None:
            raise ValueError("curl not found on PATH")
        rows = [
            check_url(
                url,
                roles,
                curl,
                timeout=args.timeout,
                checked_on=args.checked_on,
                ca_certificate=args.ca_certificate,
            )
            for url, roles in sorted(urls.items())
        ]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=OUTPUT_FIELDS, delimiter="\t", lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"CHECK FAILED: {error}")
        raise SystemExit(1) from None
    bad = [row for row in rows if row["reachable_or_access_controlled"] == "no"]
    print(f"checked {len(rows)} unique URLs; unacceptable results: {len(bad)}")
    for row in bad:
        print(row["http_status"], row["url"])


if __name__ == "__main__":
    main()
