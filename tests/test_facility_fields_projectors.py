# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — publisher-specific facility-field conformance

"""Compare every published source value and keep source-specific meanings distinct."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from metadata.facility_fields.inputs import mapping, original_rows
from metadata.facility_fields.project import project

from ._facility_field_sources import document, replace_input, replace_table, specification, table
from ._facility_field_sources import original_source as original_source


def test_all_wri_fuel_categories_are_whole_plant_assertions(original_source: Path) -> None:
    result = [
        row
        for row in project(original_source)
        if row["source_field"] in {"primary_fuel", "other_fuel1", "other_fuel2", "other_fuel3"}
    ]
    expected = {
        (row["gppd_idnr"], field): row[field]
        for row in table(original_source, "wri")
        if row["primary_fuel"] == "Nuclear"
        for field in ("primary_fuel", "other_fuel1", "other_fuel2", "other_fuel3")
        if row[field].strip()
    }
    assert {
        (row["source_record_id"], row["source_field"]): row["value"] for row in result
    } == expected
    assert Counter(row["value"] for row in result) == {
        "Nuclear": 195,
        "Oil": 4,
        "Hydro": 1,
        "Gas": 1,
    }
    assert Counter(row["basis"] for row in result) == {
        "primary-fuel-classification": 195,
        "secondary-fuel-classification": 6,
    }


def test_native_bioenergy_cells_and_ids_survive_without_feed_inference(
    original_source: Path,
) -> None:
    result = project(original_source)
    for key, native_field in [
        ("agstar-Mixed", "Biogas_End"),
        ("agstar-Cattle", "Biogas_End"),
        ("agstar-Poultry", "Biogas_End"),
        ("agstar-Swine", "Biogas_End"),
        ("agstar-Dairy", "Biogas_End"),
        ("br-epe-biomethane", "MateriaPri"),
        ("us-epa-lmop", "project_type_category"),
    ]:
        item = specification(original_source, key)
        body = document(original_source / str(item["path"]))
        native = original_rows(body["records"] if key.startswith("agstar-") else body["features"])
        if not key.startswith("agstar-"):
            native = [mapping(row["attributes"]) for row in native]
        expected = {
            str(row["OBJECTID"]): row[native_field]
            for row in native
            if row[native_field] is not None
        }
        assert {
            row["source_record_id"]: row["value"]
            for row in result
            if row["source_artifact"] == item["path"]
        } == expected
    assert Counter(row["basis"] for row in result) == {
        "published-end-use": 1092,
        "fuel-classification": 268,
        "primary-fuel-classification": 195,
        "secondary-fuel-classification": 6,
        "published-feedstock": 70,
    }


def test_all_round7_source_labels_and_per_row_provenance_survive(original_source: Path) -> None:
    result = {
        row["target_id"]: row
        for row in project(original_source)
        if row["source_field"] == "source_process_class"
    }
    targets = {row["stable_id"]: row for row in table(original_source, "industrial7", target=True)}
    for row in table(original_source, "industrial7"):
        target_id = row["source"] + ":" + row["source_record_id"]
        observation = result[target_id]
        assert observation["value"] == row["source_process_class"]
        assert observation["checked"] == row["retrieved"]
        assert observation["license"] == row["license"]
        assert observation["source_url"] == targets[target_id]["source_url"]
        assert observation["field"] == (
            "purpose" if row["source"] == "ch-sfoe-biogas" else "fuel_or_feed"
        )


def test_unreviewed_round7_namespace_is_refused(original_source: Path) -> None:
    rows = table(original_source, "industrial7")
    rows[0]["source"] = "unreviewed-source"
    replace_table(original_source, "industrial7", rows)
    with pytest.raises(ValueError, match="namespace"):
        project(original_source)


@pytest.mark.parametrize("source", ["br-epe-biomethane", "industrial7"])
def test_absent_published_value_cannot_complete_the_reviewed_projection(
    original_source: Path, source: str
) -> None:
    if source == "industrial7":
        rows = table(original_source, source)
        rows[0]["source_process_class"] = ""
        replace_table(original_source, source, rows)
    else:
        body = document(original_source / str(specification(original_source, source)["path"]))
        mapping(original_rows(body["features"])[0]["attributes"])["MateriaPri"] = None
        replace_input(original_source, source, json.dumps(body).encode())
    with pytest.raises(ValueError, match="complete reviewed explicit"):
        project(original_source)
