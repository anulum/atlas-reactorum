# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete Italian source conformance
"""Exercise the whole native layer before selecting biogas, retaining warnings and zeros."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli

ITALIAN = importlib.import_module(
    "05_global_reactor_map.imports.industrial_facilities.expansion_round7.italian"
)
SCRIPT = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/italian.py"
FIXTURES = ROOT / "tests/data/industrial_round7"


def native_paths(directory: Path) -> tuple[Path, Path, Path, list[Path]]:
    """Locate the complete original layer, count, IDs and feature page."""
    return (
        directory / "ARPAE_LAYER.json",
        directory / "ARPAE_COUNT.json",
        directory / "ARPAE_IDS.json",
        [directory / "ARPAE_COMPLETE.json"],
    )


def write_json(path: Path, value: object) -> None:
    """Persist an explicitly mutated native JSON object for public-reader tests."""
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_every_selected_native_cell_is_preserved() -> None:
    rows = ITALIAN.read_italian(*native_paths(FIXTURES), retrieved="2026-09-30")
    original = json.loads((FIXTURES / "ARPAE_COMPLETE.json").read_text())["features"]
    selected = [
        item["attributes"]
        for item in original
        if "biogas" in item["attributes"]["TIPO_COMB"].casefold()
    ]
    assert len(original) == 330
    assert len(rows) == len(selected) == 268
    indexed = {row["source_record_id"]: row for row in rows}
    for source in selected:
        row = indexed[source["COD_OE"]]
        for field, target in (
            ("IMPIANTO", "facility_name"),
            ("GESTORE", "operator"),
            ("LAT_WGS84", "lat"),
            ("LONG_WGS84", "lon"),
            ("P_MW_EL", "capacity_electrical_mw"),
            ("P_MW_T", "capacity_thermal_mw"),
            ("TIPO_COMB", "source_process_class"),
            ("TIPO_DITTA", "source_facility_class"),
            ("STATO", "source_status"),
            ("AGG_DATI", "source_date"),
            ("NOTE", "source_note"),
            ("NOTE_BIOM", "source_biomass_note"),
            ("X_E32", "source_east"),
            ("Y_E32", "source_north"),
        ):
            assert row[target] == str(source[field])
        assert str(source["NUM_IMP"]) + " (not reactor vessels)" in row["source_context"]
        assert row["retrieved"] == "2026-09-30"
    assert sum(bool(row["source_position_warning"]) for row in rows) == 23
    assert sum(float(row["capacity_electrical_mw"]) == 0 for row in rows) == 2
    assert sum(float(row["capacity_thermal_mw"]) == 0 for row in rows) == 211
    assert sum(not row["operator"].strip() for row in rows) == 32
    assert indexed["B-0168"]["source_status"] == "attivo"
    assert "Discarica chiusa" in indexed["B-0168"]["source_note"]
    provenance = json.loads((FIXTURES / "SOURCE.json").read_text())
    for source in provenance["fixtures"]:
        path = FIXTURES / source["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["fixture_sha256"]


@pytest.mark.parametrize(
    "failure",
    [
        "identity",
        "identifier_type",
        "geometry",
        "fields",
        "field_name",
        "duplicate_field",
        "string_type",
        "integer_type",
        "double_type",
        "electrical_unit",
        "thermal_unit",
        "section_unit",
    ],
)
def test_layer_contract_and_actual_unit_labels(tmp_path: Path, failure: str) -> None:
    layer = json.loads((FIXTURES / "ARPAE_LAYER.json").read_text())
    if failure == "identity":
        layer["name"] = "unrelated"
    elif failure == "identifier_type":
        layer["id"] = False
    elif failure == "geometry":
        layer["geometryType"] = "esriGeometryPolygon"
    elif failure == "fields":
        layer["fields"].pop()
    elif failure == "field_name":
        layer["fields"][0]["name"] = []
    elif failure == "duplicate_field":
        layer["fields"].append(copy.deepcopy(layer["fields"][0]))
    else:
        name = {
            "string_type": "IMPIANTO",
            "integer_type": "NUM_IMP",
            "double_type": "P_MW_EL",
            "electrical_unit": "P_MW_EL",
            "thermal_unit": "P_MW_T",
            "section_unit": "NUM_IMP",
        }[failure]
        field = next(row for row in layer["fields"] if row["name"] == name)
        field["alias" if failure.endswith("unit") else "type"] = "unrelated"
    path = tmp_path / "layer.json"
    write_json(path, layer)
    with pytest.raises(ValueError, match="Italian"):
        ITALIAN.check_layer(path)


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("count", 0),
        ("count", True),
        ("count", "330"),
        ("ids", None),
        ("ids", [True]),
        ("ids", [1, 1]),
    ],
)
def test_independent_source_counts_and_ids(tmp_path: Path, kind: str, value: object) -> None:
    layer, count, ids, pages = native_paths(FIXTURES)
    target = tmp_path / "mutated.json"
    write_json(target, {"count" if kind == "count" else "objectIds": value})
    with pytest.raises(ValueError, match="Italian"):
        ITALIAN.read_italian(
            layer,
            target if kind == "count" else count,
            target if kind == "ids" else ids,
            pages,
            retrieved="2026-09-30",
        )


@pytest.mark.parametrize(
    "failure",
    [
        "spatial_reference",
        "spatial_reference_type",
        "truncated",
        "transfer_type",
        "no_features",
        "attributes",
        "text_type",
        "integer_type",
        "quantity_type",
        "coordinate_range",
        "geometry_coordinate",
        "geometry_disagreement",
        "negative_capacity",
        "nonpositive_sections",
        "missing_identity",
        "ids_order",
        "missing_row",
        "no_selected_fuel",
        "duplicate_selected_identity",
    ],
)
def test_whole_native_feature_contract_before_selection(tmp_path: Path, failure: str) -> None:
    layer, count, ids, _ = native_paths(FIXTURES)
    page = json.loads((FIXTURES / "ARPAE_COMPLETE.json").read_text())
    row = page["features"][0]["attributes"]
    if failure == "spatial_reference":
        page["spatialReference"]["wkid"] = 2056
    elif failure == "spatial_reference_type":
        page["spatialReference"]["wkid"] = 4326.0
    elif failure == "truncated":
        page["exceededTransferLimit"] = True
    elif failure == "transfer_type":
        page["exceededTransferLimit"] = "false"
    elif failure == "no_features":
        page["features"] = []
    elif failure == "attributes":
        row.pop("TIPO")
    elif failure == "text_type":
        row["NOTE"] = None
    elif failure == "integer_type":
        row["OBJECTID"] = True
    elif failure == "quantity_type":
        row["P_MW_EL"] = "1"
    elif failure == "coordinate_range":
        row["LAT_WGS84"] = 1
    elif failure == "geometry_coordinate":
        page["features"][0]["geometry"]["y"] = None
    elif failure == "geometry_disagreement":
        page["features"][0]["geometry"]["y"] += 0.001
    elif failure == "negative_capacity":
        row["P_MW_EL"] = -1
    elif failure == "nonpositive_sections":
        row["NUM_IMP"] = 0
    elif failure == "missing_identity":
        row["COD_OE"] = ""
    elif failure == "ids_order":
        page["features"][:2] = reversed(page["features"][:2])
    elif failure == "missing_row":
        page["features"].pop()
    elif failure == "no_selected_fuel":
        for feature in page["features"]:
            feature["attributes"]["TIPO_COMB"] = "unselected fuel"
    elif failure == "duplicate_selected_identity":
        selected = [
            item["attributes"]
            for item in page["features"]
            if "biogas" in item["attributes"]["TIPO_COMB"].casefold()
        ]
        selected[1]["COD_OE"] = selected[0]["COD_OE"]
    target = tmp_path / "page.json"
    write_json(target, page)
    with pytest.raises(ValueError):
        ITALIAN.read_italian(layer, count, ids, [target], retrieved="2026-09-30")


def test_complete_ordered_pagination_and_empty_page_list(tmp_path: Path) -> None:
    layer, count, ids, pages = native_paths(FIXTURES)
    with pytest.raises(ValueError, match="no feature pages"):
        ITALIAN.read_italian(layer, count, ids, [], retrieved="2026-09-30")
    page = json.loads(pages[0].read_text())
    first, second = copy.deepcopy(page), copy.deepcopy(page)
    first["features"] = page["features"][:165]
    first["exceededTransferLimit"] = True
    second["features"] = page["features"][165:]
    second.pop("exceededTransferLimit", None)
    paths = [tmp_path / "first.json", tmp_path / "second.json"]
    for path, value in zip(paths, (first, second), strict=True):
        write_json(path, value)
    expected = ITALIAN.read_italian(layer, count, ids, pages, retrieved="2026-09-30")
    assert ITALIAN.read_italian(layer, count, ids, paths, retrieved="2026-09-30") == expected


@pytest.mark.parametrize("optimize", [False, True])
def test_native_cli_success_and_safe_failure(tmp_path: Path, optimize: bool) -> None:
    layer, count, ids, pages = native_paths(FIXTURES)
    args = [
        "--layer",
        str(layer),
        "--count",
        str(count),
        "--ids",
        str(ids),
        "--page",
        str(pages[0]),
        "--retrieved",
        "2026-09-30",
    ]
    result = run_cli(SCRIPT, *args, cwd=tmp_path, optimize=optimize)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["publisher_position_warnings"] == 23
    args[1] = str(tmp_path / "absent")
    failure = run_cli(SCRIPT, *args, cwd=tmp_path, optimize=optimize)
    assert failure.returncode == 1
    assert "ITALIAN CHECK FAILED" in failure.stdout
    assert "Traceback" not in failure.stderr
