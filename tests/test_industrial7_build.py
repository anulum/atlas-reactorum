# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete native industrial projection
"""Exercise full real source projection, immutable inputs and atomic publication."""

from __future__ import annotations

import copy
import importlib
import os
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli, write_table
from .test_industrial7_contracts import observations as observations

PREFIX = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"
BUILD = importlib.import_module(PREFIX + ".build_dataset")
RECORDS = importlib.import_module(PREFIX + ".records")
CONTRACTS = importlib.import_module(PREFIX + ".contracts")
SCRIPT = (
    ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/build_dataset.py"
)


def test_projection_preserves_complete_source_values(observations: list[dict[str, str]]) -> None:
    original = copy.deepcopy(observations)
    records = RECORDS.project_rows(observations)
    assert observations == original
    assert len(records) == 421
    assert records == RECORDS.project_rows(list(reversed(observations)))
    by_id = {row["stable_id"]: row for row in records}
    for row in observations:
        record = by_id[row["source"] + ":" + row["source_record_id"]]
        assert list(record) == CONTRACTS.FIELDS
        for field in ("facility_name", "country", "lat", "lon", "operator", "retrieved", "license"):
            assert record[field] == row[field]
        assert record["status"] == row["source_status"]
        assert record["reactor_type_if_explicit"] == ""
        assert record["pollutant_or_product_context"] == row["source_context"]
        for field in RECORDS.NOTE_FIELDS:
            if row[field]:
                assert row[field] in record["verification_notes"]
        for field, label in RECORDS.CAPACITIES.items():
            if row[field]:
                assert f"{label}: {row[field]}" in record["capacity"]
        assert row["source_process_class"] in record["process_or_activity"]
        assert row["source_facility_class"] in record["process_or_activity"]
        assert "not independently verified" in record["verification_notes"]
        assert ("publisher requests" in record["precision"]) == bool(row["source_position_warning"])
    assert sum(row["operator"] == " " for row in records) == 32
    assert sum(row["operator"] == "-" for row in records) == 14
    assert sum("publisher requests" in row["precision"] for row in records) == 23
    assert (
        sum("electrical capacity (MW): 0.0" in row["capacity"].split("; ") for row in records) == 2
    )
    assert (
        sum("thermal capacity (MW): 0.0" in row["capacity"].split("; ") for row in records) == 211
    )
    assert "source valorization:" in by_id["ch-sfoe-biogas:plant1"]["process_or_activity"]
    assert "source fuel:" in by_id["it-arpae-biogas:B-0168"]["process_or_activity"]
    assert by_id["it-arpae-biogas:B-0168"]["status"] == "attivo"
    assert "Discarica chiusa" in by_id["it-arpae-biogas:B-0168"]["verification_notes"]
    assert (
        "physical process is unresolved" in by_id["ch-sfoe-biogas:plant151"]["verification_notes"]
    )
    assert by_id["ch-sfoe-biogas:plant154"]["capacity"] == ""


@pytest.mark.parametrize(
    "failure", ["count", "row_id", "coordinates", "space_id", "slash_id", "colon_id"]
)
def test_projection_refuses_incomplete_or_ambiguous_identity(
    observations: list[dict[str, str]], failure: str
) -> None:
    changed = copy.deepcopy(observations)
    if failure == "count":
        changed.pop()
    elif failure == "row_id":
        changed[0]["source_row_id"] = " "
    elif failure == "coordinates":
        changed[0]["coordinate_basis"] = ""
    else:
        changed[0]["source_record_id"] += {
            "space_id": " ",
            "slash_id": "/other",
            "colon_id": ":other",
        }[failure]
    with pytest.raises(ValueError):
        RECORDS.project_rows(changed)


@pytest.mark.parametrize("optimize", [False, True])
def test_native_builder_complete_products_are_reproducible_and_inputs_unchanged(
    tmp_path: Path, observations: list[dict[str, str]], optimize: bool
) -> None:
    snapshot = tmp_path / "source.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    before = snapshot.read_bytes()
    output = tmp_path / "native.tsv"
    result = run_cli(
        SCRIPT,
        "--snapshot",
        str(snapshot),
        "--output",
        str(output),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "421 facility discovery records built offline" in result.stdout
    second = tmp_path / "second.tsv"
    assert BUILD.build(snapshot, second) == 421
    assert second.read_bytes() == output.read_bytes()
    assert CONTRACTS.read_table(output, CONTRACTS.FIELDS) == RECORDS.project_rows(observations)
    assert snapshot.read_bytes() == before
    assert not list(tmp_path.glob(".industrial7-*"))
    repeated = run_cli(
        SCRIPT,
        "--snapshot",
        str(snapshot),
        "--output",
        str(output),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert repeated.returncode == 1
    assert output.read_bytes() == second.read_bytes()


@pytest.mark.parametrize(
    "failure",
    [
        "input",
        "existing",
        "repository",
        "symlink",
        "dangling",
        "ancestor",
        "missing_parent",
        "file_parent",
        "hardlink",
    ],
)
def test_builder_refusals_preserve_inputs_and_existing_destinations(
    tmp_path: Path, observations: list[dict[str, str]], failure: str
) -> None:
    snapshot = tmp_path / "source.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations)
    before = snapshot.read_bytes()
    output = tmp_path / "product.tsv"
    if failure == "input":
        output = snapshot
    elif failure == "existing":
        output.write_bytes(b"existing accepted bytes")
    elif failure == "repository":
        output = SCRIPT.parent / "must_not_be_created.tsv"
    elif failure in {"symlink", "dangling"}:
        output.symlink_to(snapshot if failure == "symlink" else tmp_path / "absent")
    elif failure == "ancestor":
        parent = tmp_path / "linked"
        parent.symlink_to(tmp_path, target_is_directory=True)
        output = parent / "new.tsv"
    elif failure == "missing_parent":
        output = tmp_path / "missing/product.tsv"
    elif failure == "file_parent":
        output = snapshot / "product.tsv"
    elif failure == "hardlink":
        os.link(snapshot, output)
    existing = output.read_bytes() if output.is_file() else None
    with pytest.raises(ValueError):
        BUILD.build(snapshot, output)
    assert snapshot.read_bytes() == before
    if existing is not None:
        assert output.read_bytes() == existing
    assert not list(tmp_path.glob(".industrial7-*"))


def test_table_encoder_preserves_quoted_cells_and_enforces_readable_size(tmp_path: Path) -> None:
    rows = [{"original": 'text\twith\n"quotation" and trailing '}]
    output = tmp_path / "quoted.tsv"
    BUILD.write_output(output, BUILD.table_bytes(["original"], rows), inputs=())
    assert CONTRACTS.read_table(output, ["original"]) == rows
    with pytest.raises(ValueError, match="bounded"):
        BUILD.table_bytes(["original"], [{"original": "x" * CONTRACTS.MAX_BYTES}])


@pytest.mark.parametrize("optimize", [False, True])
def test_native_builder_rejects_incomplete_source_before_writing(
    tmp_path: Path, observations: list[dict[str, str]], optimize: bool
) -> None:
    snapshot = tmp_path / "incomplete.tsv"
    write_table(snapshot, CONTRACTS.SNAPSHOT_FIELDS, observations[:-1])
    output = tmp_path / "must_not_exist.tsv"
    result = run_cli(
        SCRIPT,
        "--snapshot",
        str(snapshot),
        "--output",
        str(output),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 1
    assert "INDUSTRIAL BUILD FAILED" in result.stdout
    assert not output.exists()
