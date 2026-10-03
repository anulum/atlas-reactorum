#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/scripts/validate.py
"""Validate required fields, enums, coordinates, IDs, URLs and GeoJSON parity."""

import csv
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

REQ = "id name record_kind domain reactor_type status evidence_maturity country_code latitude longitude coordinate_precision source_url source_publisher source_role source_license source_quality_flags last_verified verification_notes".split()
ENUM = {
    "record_kind": set(
        "facility reactor_unit experimental_device project claim taxonomy_only".split()
    ),
    "domain": set("nuclear_fission plasma_fusion chemical biochemical hybrid emerging".split()),
    "status": set(
        "operational under_construction planned suspended shutdown decommissioning decommissioned cancelled historical claimed unknown".split()
    ),
    "evidence_maturity": set(
        "established demonstrated_component active_research contested null_or_critical speculative self_reported unknown".split()
    ),
}


def main() -> bool:
    """Validate the source table and GeoJSON, returning whether errors occurred."""
    p = Path("data/reactors.tsv")
    try:
        with p.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", strict=True)
            if not set(REQ).issubset(reader.fieldnames or []):
                print("Validation failed: required table columns are missing")
                return True
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Validation failed: cannot read source table: {error}")
        return True
    errors = []
    if not rows:
        errors.append("dataset is empty")
    ids = set()
    for n, r in enumerate(rows, 2):
        if None in r or any(value is None for value in r.values()):
            errors.append(f"line {n}: malformed row")
            continue
        for k in REQ:
            if not r.get(k):
                errors.append(f"line {n}: missing {k}")
        if r.get("id") in ids:
            errors.append(f"line {n}: duplicate id")
        ids.add(r.get("id"))
        for k, v in ENUM.items():
            if r.get(k) not in v:
                errors.append(f"line {n}: bad {k}")
        try:
            if not -90 <= float(r["latitude"]) <= 90 or not -180 <= float(r["longitude"]) <= 180:
                errors.append(f"line {n}: coordinate range")
        except (ValueError, TypeError, KeyError):
            # A bare except would also swallow KeyboardInterrupt and
            # SystemExit; only a malformed or absent coordinate is expected.
            errors.append(f"line {n}: invalid coordinate")
        if not re.fullmatch(r"[A-Z]{2}", r.get("country_code", "")):
            errors.append(f"line {n}: country_code")
        if not r.get("source_url", "").startswith(("http://", "https://")):
            errors.append(f"line {n}: source_url")
        verified = r.get("last_verified", "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified):
            errors.append(f"line {n}: last_verified")
        else:
            try:
                dt.date.fromisoformat(verified)
            except ValueError:
                errors.append(f"line {n}: last_verified")
    try:
        g = json.loads(Path("data/reactors.geojson").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Validation failed: cannot read GeoJSON: {error}")
        return True
    if (
        not isinstance(g, dict)
        or g.get("type") != "FeatureCollection"
        or not isinstance(g.get("features"), list)
    ):
        print("Validation failed: GeoJSON must be a FeatureCollection")
        return True
    if len(g.get("features", [])) != len(rows):
        errors.append("GeoJSON/TSV count mismatch")
    if not errors:
        expected = {r["id"]: [float(r["longitude"]), float(r["latitude"])] for r in rows}
        seen_geo: set[str] = set()
        for feature in g["features"]:
            if not isinstance(feature, dict):
                errors.append("GeoJSON feature must be an object")
                continue
            ident = feature.get("id")
            if not isinstance(ident, str) or ident not in expected:
                errors.append("GeoJSON feature has an unknown ID")
                continue
            if ident in seen_geo:
                errors.append("GeoJSON feature has a duplicate ID")
            seen_geo.add(ident)
            geometry = feature.get("geometry")
            if (
                not isinstance(geometry, dict)
                or geometry.get("type") != "Point"
                or geometry.get("coordinates") != expected[ident]
            ):
                errors.append(f"GeoJSON coordinates disagree with TSV for {ident}")
        if seen_geo != set(expected):
            errors.append("GeoJSON/TSV ID mismatch")

    def digest(p: str | Path) -> str:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    report = [
        "# Validation report",
        "",
        f"- Records: {len(rows)}",
        f"- GeoJSON features: {len(g.get('features', []))}",
        f"- Unique IDs: {len(ids)}",
        f"- Countries/areas: {len({r.get('country_code') for r in rows if r.get('country_code')})}",
        f"- Errors: {len(errors)}",
        f"- `data/reactors.tsv` SHA-256: `{digest('data/reactors.tsv')}`",
        f"- `data/reactors.geojson` SHA-256: `{digest('data/reactors.geojson')}`",
        "",
        "## Counts by domain/status",
        "",
    ]
    for (d, s), c in sorted(
        Counter((r.get("domain") or "", r.get("status") or "") for r in rows).items()
    ):
        report.append(f"- `{d}` / `{s}`: {c}")
    report += ["", "## Errors", "", *(errors or ["None."]), ""]
    Path("VALIDATION.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report[:6]))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
