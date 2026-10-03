#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round3/build_dataset.py
"""Build the UK PRTR industrial-facility discovery expansion.

Historical builds read the accepted compact snapshot and write an explicit
separate output. Refreshes preserve the documented 2024 NACE selection and write
a separate dated source snapshot and manifest.
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
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
OUTPUT = ROOT / "industrial_facilities_round3.tsv"
RETRIEVED = "2026-09-28"
REPORTING_YEAR = "2024"
USER_AGENT = "reactor-atlas-industrial-discovery/3.0"

RAW_URL = (
    "https://assets.publishing.service.gov.uk/media/6a633033243ee000f7127f33/"
    "uk_prtr_dataset_2024.csv"
)
LANDING_URL = (
    "https://www.gov.uk/government/publications/"
    "download-industrial-emissions-and-waste-transfer-uk-prtr-data"
)
NACE_PREFIXES = ("10", "11", "17", "19", "20", "21", "22")

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
    "reporting_year",
    "facility_name",
    "operator",
    "country",
    "lat",
    "lon",
    "nace_code",
    "nace_label",
    "annex_i_activity_code",
]

RAW_FIELDS = {
    "id": "FacilityReport_NationalID",
    "operator": "FacilityReport_ParentCompanyName",
    "name": "FacilityReport_FacilityName",
    "lon": "FacilityReport_GeographicalCoordinate_LongitudeMeasure",
    "lat": "FacilityReport_GeographicalCoordinate_LatitudeMeasure",
    "nace": "FacilityReport_NACEMainEconomicActivityCode",
    "nace_label": "FacilityReport_MainEconomicActivityName",
    "activity": "FacilityReport_Activity_AnnexIActivityCode",
}


MANIFEST_FIELDS = [
    "source",
    "url",
    "retrieved",
    "reporting_year",
    "bytes",
    "sha256",
    "raw_rows",
    "selected_rows",
]


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


def select_source(raw: bytes) -> tuple[list[dict[str, str]], int]:
    """Select actual annual source rows using only the declared NACE prefixes."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    missing = set(RAW_FIELDS.values()).difference(reader.fieldnames or [])
    if missing:
        raise ValueError(f"official CSV is missing expected fields: {sorted(missing)}")
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    raw_rows = 0
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("official CSV contains a row with the wrong width")
        raw_rows += 1
        nace = clean(row[RAW_FIELDS["nace"]])
        if not nace.startswith(NACE_PREFIXES):
            continue
        source_id = clean(row[RAW_FIELDS["id"]])
        if not source_id:
            raise ValueError("selected row has no FacilityReport_NationalID")
        if source_id in seen:
            raise ValueError(f"duplicate selected FacilityReport_NationalID: {source_id}")
        seen.add(source_id)
        selected.append(
            {
                "source": "uk-prtr",
                "source_record_id": source_id,
                "reporting_year": REPORTING_YEAR,
                "facility_name": clean(row[RAW_FIELDS["name"]]),
                "operator": clean(row[RAW_FIELDS["operator"]]),
                "country": "United Kingdom",
                "lat": clean(row[RAW_FIELDS["lat"]]),
                "lon": clean(row[RAW_FIELDS["lon"]]),
                "nace_code": nace,
                "nace_label": clean(row[RAW_FIELDS["nace_label"]]),
                "annex_i_activity_code": clean(row[RAW_FIELDS["activity"]]),
            }
        )
    selected.sort(key=lambda row: row["source_record_id"])
    if not selected:
        raise ValueError("official CSV contains no qualifying records")
    return selected, raw_rows


