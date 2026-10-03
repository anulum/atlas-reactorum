#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/scripts/export_geojson.py
"""Convert normalized reactors.tsv into schema-shaped GeoJSON features."""

import argparse
import csv
import json
import math
from pathlib import Path


def null(v: str) -> str | None:
    """Return None when the value is empty, so absence stays absence."""
    return v or None


def main() -> None:
    """Read the tab-separated source into rows."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/reactors.tsv")
    ap.add_argument("--output", default="data/reactors.geojson")
    a = ap.parse_args()
    features = []
    property_fields = (
        "id",
        "name",
        "record_kind",
        "domain",
        "reactor_type",
        "status",
        "evidence_maturity",
        "country",
        "country_code",
        "coordinate_precision",
        "source_url",
        "source_publisher",
        "source_role",
        "source_license",
        "source_quality_flags",
        "last_verified",
        "verification_notes",
    )
    seen: set[str] = set()
    try:
        with open(a.input, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", strict=True)
            required = {*property_fields, "latitude", "longitude", "start_date", "end_date"}
            if not required.issubset(reader.fieldnames or []):
                ap.exit(1, "source table is missing required columns\n")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        ap.exit(1, f"cannot read source table: {error}\n")
    if not rows:
        ap.exit(1, "source table is empty\n")
    for r in rows:
        if None in r or any(value is None for value in r.values()):
            ap.exit(1, "source table has a malformed row\n")
        if not r["id"] or r["id"] in seen:
            ap.exit(1, "source IDs must be non-empty and unique\n")
        seen.add(r["id"])
        try:
            lon, lat = float(r["longitude"]), float(r["latitude"])
        except ValueError as error:
            ap.exit(1, f"source coordinates must be numeric: {error}\n")
        if not (
            math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90
        ):
            ap.exit(1, "source coordinates must be finite and within geographic bounds\n")
        props = {k: r[k] for k in property_fields}
        props["start_date"] = null(r["start_date"])
        props["end_date"] = null(r["end_date"])
        features.append(
            {
                "type": "Feature",
                "id": r["id"],
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props,
            }
        )
    out = Path(a.output)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        ap.exit(1, f"cannot write GeoJSON: {error}\n")
    print(f"wrote {len(features)} features to {out}")


if __name__ == "__main__":
    main()
