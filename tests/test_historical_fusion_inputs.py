# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — historical source selection and immutable input conformance
"""Exercise actual historical input files, native refusal and owned snapshots."""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
import os
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import run_cli
from ._fusion_layers import DIRECTORY, copy_fusion_layers

INPUTS = importlib.import_module("05_global_reactor_map.imports.fusion.historical_inputs")
SCRIPT = DIRECTORY / "historical_inputs.py"


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Copy the actual public nine-file historical input selection."""
    root = tmp_path / "source"
    root.mkdir()
    return copy_fusion_layers(root)


def test_public_selection_keeps_attributed_compilation_and_omits_separate_values() -> None:
    """All146 original identities retain the six fields without unqualified cells."""
    with (DIRECTORY / "fusion_facilities.tsv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(rows) == 146 and len({row["stable_id"] for row in rows}) == 146
    fields = ("name", "country", "configuration", "device_subtype", "status", "organization")
    assert sum(bool(row[field]) for row in rows for field in fields) == 876
    omitted = (
        "aliases",
        "latitude",
        "longitude",
        "coordinate_precision",
        "first_operation_date",
        "last_operation_date",
    )
    assert all(not row[field] for row in rows for field in omitted)
    assert all("CC-BY-4.0" in row["license"] for row in rows)
    assert all(
        "not independently established" in row["verification_evidence_notes"] for row in rows
    )


def test_actual_public_bundle_snapshot_is_byte_exact_and_independent(
    source: Path, tmp_path: Path
) -> None:
    """Later mutation of supplied input cannot alter the verified owned snapshot."""
    destination = tmp_path / "captured"
    before = {member: (source / member).read_bytes() for member in INPUTS.MEMBERS}
    digests = INPUTS.materialize(source, destination, selection="public")
    assert len(digests) == 9
    for member, data in before.items():
        assert (destination / member).read_bytes() == data
        assert digests[member] == hashlib.sha256(data).hexdigest()
    (source / "fusion_facilities.tsv").write_text("changed after snapshot")
    assert (destination / "fusion_facilities.tsv").read_bytes() == before["fusion_facilities.tsv"]


@pytest.mark.parametrize("optimize", [False, True])
def test_native_public_snapshot(source: Path, tmp_path: Path, optimize: bool) -> None:
    """Normal and optimized processes snapshot every real selected source byte."""
    destination = tmp_path / "captured"
    result = run_cli(
        SCRIPT,
        "--source-root",
        str(source),
        "--destination",
        str(destination),
        "--selection",
        "public",
        optimize=optimize,
    )
    assert result.returncode == 0, result.stderr
    assert "9 exact historical inputs" in result.stdout
    for member in INPUTS.MEMBERS:
        assert (destination / member).read_bytes() == (source / member).read_bytes()


@pytest.mark.parametrize(
    "member",
    [
        "fusion_facilities.tsv",
        "source_registry.tsv",
        "enrichment/enrichment.tsv",
        "enrichment/new_facilities.tsv",
        "enrichment/source_registry.tsv",
        "enrichment_round2/enrichment_round2.tsv",
        "enrichment_round2/source_registry.tsv",
        "enrichment_round3/enrichment_round3.tsv",
        "enrichment_round3/source_registry.tsv",
    ],
)
def test_each_changed_real_input_refuses_before_snapshot(
    source: Path, tmp_path: Path, member: str
) -> None:
    """One changed input cannot yield a partial accepted nine-file output."""
    path = source / member
    path.write_bytes(path.read_bytes() + b"\n")
    destination = tmp_path / "uncreated"
    result = run_cli(
        SCRIPT,
        "--source-root",
        str(source),
        "--destination",
        str(destination),
        "--selection",
        "public",
        optimize=True,
    )
    assert result.returncode == 2 and "SHA-256 changed" in result.stderr
    assert not destination.exists() and "Traceback" not in result.stderr


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_existing_owned_content_is_not_overwritten(source: Path, tmp_path: Path, kind: str) -> None:
    """A valid bundle does not authorize overwriting occupied output."""
    destination = tmp_path / "occupied"
    if kind == "file":
        destination.write_text("preserve")
        preserved = destination
    else:
        destination.mkdir()
        preserved = destination / "owner.txt"
        preserved.write_text("preserve")
    with pytest.raises(ValueError, match="empty owned directory"):
        INPUTS.materialize(source, destination, selection="public")
    assert preserved.read_text() == "preserve"


@pytest.mark.parametrize("selection", ["missing", "public_as_frozen"])
@pytest.mark.parametrize("optimize", [False, True])
def test_frozen_selection_cannot_fall_back_to_partial_or_public_inputs(
    source: Path, tmp_path: Path, selection: str, optimize: bool
) -> None:
    """Missing full inputs and the permitted subset cannot impersonate originals."""
    root = tmp_path / "missing" if selection == "missing" else source
    destination = tmp_path / "uncreated"
    result = run_cli(
        SCRIPT, "--source-root", str(root), "--destination", str(destination), optimize=optimize
    )
    assert result.returncode == 2 and "Historical inputs refused" in result.stderr
    assert not destination.exists() and not result.stdout and "Traceback" not in result.stderr
    if selection == "missing":
        assert result.stderr == (
            "Historical inputs refused: source inputs or snapshot output are invalid or unavailable\n"
        )


@pytest.mark.parametrize("kind", ["escape", "fifo"])
@pytest.mark.parametrize("optimize", [False, True])
def test_nonlocal_or_nonregular_inputs_refuse_without_waiting(
    source: Path, tmp_path: Path, kind: str, optimize: bool
) -> None:
    """An escaped symlink or named pipe cannot substitute for immutable input."""
    path = source / "fusion_facilities.tsv"
    if kind == "escape":
        outside = tmp_path / "outside.tsv"
        shutil.move(path, outside)
        path.symlink_to(outside)
    else:
        path.unlink()
        os.mkfifo(path)
    destination = tmp_path / "uncreated"
    result = run_cli(
        SCRIPT,
        "--source-root",
        str(source),
        "--destination",
        str(destination),
        "--selection",
        "public",
        optimize=optimize,
    )
    assert result.returncode == 2 and "Historical inputs refused" in result.stderr
    assert not destination.exists() and "Traceback" not in result.stderr


@pytest.mark.parametrize("corruption", ["members", "schema", "rows", "truncated_row", "extra_cell"])
@pytest.mark.parametrize("optimize", [False, True])
def test_native_consumer_rejects_inconsistent_declared_schema(
    source: Path, tmp_path: Path, corruption: str, optimize: bool
) -> None:
    """The original CLI rejects a caller-owned manifest against actual source bytes."""
    program = tmp_path / "program"
    program.mkdir()
    (program / SCRIPT.name).symlink_to(SCRIPT)
    manifest = json.loads((DIRECTORY / "frozen_input_manifest.json").read_text())
    public = manifest["selections"]["public"]
    if corruption == "members":
        public.pop("source_registry.tsv")
    elif corruption == "schema":
        public["fusion_facilities.tsv"]["fields"].reverse()
    elif corruption == "rows":
        public["fusion_facilities.tsv"]["rows"] += 1
    else:
        path = source / "fusion_facilities.tsv"
        lines = path.read_bytes().splitlines()
        cells = lines[-1].split(b"\t")
        lines[-1] = (
            b"\t".join(cells[:-1]) if corruption == "truncated_row" else lines[-1] + b"\textra"
        )
        data = b"\n".join(lines) + b"\n"
        path.write_bytes(data)
        public["fusion_facilities.tsv"].update(
            bytes=len(data), sha256=hashlib.sha256(data).hexdigest()
        )
    (program / "frozen_input_manifest.json").write_text(json.dumps(manifest))
    destination = tmp_path / "uncreated"
    result = run_cli(
        program / SCRIPT.name,
        "--source-root",
        str(source),
        "--destination",
        str(destination),
        "--selection",
        "public",
        optimize=optimize,
    )
    assert result.returncode == 2 and "Historical inputs refused" in result.stderr
    assert not destination.exists() and "Traceback" not in result.stderr
