# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete facility-field projection acceptance

"""Require the full original projection, stable ordering and accepted target identities."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from metadata.facility_fields.inputs import mapping, original_rows
from metadata.facility_fields.project import project

from ._facility_field_sources import (
    PINS,
    document,
    replace_input,
    replace_table,
    specification,
    table,
)
from ._facility_field_sources import original_source as original_source


def test_complete_projection_is_deterministic_and_all_inputs_stay_unchanged(
    original_source: Path,
) -> None:
    before = {
        str(path.relative_to(original_source)): path.read_bytes()
        for path in original_source.rglob("*")
        if path.is_file()
    }
    result = project(original_source)
    assert len(result) == 1631
    assert Counter(row["field"] for row in result) == {"purpose": 1092, "fuel_or_feed": 539}
    assert result == project(original_source)
    pins = document(original_source / PINS)
    for key, raw in mapping(pins["target_datasets"]).items():
        item = mapping(raw)
        ids = {row[str(item["id_field"])] for row in table(original_source, key, target=True)}
        assert all(
            row["target_id"] in ids for row in result if row["target_dataset"] == item["path"]
        )
    assert {
        str(path.relative_to(original_source)): path.read_bytes()
        for path in original_source.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize("failure", ["duplicate", "unknown_target", "missing_cell", "blank_cell"])
def test_incomplete_or_ambiguous_projection_refuses_acceptance(
    original_source: Path, failure: str
) -> None:
    if failure == "duplicate":
        rows = table(original_source, "wri")
        rows[1] = dict(rows[0])
        replace_table(original_source, "wri", rows)
    elif failure == "unknown_target":
        rows = table(original_source, "wri", target=True)
        rows[0]["id"] = "wri-gppd-unknown"
        replace_table(original_source, "wri", rows, target=True)
    else:
        key = "agstar-Mixed"
        body = document(original_source / str(specification(original_source, key)["path"]))
        original_rows(body["records"])[0]["Biogas_End"] = None if failure == "missing_cell" else " "
        replace_input(original_source, key, json.dumps(body).encode())
    with pytest.raises(ValueError):
        project(original_source)
