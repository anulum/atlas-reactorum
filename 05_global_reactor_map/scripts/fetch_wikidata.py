#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/scripts/fetch_wikidata.py
"""Fetch a CC0, map-ready starter set from Wikidata Query Service.

This is discovery data, not an authoritative reactor register.  The query is
split by exact instance-of class to keep it reproducible and endpoint-friendly.
"""

import argparse
import csv
import datetime as dt
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import requests

CLASSES = {
    "Q134447": ("nuclear_fission", "nuclear power plant", "facility", "established"),
    "Q1438105": ("nuclear_fission", "research reactor", "experimental_device", "established"),
    "Q188589": ("plasma_fusion", "tokamak", "experimental_device", "active_research"),
    "Q1360597": ("plasma_fusion", "stellarator", "experimental_device", "active_research"),
    "Q11536219": ("plasma_fusion", "fusion reactor", "experimental_device", "active_research"),
    "Q5446866": (
        "plasma_fusion",
        "field-reversed configuration",
        "experimental_device",
        "active_research",
    ),
    "Q3966636": ("plasma_fusion", "spheromak", "experimental_device", "active_research"),
}
ENDPOINT = "https://query.wikidata.org/sparql"
UA = "reactor-research-library/1.0 (reproducible public-data research)"
FIELDS = [
    "id",
    "name",
    "aliases",
    "record_kind",
    "domain",
    "reactor_type",
    "subtypes",
    "purpose",
    "status",
    "evidence_maturity",
    "site",
    "city",
    "region",
    "country",
    "country_code",
    "latitude",
    "longitude",
    "coordinate_precision",
    "coordinate_source",
    "owner",
    "operator",
    "designer",
    "regulator",
    "fuel_or_feed",
    "coolant_or_medium",
    "moderator",
    "confinement_or_flow",
    "thermal_power_mw",
    "electric_power_mw",
    "capacity_note",
    "start_date",
    "end_date",
    "source_url",
    "source_publisher",
    "source_title",
    "source_role",
    "source_license",
    "source_quality_flags",
    "last_verified",
    "verification_notes",
]


