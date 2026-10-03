#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/build_industrial_facilities.py
"""Build a licensed industrial chemical/biochemical facility discovery layer.

The script deliberately emits facility/site observations, not inferred reactor
vessels.  A reactor type is populated only for EPA AgSTAR records because that
source explicitly publishes a digester type.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import ssl
import tempfile
import urllib.parse
import urllib.request
from datetime import date
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Any

ROOT = Path(__file__).resolve().parent
RETRIEVED = "2026-09-27"
USER_AGENT = "reactor-atlas-industrial-discovery/1.0"
EEA_LAYER = "https://air.discomap.eea.europa.eu/arcgis/rest/services/Air/IED_SiteMap/MapServer/0"
EPA_BASE = "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services"
EPA_LANDING = "https://www.epa.gov/agstar/livestock-anaerobic-digester-database"
EPA_LAYERS = ("Mixed", "Cattle", "Poultry", "Swine", "Dairy")

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

COUNTRIES = {
    "AL": "Albania",
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CH": "Switzerland",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DK": "Denmark",
    "EE": "Estonia",
    "EL": "Greece",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GR": "Greece",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IS": "Iceland",
    "IT": "Italy",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "ME": "Montenegro",
    "MK": "North Macedonia",
    "MT": "Malta",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "RS": "Serbia",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "TR": "Turkiye",
    "UA": "Ukraine",
    "XK": "Kosovo",
}


def text(value: object) -> str:
    """Coerce a source value to trimmed text."""
    if value is None:
        return ""
    return str(value).strip()


def number(value: object) -> str:
    """Format a numeric source value as text, preserving its precision."""
    if value in (None, ""):
        return ""
    number_value = float(str(value))
    if not math.isfinite(number_value):
        raise ValueError("numeric observation must be finite")
    return str(int(number_value)) if number_value.is_integer() else format(number_value, ".12g")


def reported_quantity(value: object) -> str:
    """Preserve source ranges/lists while normalising simple numeric values."""
    raw = text(value)
    if not raw:
        return ""
    try:
        float(raw.replace(",", ""))
    except ValueError:
        return raw
    return number(raw.replace(",", ""))


def eea_rows(items: list[dict[str, Any]], *, retrieved: str) -> list[dict[str, str]]:
    """Build facility rows from the EEA industrial emissions registry."""
    source = (
        "https://www.eea.europa.eu/en/datahub/datahubitem-view/9405f714-8015-4b5b-a63c-280b82861b3d"
    )
    found: dict[str, dict[str, str]] = {}
    for item in items:
        source_id = text(item.get("InspireSiteId"))
        if not source_id:
            raise RuntimeError(f"EEA OBJECTID {item.get('OBJECTID')} has no InspireSiteId")
        stable_id = "eea-ied-site:" + re.sub(r"[^a-z0-9:._-]+", "_", source_id.lower()).strip("_")
        if stable_id in found:
            raise ValueError("EEA site IDs collide after normalisation")
        if not stable_id.removeprefix("eea-ied-site:"):
            raise ValueError("EEA site ID normalises to an empty identity")
        country_code = text(item.get("countryCode"))
        found[stable_id] = {
            "stable_id": stable_id,
            "facility_name": text(item.get("siteName")) or text(item.get("facilityNames")),
            "country": COUNTRIES.get(country_code, country_code),
            "lat": number(item.get("y_4258")),
            "lon": number(item.get("x_4258")),
            "precision": "reported industrial-site point; survey accuracy not independently verified",
            "sector": text(item.get("eprtr_sectors")),
            "process_or_activity": " | ".join(
                filter(None, [text(item.get("eea_activities")), text(item.get("activity_details"))])
            ),
            "reactor_type_if_explicit": "",
            "status": "reported for 2024; operating status not asserted",
            "operator": text(item.get("facilityNames")) or "not provided",
            "capacity": "",
            "pollutant_or_product_context": text(item.get("pollutants")),
            "source_url": source,
            "source_role": "official EEA industrial-site registry and activity classification",
            "retrieved": retrieved,
            "license": "CC BY 4.0 (EEA, unless item-specific terms state otherwise)",
            "verification_notes": (
                f"Selected systematically from EEA IED Site Map where reporting year=2024 and sector is "
                f"{text(item.get('eprtr_sectors'))}. This row identifies a reported industrial site; it does "
                "not establish the number, design, or presence of individual reactor vessels."
            ),
        }
    return list(found.values())


def agstar_rows(layers: dict[str, list[dict[str, Any]]], *, retrieved: str) -> list[dict[str, str]]:
    """Build facility rows from the AgSTAR anaerobic digester register."""
    rows: list[dict[str, str]] = []
    for layer_name in EPA_LAYERS:
        for item in layers[layer_name]:
            fingerprint = "\x1f".join(
                [
                    text(item.get("Project_Na")),
                    text(item.get("City")),
                    text(item.get("State")),
                ]
            ).casefold()
            digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
            capacities = []
            for label, key, unit in (
                ("population feeding digester", "Population", "animals"),
                ("estimated biogas", "Biogas_Gen", "ft3/day"),
                ("electricity generated", "Electricit", "kWh/year"),
            ):
                value = reported_quantity(item.get(key))
                if value:
                    capacities.append(f"{label}: {value} {unit}")
            context = [f"animal/feedstock class: {text(item.get('Animal_T_1')) or layer_name}"]
            if text(item.get("Co_Digesti")):
                context.append("co-digestion: " + text(item.get("Co_Digesti")))
            if text(item.get("Biogas_End")):
                context.append("biogas end use: " + text(item.get("Biogas_End")))
            if reported_quantity(item.get("Total_Emis")):
                context.append(
                    "estimated emission reductions: "
                    + reported_quantity(item.get("Total_Emis"))
                    + " MTCO2e/year"
                )
            rows.append(
                {
                    "stable_id": f"epa-agstar:{digest}",
                    "facility_name": text(item.get("Project_Na")),
                    "country": "United States",
                    "lat": number(item.get("LATITUDE__")),
                    "lon": number(item.get("LONGITUDE_")),
                    "precision": "EPA-published project map point; survey accuracy not independently verified",
                    "sector": "agricultural biogas / livestock manure management",
                    "process_or_activity": text(item.get("Project_Ty")) or "anaerobic digestion",
                    "reactor_type_if_explicit": text(item.get("Digester_T")),
                    "status": "operational",
                    "operator": "not provided by mapped layer",
                    "capacity": " | ".join(capacities),
                    "pollutant_or_product_context": " | ".join(context),
                    "source_url": EPA_LANDING,
                    "source_role": "official EPA AgSTAR operational-project map; explicit digester type",
                    "retrieved": retrieved,
                    "license": "U.S. Public Domain (EPA-produced data; 17 U.S.C. 105)",
                    "verification_notes": (
                        f"Imported from the EPA AgSTAR {layer_name} operational map layer, OBJECTID "
                        f"{item.get('OBJECTID')}; project-map coordinates and source labels are preserved. "
                        "AgSTAR says its voluntary-source database is not exhaustive and accuracy is not guaranteed."
                    ),
                }
            )
    return rows


EEA_FIELDS = "OBJECTID,x_4258,y_4258,pollutants,eprtr_sectors,eea_activities,activity_details,Site_reporting_year,siteName,InspireSiteId,countryCode,facilityNames"
EPA_FIELDS = "OBJECTID,Project_Na,Project_Ty,City,State,Digester_T,Year_Opera,Animal_T_1,Population,Co_Digesti,Biogas_Gen,Electricit,Biogas_End,Total_Emis,LATITUDE__,LONGITUDE_"
EEA_WHERE = "Site_reporting_year=2024 AND eprtr_sectors IN ('CHEMICALS','FOOD AND BEVERAGE')"
SOURCES = {"EEA": EEA_LAYER, **{name: f"{EPA_BASE}/{name}/FeatureServer/0" for name in EPA_LAYERS}}
LIBRARY = ROOT.parents[2]


def check_https(url: str) -> None:
    """Require anonymous HTTPS for source requests and every redirect."""
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.port == 0
        or parsed.fragment
        or any(c.isspace() for c in url)
    ):
        raise ValueError("source URL must be valid anonymous HTTPS")


class SourceRedirect(urllib.request.HTTPRedirectHandler):
    """Validate actual server redirect destinations before following them."""

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
        """Refuse downgraded or credential-bearing redirect destinations."""
        check_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request_json(
    url: str,
    params: dict[str, str],
    *,
    ca_file: Path | None = None,
    timeout: float = 30,
    max_bytes: int = 16 * 1024 * 1024,
) -> dict[str, Any]:
    """Read one trusted, bounded ArcGIS response without writing any output."""
    check_https(url)
    if not math.isfinite(timeout) or timeout <= 0 or max_bytes <= 0:
        raise ValueError("request limits must be finite and positive")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context), SourceRedirect()
    )
    full = url + ("&" if urllib.parse.urlsplit(url).query else "?") + urllib.parse.urlencode(params)
    request = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    with opener.open(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"ArcGIS returned HTTP {response.status}")
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError("ArcGIS response exceeds its byte limit")
    payload = json.loads(body)
    if not isinstance(payload, dict) or "error" in payload:
        raise ValueError("ArcGIS response must be an object without an API error")
    return payload


def query_all(
    url: str,
    where: str,
    out_fields: str,
    page_size: int = 1000,
    *,
    ca_file: Path | None = None,
    timeout: float = 30,
    max_bytes: int = 16 * 1024 * 1024,
    max_pages: int = 100,
) -> dict[str, Any]:
    """Acquire ordered pages and require their independent service count."""
    if page_size <= 0 or max_pages <= 0:
        raise ValueError("pagination limits must be positive")
    count = request_json(
        url + "/query",
        {"f": "json", "where": where, "returnCountOnly": "true"},
        ca_file=ca_file,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    expected = count.get("count")
    if type(expected) is not int or expected < 0:
        raise ValueError("service count must be a nonnegative integer")
    records: list[dict[str, Any]] = []
    for _page in range(max_pages):
        if len(records) == expected:
            return {"count": expected, "records": records}
        payload = request_json(
            url + "/query",
            {
                "f": "json",
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "false",
                "orderByFields": "OBJECTID ASC",
                "resultOffset": str(len(records)),
                "resultRecordCount": str(page_size),
            },
            ca_file=ca_file,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        features = payload.get("features")
        if (
            not isinstance(features, list)
            or not features
            or len(features) > page_size
            or (
                "exceededTransferLimit" in payload
                and type(payload["exceededTransferLimit"]) is not bool
            )
        ):
            raise ValueError("service page must contain a bounded nonempty feature list")
        for feature in features:
            if not isinstance(feature, dict) or not isinstance(feature.get("attributes"), dict):
                raise ValueError("service feature must have its attribute object")
            records.append(feature["attributes"])
        if len(records) > expected:
            raise ValueError("service pages exceed their independent count")
    if len(records) != expected:
        raise ValueError("service acquisition exceeds its page limit")
    return {"count": expected, "records": records}


def validate_sources(loaded: object) -> dict[str, list[dict[str, Any]]]:
    """Check full six-source envelopes, source identities and preserved scalars."""
    if (
        not isinstance(loaded, dict)
        or loaded.get("schema_version") != "1.0.0"
        or not isinstance(loaded.get("sources"), dict)
        or set(loaded["sources"]) != set(SOURCES)
    ):
        raise ValueError("snapshot requires its exact versioned six-source envelope")
    captured = loaded.get("captured_at")
    if not isinstance(captured, str) or date.fromisoformat(captured).isoformat() != captured:
        raise ValueError("snapshot requires an exact ISO capture date")
    result: dict[str, list[dict[str, Any]]] = {}
    for source, content in loaded["sources"].items():
        if (
            not isinstance(content, dict)
            or type(content.get("count")) is not int
            or not isinstance(content.get("records"), list)
            or content["count"] != len(content["records"])
        ):
            raise ValueError("source count must match every saved record")
        fields = (EEA_FIELDS if source == "EEA" else EPA_FIELDS).split(",")
        seen: set[int] = set()
        for record in content["records"]:
            if (
                not isinstance(record, dict)
                or not set(fields).issubset(record)
                or any(
                    value is not None and type(value) not in (str, int, float)
                    for value in record.values()
                )
            ):
                raise ValueError("source record must retain the required scalar fields")
            identifier = record["OBJECTID"]
            if type(identifier) is not int or identifier <= 0 or identifier in seen:
                raise ValueError("source OBJECTID must be a positive unique integer")
            seen.add(identifier)
            lat, lon = (
                (record["y_4258"], record["x_4258"])
                if source == "EEA"
                else (record["LATITUDE__"], record["LONGITUDE_"])
            )
            if (
                not number(lat)
                or not number(lon)
                or not (-90 <= float(str(lat)) <= 90)
                or not (-180 <= float(str(lon)) <= 180)
            ):
                raise ValueError("source requires finite in-range reported coordinates")
            if source == "EEA":
                if (
                    record["Site_reporting_year"] != 2024
                    or record["eprtr_sectors"] not in {"CHEMICALS", "FOOD AND BEVERAGE"}
                    or not text(record["countryCode"])
                    or not (text(record["siteName"]) or text(record["facilityNames"]))
                ):
                    raise ValueError(
                        "EEA source must retain its selected year/sector and site identity"
                    )
            elif not text(record["Project_Na"]):
                raise ValueError("AgSTAR source must retain its project name")
        result[source] = content["records"]
    return result


def render(loaded: object, *, retrieved: str) -> bytes:
    """Prepare the complete sorted facility table before any destination changes."""
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO date")
    sources = validate_sources(loaded)
    rows = eea_rows(sources["EEA"], retrieved=retrieved) + agstar_rows(sources, retrieved=retrieved)
    if not rows or len({row["stable_id"] for row in rows}) != len(rows):
        raise ValueError("facility rows must be nonempty with unique stable identities")
    rows.sort(key=lambda row: row["stable_id"])
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def check_output(path: Path, inputs: tuple[Path, ...] = ()) -> None:
    """Protect all accepted Atlas paths and resolved caller-supplied inputs."""
    target = path.resolve()
    if target.is_relative_to(LIBRARY) or target in {value.resolve() for value in inputs}:
        raise ValueError("output must be separate from accepted Atlas files and inputs")


def atomic_write(path: Path, body: bytes) -> None:
    """Replace one explicit candidate and clean write/close/replace failures."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(body)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build(loaded: object, output: Path, *, retrieved: str, inputs: tuple[Path, ...] = ()) -> None:
    """Validate every source and write only an explicit isolated candidate."""
    check_output(output, inputs)
    atomic_write(output, render(loaded, retrieved=retrieved))


