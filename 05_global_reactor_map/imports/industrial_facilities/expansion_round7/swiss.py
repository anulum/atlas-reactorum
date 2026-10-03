# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Swiss biogas source observations
"""Read every Swiss plant and catalogue from the complete publisher CSV archive."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import zipfile
from collections.abc import Callable
from datetime import date
from importlib import import_module
from pathlib import Path
from typing import cast

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .contracts import MAX_BYTES, SNAPSHOT_FIELDS, ImportRefused, check_observations, quantity

SCHEMAS = {
    "BiogasPlant.csv": "Number Name Place Operator BeginningOfOperation Web CombinedHeatAndPower UpgradingCapacity FacilityKind ValorizationType UpgradingTechnology x y".split(),
    "FacilityKindCatalogue.csv": "idFacilityKind FacilityKind_DE FacilityKind_FR FacilityKind_IT FacilityKind_EN".split(),
    "UpgradingTechnologyCatalogue.csv": "idTechnology Technology_DE Technology_FR Technology_IT Technology_EN".split(),
    "ValorizationTypeCatalogue.csv": "idValorizationType ValorizationType_DE ValorizationType_FR ValorizationType_IT ValorizationType_EN".split(),
    "Production.csv": "xtf_id Year Electricity Heat BiomethaneInjection BiomethaneDirect BiogasPlantR".split(),
}
_lv95 = cast(
    Callable[[float, float], tuple[float, float]],
    import_module(
        "05_global_reactor_map.imports.industrial_facilities.expansion_round4.build_dataset"
    ).lv95_to_wgs84,
)


def read_archive(path: Path) -> dict[str, list[dict[str, str]]]:
    """Read a complete bounded archive under all five original CSV schemas.

    Parameters
    ----------
    path : pathlib.Path
        Original publisher CSV ZIP capture.

    Returns
    -------
    dict
        All verbatim plant, catalogue and annual-production rows.

    Raises
    ------
    ImportRefused
        Archive integrity, membership, expansion or a CSV contract is invalid.
    """
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ImportRefused("Swiss archive must be a bounded regular file")
    tables: dict[str, list[dict[str, str]]] = {}
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(SCHEMAS) or set(names) != set(SCHEMAS):
                raise ImportRefused("Swiss archive differs from the complete member contract")
            if sum(member.file_size for member in archive.infolist()) > 5 * 1024 * 1024:
                raise ImportRefused("Swiss archive exceeds its expanded byte limit")
            for name, fields in SCHEMAS.items():
                text = archive.read(name).decode("latin-1")
                reader = csv.reader(io.StringIO(text), strict=True)
                if next(reader, []) != fields:
                    raise ImportRefused("Swiss CSV header differs from its source schema")
                values = list(reader)
                if not values or any(len(row) != len(fields) for row in values):
                    raise ImportRefused("Swiss CSV is empty or has a malformed row")
                tables[name] = [dict(zip(fields, row, strict=True)) for row in values]
    except (zipfile.BadZipFile, csv.Error, RuntimeError):
        raise ImportRefused("Swiss archive or CSV integrity check failed") from None
    return tables


def _catalogue(rows: list[dict[str, str]], key: str, label: str) -> dict[str, str]:
    """Join complete source catalogue identities to their verbatim English labels."""
    result = {row[key]: row[label] for row in rows}
    if len(result) != len(rows) or any(not k.strip() or not v.strip() for k, v in result.items()):
        raise ImportRefused("Swiss catalogue identity or label is missing or duplicated")
    return result


def read_swiss(path: Path, *, retrieved: str, source_date: str) -> list[dict[str, str]]:
    """Normalise all source plants without inferring their actual reactor designs.

    Parameters
    ----------
    path : pathlib.Path
        Complete original five-member CSV archive.
    retrieved : str
        Actual capture date in ISO format.
    source_date : str
        Publisher resource reference date from bound native metadata.

    Returns
    -------
    list of dict
        All plant observations under SNAPSHOT_FIELDS; raw sentinels retained.

    Raises
    ------
    ImportRefused
        Dates, identities, catalogues, quantities or annual references are invalid.
    """
    try:
        date.fromisoformat(source_date)
    except ValueError:
        raise ImportRefused("Swiss source reference date is invalid") from None
    tables = read_archive(path)
    plants = tables["BiogasPlant.csv"]
    facility = _catalogue(tables["FacilityKindCatalogue.csv"], "idFacilityKind", "FacilityKind_EN")
    valorization = _catalogue(
        tables["ValorizationTypeCatalogue.csv"], "idValorizationType", "ValorizationType_EN"
    )
    technology = _catalogue(
        tables["UpgradingTechnologyCatalogue.csv"], "idTechnology", "Technology_EN"
    )
    ids = {row["Number"] for row in plants}
    if len(ids) != len(plants):
        raise ImportRefused("Swiss plant IDs are duplicated")
    annual_ids: set[str] = set()
    annual_pairs: set[tuple[str, str]] = set()
    for annual in tables["Production.csv"]:
        identity = annual["xtf_id"]
        pair = (annual["BiogasPlantR"], annual["Year"])
        if (
            not identity.strip()
            or identity in annual_ids
            or pair in annual_pairs
            or pair[0] not in ids
        ):
            raise ImportRefused("Swiss annual production identity or plant reference is invalid")
        annual_ids.add(identity)
        annual_pairs.add(pair)
        year = quantity(annual["Year"], minimum=1900, maximum=2999)
        if not year.is_integer():
            raise ImportRefused("Swiss annual production year is not integral")
        for field in ("Electricity", "Heat", "BiomethaneInjection", "BiomethaneDirect"):
            if annual[field]:
                quantity(annual[field], minimum=0, maximum=1_000_000_000)
    observations: list[dict[str, str]] = []
    for plant in plants:
        if not all(plant[key].strip() for key in ("Number", "Name", "Place", "Operator")):
            raise ImportRefused("Swiss plant identity or required text is missing")
        year = quantity(plant["BeginningOfOperation"], minimum=1900, maximum=2999)
        if not year.is_integer():
            raise ImportRefused("Swiss beginning-of-operation year is not integral")
        if plant["FacilityKind"] not in facility or plant["ValorizationType"] not in valorization:
            raise ImportRefused("Swiss mandatory catalogue reference is unresolved")
        upgrade = plant["UpgradingTechnology"]
        if upgrade and upgrade not in technology:
            raise ImportRefused("Swiss upgrading technology reference is unresolved")
        east = quantity(plant["x"], minimum=2_480_000, maximum=2_840_000)
        north = quantity(plant["y"], minimum=1_070_000, maximum=1_300_000)
        latitude, longitude = _lv95(east, north)
        row = dict.fromkeys(SNAPSHOT_FIELDS, "")
        row.update(
            source="ch-sfoe-biogas",
            source_record_id=plant["Number"],
            source_row_id=plant["Number"],
            facility_name=plant["Name"],
            operator=plant["Operator"],
            country="Switzerland",
            locality=plant["Place"],
            lat=str(latitude),
            lon=str(longitude),
            coordinate_basis="Source LV95 plant point; swisstopo December 2016 navigation approximation, not surveying",
            source_process_class=valorization[plant["ValorizationType"]],
            source_facility_class=facility[plant["FacilityKind"]],
            source_status="Publisher reference state; current operation not independently verified",
            capacity_chp_kw=plant["CombinedHeatAndPower"],
            upgrading_capacity_m3_hour=plant["UpgradingCapacity"],
            source_date=source_date,
            source_beginning_operation=plant["BeginningOfOperation"],
            source_context="Source biogas catalogue classification; physical process and vessel design unverified",
            source_east=plant["x"],
            source_north=plant["y"],
            source_upgrading_technology=technology.get(upgrade, ""),
            retrieved=retrieved,
            license="LicenseRef-opendata-swiss-terms-by",
        )
        if "holzgas" in plant["Name"].casefold():
            row["source_note"] = (
                "Source name contains Holzgas while catalogue classifies a biogas plant; "
                "physical process is unresolved"
            )
        observations.append(row)
    check_observations(observations)
    return observations


def main() -> None:
    """Inspect the full archive with dates supplied from its acquisition receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--retrieved", required=True)
    parser.add_argument("--source-date", required=True)
    args = parser.parse_args()
    try:
        rows = read_swiss(args.archive, retrieved=args.retrieved, source_date=args.source_date)
    except (OSError, ImportRefused):
        print("SWISS CHECK FAILED: archive or source observation contract is invalid")
        raise SystemExit(1) from None
    print(
        json.dumps({"plant_observations": len(rows), "annual_production_is_not_facilities": True})
    )


if __name__ == "__main__":
    main()
