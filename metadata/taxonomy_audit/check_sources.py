# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/taxonomy_audit/check_sources.py
"""Observe source access and work identity without approving scientific claims."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import json
import math
import re
import shutil
import subprocess  # nosec B404 # Import creates no process; calls have scoped reviews.
from dataclasses import dataclass, field
from pathlib import Path
from typing import NotRequired, TypedDict
from urllib.parse import quote, unquote, urljoin, urlsplit

import requests

ROOT = Path(__file__).resolve().parent
MAX_TIMEOUT_SECONDS = 3600
FIELDS = (
    "url",
    "status",
    "final_url",
    "content_type",
    "title",
    "registered_title",
    "doi_registered",
    "access",
    "checked_date",
    "error",
)
SNAPSHOT_FIELDS = (
    "id",
    "name",
    "domain",
    "family",
    "parent_id",
    "kind",
    "maturity",
    "evidence",
    "evidence_scope",
    "source_urls",
    "source_audit",
)


class CheckRecord(TypedDict):
    """Access observations with optional independent DOI registration results."""

    url: str
    status: int | str
    final_url: str
    content_type: str
    title: str
    access: str
    checked_date: str
    registered_title: NotRequired[str]
    doi_registered: NotRequired[bool]
    error: NotRequired[str]


class SourceObservationRefused(ValueError):
    """Deliberately authored refusal for invalid source-observation inputs."""


def validate_url(url: str) -> None:
    """Require an anonymous absolute HTTPS reference before transferring bytes.

    Parameters
    ----------
    url : str
        Initial source, redirect target or registration service URL.

    Raises
    ------
    SourceObservationRefused
        URL is malformed, contains credentials or uses another protocol.
    """
    try:
        parsed = urlsplit(url)
        valid = (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not any(character.isspace() for character in url)
        )
        port = parsed.port
    except ValueError:
        valid, port = False, None
    if not valid or port == 0:
        raise SourceObservationRefused("source references must use anonymous HTTPS")


@dataclass(frozen=True)
class CheckConfig:
    """Validated observation limits and HTTPS registration service locations.

    Attributes
    ----------
    timeout : float
        Connection and per-read inactivity limit in (0, 3600] seconds, not a
        total transfer deadline.
    max_bytes : int
        Maximum retained decoded body bytes for each HTTP response.
    pdf_timeout : float
        Native first-five-page extraction process wait limit in (0, 3600] seconds.
    doi_origin, crossref_base : str
        HTTPS resolver prefix and work API prefix, including institutional mirrors.
    ca_certificate : pathlib.Path, optional
        Additional trusted certificate bundle; TLS verification remains enabled.
    pdf_executable : str, optional
        Trusted resolved pdftotext executable; None disables native extraction.
    checked_on : str
        Observation date, defaulting to the current UTC calendar date.
    """

    timeout: float = 18
    max_bytes: int = 8_000_000
    pdf_timeout: float = 5
    doi_origin: str = "https://doi.org"
    crossref_base: str = "https://api.crossref.org/works"
    ca_certificate: Path | None = None
    pdf_executable: str | None = None
    checked_on: str = field(default_factory=lambda: dt.datetime.now(dt.UTC).date().isoformat())

    def __post_init__(self) -> None:
        """Reject unsafe endpoints, nonfinite limits and invalid observation dates."""
        if any(
            not math.isfinite(value) or value <= 0 or value > MAX_TIMEOUT_SECONDS
            for value in (self.timeout, self.pdf_timeout)
        ):
            raise SourceObservationRefused(
                "timeouts must be positive, finite and at most 3600 seconds"
            )
        if type(self.max_bytes) is not int or self.max_bytes <= 0:
            raise SourceObservationRefused("body byte limit must be a positive integer")
        try:
            valid_date = dt.date.fromisoformat(self.checked_on).isoformat() == self.checked_on
        except ValueError:
            valid_date = False
        if not valid_date:
            raise SourceObservationRefused("observation date must use YYYY-MM-DD")
        validate_url(self.doi_origin)
        validate_url(self.crossref_base)
        if any(
            urlsplit(url).query or urlsplit(url).fragment
            for url in (self.doi_origin, self.crossref_base)
        ):
            raise SourceObservationRefused(
                "registration service prefixes cannot contain queries or fragments"
            )


def collect_urls(snapshot: Path, additional: Path | None = None) -> list[str]:
    """Collect the full original source set and optional saved supplementary URLs.

    Parameters
    ----------
    snapshot : pathlib.Path
        Intact original eleven-column taxonomy TSV.
    additional : pathlib.Path, optional
        Schema 1.0.0 supplementary envelope or historical bare URL array.

    Returns
    -------
    list of str
        Sorted unique anonymous HTTPS source references.

    Raises
    ------
    ValueError
        Snapshot or supplementary structure is invalid or references are unsafe.
    """
    urls: set[str] = set()
    with snapshot.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if tuple(reader.fieldnames or ()) != SNAPSHOT_FIELDS:
            raise SourceObservationRefused("taxonomy source header mismatch")
        count = 0
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise SourceObservationRefused("taxonomy source row shape mismatch")
            for url in row["source_urls"].split(" | "):
                validate_url(url)
                urls.add(url)
            count += 1
        if not count:
            raise SourceObservationRefused("empty taxonomy source snapshot")
    if additional is not None:
        document: object = json.loads(additional.read_text(encoding="utf-8"))
        if isinstance(document, dict):
            if (
                set(document) != {"schema_version", "record_count", "records"}
                or document["schema_version"] != "1.0.0"
            ):
                raise SourceObservationRefused("unsupported supplementary source envelope")
            records: object = document["records"]
            size: object = document["record_count"]
            if type(size) is not int or not isinstance(records, list) or size != len(records):
                raise SourceObservationRefused("supplementary source count mismatch")
        else:
            records = document
        if not isinstance(records, list):
            raise SourceObservationRefused("supplementary sources must be an array")
        for record in records:
            if not isinstance(record, str):
                raise SourceObservationRefused("supplementary source must be a URL string")
            validate_url(record)
            urls.add(record)
    return sorted(urls)


def _get_body(url: str, config: CheckConfig) -> tuple[int, str, str, bytes, bool]:
    for _ in range(6):
        validate_url(url)
        with requests.get(
            url,
            timeout=(config.timeout, config.timeout),
            headers={"User-Agent": "ReactorAtlas-ResearchAudit/1.0"},
            stream=True,
            allow_redirects=False,
            verify=str(config.ca_certificate) if config.ca_certificate is not None else True,
        ) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location:
                    raise SourceObservationRefused("redirect has no Location")
                url = urljoin(url, location)
                continue
            body = bytearray()
            truncated = False
            for part in response.iter_content(65536):
                remaining = config.max_bytes - len(body)
                body.extend(part[:remaining])
                if len(part) > remaining:
                    truncated = True
                    break
            return (
                response.status_code,
                response.url,
                response.headers.get("Content-Type", ""),
                bytes(body),
                truncated,
            )
    raise SourceObservationRefused("source redirect limit exceeded")


def check(url: str, config: CheckConfig | None = None) -> CheckRecord:
    """Observe one source and, for DOI references, a matching work registration.

    Parameters
    ----------
    url : str
        Anonymous HTTPS source reference.
    config : CheckConfig, optional
        Limits, trust roots and resolver mirrors. Native PDF extraction requires
        an explicitly resolved executable, which the CLI discovers on PATH.

    Returns
    -------
    CheckRecord
        Response/access observations. Failed or truncated transfers, extraction
        failures and registration failures never become approval of a source.

    Raises
    ------
    SourceObservationRefused
        Initial reference is unsafe; no request is attempted.
    """
    validate_url(url)
    config = config or CheckConfig()
    out = CheckRecord(
        url=url,
        status="",
        final_url="",
        content_type="",
        title="",
        access="",
        checked_date=config.checked_on,
    )
    try:
        status, final_url, content_type, body, truncated = _get_body(url, config)
        out["status"] = status
        out["final_url"] = final_url
        out["content_type"] = content_type
        if truncated:
            out["access"] = "response-body-limit-exceeded"
            out["error"] = "response body exceeded retained byte limit"
        elif body.startswith(b"%PDF"):
            out["access"] = "pdf-response-text-unavailable"
            if config.pdf_executable is not None:
                try:
                    # Operator-selected PDF tool; fixed argv; source bytes only on stdin; deadline.
                    process = subprocess.run(  # nosec B603
                        [config.pdf_executable, "-f", "1", "-l", "5", "-", "-"],
                        input=body,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        timeout=config.pdf_timeout,
                        check=False,
                    )
                    text = process.stdout.decode(errors="replace")
                    if process.returncode == 0 and text.strip():
                        out["title"] = " ".join(text.split())[:700]
                        out["access"] = "pdf-extracted"
                except subprocess.TimeoutExpired:
                    out["error"] = "native PDF extraction timed out"
                except OSError:
                    out["error"] = "native PDF extraction unavailable"
        else:
            text = body.decode(errors="replace")
            title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
            out["title"] = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
            out["access"] = (
                "html-response-not-fulltext-verified"
                if status == 200
                else "http-error-or-access-barrier"
            )
        source = urlsplit(url)
        resolver = urlsplit(config.doi_origin.rstrip("/") + "/")
        if source.netloc.casefold() == resolver.netloc.casefold() and source.path.startswith(
            resolver.path
        ):
            doi = unquote(source.path[len(resolver.path) :])
            out["doi_registered"] = False
            try:
                work_status, _, _, work_body, work_truncated = _get_body(
                    config.crossref_base.rstrip("/") + "/" + quote(doi, safe="/"), config
                )
                if work_status != 200 or work_truncated:
                    raise SourceObservationRefused("registration response unavailable or truncated")
                document: object = json.loads(work_body)
                message: object = document.get("message") if isinstance(document, dict) else None
                if not isinstance(message, dict):
                    raise SourceObservationRefused("registration message missing")
                identity: object = message.get("DOI")
                titles: object = message.get("title")
                if not isinstance(identity, str) or identity.casefold() != doi.casefold():
                    raise SourceObservationRefused("registration identifies another work")
                if (
                    not isinstance(titles, list)
                    or not titles
                    or any(not isinstance(title, str) or not title.strip() for title in titles)
                ):
                    raise SourceObservationRefused("registration titles missing or invalid")
                out["registered_title"] = "; ".join(str(title) for title in titles)
                out["doi_registered"] = True
            except (requests.RequestException, OSError, ValueError):
                out["doi_registered"] = False
    except SourceObservationRefused as exc:
        out["access"] = "request-failed"
        out["error"] = str(exc)
    except (requests.RequestException, OSError, ValueError):
        out["access"] = "request-failed"
        out["error"] = "source request failed"
    return out


def main(argv: list[str] | None = None) -> int:
    """Write a new access snapshot without overwriting historical audit inputs.

    Parameters
    ----------
    argv : list of str, optional
        CLI arguments, defaulting to process arguments.

    Returns
    -------
    int
        Zero when observations are saved, including failed source requests;
        one on input/output failures; argument errors use argparse status two.

    Notes
    -----
    Only authored refusals and fixed error messages reach caller output.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "input-taxonomy-snapshot.tsv")
    parser.add_argument("--additional", type=Path, default=ROOT / "additional_sources.json")
    parser.add_argument("--no-additional", action="store_true")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=18)
    parser.add_argument("--max-bytes", type=int, default=8_000_000)
    parser.add_argument("--pdf-timeout", type=float, default=5)
    parser.add_argument("--no-pdf-text", action="store_true")
    parser.add_argument("--ca-certificate", type=Path)
    parser.add_argument("--doi-origin", default="https://doi.org")
    parser.add_argument("--crossref-base", default="https://api.crossref.org/works")
    parser.add_argument("--checked-on", default=dt.datetime.now(dt.UTC).date().isoformat())
    args = parser.parse_args(argv)
    try:
        config = CheckConfig(
            timeout=args.timeout,
            max_bytes=args.max_bytes,
            pdf_timeout=args.pdf_timeout,
            ca_certificate=args.ca_certificate,
            doi_origin=args.doi_origin,
            crossref_base=args.crossref_base,
            checked_on=args.checked_on,
            pdf_executable=None if args.no_pdf_text else shutil.which("pdftotext"),
        )
        output = args.output_directory.resolve()
        paths = [output / "url_checks.json", output / "sources.tsv"]
        protected = {
            ROOT / name
            for name in (
                "input-taxonomy-snapshot.tsv",
                "additional_sources.json",
                "url_checks.json",
                "sources.tsv",
            )
        }
        protected.update({args.input.resolve(), args.additional.resolve()})
        if output == ROOT or any(path.resolve() in protected for path in paths):
            raise SourceObservationRefused(
                "output cannot replace maintained observations or source inputs"
            )
        urls = collect_urls(args.input, None if args.no_additional else args.additional)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            result = list(pool.map(lambda url: check(url, config), urls))
        output.mkdir(parents=True, exist_ok=True)
        paths[0].write_text(
            json.dumps(
                {"schema_version": "1.0.0", "record_count": len(result), "records": result},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with paths[1].open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, FIELDS, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(result)
    except SourceObservationRefused as exc:
        print(f"CHECK FAILED: {exc}")
        return 1
    except (OSError, UnicodeError, ValueError, csv.Error):
        print("CHECK FAILED: source input or observation output is invalid or unavailable")
        return 1
    for record in result:
        print(
            record["status"],
            record["url"],
            record.get("registered_title") or record["title"][:130],
            record["access"],
            sep=" | ",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
