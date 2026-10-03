#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round6/build_dataset.py
"""Build round-six Brazil biofuel and US landfill-gas discovery records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import ssl
import tempfile
import urllib.parse
import urllib.request
from datetime import date
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Any

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
OUTPUT = ROOT / "industrial_facilities_round6.tsv"
RETRIEVED = "2026-09-28"
USER_AGENT = "reactor-atlas-industrial-discovery/6.0"

EPE_SERVICE = (
    "https://gisepeprd2.epe.gov.br/arcgis/rest/services/SMA/Webmap_EPE_Biocombustiveis/MapServer"
)
EPE_LANDING = "https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/webmap-epe"
LMOP_SERVICE = "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/LMOP_Projects/FeatureServer/0"
LMOP_LANDING = "https://www.epa.gov/lmop/lmop-landfill-and-project-database"

SOURCES = {
    "br-epe-ethanol": (f"{EPE_SERVICE}/0", "EPE ethanol plants"),
    "br-epe-biodiesel": (f"{EPE_SERVICE}/1", "EPE biodiesel plants"),
    "br-epe-biomethane": (f"{EPE_SERVICE}/2", "EPE biomethane plants"),
    "us-epa-lmop": (LMOP_SERVICE, "EPA operational landfill-gas energy projects"),
}

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
    "country",
    "subdivision",
    "municipality_or_county",
    "lat",
    "lon",
    "coordinate_basis",
    "plant_or_project_type",
    "source_status",
    "operator_or_parties",
    "capacity",
    "feedstock_or_context",
    "start_date",
    "source_row_notes",
]


MANIFEST_FIELDS = [
    "source",
    "title",
    "url",
    "retrieved",
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


def positive(value: object) -> str:
    """Preserve a finite positive published capacity; blanks/nonpositive stay blank."""
    text = clean(value)
    if not text:
        return ""
    number = float(text)
    if isinstance(value, bool) or not math.isfinite(number):
        raise ValueError("source capacity must be a finite numeric scalar")
    return text if number > 0 else ""


def query_url(service: str) -> str:
    """Request every field and WGS84 geometry in deterministic service order."""
    return (
        service
        + "/query?"
        + urllib.parse.urlencode(
            {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": "OBJECTID",
                "f": "json",
            }
        )
    )


def count_url(url: str) -> str:
    """Count the same query selection independently of the feature response."""
    check_https(url)
    parsed = urllib.parse.urlsplit(url)
    parameters = dict(urllib.parse.parse_qsl(parsed.query))
    for name in (
        "outFields",
        "returnGeometry",
        "outSR",
        "orderByFields",
        "resultOffset",
        "resultRecordCount",
    ):
        parameters.pop(name, None)
    parameters.update({"returnCountOnly": "true", "f": "json"})
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(parameters)))


def epe_snapshot(source: str, feature: dict[str, Any]) -> dict[str, str]:
    """Map an EPE feature to an atlas facility record."""
    a = feature["attributes"]
    geometry = feature.get("geometry") or {}
    oid = clean(a["OBJECTID"])
    if source == "br-epe-ethanol":
        capacity_parts = []
        if clean(a.get("Classecap")):
            capacity_parts.append(f"source cane-processing capacity class: {clean(a['Classecap'])}")
        for field, label in (
            ("Caprocmi", "corn processing t"),
            ("Cpanhm3d", "anhydrous ethanol m3/day"),
            ("Cphidrm3d", "hydrated ethanol m3/day"),
        ):
            if positive(a.get(field)):
                capacity_parts.append(f"{positive(a[field])} {label}")
        name, municipality = clean(a.get("Nome")), clean(a.get("Cidade"))
        plant_type, status = clean(a.get("Tipo")), clean(a.get("Situacao"))
        context = f"EPE ethanol-layer source plant type: {plant_type}"
        operator = "not separately provided; source name retained as facility name"
        start = ""
    elif source == "br-epe-biodiesel":
        capacity_parts = []
        if positive(a.get("Capm3dia")):
            capacity_parts.append(f"{positive(a['Capm3dia'])} m3/day capacity")
        if positive(a.get("Capm3ano")):
            capacity_parts.append(f"{positive(a['Capm3ano'])} m3/year capacity")
        name, municipality = clean(a.get("Nome")), clean(a.get("Municipio"))
        plant_type, status = "Biodiesel plant", clean(a.get("AutANP"))
        context = "biodiesel production; source social-biofuel seal: " + (
            clean(a.get("SeloBSoc")) or "not provided"
        )
        operator = "not separately provided; source name retained as facility name"
        start = ""
    elif source == "br-epe-biomethane":
        capacity_parts = []
        if positive(a.get("Capacidade")):
            capacity_parts.append(f"{positive(a['Capacidade'])} Nm3/day plant capacity")
        name, municipality = clean(a.get("Empresa")), clean(a.get("Municipio"))
        plant_type, status = "Biomethane plant", clean(a.get("Situacao"))
        context = "biomethane production; source feedstock: " + (
            clean(a.get("MateriaPri")) or "not provided"
        )
        operator = clean(a.get("Empresa")) or "not provided"
        start = clean(a.get("InicioOper"))
        authorization = clean(a.get("Autorizaca"))
        if authorization:
            status += f" | source operation-authorization field: {authorization}"
    else:
        raise ValueError(source)
    lat, lon = clean(a.get("Latitude")), clean(a.get("Longitude"))
    if not lat or not lon:
        raise ValueError(f"{source}:{oid} has no published coordinate")
    # Retain both the attribute and service geometry check without creating a new point.
    gx, gy = clean(geometry.get("x")), clean(geometry.get("y"))
    notes = f"ArcGIS OBJECTID {oid}; service geometry {gy},{gx}"
    canonical = "|".join(
        (
            source,
            oid,
            name,
            clean(a.get("UF")),
            municipality,
            lat,
            lon,
            plant_type,
            status,
            "; ".join(capacity_parts),
        )
    )
    stable_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return {
        "source": source,
        "source_record_id": stable_key,
        "source_row_id": oid,
        "facility_name": name,
        "country": "Brazil",
        "subdivision": clean(a.get("UF")),
        "municipality_or_county": municipality,
        "lat": lat,
        "lon": lon,
        "coordinate_basis": "EPE-published latitude/longitude attribute and point geometry",
        "plant_or_project_type": plant_type,
        "source_status": status,
        "operator_or_parties": operator,
        "capacity": "; ".join(capacity_parts),
        "feedstock_or_context": context,
        "start_date": start,
        "source_row_notes": notes,
    }


def lmop_snapshot(feature: dict[str, Any]) -> dict[str, str]:
    """Map an LMOP landfill-gas feature to an atlas facility record."""
    a = feature["attributes"]
    geometry = feature.get("geometry") or {}
    oid = clean(a["OBJECTID"])
    capacity_parts = []
    if positive(a.get("total_mw_capacity")):
        capacity_parts.append(f"{positive(a['total_mw_capacity'])} MW total capacity")
    if positive(a.get("total_lfg_flow")):
        capacity_parts.append(f"{positive(a['total_lfg_flow'])} mmscfd total LFG flow to project")
    parties = []
    for field, label in (
        ("project_owners", "project owner"),
        ("project_developers", "project developer"),
        ("landfill_owner_org", "landfill owner"),
    ):
        if clean(a.get(field)):
            parties.append(f"{label}: {clean(a[field])}")
    context = f"landfill gas energy; source category: {clean(a.get('project_type_category'))}"
    if clean(a.get("end_users")):
        context += f"; source end user(s): {clean(a['end_users'])}"
    lat, lon = clean(a.get("latitude")), clean(a.get("longitude"))
    if not lat or not lon:
        raise ValueError(f"us-epa-lmop:{oid} has no published coordinate")
    gx, gy = clean(geometry.get("x")), clean(geometry.get("y"))
    canonical = "|".join(
        (
            oid,
            clean(a.get("ghgrp_id")),
            clean(a.get("landfill_name")),
            clean(a.get("county_state")),
            clean(a.get("initial_project_start_date")),
            clean(a.get("lfg_energy_project_type")),
            clean(a.get("project_type_category")),
        )
    )
    stable_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return {
        "source": "us-epa-lmop",
        "source_record_id": stable_key,
        "source_row_id": oid,
        "facility_name": clean(a.get("landfill_name")),
        "country": "United States",
        "subdivision": clean(a.get("county_state")).rsplit(",", 1)[-1].strip(),
        "municipality_or_county": clean(a.get("county_state")),
        "lat": lat,
        "lon": lon,
        "coordinate_basis": "EPA LMOP-published latitude/longitude attribute and point geometry",
        "plant_or_project_type": clean(a.get("lfg_energy_project_type")),
        "source_status": "Operational landfill-gas energy project (official map scope; September 2024 data release)",
        "operator_or_parties": " | ".join(parties) or "not provided",
        "capacity": "; ".join(capacity_parts),
        "feedstock_or_context": context,
        "start_date": clean(a.get("initial_project_start_date")),
        "source_row_notes": f"ArcGIS OBJECTID {oid}; GHGRP cross-reference {clean(a.get('ghgrp_id')) or 'not provided'}; service geometry {gy},{gx}",
    }


def select_source(source: str, raw: bytes, count_raw: bytes) -> list[dict[str, str]]:
    """Require a complete, uniquely identified WGS84 layer before mapping its facts."""
    if source not in SOURCES:
        raise ValueError("unknown source layer")
    payload, count = json.loads(raw), json.loads(count_raw)
    if (
        not isinstance(count, dict)
        or type(count.get("count")) is not int
        or count["count"] <= 0
        or count.get("error")
    ):
        raise ValueError("source count response must contain a positive integer count")
    if (
        not isinstance(payload, dict)
        or payload.get("error")
        or not isinstance(payload.get("features"), list)
    ):
        raise ValueError("source response must contain a feature list without an API error")
    features = payload["features"]
    if payload.get("exceededTransferLimit") not in (None, False) or len(features) != count["count"]:
        raise ValueError("source response is incomplete; obtain all pages before refreshing")
    reference = payload.get("spatialReference")
    if not isinstance(reference, dict) or reference.get("wkid") != 4326:
        raise ValueError("source geometry must explicitly use WGS84 EPSG4326")
    identifiers: set[str] = set()
    rows = []
    for feature in features:
        if (
            not isinstance(feature, dict)
            or not isinstance(feature.get("attributes"), dict)
            or not isinstance(feature.get("geometry"), dict)
        ):
            raise ValueError("source feature requires attributes and point geometry")
        attributes, geometry = feature["attributes"], feature["geometry"]
        if any(
            v is not None and (isinstance(v, bool) or not isinstance(v, (str, int, float)))
            for v in attributes.values()
        ):
            raise ValueError("source attribute must be a scalar")
        identifier = clean(attributes.get("OBJECTID"))
        if (
            isinstance(attributes.get("OBJECTID"), bool)
            or not identifier
            or int(identifier) <= 0
            or identifier in identifiers
        ):
            raise ValueError("source OBJECTIDs must be positive, nonempty and unique")
        identifiers.add(identifier)
        lat_field, lon_field = (
            ("Latitude", "Longitude") if source.startswith("br-epe-") else ("latitude", "longitude")
        )
        for name, lower, upper in ((lat_field, -90, 90), (lon_field, -180, 180)):
            value = attributes.get(name)
            if isinstance(value, bool) or value is None or not lower <= float(value) <= upper:
                raise ValueError("source attribute point must be finite and within WGS84 bounds")
        for name, lower, upper in (("y", -90, 90), ("x", -180, 180)):
            value = geometry.get(name)
            if isinstance(value, bool) or value is None or not lower <= float(value) <= upper:
                raise ValueError("source geometry point must be finite and within WGS84 bounds")
        if (
            abs(float(attributes[lat_field]) - float(geometry["y"])) > 0.000001
            or abs(float(attributes[lon_field]) - float(geometry["x"])) > 0.000001
        ):
            raise ValueError("source attribute and service point disagree beyond decimal rounding")
        rows.append(
            epe_snapshot(source, feature)
            if source.startswith("br-epe-")
            else lmop_snapshot(feature)
        )
    rows_from_snapshot(rows)
    return rows


def rows_from_snapshot(
    source_rows: list[dict[str, str]], *, retrieved: str = RETRIEVED
) -> list[dict[str, str]]:
    """Validate the compact facts and preserve the original curated output mapping."""
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO calendar date")
    if not source_rows:
        raise ValueError("compact snapshot contains no records")
    if any(
        set(row) != set(SNAPSHOT_FIELDS) or any(not isinstance(v, str) for v in row.values())
        for row in source_rows
    ):
        raise ValueError("compact snapshot differs from its required string schema")
    keys: set[tuple[str, str]] = set()
    row_keys: set[tuple[str, str]] = set()
    for row in source_rows:
        if row["source"] not in SOURCES:
            raise ValueError("unknown compact source")
        for field in (
            "source_record_id",
            "source_row_id",
            "facility_name",
            "country",
            "subdivision",
            "municipality_or_county",
            "lat",
            "lon",
            "coordinate_basis",
            "plant_or_project_type",
            "source_status",
            "operator_or_parties",
            "feedstock_or_context",
            "source_row_notes",
        ):
            if not row[field].strip():
                raise ValueError(f"compact snapshot is missing {field}")
        key, row_key = (
            (row["source"], row["source_record_id"]),
            (row["source"], row["source_row_id"]),
        )
        if key in keys or row_key in row_keys:
            raise ValueError("compact snapshot contains duplicate source identities")
        keys.add(key)
        row_keys.add(row_key)
        lat, lon = float(row["lat"]), float(row["lon"])
        if row["source"].startswith("br-epe-"):
            if (
                row["country"] != "Brazil"
                or not (-35 <= lat <= 6 and -75 <= lon <= -30)
                or "EPE-published" not in row["coordinate_basis"]
            ):
                raise ValueError("compact snapshot has invalid EPE country/point/provenance")
        elif (
            row["country"] != "United States"
            or not (15 <= lat <= 75 and -170 <= lon <= -60)
            or "EPA LMOP-published" not in row["coordinate_basis"]
            or not row["source_status"].startswith("Operational landfill-gas energy project")
        ):
            raise ValueError("compact snapshot has invalid LMOP country/point/scope")
    lmop_total = sum(row["source"] == "us-epa-lmop" for row in source_rows)
    rows = []
    for src in source_rows:
        source = src["source"]
        if source.startswith("br-epe-"):
            subtype = source.removeprefix("br-epe-")
            process = (
                f"EPE {subtype} plant layer | source plant type: {src['plant_or_project_type']}"
            )
            status = (
                f"EPE-published source status: {src['source_status']}; not independently verified"
            )
            if src["start_date"]:
                status += f" | source start field: {src['start_date']}"
            note = "Every record in this official EPE plant layer is retained. Multiple source rows may describe operating, construction or expansion records at the same physical site; they are not merged into inferred facilities. No fermentation, digestion, upgrading, reactor or vessel design is inferred."
            sector = {
                "ethanol": "ethanol, sugar or alcohol production (EPE ethanol-layer classification)",
                "biodiesel": "biodiesel production / biofuels",
                "biomethane": "biomethane production / biofuels",
            }[subtype]
            row = {
                "stable_id": f"br-epe-{subtype}:{src['source_record_id']}",
                "facility_name": src["facility_name"],
                "country": src["country"],
                "lat": src["lat"],
                "lon": src["lon"],
                "precision": "EPE-published facility point; positional accuracy not stated and not independently verified",
                "sector": sector,
                "process_or_activity": process,
                "reactor_type_if_explicit": "",
                "status": status,
                "operator": src["operator_or_parties"],
                "capacity": src["capacity"],
                "pollutant_or_product_context": src["feedstock_or_context"],
                "source_url": EPE_LANDING,
                "source_role": "official EPE Webmap biofuel plant layer",
                "retrieved": retrieved,
                "license": "Creative Commons Attribution 4.0 International",
                "verification_notes": note,
            }
        else:
            row = {
                "stable_id": f"us-epa-lmop:{src['source_record_id']}",
                "facility_name": src["facility_name"],
                "country": src["country"],
                "lat": src["lat"],
                "lon": src["lon"],
                "precision": "EPA LMOP-published project point; EPA says coordinates are best available and may represent a landfill center or entrance; not independently verified",
                "sector": "municipal solid-waste landfill gas energy",
                "process_or_activity": f"EPA LMOP project category and explicit energy-use technology: {src['feedstock_or_context']} | {src['plant_or_project_type']}",
                "reactor_type_if_explicit": "",
                "status": f"EPA-published status: {src['source_status']}; not independently verified",
                "operator": src["operator_or_parties"],
                "capacity": src["capacity"],
                "pollutant_or_product_context": "landfill gas/methane recovery and energy use",
                "source_url": LMOP_LANDING,
                "source_role": "official EPA LMOP operational landfill-gas energy project map",
                "retrieved": retrieved,
                "license": "CC0 1.0 / U.S. EPA public-use data",
                "verification_notes": f"All {lmop_total} operational project rows in the official September 2024 LMOP map layer are retained. LMOP is voluntary and not exhaustive. The explicit LFG energy project type is preserved in process_or_activity, not mislabelled as a reactor type; landfill digestion or vessel equipment is not inferred.",
            }
        rows.append(row)
    rows.sort(key=lambda row: row["stable_id"])
    return rows


def refresh_snapshot(
    raws: dict[str, bytes],
    counts: dict[str, bytes],
    *,
    snapshot: Path,
    manifest: Path,
    retrieved: str,
) -> dict[str, int]:
    """Write isolated candidates only after all four complete source layers validate."""
    check_output(snapshot, (manifest,))
    check_output(manifest, (snapshot,))
    if set(raws) != set(SOURCES) or set(counts) != set(SOURCES):
        raise ValueError("refresh requires all four source and independent count responses")
    selected: list[dict[str, str]] = []
    records = []
    sizes = {}
    for source, (service, title) in SOURCES.items():
        rows = select_source(source, raws[source], counts[source])
        selected.extend(rows)
        sizes[source] = len(rows)
        records.append(
            {
                "source": source,
                "title": title,
                "url": query_url(service),
                "retrieved": retrieved,
                "bytes": str(len(raws[source])),
                "sha256": hashlib.sha256(raws[source]).hexdigest(),
                "raw_rows": str(len(rows)),
                "selected_rows": str(len(rows)),
            }
        )
    selected.sort(key=lambda row: (row["source"], row["source_record_id"]))
    rows_from_snapshot(selected, retrieved=retrieved)
    write_table(snapshot, SNAPSHOT_FIELDS, selected)
    write_table(manifest, MANIFEST_FIELDS, records)
    return sizes


def build(snapshot: Path, output: Path, *, retrieved: str = RETRIEVED) -> int:
    """Reproduce explicit output without rewriting the accepted snapshot or dataset."""
    check_output(output, (snapshot,))
    rows = rows_from_snapshot(read_snapshot(snapshot), retrieved=retrieved)
    write_table(output, FIELDS, rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    """Build a separate offline output or four-source refresh candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument(
        "--source-url", action="append", default=[], metavar="SOURCE=HTTPS_QUERY_URL"
    )
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        urls = {source: query_url(service) for source, (service, _) in SOURCES.items()}
        replaced: set[str] = set()
        for value in args.source_url:
            source, url = value.split("=", 1)
            if source not in SOURCES or source in replaced:
                raise ValueError("source override must name a unique known source")
            check_https(url)
            urls[source] = url
            replaced.add(source)
        inputs = (
            tuple(
                args.raw_dir / (source + suffix)
                for source in SOURCES
                for suffix in (".json", "-count.json")
            )
            if args.raw_dir
            else ()
        )
        inputs += (args.ca_file,) if args.ca_file else ()
        check_output(
            args.output, (args.snapshot, *inputs, *((args.manifest,) if args.manifest else ()))
        )
        retrieved = args.date or (date.today().isoformat() if args.refresh else RETRIEVED)
        if args.refresh:
            if args.manifest is None:
                raise ValueError("refresh requires an explicit separate manifest")
            check_output(args.snapshot, (args.output, args.manifest, *inputs))
            check_output(args.manifest, (args.snapshot, args.output, *inputs))
            raws, counts = {}, {}
            for source in SOURCES:
                raws[source] = (
                    (args.raw_dir / (source + ".json")).read_bytes()
                    if args.raw_dir
                    else download(urls[source], ca_file=args.ca_file)
                )
                counts[source] = (
                    (args.raw_dir / (source + "-count.json")).read_bytes()
                    if args.raw_dir
                    else download(count_url(urls[source]), ca_file=args.ca_file)
                )
            print(
                "refreshed",
                refresh_snapshot(
                    raws,
                    counts,
                    snapshot=args.snapshot,
                    manifest=args.manifest,
                    retrieved=retrieved,
                ),
            )
        elif args.raw_dir or args.source_url or args.manifest:
            raise ValueError("source/manifest options require --refresh")
        size = build(args.snapshot, args.output, retrieved=retrieved)
    except (OSError, UnicodeError, csv.Error, ValueError, TypeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote {size} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
