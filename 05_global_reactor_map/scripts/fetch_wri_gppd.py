#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/scripts/fetch_wri_gppd.py
"""Fetch the CC BY 4.0 WRI GPPD snapshot and export its nuclear subset."""

import argparse
import csv
import datetime as dt
import io
import math
from pathlib import Path

import requests
from fetch_wikidata import FIELDS, UA

COMMIT = "7a91cfbb2a4e272597acbc00506d61fc1ec73b3d"
URL = f"https://raw.githubusercontent.com/wri/global-power-plant-database/{COMMIT}/output_database/global_power_plant_database.csv"
ALPHA3_TO_ALPHA2 = {
    "ARG": "AR",
    "ARM": "AM",
    "BEL": "BE",
    "BGR": "BG",
    "BRA": "BR",
    "CAN": "CA",
    "CHE": "CH",
    "CHN": "CN",
    "CZE": "CZ",
    "DEU": "DE",
    "ESP": "ES",
    "FIN": "FI",
    "FRA": "FR",
    "GBR": "GB",
    "HUN": "HU",
    "IND": "IN",
    "IRN": "IR",
    "JPN": "JP",
    "KOR": "KR",
    "MEX": "MX",
    "NLD": "NL",
    "PAK": "PK",
    "ROU": "RO",
    "RUS": "RU",
    "SVK": "SK",
    "SVN": "SI",
    "SWE": "SE",
    "TWN": "TW",
    "UKR": "UA",
    "USA": "US",
    "ZAF": "ZA",
}


def main() -> None:
    """Read the tab-separated source into rows."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/reactors.tsv")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    source = ap.add_mutually_exclusive_group()
    source.add_argument("--source", type=Path)
    source.add_argument("--source-url", default=URL)
    ap.add_argument("--timeout", type=float, default=120)
    a = ap.parse_args()
    if not math.isfinite(a.timeout) or a.timeout <= 0:
        ap.error("timeout must be positive and finite")
    try:
        if a.source:
            payload = a.source.read_bytes()
        else:
            with requests.get(
                a.source_url, headers={"User-Agent": UA}, timeout=a.timeout
            ) as response:
                response.raise_for_status()
                payload = response.content
        text = payload.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), strict=True)
        required = {
            "primary_fuel",
            "country",
            "country_long",
            "gppd_idnr",
            "name",
            "latitude",
            "longitude",
        }
        if not required.issubset(reader.fieldnames or []):
            ap.exit(1, "source is missing required GPPD columns\n")
        rows = list(reader)
    except (OSError, UnicodeError, csv.Error, requests.RequestException) as error:
        ap.exit(1, f"cannot read GPPD source: {error}\n")
    records = []
    ids: set[str] = set()
    for x in rows:
        if None in x or any(value is None for value in x.values()):
            ap.exit(1, "GPPD source has a malformed row\n")
        if x.get("primary_fuel") != "Nuclear":
            continue
        if not x["gppd_idnr"] or x["gppd_idnr"].casefold() in ids:
            ap.exit(1, "GPPD nuclear IDs must be non-empty and unique\n")
        ids.add(x["gppd_idnr"].casefold())
        r = {k: "" for k in FIELDS}
        year = x.get("commissioning_year", "")
        year = (year[:4] + "-01-01") if year else ""
        cc = ALPHA3_TO_ALPHA2.get(x["country"])
        if not cc:
            ap.exit(1, f"unmapped ISO alpha-3 code {x['country']}\n")
        r.update(
            {
                "id": "wri-gppd-" + x["gppd_idnr"].lower(),
                "name": x["name"],
                "record_kind": "facility",
                "domain": "nuclear_fission",
                "reactor_type": "nuclear power plant (type not supplied)",
                "purpose": "electricity generation",
                "status": "unknown",
                "evidence_maturity": "established",
                "country": x["country_long"],
                "country_code": cc,
                "latitude": x["latitude"],
                "longitude": x["longitude"],
                "coordinate_precision": "unknown",
                "coordinate_source": URL,
                "owner": x.get("owner", "") or "",
                "electric_power_mw": x.get("capacity_mw", "") or "",
                "capacity_note": "Plant-level aggregate capacity in WRI GPPD; not reactor-unit capacity.",
                "start_date": year,
                "source_url": x.get("url") or URL,
                "source_publisher": "World Resources Institute",
                "source_title": "Global Power Plant Database (repository snapshot)",
                "source_role": "registry",
                "source_license": "CC BY 4.0",
                "source_quality_flags": "plant_level_not_unit;status_not_supplied;historic_shutdown_not_covered;coordinate_precision_unverified;source_may_be_stale",
                "last_verified": a.date,
                "verification_notes": "Open plant-level discovery record. Verify units, current status, dates and location against PRIS and the national regulator.",
            }
        )
        records.append(r)
    if not records:
        ap.exit(1, "GPPD source contains no nuclear plants\n")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(records, key=lambda r: (r["country_code"], r["name"])))
    print(f"wrote {len(records)} nuclear plants to {out} from pinned commit {COMMIT}")


if __name__ == "__main__":
    main()