def main(argv: list[str] | None = None) -> int:
    """Build an isolated offline candidate or capture six real service sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--snapshot-out", type=Path)
    parser.add_argument("--eea-url", default=EEA_LAYER)
    parser.add_argument("--epa-base", default=EPA_BASE)
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        inputs = tuple(p for p in (args.source, args.ca_file) if p is not None)
        check_output(args.output, (*inputs, *((args.snapshot_out,) if args.snapshot_out else ())))
        if args.refresh:
            if args.source or args.snapshot_out is None:
                raise ValueError(
                    "refresh requires a separate snapshot output and no offline source"
                )
            check_output(args.snapshot_out, (*inputs, args.output))
            loaded: dict[str, Any] = {
                "schema_version": "1.0.0",
                "captured_at": date.today().isoformat(),
                "sources": {},
            }
            for name in SOURCES:
                url = args.eea_url if name == "EEA" else f"{args.epa_base}/{name}/FeatureServer/0"
                loaded["sources"][name] = query_all(
                    url,
                    EEA_WHERE if name == "EEA" else "1=1",
                    EEA_FIELDS if name == "EEA" else EPA_FIELDS,
                    ca_file=args.ca_file,
                )
            body = render(loaded, retrieved=args.date or loaded["captured_at"])
            snapshot = (json.dumps(loaded, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            atomic_write(args.snapshot_out, snapshot)
            atomic_write(args.output, body)
        else:
            if (
                args.source is None
                or args.snapshot_out
                or args.ca_file
                or args.eea_url != EEA_LAYER
                or args.epa_base != EPA_BASE
            ):
                raise ValueError("offline build requires a source; network options require refresh")
            loaded = json.loads(args.source.read_bytes())
            # Validate before accessing the date so malformed envelopes fail consistently.
            validate_sources(loaded)
            build(loaded, args.output, retrieved=args.date or loaded["captured_at"], inputs=inputs)
    except (OSError, UnicodeError, ValueError, TypeError, csv.Error, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote isolated industrial facility candidate to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
