#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round2/build_dataset.py
"""Build Canada NPRI + Australia NPI industrial discovery records.

Offline builds preserve the historical compact snapshot. Every output path is
explicit; refreshes write isolated snapshots with an explicit retrieval date.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import os
import ssl
import tempfile
import urllib.parse
import urllib.request
from datetime import date
from http.client import HTTPMessage
from pathlib import Path
from typing import IO

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
OUTPUT = ROOT / "industrial_facilities_round2.tsv"
RETRIEVED = "2026-09-27"
USER_AGENT = "reactor-atlas-industrial-discovery/2.0"

CANADA_URL = (
    "https://data-donnees.az.ec.gc.ca/api/file?path=%2Fsubstances%2Fplansreports%2F"
    "reporting-facilities-pollutant-release-and-transfer-data%2Fbulk-data-files-for-all-years-"
    "releases-disposals-transfers-and-facility-locations%2F"
    "NPRI-INRP_GeolocationsGeolocalisation_1993-present.csv"
)
CANADA_LANDING = "https://open.canada.ca/data/en/dataset/40e01423-7728-429c-ac9d-2954385ccdfb"
AUSTRALIA_URL = (
    "https://data.gov.au/data/dataset/043f58e0-a188-4458-b61c-04e5b540aea4/resource/"
    "f83cdee9-ebcb-4f24-941b-34bb2f0996cf/download/facilities.csv"
)
AUSTRALIA_LANDING = "https://www.dcceew.gov.au/environment/protection/npi/data"

CANADA_PREFIXES = ("311", "3121", "322", "324", "325")
AUSTRALIA_PREFIXES = ("11", "12", "15", "17", "18", "19")

FIELDS = [
    "stable_id",
    "facility_name",
    "country",
    "lat",
    "lon",
    "precision",
    "sector",
    "process_or_activity",
    "reactor_type_if_explicit",
    "status",
    "operator",
    "capacity",
    "pollutant_or_product_context",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]
SNAPSHOT_FIELDS = [
    "source",
    "source_record_id",
    "latest_report_year",
    "facility_name",
    "operator",
    "country",
    "lat",
    "lon",
    "sector_code",
    "sector_label",
    "process_code",
    "process_label",
    "main_activities",
    "datum",
    "source_row_url",
]


CANADA_REQUIRED = (
    "Year of last filed report / Année de déclaration la plus récente",
    "NAICS / Code SCIAN",
    "NPRI ID / ID INRP",
    "Facility Name / Nom de l'installation",
    "Company Name / Raison Sociale",
    "Latitude / Latitude",
    "Longitude / Longitude",
    "Key Industrial Sector Code / Code des Secteurs industriels clés",
    "Key Industrial Sector (English) / Secteurs industriels clés (Anglais)",
    "NAICS Code Title (English) / Titre Code SCIAN (Anglais)",
    "Datum / Datum",
)
AUSTRALIA_REQUIRED = (
    "latest_report_year",
    "primary_anzsic_class_code",
    "facility_id",
    "facility_name",
    "registered_business_name",
    "latitude",
    "longitude",
    "primary_anzsic_class_name",
    "main_activities",
    "latest_report_url",
)
MANIFEST_FIELDS = ["source", "url", "retrieved", "bytes", "sha256", "selected_rows"]


def check_https(url: str) -> None:
    """Require an anonymous HTTPS URL for every request and redirect."""
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.port == 0
        or any(c.isspace() for c in url)
    ):
        raise ValueError("source URL must be valid anonymous HTTPS")


class SourceRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse non-HTTPS or credential-bearing redirect destinations."""

    max_redirections = 5

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Validate the real server's destination before urllib follows it."""
        check_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(
    url: str,
    *,
    timeout: float = 60,
    max_bytes: int = 32 * 1024 * 1024,
    ca_file: Path | None = None,
) -> bytes:
    """Read a bounded HTTPS resource with certificate verification.

    The timeout bounds socket operations, not the entire download duration.
    An optional CA file supports a trusted institutional mirror.
    """
    check_https(url)
    if not math.isfinite(timeout) or timeout <= 0 or max_bytes <= 0:
        raise ValueError("source limits must be positive and finite")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context),
        SourceRedirect(),
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"source returned HTTP {response.status}")
        body: bytes = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError("source exceeds the download byte limit")
    return body