def query(
    source: Path | None = None, endpoint: str = ENDPOINT, timeout: float = 120
) -> list[dict[str, dict[str, str]]]:
    """Read a captured response or query SPARQL, validating the binding structure."""
    values = " ".join("wd:" + q for q in CLASSES)
    q = f"""SELECT DISTINCT ?class ?item ?itemLabel ?coord ?country ?countryLabel ?countryCode ?statusLabel ?inception ?dissolved WHERE {{
      VALUES ?class {{ {values} }}
      ?item wdt:P31 ?class; wdt:P625 ?coord.
      OPTIONAL {{ ?item wdt:P17 ?country. OPTIONAL {{ ?country wdt:P297 ?countryCode. }} }}
      OPTIONAL {{ ?item wdt:P5817 ?status. }} OPTIONAL {{ ?item wdt:P571 ?inception. }} OPTIONAL {{ ?item wdt:P576 ?dissolved. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}"""
    if source is not None:
        data = json.loads(source.read_bytes())
    else:
        with requests.get(
            endpoint,
            params={"query": q, "format": "json"},
            headers={"User-Agent": UA, "Accept": "application/sparql-results+json"},
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            data = json.loads(response.content)
    if not isinstance(data, dict) or not isinstance(data.get("results"), dict):
        raise ValueError("SPARQL response must contain object results")
    bindings = data["results"].get("bindings")
    if not isinstance(bindings, list):
        raise ValueError("SPARQL bindings must be a list")
    for binding in bindings:
        if not isinstance(binding, dict) or any(
            not isinstance(node, dict) or not isinstance(node.get("value"), str)
            for node in binding.values()
        ):
            raise ValueError("SPARQL binding values must be string-valued objects")
    return bindings


def val(b: Mapping[str, Mapping[str, str]], key: str) -> str:
    """Read a binding's value, or empty when the source supplied none."""
    return b.get(key, {}).get("value", "")


def date(v: str) -> str:
    """Normalise a source date to the atlas date form."""
    return v[:10] if v else ""


def norm_status(label: str, dissolved: str) -> str:
    """Map a source status label onto the atlas status set."""
    s = " ".join(label.casefold().split())
    if dissolved and not s:
        return "shutdown"
    aliases = {
        "operational": "operational",
        "operating": "operational",
        "active": "operational",
        "in use": "operational",
        "in partial operation": "operational",
        "under construction": "under_construction",
        "building or structure under construction": "under_construction",
        "planned": "planned",
        "proposed": "planned",
        "proposed building or structure": "planned",
        "suspended": "suspended",
        "decommissioned": "decommissioned",
        "retired": "decommissioned",
        "decommissioning": "decommissioning",
        "nuclear decommissioning": "decommissioning",
        "shutdown": "shutdown",
        "closed": "shutdown",
        "permanently closed": "shutdown",
        "cancelled": "cancelled",
        "canceled": "cancelled",
    }
    return aliases.get(s, "unknown")


def main() -> None:
    """Run this script's build and validation steps."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/reactors.tsv")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    source = ap.add_mutually_exclusive_group()
    source.add_argument("--source", type=Path)
    source.add_argument("--endpoint", default=ENDPOINT)
    ap.add_argument("--timeout", type=float, default=120)
    a = ap.parse_args()
    if not math.isfinite(a.timeout) or a.timeout <= 0:
        ap.error("timeout must be positive and finite")
    try:
        bindings = query(a.source, a.endpoint, a.timeout)
    except (OSError, ValueError, requests.RequestException) as error:
        ap.exit(1, f"cannot read SPARQL source: {error}\n")
    records: dict[str, dict[str, Any]] = {}
    for b in bindings:
        qid = val(b, "class").rsplit("/", 1)[-1]
        if qid not in CLASSES:
            ap.exit(1, f"unexpected SPARQL reactor class: {qid}\n")
        meta = CLASSES[qid]
        item = val(b, "item")
        wid = item.rsplit("/", 1)[-1].lower()
        m = re.fullmatch(r"Point\(([-0-9.]+) ([-0-9.]+)\)", val(b, "coord"))
        cc = val(b, "countryCode").upper()
        if not m or not re.fullmatch(r"[A-Z]{2}", cc):
            continue
        try:
            longitude, latitude = float(m.group(1)), float(m.group(2))
        except ValueError:
            continue
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            continue
        domain, rtype, kind, maturity = meta
        dissolved = date(val(b, "dissolved"))
        name = val(b, "itemLabel")
        rec = {k: "" for k in FIELDS}
        rec.update(
            {
                "id": "wikidata-" + wid,
                "name": name,
                "record_kind": kind,
                "domain": domain,
                "reactor_type": rtype,
                "status": norm_status(val(b, "statusLabel"), dissolved),
                "evidence_maturity": maturity,
                "country": val(b, "countryLabel"),
                "country_code": cc,
                "latitude": m.group(2),
                "longitude": m.group(1),
                "coordinate_precision": "unknown",
                "coordinate_source": item,
                "start_date": date(val(b, "inception")),
                "end_date": dissolved,
                "source_url": item,
                "source_publisher": "Wikidata contributors",
                "source_title": "Wikidata entity " + wid.upper(),
                "source_role": "registry",
                "source_license": "CC0 1.0",
                "source_quality_flags": "community_edited;not_authoritative;exact_instance_class_only;status_may_be_missing;coordinate_precision_unverified",
                "last_verified": a.date,
                "verification_notes": "Automated discovery record; verify status and coordinates against authoritative registry, regulator, or operator before consequential use.",
            }
        )
        old = records.get(rec["id"])
        if old:
            if rtype not in old["reactor_type"].split("|"):
                old["reactor_type"] += "|" + rtype
        else:
            records[rec["id"]] = rec
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(
            sorted(records.values(), key=lambda x: (x["domain"], x["country_code"], x["name"]))
        )
    print(f"wrote {len(records)} records to {out}")


if __name__ == "__main__":
    main()
