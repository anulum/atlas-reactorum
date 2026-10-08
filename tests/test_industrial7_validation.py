# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete source cell and previous-layer validation
"""Refuse whole-product drift and identity collisions using read-only native validation."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli, write_table
from .test_industrial7_contracts import observations as observations

PREFIX = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"
BUILD = importlib.import_module(PREFIX + ".build_dataset")
RECORDS = importlib.import_module(PREFIX + ".records")
CONTRACTS = importlib.import_module(PREFIX + ".contracts")
VALIDATION = importlib.import_module(PREFIX + ".validate")
SCRIPT = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/validate.py"


@pytest.mark.parametrize("optimize", [False, True])
def test_native_validation_exercises_all_canonical_previous_layers_without_writes(
    tmp_path: Path, observations: list[dict[str, str]], optimize: bool
) -> None:
    """Validate 421 exact projections against canonical previous layers without changing source bytes."""
    snapshot, dataset = tmp_path / "source.tsv", tmp_path / "product.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    assert BUILD.build(snapshot, dataset) == 421
    inputs = (snapshot, dataset, *VALIDATION.OTHER_LAYERS)
    before = {path: path.read_bytes() for path in inputs}
    result = run_cli(
        SCRIPT,
        "--snapshot",
        str(snapshot),
        "--dataset",
        str(dataset),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "421 discovery records match all source fields" in result.stdout
    assert VALIDATION.validate(snapshot, dataset) == 421
    assert {path: path.read_bytes() for path in inputs} == before


@pytest.mark.parametrize("field", CONTRACTS.FIELDS)
def test_every_consumer_field_is_checked_against_the_full_source_snapshot(
    tmp_path: Path, observations: list[dict[str, str]], field: str
) -> None:
    """Reject alteration of every consumer field against the full snapshot without rewriting inputs."""
    snapshot, dataset = tmp_path / "source.tsv", tmp_path / "altered.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    records = RECORDS.project_rows(observations)
    records[0][field] += " changed"
    write_table(dataset, CONTRACTS.FIELDS, records)
    before = {path: path.read_bytes() for path in (snapshot, dataset)}
    with pytest.raises(ValueError, match="projection"):
        VALIDATION.validate(snapshot, dataset)
    assert {path: path.read_bytes() for path in (snapshot, dataset)} == before


@pytest.mark.parametrize("failure", ["missing_row", "reordered", "duplicate_row"])
def test_record_count_order_and_duplicates_cannot_pass_cell_parity(
    tmp_path: Path, observations: list[dict[str, str]], failure: str
) -> None:
    """Reject missing, reordered or duplicated consumer rows through the native public validator."""
    snapshot, dataset = tmp_path / "source.tsv", tmp_path / "altered.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    records = RECORDS.project_rows(observations)
    if failure == "missing_row":
        records.pop()
    elif failure == "reordered":
        records.reverse()
    else:
        records[-1] = records[0]
    write_table(dataset, CONTRACTS.FIELDS, records)
    with pytest.raises(ValueError, match="projection"):
        VALIDATION.validate(snapshot, dataset)


@pytest.mark.parametrize("failure", ["collision", "empty", "duplicate", "missing", "schema"])
def test_invalid_previous_layer_or_casefold_collision_is_refused_without_writing(
    tmp_path: Path, observations: list[dict[str, str]], failure: str
) -> None:
    """Refuse previous-layer corruption or casefold identity collisions while retaining source bytes."""
    snapshot, dataset, previous = (
        tmp_path / "source.tsv",
        tmp_path / "product.tsv",
        tmp_path / "previous.tsv",
    )
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    BUILD.build(snapshot, dataset)
    rows = CONTRACTS.read_table(VALIDATION.OTHER_LAYERS[0], CONTRACTS.FIELDS)
    if failure == "collision":
        rows[0]["stable_id"] = "CH-SFOE-BIOGAS:PLANT1"
    elif failure == "empty":
        rows[0]["stable_id"] = " "
    elif failure == "duplicate":
        rows[1]["stable_id"] = rows[0]["stable_id"].upper()
    if failure == "schema":
        previous.write_text("wrong\n")
    elif failure != "missing":
        write_table(previous, CONTRACTS.FIELDS, rows)
    inputs = [path for path in (snapshot, dataset, previous) if path.exists()]
    before = {path: path.read_bytes() for path in inputs}
    with pytest.raises(ValueError):
        VALIDATION.validate(snapshot, dataset, previous_layers=(previous,))
    assert {path: path.read_bytes() for path in inputs} == before


@pytest.mark.parametrize("optimize", [False, True])
def test_native_readonly_validator_refuses_changed_product(
    tmp_path: Path, observations: list[dict[str, str]], optimize: bool
) -> None:
    """Reject invented capacity text normally and under -O while preserving the refused product."""
    snapshot, dataset = tmp_path / "source.tsv", tmp_path / "altered.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    records = RECORDS.project_rows(observations)
    records[-1]["capacity"] += "; invented power"
    write_table(dataset, CONTRACTS.FIELDS, records)
    before = dataset.read_bytes()
    result = run_cli(
        SCRIPT,
        "--snapshot",
        str(snapshot),
        "--dataset",
        str(dataset),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 1
    assert "INDUSTRIAL VALIDATION FAILED" in result.stdout
    assert dataset.read_bytes() == before
