# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — fusion enrichment validator conformance

"""Validate genuine fusion enrichment, new facilities and source registry copies."""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/fusion"
SCRIPT = DIRECTORY / "enrichment/validate_enrichment.py"


@pytest.fixture
def layers(tmp_path: Path) -> dict[str, Path]:
    """Copy the four actual source tables while preserving the pinned base bytes."""
    paths = {
        "base": DIRECTORY / "fusion_facilities.tsv",
        "enrichment": DIRECTORY / "enrichment/enrichment.tsv",
        "new": DIRECTORY / "enrichment/new_facilities.tsv",
        "registry": DIRECTORY / "enrichment/source_registry.tsv",
    }
    for key, source in paths.items():
        destination = tmp_path / source.name
        shutil.copy2(source, destination)
        paths[key] = destination
    return paths


def arguments(layers: dict[str, Path]) -> list[str]:
    """Select isolated files through the validator's actual public CLI."""
    return [argument for key, path in layers.items() for argument in ("--" + key, str(path))]


def test_actual_fusion_enrichment_passes(layers: dict[str, Path]) -> None:
    """Both interpreters retain source bytes and accept the entire original layer."""
    before = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in layers.items()}
    for optimize in (False, True):
        result = run_cli(SCRIPT, *arguments(layers), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "immutable base hash verified" in result.stdout
    assert before == {
        key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in layers.items()
    }


@pytest.mark.parametrize(
    ("layer", "field", "value", "diagnostic"),
    [
        ("enrichment", "stable_id", "", "absent from base"),
        ("new", "name", "", "missing name"),
        ("new", "country", "", "missing country"),
        ("new", "configuration", "", "missing configuration"),
        ("new", "device_subtype", "", "missing device_subtype"),
        ("new", "status", "", "missing status"),
        ("new", "organization", "", "missing organization"),
        ("enrichment", "retrieved_date", "", "retrieved_date must be"),
        ("enrichment", "source_role", "", "provenance fields"),
        ("enrichment", "verification_evidence_notes", "", "provenance fields"),
        ("enrichment", "source_url", "", "source_url is required"),
        ("enrichment", "source_url", "file:///source", "invalid HTTPS URL"),
        ("enrichment", "source_url", "https:///source", "invalid HTTPS URL"),
        ("enrichment", "source_url", "https://[invalid", "invalid HTTPS URL"),
        ("enrichment", "first_operation_date", "2026-02-30", "invalid first_operation_date"),
        ("enrichment", "last_operation_date", "2026-13", "invalid last_operation_date"),
        ("enrichment", "first_operation_date", "yesterday", "invalid first_operation_date"),
        ("enrichment", "latitude", "91", "coordinate out of range"),
        ("enrichment", "longitude", "181", "coordinate out of range"),
        ("enrichment", "latitude", "NaN", "coordinate out of range"),
        ("enrichment", "latitude", "unknown", "non-numeric coordinate"),
        ("enrichment", "latitude", "", "pair is incomplete"),
        ("enrichment", "longitude", "", "pair is incomplete"),
        ("enrichment", "coordinate_precision", "", "precision is required"),
        ("registry", "source_id", "", "duplicate/empty ID"),
        ("registry", "url", "file:///source", "registry invalid URL"),
        ("registry", "retrieved_date", "", "wrong retrieval date"),
    ],
)
def test_fusion_enrichment_corrupt_facts_refuse(
    layers: dict[str, Path], layer: str, field: str, value: str, diagnostic: str
) -> None:
    """Invalid copied source facts cannot pass even with assertions disabled."""
    fields, rows = read_table(layers[layer])
    if layer == "enrichment":
        rows[0].update(latitude="0", longitude="0", coordinate_precision="source point")
    rows[0][field] = value
    write_table(layers[layer], fields, rows)
    result = run_cli(SCRIPT, *arguments(layers), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "base_hash",
        "base_count",
        "duplicate",
        "registry_duplicate",
        "new_id_collision",
        "new_name_collision",
        "empty_registry",
        "empty_both",
        "header",
        "truncated",
        "extra",
        "utf8",
        "quote",
        "missing",
    ],
)
def test_fusion_enrichment_integrity_refuses(layers: dict[str, Path], corruption: str) -> None:
    """Hash pins, cross-layer identity, source registries and CSV boundaries are enforced."""
    fields, rows = read_table(layers["enrichment"])
    if corruption == "base_hash":
        layers["base"].write_bytes(layers["base"].read_bytes() + b"\n")
    elif corruption == "base_count":
        columns, base_rows = read_table(layers["base"])
        write_table(layers["base"], columns, base_rows[:-1])
    elif corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "registry_duplicate":
        columns, registry = read_table(layers["registry"])
        registry.append(registry[0].copy())
        write_table(layers["registry"], columns, registry)
    elif corruption in {"new_id_collision", "new_name_collision"}:
        columns, new = read_table(layers["new"])
        _, base = read_table(layers["base"])
        field = "stable_id" if corruption == "new_id_collision" else "name"
        new[0][field] = base[0][field]
        write_table(layers["new"], columns, new)
    elif corruption == "empty_registry":
        columns, _ = read_table(layers["registry"])
        write_table(layers["registry"], columns, [])
    elif corruption == "empty_both":
        rows.clear()
        write_table(layers["new"], fields, [])
    elif corruption == "header":
        fields = fields[::-1]
    write_table(layers["enrichment"], fields, rows)
    path = layers["enrichment"]
    if corruption == "truncated":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, *arguments(layers), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "FAIL" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize("date", ["1957", "1957-09", "1957-09-01"])
def test_fusion_enrichment_source_precision(layers: dict[str, Path], date: str) -> None:
    """Calendar validation retains the explicitly allowed source date precision."""
    fields, rows = read_table(layers["enrichment"])
    rows[0]["first_operation_date"] = date
    write_table(layers["enrichment"], fields, rows)
    result = run_cli(SCRIPT, *arguments(layers))
    assert result.returncode == 0, result.stdout + result.stderr


def test_fusion_enrichment_public_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public entry point checks actual defaults and preserves the public loader API."""
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_fusion_enrichment")
    assert (
        module.load(DIRECTORY / "enrichment/enrichment.tsv")
        == read_table(DIRECTORY / "enrichment/enrichment.tsv")[1]
    )
    module.main()
