#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round5/build_dataset.py
"""Build process-specific UK anaerobic-digestion and French hydrogen layers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import ssl
import tempfile
import urllib.parse
import urllib.request
from datetime import date, datetime
from http.client import HTTPMessage
from pathlib import Path
from typing import IO

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
OUTPUT = ROOT / "industrial_facilities_round5.tsv"
RETRIEVED = "2026-09-28"
USER_AGENT = "reactor-atlas-industrial-discovery/5.0"

REPD_RAW_URL = "https://assets.publishing.service.gov.uk/media/6a6cbdc00c36759b5ccaa305/REPD_Publication_Q2_2026.csv"
REPD_LANDING = "https://www.gov.uk/government/publications/renewable-energy-planning-database-quarterly-extract"
ADEME_SLUG = "liste-des-sites-de-production-et-de-distribution-dhydrogene-finances-par-lademe"
ADEME_RAW_URL = (
    f"https://data.ademe.fr/data-fair/api/v1/datasets/{ADEME_SLUG}/lines?size=1000&sort=_id"
)
ADEME_LANDING = f"https://data.ademe.fr/datasets/{ADEME_SLUG}"
GB_JURISDICTIONS = {"England", "Scotland", "Wales"}

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
    "source_row_id",
    "facility_name",
    "operator",
    "country",
    "region_or_commune",
    "lat",
    "lon",
    "coordinate_basis",
    "source_x",
    "source_y",
    "technology_type",
    "process_detail",
    "status",
    "capacity",
    "project_name",
    "source_record_updated",
]


MANIFEST_FIELDS = ["source", "url", "retrieved", "bytes", "sha256", "raw_rows", "selected_rows"]
REPD_FIELDS = [
    "Technology Type",
    "Country",
    "X-coordinate",
    "Y-coordinate",
    "Installed Capacity (MWelec)",
    "Ref ID",
    "Site Name",
    "Operator (or Applicant)",
    "CHP Enabled",
    "Development Status",
    "Record Last Updated (dd/mm/yyyy)",
]
ADEME_FIELDS = [
    "site_type",
    "puissance_mw",
    "capacite_production",
    "site_nom",
    "projet",
    "station_code_commune",
    "_id",
    "station_operateur",
    "station_commune",
    "station_latitude",
    "station_longitude",
    "site_statut",
]
ADEME_REQUIRED = [
    "site_nom",
    "projet",
    "station_code_commune",
    "_id",
    "station_latitude",
    "station_longitude",
    "site_statut",
]
ADEME_METADATA_URL = f"https://data.ademe.fr/data-fair/api/v1/datasets/{ADEME_SLUG}"


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


def osgb36_grid_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """Approximate BNG to WGS84 transformation using OS-published equations.

    This uses inverse Transverse Mercator on Airy 1830 followed by the inverse
    of Ordnance Survey's approximate WGS84-to-OSGB36 Helmert transform. OS
    characterises the simple Helmert method as about 3 metres accuracy.
    """
    if not 0 <= easting <= 700000 or not 0 <= northing <= 1300000:
        raise ValueError("BNG point must be finite and within Great Britain grid bounds")
    a, b = 6377563.396, 6356256.909
    f0 = 0.9996012717
    lat0, lon0 = math.radians(49), math.radians(-2)
    n0, e0 = -100000.0, 400000.0
    e2 = 1 - (b * b) / (a * a)
    n = (a - b) / (a + b)

    lat = lat0
    meridional = 0.0
    while abs(northing - n0 - meridional) >= 0.00001:
        lat = (northing - n0 - meridional) / (a * f0) + lat
        d = lat - lat0
        s = lat + lat0
        meridional = (
            b
            * f0
            * (
                (1 + n + 1.25 * n**2 + 1.25 * n**3) * d
                - (3 * n + 3 * n**2 + 2.625 * n**3) * math.sin(d) * math.cos(s)
                + (1.875 * n**2 + 1.875 * n**3) * math.sin(2 * d) * math.cos(2 * s)
                - (35 / 24) * n**3 * math.sin(3 * d) * math.cos(3 * s)
            )
        )

    sin_lat, cos_lat, tan_lat = math.sin(lat), math.cos(lat), math.tan(lat)
    nu = a * f0 / math.sqrt(1 - e2 * sin_lat**2)
    rho = a * f0 * (1 - e2) / (1 - e2 * sin_lat**2) ** 1.5
    eta2 = nu / rho - 1
    de = easting - e0
    vii = tan_lat / (2 * rho * nu)
    viii = tan_lat / (24 * rho * nu**3) * (5 + 3 * tan_lat**2 + eta2 - 9 * tan_lat**2 * eta2)
    ix = tan_lat / (720 * rho * nu**5) * (61 + 90 * tan_lat**2 + 45 * tan_lat**4)
    x = 1 / (cos_lat * nu)
    xi = 1 / (cos_lat * 6 * nu**3) * (nu / rho + 2 * tan_lat**2)
    xii = 1 / (cos_lat * 120 * nu**5) * (5 + 28 * tan_lat**2 + 24 * tan_lat**4)
    xiia = (
        1
        / (cos_lat * 5040 * nu**7)
        * (61 + 662 * tan_lat**2 + 1320 * tan_lat**4 + 720 * tan_lat**6)
    )
    lat_airy = lat - vii * de**2 + viii * de**4 - ix * de**6
    lon_airy = lon0 + x * de - xi * de**3 + xii * de**5 - xiia * de**7

    height = 0.0
    nu_airy = a / math.sqrt(1 - e2 * math.sin(lat_airy) ** 2)
    x1 = (nu_airy + height) * math.cos(lat_airy) * math.cos(lon_airy)
    y1 = (nu_airy + height) * math.cos(lat_airy) * math.sin(lon_airy)
    z1 = ((1 - e2) * nu_airy + height) * math.sin(lat_airy)

    # Inverse of OS guide table 4: OSGB36 -> WGS84. These are already inverse signs.
    tx, ty, tz = 446.448, -125.157, 542.060
    rx, ry, rz = [math.radians(v / 3600) for v in (0.1502, 0.2470, 0.8421)]
    scale = -20.4894e-6
    x2 = tx + (1 + scale) * x1 - rz * y1 + ry * z1
    y2 = ty + rz * x1 + (1 + scale) * y1 - rx * z1
    z2 = tz - ry * x1 + rx * y1 + (1 + scale) * z1

    aw, bw = 6378137.0, 6356752.3141
    e2w = 1 - (bw * bw) / (aw * aw)
    p = math.hypot(x2, y2)
    lat_wgs = math.atan2(z2, p * (1 - e2w))
    previous = 2 * math.pi
    while abs(lat_wgs - previous) > 1e-12:
        previous = lat_wgs
        nu_wgs = aw / math.sqrt(1 - e2w * math.sin(lat_wgs) ** 2)
        lat_wgs = math.atan2(z2 + e2w * nu_wgs * math.sin(lat_wgs), p)
    lon_wgs = math.atan2(y2, x2)
    return math.degrees(lat_wgs), math.degrees(lon_wgs)


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


def metadata_date(raw: bytes) -> str:
    """Use the dataset's actual data timestamp, distinct from description updates."""
    metadata = json.loads(raw)
    if not isinstance(metadata, dict) or not isinstance(metadata.get("dataUpdatedAt"), str):
        raise ValueError("ADEME metadata requires a dataUpdatedAt timestamp")
    timestamp = datetime.fromisoformat(metadata["dataUpdatedAt"])
    if timestamp.tzinfo is None:
        raise ValueError("ADEME dataUpdatedAt timestamp must include its timezone")
    return timestamp.date().isoformat()


