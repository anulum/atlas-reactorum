# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility-field read-only validator conformance

"""Require every original assertion and byte-order through the real validator CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from metadata.facility_fields.build import build
from metadata.facility_fields.inputs import original_rows
from metadata.facility_fields.validate import validate

from ._facility_field_sources import document, run_cli
from ._facility_field_sources import original_source as original_source


@pytest.mark.parametrize("optimize", [False, True])
def test_native_validator_is_read_only_and_matches_all_original_values(
    original_source: Path, optimize: bool
) -> None:
    dataset = original_source.parent / "dataset.json"
    build(original_source, dataset)
    before = dataset.read_bytes()
    result = run_cli("validate", original_source, "--dataset", str(dataset), optimize=optimize)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1631 assertions match complete original fields; no input rewritten" in result.stdout
    assert validate(original_source, dataset) == 1631
    assert dataset.read_bytes() == before


@pytest.mark.parametrize("failure", ["missing", "value", "order", "binding", "count"])
@pytest.mark.parametrize("optimize", [False, True])
def test_native_validator_refuses_partial_or_changed_projection_without_writing(
    original_source: Path, failure: str, optimize: bool
) -> None:
    dataset = original_source.parent / "dataset.json"
    build(original_source, dataset)
    body = document(dataset)
    if failure == "missing":
        dataset.rename(dataset.with_suffix(".unavailable"))
    else:
        if failure == "count":
            body["record_count"] = 1630
        else:
            records = original_rows(body["records"])
            if failure == "order":
                records.reverse()
                body["records"] = records
            else:
                records[0]["value" if failure == "value" else "source_sha256"] = "changed"
        dataset.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n")
    before = dataset.read_bytes() if dataset.exists() else None
    result = run_cli("validate", original_source, "--dataset", str(dataset), optimize=optimize)
    assert result.returncode == 1
    assert (
        result.stdout.strip()
        == "FACILITY FIELD VALIDATION FAILED: original cells or source bindings differ"
    )
    assert "Traceback" not in result.stderr
    assert (dataset.read_bytes() if dataset.exists() else None) == before
