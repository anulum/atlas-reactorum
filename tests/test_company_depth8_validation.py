# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_company_depth8_validation.py

"""Validate every persisted row and protect frozen sources and prior evidence reports."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table

ROUND = ROOT / "metadata/company_audit/depth_round8"
INPUTS = ROUND / "reviewed_inputs"
SCRIPT = ROUND / "validate.py"

PRODUCTS = [
    "enrichment_overlays.tsv",
    "source_registry.tsv",
    "field_source_bindings.tsv",
    "gap_review.tsv",
]


@pytest.mark.parametrize("name", PRODUCTS)
@pytest.mark.parametrize("damage", ["text", "order", "header", "empty", "missing"])
def test_actual_persisted_products_reject_change_without_rebuild(
    tmp_path: Path, name: str, damage: str
) -> None:
    """Reject product drift under -O, preserving inputs and old reports on structural failure."""
    output = tmp_path / "output"
    output.mkdir()
    for product in [*PRODUCTS, "validation.json"]:
        shutil.copy2(ROUND / product, output / product)
    path = output / name
    fields, rows = read_table(path)
    if damage == "text":
        rows[0][fields[-2]] += " unsupported alteration"
    elif damage == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    write_table(path, fields, rows)
    if damage == "missing":
        path.unlink()
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    result = run_cli(SCRIPT, "--directory", str(output), optimize=True)
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert all(
        (output / n).read_bytes() == data for n, data in before.items() if n != "validation.json"
    )
    if damage in ("text", "order"):
        report = json.loads((output / "validation.json").read_text())
        assert report["valid"] is False and len(report["errors"]) == 1
    else:
        assert (output / "validation.json").read_bytes() == before["validation.json"]


@pytest.mark.parametrize(
    "input_name", ["reviewed_profiles.tsv", "reviewed_sources.tsv", "field_source_bindings.tsv"]
)
def test_report_never_replaces_actual_reviewed_inputs(tmp_path: Path, input_name: str) -> None:
    """Reject report aliases of each reviewed input and preserve its actual source bytes."""
    path = INPUTS / input_name
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--report", str(path), cwd=tmp_path)
    assert result.returncode == 1 and "replace a source input" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize("name", PRODUCTS)
def test_report_never_replaces_actual_persisted_product(name: str) -> None:
    """Reject report aliases of each persisted product and preserve its actual source bytes."""
    path = ROUND / name
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--report", str(path))
    assert result.returncode == 1 and "replace a source input" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize("kind", ["missing_parent", "directory", "symlink"])
def test_report_write_refusal_is_controlled_and_preserves_proofs(tmp_path: Path, kind: str) -> None:
    """Refuse invalid report destinations without traceback or alteration of the owned proof."""
    report = tmp_path / "report"
    victim = tmp_path / "victim"
    victim.write_text("owned proof\n")
    if kind == "missing_parent":
        report = tmp_path / "missing-parent/report.json"
    elif kind == "directory":
        report.mkdir()
    else:
        report.symlink_to(victim)
    result = run_cli(SCRIPT, "--report", str(report))
    assert result.returncode == 1 and "VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr and victim.read_text() == "owned proof\n"


def test_public_validation_entry_point_checks_real_full_products(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate all real products with exact counts and retain the physical-closure limitation."""
    import sys

    from .conftest import load_module

    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth8_validation")
    report = tmp_path / "validated.json"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--report", str(report)])
    module.main()
    data = json.loads(report.read_text())
    assert data["valid"] and (
        data["overlay_count"],
        data["source_count"],
        data["field_association_count"],
    ) == (10, 33, 60)
    assert (
        data["metadata_gap_fields_reviewed"] == 21
        and "not established" in data["physical_gap_closure"]
    )