def select_sources(
    repd_raw: bytes, ademe_raw: bytes, *, ademe_updated: str
) -> tuple[list[dict[str, str]], int, int]:
    """Select every explicit process record from genuine complete source responses."""
    if date.fromisoformat(ademe_updated).isoformat() != ademe_updated:
        raise ValueError("ADEME source date must be an exact ISO calendar date")
    selected: list[dict[str, str]] = []

    repd_reader = csv.DictReader(io.StringIO(repd_raw.decode("windows-1252")), strict=True)
    if not set(REPD_FIELDS).issubset(repd_reader.fieldnames or []):
        raise ValueError("REPD source is missing required columns")
    repd_rows = list(repd_reader)
    for row in repd_rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("REPD source row has the wrong width")
        if clean(row["Technology Type"]) != "Anaerobic Digestion":
            continue
        subdivision = clean(row["Country"])
        if subdivision not in GB_JURISDICTIONS:
            continue
        east, north = float(row["X-coordinate"]), float(row["Y-coordinate"])
        lat, lon = osgb36_grid_to_wgs84(east, north)
        capacity = clean(row["Installed Capacity (MWelec)"])
        if capacity == "Not set":
            capacity = ""
        selected.append(
            {
                "source": "uk-repd-ad",
                "source_record_id": clean(row["Ref ID"]),
                "source_row_id": clean(row["Ref ID"]),
                "facility_name": clean(row["Site Name"]),
                "operator": clean(row["Operator (or Applicant)"]),
                "country": "United Kingdom",
                "region_or_commune": subdivision,
                "lat": f"{lat:.6f}",
                "lon": f"{lon:.6f}",
                "coordinate_basis": "REPD British National Grid project point; approximate WGS84 transform",
                "source_x": clean(row["X-coordinate"]),
                "source_y": clean(row["Y-coordinate"]),
                "technology_type": "Anaerobic Digestion",
                "process_detail": "CHP Enabled: " + clean(row["CHP Enabled"]),
                "status": clean(row["Development Status"]),
                "capacity": (capacity + " MW electrical installed capacity") if capacity else "",
                "project_name": clean(row["Site Name"]),
                "source_record_updated": clean(row["Record Last Updated (dd/mm/yyyy)"]),
            }
        )

    ademe_payload = json.loads(ademe_raw)
    if not isinstance(ademe_payload, dict) or not isinstance(ademe_payload.get("results"), list):
        raise ValueError("ADEME source must contain a results list")
    ademe_rows = ademe_payload["results"]
    if ademe_payload.get("total") != len(ademe_rows):
        raise ValueError("ADEME response is incomplete or has an invalid total")
    for row in ademe_rows:
        if not isinstance(row, dict) or any(
            isinstance(v, (dict, list)) for k, v in row.items() if k in ADEME_FIELDS
        ):
            raise ValueError("ADEME source record has invalid scalar fields")
        if clean(row.get("site_type")) != "Production":
            continue
        if not set(ADEME_REQUIRED).issubset(row):
            raise ValueError("ADEME production record is missing required fields")
        capacity_parts = []
        for field in ("puissance_mw", "capacite_production"):
            if row.get(field) is not None and (
                isinstance(row[field], bool)
                or not math.isfinite(float(row[field]))
                or float(row[field]) < 0
            ):
                raise ValueError("ADEME capacity must be finite and nonnegative")
        if row.get("puissance_mw") is not None:
            capacity_parts.append(f"planned power {row['puissance_mw']} MW")
        if row.get("capacite_production") is not None:
            capacity_parts.append(f"production capacity {row['capacite_production']} kg H2/day")
        canonical_key = "|".join(
            [
                clean(row.get("site_nom")),
                clean(row.get("projet")),
                clean(row.get("station_code_commune")),
            ]
        )
        stable_key = hashlib.sha256(canonical_key.encode("utf-8")).hexdigest()[:16]
        selected.append(
            {
                "source": "fr-ademe-h2",
                "source_record_id": stable_key,
                "source_row_id": clean(row["_id"]),
                "facility_name": clean(row.get("site_nom")),
                "operator": clean(row.get("station_operateur")) or "not provided",
                "country": "France",
                "region_or_commune": clean(row.get("station_commune")),
                "lat": clean(row.get("station_latitude")),
                "lon": clean(row.get("station_longitude")),
                "coordinate_basis": "ADEME-published project point; parcel when known, otherwise commune coordinate",
                "source_x": "",
                "source_y": "",
                "technology_type": "Hydrogen production",
                "process_detail": "ADEME site type: Production",
                "status": clean(row.get("site_statut")),
                "capacity": "; ".join(capacity_parts),
                "project_name": clean(row.get("projet")),
                "source_record_updated": "dataset updated " + ademe_updated,
            }
        )

    selected.sort(key=lambda row: (row["source"], row["source_record_id"]))
    if not selected:
        raise ValueError("source files contain no qualifying records")
    rows_from_snapshot(selected)
    return selected, len(repd_rows), len(ademe_rows)