def clean(value: object) -> str:
    """Normalize source text without inventing absent observations."""
    return "" if value is None else str(value).strip()


def source_records(body: str, required: tuple[str, ...]) -> list[dict[str, str]]:
    """Read genuine raw CSV cells, refusing missing fields or ragged rows."""
    reader = csv.DictReader(io.StringIO(body), strict=True)
    if reader.fieldnames is None or not set(required).issubset(reader.fieldnames):
        raise ValueError("raw source is missing required columns")
    rows: list[dict[str, str]] = []
    for raw in reader:
        if None in raw or any(v is None for v in raw.values()):
            raise ValueError("raw source contains a row with the wrong width")
        rows.append({field: raw[field] for field in required})
    if not rows:
        raise ValueError("raw source contains no records")
    return rows


def select_sources(canada_raw: bytes, australia_raw: bytes) -> list[dict[str, str]]:
    """Apply the historical report-year and industry-prefix selection rules."""
    selected: list[dict[str, str]] = []

    canada_text = canada_raw.decode("windows-1252")
    for row in source_records(canada_text, CANADA_REQUIRED):
        year = clean(row["Year of last filed report / Année de déclaration la plus récente"])
        naics = clean(row["NAICS / Code SCIAN"])
        if year != "2024" or not naics.startswith(CANADA_PREFIXES):
            continue
        selected.append(
            {
                "source": "canada-npri",
                "source_record_id": clean(row["NPRI ID / ID INRP"]),
                "latest_report_year": year,
                "facility_name": clean(row["Facility Name / Nom de l'installation"])
                or clean(row["Company Name / Raison Sociale"]),
                "operator": clean(row["Company Name / Raison Sociale"]),
                "country": "Canada",
                "lat": clean(row["Latitude / Latitude"]),
                "lon": clean(row["Longitude / Longitude"]),
                "sector_code": clean(
                    row["Key Industrial Sector Code / Code des Secteurs industriels clés"]
                ),
                "sector_label": clean(
                    row["Key Industrial Sector (English) / Secteurs industriels clés (Anglais)"]
                ),
                "process_code": naics,
                "process_label": clean(
                    row["NAICS Code Title (English) / Titre Code SCIAN (Anglais)"]
                ),
                "main_activities": "",
                "datum": clean(row["Datum / Datum"]),
                "source_row_url": "",
            }
        )

    australia_text = australia_raw.decode("utf-8-sig")
    for row in source_records(australia_text, AUSTRALIA_REQUIRED):
        year = clean(row["latest_report_year"])
        anzsic = clean(row["primary_anzsic_class_code"])
        if year != "2024/2025" or not anzsic.startswith(AUSTRALIA_PREFIXES):
            continue
        selected.append(
            {
                "source": "australia-npi",
                "source_record_id": clean(row["facility_id"]),
                "latest_report_year": year,
                "facility_name": clean(row["facility_name"])
                or clean(row["registered_business_name"]),
                "operator": clean(row["registered_business_name"]),
                "country": "Australia",
                "lat": clean(row["latitude"]),
                "lon": clean(row["longitude"]),
                "sector_code": anzsic,
                "sector_label": clean(row["primary_anzsic_class_name"]),
                "process_code": anzsic,
                "process_label": clean(row["primary_anzsic_class_name"]),
                "main_activities": clean(row["main_activities"]),
                "datum": "",
                "source_row_url": clean(row["latest_report_url"]),
            }
        )
    selected.sort(key=lambda row: (row["source"], row["source_record_id"]))
    if not selected:
        raise ValueError("source selection contains no qualifying records")
    return selected