def rows_from_snapshot(
    source_rows: list[dict[str, str]],
    *,
    retrieved: str = RETRIEVED,
) -> list[dict[str, str]]:
    """Preserve reported facility observations without inferring reactor vessels."""
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO calendar date")
    if not source_rows:
        raise ValueError("compact snapshot contains no records")
    if any(
        set(row) != set(SNAPSHOT_FIELDS) or any(not isinstance(v, str) for v in row.values())
        for row in source_rows
    ):
        raise ValueError("compact snapshot record differs from the required string schema")
    ids: set[str] = set()
    for row in source_rows:
        for field in (
            "source_record_id",
            "facility_name",
            "operator",
            "lat",
            "lon",
            "nace_code",
            "nace_label",
        ):
            if not row[field].strip():
                raise ValueError(f"compact snapshot is missing {field}")
        if row["source_record_id"] in ids:
            raise ValueError("compact snapshot contains a duplicate source ID")
        ids.add(row["source_record_id"])
        if (
            row["source"] != "uk-prtr"
            or row["reporting_year"] != REPORTING_YEAR
            or row["country"] != "United Kingdom"
        ):
            raise ValueError("compact snapshot has an unexpected source, report year or country")
        if not row["nace_code"].startswith(NACE_PREFIXES):
            raise ValueError("compact snapshot NACE code is outside the documented filter")
        lat, lon = float(row["lat"]), float(row["lon"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("compact snapshot coordinates are out of range")
    rows: list[dict[str, str]] = []
    for src in source_rows:
        process = f"NACE {src['nace_code']} — {src['nace_label']}"
        if src["annex_i_activity_code"]:
            process += f" | UK PRTR Annex I activity {src['annex_i_activity_code']}"
        rows.append(
            {
                "stable_id": f"uk-prtr:{src['source_record_id']}",
                "facility_name": src["facility_name"],
                "country": src["country"],
                "lat": src["lat"],
                "lon": src["lon"],
                "precision": "UK PRTR-published facility point; positional accuracy not independently verified",
                "sector": f"NACE {src['nace_code']} — {src['nace_label']}",
                "process_or_activity": process,
                "reactor_type_if_explicit": "",
                "status": f"reported in UK PRTR for {src['reporting_year']}; operating status not asserted",
                "operator": src["operator"],
                "capacity": "",
                "pollutant_or_product_context": "source industry classification only; pollutant and waste quantities excluded",
                "source_url": LANDING_URL,
                "source_role": "official UK pollutant-register facility and activity classification",
                "retrieved": retrieved,
                "license": "Open Government Licence v3.0",
                "verification_notes": (
                    f"Selected systematically from the {REPORTING_YEAR} UK PRTR CSV by NACE prefix in "
                    f"{', '.join(NACE_PREFIXES)}. This facility-level discovery record does not establish "
                    "a process-reactor inventory, reactor design, capacity, or current operating state."
                ),
            }
        )

    rows.sort(key=lambda row: row["stable_id"])
    return rows


def refresh_snapshot(
    raw: bytes,
    *,
    snapshot: Path,
    manifest: Path,
    retrieved: str,
) -> tuple[int, int]:
    """Write separate snapshot and raw-source manifest after complete parsing.

    Individual TSV replacements are atomic; the pair is not a multi-file
    transaction. Reporting year derives from the official annual source.
    """
    check_output(snapshot, (manifest,))
    check_output(manifest, (snapshot,))
    selected, raw_rows = select_source(raw)
    rows_from_snapshot(selected, retrieved=retrieved)
    records = [
        {
            "source": "uk-prtr",
            "url": RAW_URL,
            "retrieved": retrieved,
            "reporting_year": REPORTING_YEAR,
            "bytes": str(len(raw)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_rows": str(raw_rows),
            "selected_rows": str(len(selected)),
        }
    ]
    write_table(snapshot, SNAPSHOT_FIELDS, selected)
    write_table(manifest, MANIFEST_FIELDS, records)
    return raw_rows, len(selected)


def build(snapshot: Path, output: Path, *, retrieved: str = RETRIEVED) -> int:
    """Rebuild one explicit output from a read-only historical snapshot."""
    check_output(output, (snapshot,))
    rows = rows_from_snapshot(read_snapshot(snapshot), retrieved=retrieved)
    write_table(output, FIELDS, rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    """Build isolated outputs and report invalid source inputs without traceback."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--raw-source", type=Path)
    parser.add_argument("--source-url", default=RAW_URL)
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        inputs = tuple(p for p in (args.raw_source, args.ca_file) if p)
        check_output(
            args.output, (args.snapshot, *inputs, *((args.manifest,) if args.manifest else ()))
        )
        retrieved = args.date or (date.today().isoformat() if args.refresh else RETRIEVED)
        if args.refresh:
            if args.manifest is None:
                raise ValueError("refresh requires an explicit separate manifest path")
            check_output(args.snapshot, (args.manifest, *inputs))
            check_output(args.manifest, (args.output, args.snapshot, *inputs))
            raw = (
                args.raw_source.read_bytes()
                if args.raw_source
                else download(args.source_url, ca_file=args.ca_file)
            )
            raw_rows, selected_rows = refresh_snapshot(
                raw,
                snapshot=args.snapshot,
                manifest=args.manifest,
                retrieved=retrieved,
            )
            print(f"refreshed snapshot: {raw_rows} raw rows, {selected_rows} selected rows")
        elif args.raw_source or args.manifest:
            raise ValueError("raw source and manifest options require --refresh")
        count = build(args.snapshot, args.output, retrieved=retrieved)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote {count} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
