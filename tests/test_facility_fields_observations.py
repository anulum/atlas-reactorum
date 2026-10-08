# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility-field verbatim observation conformance

"""Verify source scalars and per-cell provenance using complete original records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from metadata.facility_fields.inputs import original_rows
from metadata.facility_fields.project import project

from ._facility_field_sources import document, replace_input, specification
from ._facility_field_sources import original_source as original_source


def test_every_observation_carries_original_byte_and_cell_bindings(original_source: Path) -> None:
    """Bind each observation to source and target hashes while omitting absent Dairy end-use cells."""
    result = project(original_source)
    for row in result:
        assert (
            row["source_sha256"]
            == hashlib.sha256((original_source / row["source_artifact"]).read_bytes()).hexdigest()
        )
        assert (
            row["target_sha256"]
            == hashlib.sha256((original_source / row["target_dataset"]).read_bytes()).hexdigest()
        )
        assert row["source_url"].startswith("https://")
        assert row["checked"].startswith("2026-09-")
        assert row["license"].strip()
    dairy = specification(original_source, "agstar-Dairy")
    native = original_rows(document(original_source / str(dairy["path"]))["records"])
    missing = {str(row["OBJECTID"]) for row in native if row["Biogas_End"] is None}
    assert len(missing) == 3
    assert not [
        row
        for row in result
        if row["source_artifact"] == dairy["path"] and row["source_record_id"] in missing
    ]


@pytest.mark.parametrize("value", [True, 1.5, None, " "])
def test_invalid_publisher_identity_refuses_complete_projection(
    original_source: Path, value: object
) -> None:
    """Reject boolean, fractional, missing or blank publisher record identities."""
    key = "agstar-Mixed"
    body = document(original_source / str(specification(original_source, key)["path"]))
    original_rows(body["records"])[0]["OBJECTID"] = value
    replace_input(original_source, key, json.dumps(body).encode())
    with pytest.raises(ValueError):
        project(original_source)


@pytest.mark.parametrize(
    "field,value", [("Biogas_End", True), ("Biogas_End", 42), ("OBJECTID", " ")]
)
def test_present_original_scalars_are_not_coerced(
    original_source: Path, field: str, value: object
) -> None:
    """Reject non-string end-use cells or blank identities instead of coercing source values."""
    body = document(original_source / str(specification(original_source, "agstar-Mixed")["path"]))
    original_rows(body["records"])[0][field] = value
    replace_input(original_source, "agstar-Mixed", json.dumps(body).encode())
    with pytest.raises(ValueError):
        project(original_source)


def test_text_identifiers_retain_published_value_and_original_whitespace(
    original_source: Path,
) -> None:
    """Preserve literal whitespace in accepted text identities and their published end-use values."""
    body = document(original_source / str(specification(original_source, "agstar-Mixed")["path"]))
    row = original_rows(body["records"])[0]
    original = row["Biogas_End"]
    row["OBJECTID"] = "  published-id  "
    row["Biogas_End"] = "  " + str(original) + "  "
    replace_input(original_source, "agstar-Mixed", json.dumps(body).encode())
    result = project(original_source)
    selected = [row for row in result if row["source_record_id"] == "  published-id  "]
    assert len(selected) == 1
    assert selected[0]["value"] == "  " + str(original) + "  "
