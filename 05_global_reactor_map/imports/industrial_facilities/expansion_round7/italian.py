# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Italian bioenergy source observations
"""Verify complete ArcGIS count/ID/page captures before applying the biogas selector."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .contracts import (
    SNAPSHOT_FIELDS,
    ImportRefused,
    check_observations,
    object_fields,
    object_rows,
    quantity,
    read_json,
)

STRING_FIELDS = (
    "TIPO COD_OE IMPIANTO GESTORE INDIRIZZO COMUNE LOCALITA PROVINCIA SIGLA COD_COM "
    "TIPO_DITTA TIPO_COMB STATO COGENERAZ TELERISCAL TIPO_AUTOR FONTE AGG_DATI NOTE NOTE_BIOM"
).split()
INTEGER_FIELDS = "OBJECTID ID_GSE NUM_IMP X_E32 Y_E32".split()
DOUBLE_FIELDS = "P_MW_EL P_MW_T LONG_WGS84 LAT_WGS84".split()
NATIVE_FIELDS = set(STRING_FIELDS + INTEGER_FIELDS + DOUBLE_FIELDS)
TYPE_FIELDS = {
    "OBJECTID": "esriFieldTypeOID",
    "NUM_IMP": "esriFieldTypeSmallInteger",
    "ID_GSE": "esriFieldTypeInteger",
    "X_E32": "esriFieldTypeInteger",
    "Y_E32": "esriFieldTypeInteger",
}
UNIT_ALIASES = {
    "P_MW_EL": "POTENZA ELETTRICA (MW)",
    "P_MW_T": "POTENZA TERMICA (MW)",
    "NUM_IMP": "NUMERO SEZIONI PRODUTTIVE",
}


def check_layer(path: Path) -> None:
    """Require the publisher point layer's full native schema and unit aliases.

    Parameters
    ----------
    path : pathlib.Path
        Original layer metadata capture.

    Raises
    ------
    ImportRefused
        Layer identity, geometry, fields, types or published units differ.
    """
    layer = read_json(path)
    if (
        type(layer.get("id")) is not int
        or layer.get("id") != 0
        or layer.get("name") != "Impianti a Bioenergie"
        or layer.get("geometryType") != "esriGeometryPoint"
    ):
        raise ImportRefused("Italian source layer identity or geometry differs")
    fields = object_rows(layer.get("fields"))
    if any(not isinstance(field.get("name"), str) for field in fields):
        raise ImportRefused("Italian layer field name is not text")
    indexed = {field.get("name"): field for field in fields}
    if len(indexed) != len(fields) or set(indexed) != NATIVE_FIELDS | {"SHAPE"}:
        raise ImportRefused("Italian layer field contract differs")
    for name in NATIVE_FIELDS:
        expected = (
            "esriFieldTypeString"
            if name in STRING_FIELDS
            else "esriFieldTypeDouble"
            if name in DOUBLE_FIELDS
            else TYPE_FIELDS[name]
        )
        if indexed[name].get("type") != expected:
            raise ImportRefused("Italian layer field type differs")
    for name, alias in UNIT_ALIASES.items():
        if indexed[name].get("alias") != alias:
            raise ImportRefused("Italian layer capacity or section unit differs")


def read_italian(
    layer: Path, count: Path, ids: Path, pages: list[Path], *, retrieved: str
) -> list[dict[str, str]]:
    """Verify every native row and the complete ID set, then select biogas fuel.

    Parameters
    ----------
    layer, count, ids : pathlib.Path
        Independent native layer, whole-source count and whole-source ID captures.
    pages : list of pathlib.Path
        Complete ordered feature pages with outSR 4326, including the final page.
    retrieved : str
        Actual capture date, distinct from the source row's update text.

    Returns
    -------
    list of dict
        All fuel-selected source observations, including every original note.

    Raises
    ------
    ImportRefused
        Pages are incomplete, identities/types/coordinates are invalid, or units differ.
    """
    check_layer(layer)
    whole_count = read_json(count).get("count")
    whole_ids = read_json(ids).get("objectIds")
    if type(whole_count) is not int or whole_count <= 0:
        raise ImportRefused("Italian whole-source count is not a positive integer")
    if not isinstance(whole_ids, list) or any(type(value) is not int for value in whole_ids):
        raise ImportRefused("Italian whole-source IDs are not integer IDs")
    if len(whole_ids) != whole_count or len(set(whole_ids)) != whole_count:
        raise ImportRefused("Italian source count and distinct ID set disagree")
    if not pages:
        raise ImportRefused("Italian source has no feature pages")
    all_rows: list[dict[str, object]] = []
    for index, page_path in enumerate(pages):
        page = read_json(page_path)
        reference = object_fields(page.get("spatialReference")).get("wkid")
        if type(reference) is not int or reference != 4326:
            raise ImportRefused("Italian feature page is not WGS84")
        transfer_limit = page.get("exceededTransferLimit", False)
        if type(transfer_limit) is not bool or (index == len(pages) - 1 and transfer_limit):
            raise ImportRefused("Italian final feature page is truncated")
        for feature in object_rows(page.get("features")):
            row = object_fields(feature.get("attributes"))
            geometry = object_fields(feature.get("geometry"))
            if set(row) != NATIVE_FIELDS:
                raise ImportRefused("Italian feature attributes differ from native schema")
            if any(not isinstance(row[name], str) for name in STRING_FIELDS):
                raise ImportRefused("Italian native text field has the wrong type")
            if any(type(row[name]) is not int for name in INTEGER_FIELDS):
                raise ImportRefused("Italian native integer field has the wrong type")
            if any(type(row[name]) not in (int, float) for name in DOUBLE_FIELDS):
                raise ImportRefused("Italian native quantity field has the wrong type")
            latitude = quantity(row["LAT_WGS84"], minimum=43, maximum=46)
            longitude = quantity(row["LONG_WGS84"], minimum=9, maximum=13)
            geometry_lat = quantity(geometry.get("y"), minimum=43, maximum=46)
            geometry_lon = quantity(geometry.get("x"), minimum=9, maximum=13)
            if max(abs(latitude - geometry_lat), abs(longitude - geometry_lon)) > 1e-7:
                raise ImportRefused("Italian geometry and coordinate attributes disagree")
            for name in ("P_MW_EL", "P_MW_T"):
                quantity(row[name], minimum=0, maximum=1_000_000_000)
            quantity(row["NUM_IMP"], minimum=1, maximum=1_000_000_000)
            if not all(str(row[key]).strip() for key in ("COD_OE", "IMPIANTO", "TIPO_COMB")):
                raise ImportRefused("Italian feature identity, name or fuel is missing")
            all_rows.append(row)
    actual_ids = [row["OBJECTID"] for row in all_rows]
    if actual_ids != sorted(whole_ids):
        raise ImportRefused("Italian feature pages do not equal the ordered complete source ID set")
    observations: list[dict[str, str]] = []
    for source in all_rows:
        fuel = str(source["TIPO_COMB"])
        if "biogas" not in fuel.casefold():
            continue
        observation = dict.fromkeys(SNAPSHOT_FIELDS, "")
        note = str(source["NOTE"])
        observation.update(
            source="it-arpae-biogas",
            source_record_id=str(source["COD_OE"]),
            source_row_id=str(source["OBJECTID"]),
            facility_name=str(source["IMPIANTO"]),
            operator=str(source["GESTORE"]),
            country="Italy",
            locality=str(source["COMUNE"]) + " | " + str(source["PROVINCIA"]),
            lat=str(source["LAT_WGS84"]),
            lon=str(source["LONG_WGS84"]),
            coordinate_basis="Source WGS84 attributes and API point geometry; positional accuracy unverified",
            source_process_class=fuel,
            source_facility_class=str(source["TIPO_DITTA"]),
            source_status=str(source["STATO"]),
            capacity_electrical_mw=str(source["P_MW_EL"]),
            capacity_thermal_mw=str(source["P_MW_T"]),
            source_date=str(source["AGG_DATI"]),
            source_context=(
                f"Source productive sections: {source['NUM_IMP']} (not reactor vessels); "
                f"source cogeneration: {source['COGENERAZ']}; "
                f"source district heating: {source['TELERISCAL']}"
            ),
            source_note=note,
            source_biomass_note=str(source["NOTE_BIOM"]),
            source_position_warning="POSIZIONE DA VERIFICARE"
            if "POSIZIONE DA VERIFICARE" in note.upper()
            else "",
            source_east=str(source["X_E32"]),
            source_north=str(source["Y_E32"]),
            retrieved=retrieved,
            license="CC-BY-4.0",
        )
        observations.append(observation)
    if not observations:
        raise ImportRefused("Italian complete source has no biogas observations")
    check_observations(observations)
    return observations


def main() -> None:
    """Read complete real page captures without refreshing or rewriting them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", type=Path, required=True)
    parser.add_argument("--count", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--page", type=Path, action="append", required=True)
    parser.add_argument("--retrieved", required=True)
    args = parser.parse_args()
    try:
        rows = read_italian(args.layer, args.count, args.ids, args.page, retrieved=args.retrieved)
    except (OSError, ImportRefused):
        print("ITALIAN CHECK FAILED: complete source captures or their contract are invalid")
        raise SystemExit(1) from None
    print(
        json.dumps(
            {
                "biogas_observations": len(rows),
                "publisher_position_warnings": sum(
                    bool(row["source_position_warning"]) for row in rows
                ),
                "physical_positional_accuracy": "not established",
            }
        )
    )


if __name__ == "__main__":
    main()
