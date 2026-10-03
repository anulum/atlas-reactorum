# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — verified public historical build contracts

"""Rebuild the actual historical selection from a verified nine-file snapshot."""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli
from ._fusion_layers import DIRECTORY, copy_fusion_layers

INPUTS = importlib.import_module("05_global_reactor_map.imports.fusion.historical_inputs")
BUILDER = ROOT / "04_interactive_presentation/scripts/build_datasets.py"
CAPTURE = DIRECTORY / "historical_inputs.py"
SUPPLEMENT = ROOT / "04_interactive_presentation/data/facilities-supplemental.json"


@pytest.mark.parametrize("optimize", [False, True])
def test_public_snapshot_rebuild_matches_direct_source_and_binds_every_input(
    tmp_path: Path, optimize: bool
) -> None:
    """Native snapshot and build retain all records, unknowns and nine source hashes."""
    bundle = tmp_path / "bundle"
    captured = run_cli(
        CAPTURE,
        "--source-root",
        str(DIRECTORY),
        "--destination",
        str(bundle),
        "--selection",
        "public",
        optimize=optimize,
    )
    assert captured.returncode == 0, captured.stdout + captured.stderr
    hashes = {
        member: hashlib.sha256((DIRECTORY / member).read_bytes()).hexdigest()
        for member in INPUTS.MEMBERS
    }
    outputs = []
    for mode in ("direct", "bundle"):
        data = tmp_path / (mode + "-output")
        data.mkdir()
        shutil.copy2(SUPPLEMENT, data / SUPPLEMENT.name)
        arguments = ["--data-dir", str(data), "--fusion-source", "historical"]
        if mode == "bundle":
            arguments.extend(["--historical-bundle", str(bundle)])
        result = run_cli(BUILDER, *arguments, optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        outputs.append(data)
    direct, snapshotted = outputs
    for name in (
        "global_reactors.sample.json",
        "global_reactors.sample.js",
        "fusion_companies.sample.json",
        "fusion_companies.sample.js",
    ):
        assert (direct / name).read_bytes() == (snapshotted / name).read_bytes()
    inventory = json.loads((snapshotted / "dataset-inventory.json").read_text())
    assert inventory["fusion_source"] == "historical"
    assert inventory["imported_fusion_facilities"] == 146
    assert inventory["facilities"] == 13438
    for member, digest in hashes.items():
        key = "05_global_reactor_map/imports/fusion/" + member
        assert inventory["inputs"][key] == digest
        assert hashlib.sha256((bundle / member).read_bytes()).hexdigest() == digest
        assert hashlib.sha256((DIRECTORY / member).read_bytes()).hexdigest() == digest
    assert not any("/ffdb/" in key for key in inventory["inputs"])


@pytest.mark.parametrize("selection", ["historical", "historical-full"])
@pytest.mark.parametrize("optimize", [False, True])
def test_unavailable_bundle_refuses_before_any_dataset_output(
    tmp_path: Path, selection: str, optimize: bool
) -> None:
    """An explicit unavailable bundle never falls back to the retained catalogue."""
    data = tmp_path / "uncreated"
    result = run_cli(
        BUILDER,
        "--fusion-source",
        selection,
        "--historical-bundle",
        str(tmp_path / "unavailable"),
        "--data-dir",
        str(data),
        optimize=optimize,
    )
    assert result.returncode == 2 and "Historical inputs refused" in result.stderr
    assert not data.exists() and not result.stdout and "Traceback" not in result.stderr
    assert result.stderr == (
        "Historical inputs refused: source inputs or snapshot output are invalid or unavailable\n"
    )


@pytest.mark.parametrize("member", INPUTS.MEMBERS)
def test_each_changed_public_bundle_input_refuses_before_dataset_output(
    tmp_path: Path, member: str
) -> None:
    """Each selected source and registry has an enforced original byte binding."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    copy_fusion_layers(bundle)
    changed = bundle / member
    changed.write_bytes(changed.read_bytes() + b"\n")
    data = tmp_path / "uncreated"
    result = run_cli(
        BUILDER,
        "--fusion-source",
        "historical",
        "--historical-bundle",
        str(bundle),
        "--data-dir",
        str(data),
    )
    assert result.returncode == 2 and "Historical inputs refused" in result.stderr
    assert member in result.stderr and "SHA-256 changed" in result.stderr
    assert not data.exists() and not result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize("optimize", [False, True])
def test_public_bundle_cannot_impersonate_complete_original_inputs(
    tmp_path: Path, optimize: bool
) -> None:
    """The full historical route retains its distinct immutable original hashes."""
    data = tmp_path / "uncreated"
    result = run_cli(
        BUILDER,
        "--fusion-source",
        "historical-full",
        "--historical-bundle",
        str(DIRECTORY),
        "--data-dir",
        str(data),
        optimize=optimize,
    )
    assert result.returncode == 2 and "fusion_facilities.tsv" in result.stderr
    assert "SHA-256 changed" in result.stderr
    assert not data.exists() and not result.stdout and "Traceback" not in result.stderr