def rows_from_snapshot(
    source_rows: list[dict[str, str]], *, retrieved: str = RETRIEVED
) -> list[dict[str, str]]:
    """Preserve reported projects, source status and explicit capacity without inference."""
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO calendar date")
    if not source_rows:
        raise ValueError("compact snapshot contains no records")
    if any(
        set(row) != set(SNAPSHOT_FIELDS) or any(not isinstance(v, str) for v in row.values())
        for row in source_rows
    ):
        raise ValueError("compact snapshot record differs from its required string schema")
    ids: set[tuple[str, str]] = set()
    for row in source_rows:
        for field in (
            "source_record_id",
            "source_row_id",
            "facility_name",
            "operator",
            "country",
            "lat",
            "lon",
            "coordinate_basis",
            "technology_type",
            "status",
            "project_name",
            "source_record_updated",
        ):
            if not row[field].strip():
                raise ValueError(f"compact snapshot is missing {field}")
        key = row["source"], row["source_record_id"]
        if key in ids:
            raise ValueError("compact snapshot contains duplicate source IDs")
        ids.add(key)
        latitude, longitude = float(row["lat"]), float(row["lon"])
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("compact snapshot coordinates are out of range")
        if row["source"] == "uk-repd-ad":
            if (
                row["country"] != "United Kingdom"
                or row["region_or_commune"] not in GB_JURISDICTIONS
                or row["technology_type"] != "Anaerobic Digestion"
            ):
                raise ValueError("compact snapshot has an invalid UK selection")
            lat, lon = osgb36_grid_to_wgs84(float(row["source_x"]), float(row["source_y"]))
            if row["lat"] != f"{lat:.6f}" or row["lon"] != f"{lon:.6f}":
                raise ValueError(
                    "compact snapshot WGS84 point differs from its published BNG point"
                )
        elif row["source"] == "fr-ademe-h2":
            if (
                row["country"] != "France"
                or row["technology_type"] != "Hydrogen production"
                or row["process_detail"] != "ADEME site type: Production"
            ):
                raise ValueError("compact snapshot has an invalid ADEME selection")
    rows = []
    for src in source_rows:
        if src["source"] == "uk-repd-ad":
            row = {
                "stable_id": f"uk-repd:{src['source_record_id']}",
                "facility_name": src["facility_name"],
                "country": src["country"],
                "lat": src["lat"],
                "lon": src["lon"],
                "precision": "REPD-published British National Grid project point transformed with OS approximate Helmert method (about 3 m); source position not independently verified",
                "sector": "anaerobic digestion / renewable energy planning",
                "process_or_activity": f"REPD technology: Anaerobic Digestion | {src['process_detail']} | jurisdiction: {src['region_or_commune']}",
                "reactor_type_if_explicit": "Anaerobic digestion (source technology type; vessel design and count not published)",
                "status": f"REPD-published development status: {src['status']}; not independently verified",
                "operator": src["operator"],
                "capacity": src["capacity"],
                "pollutant_or_product_context": "biogas/renewable-energy project context; feedstock and gas output not inferred",
                "source_url": REPD_LANDING,
                "source_role": "official UK renewable-energy planning project technology and status register",
                "retrieved": retrieved,
                "license": "Open Government Licence v3.0",
                "verification_notes": "All July 2026 REPD Anaerobic Digestion records in England, Scotland and Wales are included. Northern Ireland is excluded because its coordinates use a different grid. REPD records are planning projects and may represent revised applications at the same physical site.",
            }
        elif src["source"] == "fr-ademe-h2":
            status = {"Opérationnel": "Operational", "Engagé": "Committed"}.get(
                src["status"], src["status"]
            )
            row = {
                "stable_id": f"fr-ademe-h2:{src['source_record_id']}",
                "facility_name": src["facility_name"],
                "country": src["country"],
                "lat": src["lat"],
                "lon": src["lon"],
                "precision": "ADEME-published point; dataset uses parcel location when known and otherwise a commune coordinate; row-level basis not identified",
                "sector": "low-carbon or renewable hydrogen production",
                "process_or_activity": f"ADEME site type: Production | supported project: {src['project_name']}",
                "reactor_type_if_explicit": "",
                "status": f"ADEME-published status: {status} (source label: {src['status']}); not independently verified",
                "operator": src["operator"],
                "capacity": src["capacity"],
                "pollutant_or_product_context": "hydrogen production; individual production pathway not stated in the source row",
                "source_url": ADEME_LANDING,
                "source_role": "official ADEME-supported hydrogen production project register",
                "retrieved": retrieved,
                "license": "Licence Ouverte / Open Licence 2.0",
                "verification_notes": "All rows explicitly classified by ADEME as site type Production are included. The dataset description says production is mainly electrolysis, but no production pathway is assigned to an individual row unless the source explicitly supplies it; therefore reactor type remains blank.",
            }
        else:
            raise ValueError(f"unknown source {src['source']}")
        rows.append(row)
    rows.sort(key=lambda row: row["stable_id"])
    return rows