def read_snapshot(path: Path) -> list[dict[str, str]]:
    """Read the exact field-minimised snapshot schema without modifying it."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != SNAPSHOT_FIELDS:
            raise ValueError("compact snapshot header differs from the required schema")
        rows: list[dict[str, str]] = []
        for raw in reader:
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError("compact snapshot row has the wrong width")
            rows.append({field: raw[field] for field in SNAPSHOT_FIELDS})
    if not rows:
        raise ValueError("compact snapshot contains no records")
    return rows


def rows_from_snapshot(
    source_rows: list[dict[str, str]],
    *,
    retrieved: str = RETRIEVED,
) -> list[dict[str, str]]:
    """Build discovery records using only the source-published observations."""
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO calendar date")
    if not source_rows:
        raise ValueError("compact snapshot contains no records")
    if any(
        set(row) != set(SNAPSHOT_FIELDS) or any(not isinstance(v, str) for v in row.values())
        for row in source_rows
    ):
        raise ValueError("compact snapshot record differs from the required schema")
    ids: set[str] = set()
    for row in source_rows:
        for field in (
            "source",
            "source_record_id",
            "latest_report_year",
            "facility_name",
            "country",
            "lat",
            "lon",
            "sector_label",
            "process_code",
            "process_label",
        ):
            if not row[field].strip():
                raise ValueError(f"compact snapshot is missing {field}")
        key = f"{row['source']}:{row['source_record_id']}"
        if key in ids:
            raise ValueError(f"compact snapshot has duplicate record {key}")
        ids.add(key)
        lat, lon = float(row["lat"]), float(row["lon"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"compact snapshot coordinates out of range for {key}")
        if row["source"] == "canada-npri":
            if (
                row["country"] != "Canada"
                or row["latest_report_year"] != "2024"
                or not row["process_code"].startswith(CANADA_PREFIXES)
            ):
                raise ValueError("Canadian snapshot record is outside the declared selection")
        elif row["source"] == "australia-npi":
            if (
                row["country"] != "Australia"
                or row["latest_report_year"] != "2024/2025"
                or not row["process_code"].startswith(AUSTRALIA_PREFIXES)
            ):
                raise ValueError("Australian snapshot record is outside the declared selection")
    rows = []
    for src in source_rows:
        if src["source"] == "canada-npri":
            source_url = CANADA_LANDING
            precision = "NPRI-published facility point"
            if src["datum"]:
                precision += f"; source datum {src['datum']}"
            precision += "; positional accuracy not independently verified"
            process = f"NAICS {src['process_code']} — {src['process_label']}"
            status = "latest NPRI report filed for 2024; operating status not asserted"
            role = "official Canadian pollutant-register facility and industry classification"
            license_text = "Open Government Licence — Canada"
            notes = (
                f"Selected systematically from the NPRI geolocation file: latest filed report=2024 and "
                f"NAICS prefix in {', '.join(CANADA_PREFIXES)}. This is a facility-level discovery record; "
                "it does not establish any process-reactor inventory or design."
            )
        elif src["source"] == "australia-npi":
            source_url = src["source_row_url"].replace("http://", "https://") or AUSTRALIA_LANDING
            precision = (
                "NPI-published facility point; positional accuracy not independently verified"
            )
            process = f"ANZSIC 2006 {src['process_code']} — {src['process_label']}"
            if src["main_activities"] and src["main_activities"] != src["process_label"]:
                process += " | source main activities: " + src["main_activities"]
            status = "latest NPI report is 2024/2025; operating status not asserted"
            role = "official Australian pollutant-register facility and industry classification"
            license_text = "Creative Commons Attribution 4.0 International"
            notes = (
                f"Selected systematically from the NPI facilities file: latest report=2024/2025 and "
                f"primary ANZSIC prefix in {', '.join(AUSTRALIA_PREFIXES)}. This is a facility-level "
                "discovery record; it does not establish any process-reactor inventory or design."
            )
        else:
            raise ValueError(f"unknown snapshot source {src['source']}")
        rows.append(
            {
                "stable_id": f"{src['source']}:{src['source_record_id']}",
                "facility_name": src["facility_name"],
                "country": src["country"],
                "lat": src["lat"],
                "lon": src["lon"],
                "precision": precision,
                "sector": src["sector_label"],
                "process_or_activity": process,
                "reactor_type_if_explicit": "",
                "status": status,
                "operator": src["operator"] or "not provided",
                "capacity": "",
                "pollutant_or_product_context": "source industry classification only; pollutant quantities excluded",
                "source_url": source_url,
                "source_role": role,
                "retrieved": retrieved,
                "license": license_text,
                "verification_notes": notes,
            }
        )
    rows.sort(key=lambda row: row["stable_id"])
    return rows


def check_output(path: Path, inputs: tuple[Path, ...] = ()) -> None:
    """Protect historical source files and all caller-supplied inputs."""
    target = path.resolve()
    if target.is_relative_to(ROOT) or target in {p.resolve() for p in inputs}:
        raise ValueError("output must be separate from historical files and inputs")


def write_table(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    """Atomically replace one explicitly requested TSV after validation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        try:
            writer = csv.DictWriter(
                handle, fieldnames=fields, dialect="excel-tab", lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        except Exception:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def refresh_snapshot(
    canada_raw: bytes,
    australia_raw: bytes,
    *,
    snapshot: Path,
    manifest: Path,
    retrieved: str,
) -> tuple[int, int]:
    """Write a separate compact snapshot and manifest from actual raw bytes.

    Each file is replaced atomically; the pair is not a multi-file transaction.
    The manifest records full raw-source hashes, not derived snapshot hashes.
    """
    check_output(snapshot, (manifest,))
    check_output(manifest, (snapshot,))
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO calendar date")
    selected = select_sources(canada_raw, australia_raw)
    rows_from_snapshot(selected, retrieved=retrieved)
    rows = [
        {
            "source": source,
            "url": url,
            "retrieved": retrieved,
            "bytes": str(len(raw)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "selected_rows": str(sum(r["source"] == source for r in selected)),
        }
        for source, url, raw in (
            ("canada-npri", CANADA_URL, canada_raw),
            ("australia-npi", AUSTRALIA_URL, australia_raw),
        )
    ]
    write_table(snapshot, SNAPSHOT_FIELDS, selected)
    write_table(manifest, MANIFEST_FIELDS, rows)
    return len(canada_raw), len(australia_raw)


def build(snapshot: Path, output: Path, *, retrieved: str = RETRIEVED) -> int:
    """Rebuild a requested output from a read-only compact snapshot."""
    check_output(output, (snapshot,))
    rows = rows_from_snapshot(read_snapshot(snapshot), retrieved=retrieved)
    write_table(output, FIELDS, rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    """Build explicit isolated outputs, reporting input failures without traceback."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--canada-source", type=Path)
    parser.add_argument("--australia-source", type=Path)
    parser.add_argument("--canada-url", default=CANADA_URL)
    parser.add_argument("--australia-url", default=AUSTRALIA_URL)
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        raw_inputs = tuple(
            p for p in (args.canada_source, args.australia_source, args.ca_file) if p
        )
        inputs = (*raw_inputs, *((args.manifest,) if args.manifest else ()))
        check_output(args.output, (args.snapshot, *inputs))
        retrieved = args.date or (date.today().isoformat() if args.refresh else RETRIEVED)
        if args.refresh:
            if args.manifest is None:
                raise ValueError("refresh requires an explicit separate manifest path")
            check_output(args.snapshot, inputs)
            check_output(args.manifest, (args.output, args.snapshot, *raw_inputs))
            canada = (
                args.canada_source.read_bytes()
                if args.canada_source
                else download(args.canada_url, ca_file=args.ca_file)
            )
            australia = (
                args.australia_source.read_bytes()
                if args.australia_source
                else download(args.australia_url, ca_file=args.ca_file)
            )
            sizes = refresh_snapshot(
                canada,
                australia,
                snapshot=args.snapshot,
                manifest=args.manifest,
                retrieved=retrieved,
            )
            print(
                f"refreshed source snapshot from {sizes[0]} Canada bytes and {sizes[1]} Australia bytes"
            )
        elif args.canada_source or args.australia_source or args.manifest:
            raise ValueError("raw sources and manifest options require --refresh")
        count = build(args.snapshot, args.output, retrieved=retrieved)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote {count} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
