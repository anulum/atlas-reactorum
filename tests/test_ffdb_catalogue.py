# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB catalogue source provenance tests

"""Check catalogue semantics against the complete real publisher capture."""

from __future__ import annotations

import importlib
from types import ModuleType

import pytest

from .conftest import ROOT

LAYER = "05_global_reactor_map/imports/fusion/ffdb"
CAPTURE = ROOT / "tests/data/fusion_ffdb/visible_data.frames"


@pytest.fixture
def catalogue() -> ModuleType:
    return importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.catalogue")


def test_all_source_records_and_absences_are_preserved(catalogue: ModuleType) -> None:
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    dashboard = reader.read_dashboard(CAPTURE)
    product = catalogue.build_catalogue(dashboard, "2026-10-02")
    assert len(product.rows) == 174
    assert len({row["stable_id"] for row in product.rows}) == 174
    assert sum(bool(row["lat"]) for row in product.rows) == 137
    for source, row in zip(dashboard.table, product.rows, strict=True):
        assert row["name"] == source.cells["Facility Name"].raw
        assert row["organization"] == source.cells["Organization"].raw
        assert row["status"] == source.cells["Status"].raw
        assert row["configuration"] == source.cells["Configuration"].raw
        assert row["device_subtype"] == source.cells["Type"].raw
        assert row["first_operation_date"] == row["last_operation_date"] == ""
        assert row["aliases"] == ""
        assert set(row) == set(catalogue.FIELDS)
    first = product.rows[0]
    assert first["stable_id"] == "iaea-ffdb:HB11/Australia/HB11%20Energy"
    assert first["lat"] == "-33.7749"
    assert first["lon"] == "151.28783"
    point = next(row for row in product.rows if row["name"] == "UH-MCPG1")
    assert point["lat"] == "34.87691"
    assert point["operator_website"] == ""
    assert "unspecified" in point["coordinate_precision"]
    assert product.provenance["scientific_approval"] is False
    assert product.provenance["historical146_reconstructed"] is False


def test_all_cell_provenance_is_bound_and_display_precision_is_separate(
    catalogue: ModuleType,
) -> None:
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    dashboard = reader.read_dashboard(CAPTURE)
    product = catalogue.build_catalogue(dashboard, "2026-10-02")
    assert product.provenance["source_sha256"] == dashboard.source_sha256
    records = product.provenance["records"]
    assert len(records) == 174
    record = next(row for row in records if row["identity"][0] == "UH-MCPG1")
    latitude = next(field for field in record["fields"] if field["source_field"] == "Latitude")
    assert latitude == {
        "source_field": "Latitude",
        "source_view": "Main",
        "source_tuple_id": 1,
        "raw": 34.87691,
        "display": "34.9",
    }
    assert sum(len(record["fields"]) == 11 for record in records) == 137
    assert sum(len(record["fields"]) == 8 for record in records) == 37


@pytest.mark.parametrize("retrieved", ["", "2026-02-30", "20261002", "2026-W40-5"])
def test_noncanonical_capture_dates_refuse(catalogue: ModuleType, retrieved: str) -> None:
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    with pytest.raises(catalogue.DashboardRefused, match="ISO calendar date"):
        catalogue.build_catalogue(reader.read_dashboard(CAPTURE), retrieved)


def test_catalogue_cannot_change_selected_source_acquisition_date(catalogue: ModuleType) -> None:
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    with pytest.raises(catalogue.DashboardRefused, match="differs from its source selection"):
        catalogue.build_catalogue(reader.read_dashboard(CAPTURE), "2026-10-03")