def refresh_snapshot(
    repd_raw: bytes,
    ademe_raw: bytes,
    *,
    ademe_updated: str,
    snapshot: Path,
    manifest: Path,
    retrieved: str,
) -> tuple[int, int, int, int]:
    """Write isolated source/provenance candidates after full parsing and validation."""
    check_output(snapshot, (manifest,))
    check_output(manifest, (snapshot,))
    selected, uk_count, fr_count = select_sources(repd_raw, ademe_raw, ademe_updated=ademe_updated)
    rows_from_snapshot(selected, retrieved=retrieved)
    uk_selected = sum(row["source"] == "uk-repd-ad" for row in selected)
    fr_selected = sum(row["source"] == "fr-ademe-h2" for row in selected)
    records = [
        {
            "source": source,
            "url": url,
            "retrieved": retrieved,
            "bytes": str(len(raw)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_rows": str(count),
            "selected_rows": str(chosen),
        }
        for source, url, raw, count, chosen in [
            ("uk-repd-ad", REPD_RAW_URL, repd_raw, uk_count, uk_selected),
            ("fr-ademe-h2", ADEME_RAW_URL, ademe_raw, fr_count, fr_selected),
        ]
    ]
    write_table(snapshot, SNAPSHOT_FIELDS, selected)
    write_table(manifest, MANIFEST_FIELDS, records)
    return uk_count, fr_count, uk_selected, fr_selected


def build(snapshot: Path, output: Path, *, retrieved: str = RETRIEVED) -> int:
    """Rebuild an explicit output without changing accepted inputs."""
    check_output(output, (snapshot,))
    rows = rows_from_snapshot(read_snapshot(snapshot), retrieved=retrieved)
    write_table(output, FIELDS, rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    """Build separate outputs or an explicitly dated source-refresh candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--repd-source", type=Path)
    parser.add_argument("--ademe-source", type=Path)
    parser.add_argument("--ademe-metadata", type=Path)
    parser.add_argument("--repd-url", default=REPD_RAW_URL)
    parser.add_argument("--ademe-url", default=ADEME_RAW_URL)
    parser.add_argument("--ademe-metadata-url", default=ADEME_METADATA_URL)
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        inputs = tuple(
            p for p in (args.repd_source, args.ademe_source, args.ademe_metadata, args.ca_file) if p
        )
        check_output(
            args.output, (args.snapshot, *inputs, *((args.manifest,) if args.manifest else ()))
        )
        retrieved = args.date or (date.today().isoformat() if args.refresh else RETRIEVED)
        if args.refresh:
            if args.manifest is None:
                raise ValueError("refresh requires an explicit separate manifest path")
            check_output(args.snapshot, (args.manifest, *inputs))
            check_output(args.manifest, (args.output, args.snapshot, *inputs))
            repd = (
                args.repd_source.read_bytes()
                if args.repd_source
                else download(args.repd_url, ca_file=args.ca_file)
            )
            ademe = (
                args.ademe_source.read_bytes()
                if args.ademe_source
                else download(args.ademe_url, ca_file=args.ca_file)
            )
            metadata = (
                args.ademe_metadata.read_bytes()
                if args.ademe_metadata
                else download(args.ademe_metadata_url, ca_file=args.ca_file)
            )
            counts = refresh_snapshot(
                repd,
                ademe,
                ademe_updated=metadata_date(metadata),
                snapshot=args.snapshot,
                manifest=args.manifest,
                retrieved=retrieved,
            )
            print(
                f"refreshed {counts[0]}/{counts[1]} source rows; {counts[2]}/{counts[3]} selected"
            )
        elif any((args.repd_source, args.ademe_source, args.ademe_metadata, args.manifest)):
            raise ValueError("source and manifest options require --refresh")
        count = build(args.snapshot, args.output, retrieved=retrieved)
    except (OSError, UnicodeError, csv.Error, ValueError, TypeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote {count} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
