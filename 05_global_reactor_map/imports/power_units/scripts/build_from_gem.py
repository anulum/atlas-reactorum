#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/power_units/scripts/build_from_gem.py
"""Build the power-reactor unit discovery table from GEM's dated GNPT map export.

The map export is intentionally used instead of IAEA PRIS.  It is a public,
unit-level GEM publication covered by GEM's CC BY 4.0 notice.  Fields absent
from the export remain empty; in particular its generic nameplate-capacity
field is not guessed to be net or gross electrical capacity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib

import requests

SOURCE_URL = (
    "https://publicgemdata.nyc3.cdn.digitaloceanspaces.com/"
    "Current_maps/gnpt/gnpt_map_2026-08.geojson"
)
SOURCE_SHA256 = "d85e489c2eed4cc67c9c2b2dec8548b00d0d591ac693cd56fd3388616c1c7c1f"
TRACKER_URL = "https://globalenergymonitor.org/projects/global-nuclear-power-tracker/"
LICENSE_URL = "https://globalenergymonitor.org/creative-commons-license/"
FIELDS = [
    "stable_id",
    "unit_name",
    "plant_name",
    "country",
    "lat",
    "lon",
    "precision",
    "reactor_type",
    "model",
    "status",
    "nameplate_mw",
    "net_mwe",
    "gross_mwe",
    "thermal_mw",
    "operator",
    "owner",
    "construction_start",
    "first_criticality",
    "grid_connection",
    "commercial_operation",
    "permanent_shutdown",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]


def text(value: object) -> str:
    """Coerce a source value to trimmed text."""
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value.lower() == "unknown" else value


def number(value: object) -> str:
    """Format a numeric source value as text, preserving its precision."""
    if value in (None, ""):
        return ""
    numeric = float(str(value))
    if not math.isfinite(numeric):
        raise ValueError("source number must be finite")
    return format(numeric, ".10g")


def main() -> None:
    """Fetch the remote resource and return its payload."""
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--source", type=pathlib.Path)
    source.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--date", default="2026-09-26")
    parser.add_argument("--allow-changed-source", action="store_true")
    args = parser.parse_args()

    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be positive and finite")
    try:
        if args.source:
            payload = args.source.read_bytes()
        else:
            with requests.get(
                args.source_url,
                headers={"User-Agent": "reactor-atlas-builder/1.0"},
                timeout=args.timeout,
            ) as response:
                response.raise_for_status()
                payload = response.content
    except (OSError, requests.RequestException) as error:
        parser.exit(1, f"cannot read source: {error}\n")

    digest = hashlib.sha256(payload).hexdigest()
    if digest != SOURCE_SHA256 and not args.allow_changed_source:
        raise SystemExit(
            f"source SHA-256 changed: {digest}; expected {SOURCE_SHA256}. "
            "Review the new source before rebuilding, or use --allow-changed-source explicitly."
        )
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeError) as error:
        parser.exit(1, f"invalid source JSON: {error}\n")
    if (
        not isinstance(data, dict)
        or data.get("type") != "FeatureCollection"
        or not isinstance(data.get("features"), list)
    ):
        parser.exit(1, "source must be a GeoJSON FeatureCollection\n")
    rows = []
    for feature in data.get("features", []):
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            parser.exit(1, "GNPT feature must have object properties\n")
        p = feature.get("properties") or {}
        # GNPT 2026 added two explicitly fusion-labelled proposals.  They are
        # outside this fission power-reactor unit layer and are not silently
        # mixed into it.  Unknown reactor types remain included.
        if text(p.get("reactor-type")).lower() == "fusion":
            continue
        unit_id = text(p.get("unit-id"))
        if not unit_id:
            raise SystemExit("GNPT feature lacks unit-id")
        source_capacity = p.get("capacity")
        try:
            capacity, latitude, longitude = (
                number(value) for value in (source_capacity, p.get("Latitude"), p.get("Longitude"))
            )
        except (ValueError, OverflowError) as error:
            parser.exit(1, f"invalid source number for {unit_id}: {error}\n")
        capacity_note = (
            f"GNPT publishes nameplate capacity {capacity} MW, but the map export does not "
            "identify it as net or gross; net_mwe and gross_mwe are therefore blank. "
            if source_capacity not in (None, "")
            else "GNPT map export has no capacity value for this unit. "
        )
        project_url = text(p.get("url"))
        source_urls = "|".join(x for x in (SOURCE_URL, project_url) if x)
        source_roles = "|".join(
            ("unit_tracker_map_export", "project_evidence_page")
            if project_url
            else ("unit_tracker_map_export",)
        )
        rows.append(
            {
                "stable_id": f"gem-gnpt:{unit_id.lower()}",
                "unit_name": text(p.get("unit-name")),
                "plant_name": text(p.get("name")),
                "country": text(p.get("country-area1")),
                "lat": latitude,
                "lon": longitude,
                "precision": text(p.get("location-accuracy")) or "unknown",
                "reactor_type": text(p.get("reactor-type")),
                "model": text(p.get("model")),
                "status": text(p.get("status")) or "unknown",
                "nameplate_mw": capacity,
                "net_mwe": "",
                "gross_mwe": "",
                "thermal_mw": "",
                "operator": text(p.get("operator")),
                "owner": text(p.get("owner")),
                "construction_start": "",
                "first_criticality": "",
                "grid_connection": "",
                "commercial_operation": "",
                "permanent_shutdown": "",
                "source_url": source_urls,
                "source_role": source_roles,
                "retrieved": args.date,
                "license": "CC BY 4.0 (Global Energy Monitor GNPT)",
                "verification_notes": (
                    "Unit-level GEM GNPT August 2026 discovery record; plant_name is the parent project/site name and "
                    "unit_name is GEM's unit designator. "
                    + capacity_note
                    + "Dates and thermal power are absent from this map export and remain blank. Confirm consequential "
                    "facts with the national regulator or operator. Adapted by filtering two explicitly fusion-labelled "
                    "proposals and mapping source fields; no IAEA PRIS data were copied."
                ),
            }
        )

    if not rows:
        parser.exit(1, "source contains no fission or unknown-type units\n")
    rows.sort(key=lambda r: (r["country"], r["plant_name"], r["unit_name"], r["stable_id"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} fission/unknown-type power-reactor unit records to {args.out}")
    print(f"source sha256 {digest}")


if __name__ == "__main__":
    main()
