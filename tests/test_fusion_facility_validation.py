# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — fusion facility validator conformance

"""Validate the full fusion catalogue and refuse corrupted copies using its CLI."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/fusion"
SCRIPT = DIRECTORY / "validate_fusion_facilities.py"
SOURCE = DIRECTORY / "fusion_facilities.tsv"


def test_actual_fusion_catalogue_passes(tmp_path: Path) -> None:
    """Validation writes only the requested report and leaves canonical data intact."""
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    _, rows = read_table(SOURCE)
    report = tmp_path / "report.md"
    for optimize in (False, True):
        result = run_cli(
            SCRIPT, "--dataset", str(SOURCE), "--report", str(report), optimize=optimize
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"Rows: {len(rows)}" in report.read_text() and "**PASS**" in report.read_text()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("stable_id", "", "missing stable_id"),
        ("name", "", "missing name"),
        ("country", "", "missing country"),
        ("configuration", "", "missing configuration"),
        ("device_subtype", "", "missing device_subtype"),
        ("status", "", "missing status"),
        ("latitude", "91", "coordinates out of range"),
        ("longitude", "181", "coordinates out of range"),
        ("latitude", "NaN", "coordinates out of range"),
        ("latitude", "unknown", "non-numeric coordinates"),
        ("latitude", "", "both present or both empty"),
        ("longitude", "", "both present or both empty"),
        ("coordinate_precision", "", "precision note"),
        ("first_operation_date", "2026-02-30", "invalid ISO date"),
        ("last_operation_date", "2026-13-01", "invalid ISO date"),
        ("retrieved_date", "", "missing retrieved_date"),
        ("source_url", "file:///source", "malformed source URL"),
        ("source_url", "https:///source", "malformed source URL"),
        ("source_url", "https://[invalid", "malformed source URL"),
        ("source_role", "extra|extra|extra|extra", "counts differ"),
        ("license", "", "missing license"),
    ],
)
def test_fusion_corrupt_facts_refuse(
    tmp_path: Path, field: str, value: str, diagnostic: str
) -> None:
    """Invalid facts receive an explicit failing report without a traceback."""
    fields, rows = read_table(SOURCE)
    rows[0].update(latitude="0", longitude="0", coordinate_precision="source point")
    rows[0][field] = value
    path, report = tmp_path / "changed.tsv", tmp_path / "report.md"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--dataset", str(path), "--report", str(report), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in report.read_text() and "**FAIL**" in report.read_text()
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption", ["duplicate", "empty", "header", "truncated", "extra", "quote", "utf8", "missing"]
)
def test_fusion_table_integrity_refuses(tmp_path: Path, corruption: str) -> None:
    """Unreadable or incomplete tables cannot receive a passing report."""
    fields, rows = read_table(SOURCE)
    path, report = tmp_path / "changed.tsv", tmp_path / "report.md"
    if corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    write_table(path, fields, rows)
    if corruption == "truncated":
        path.write_text("\t".join(fields) + "\n" + rows[0]["stable_id"] + "\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, "--dataset", str(path), "--report", str(report))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "FAIL" in result.stdout
    assert "Traceback" not in result.stderr


def test_fusion_unknown_coordinates_and_duplicate_name_warning(tmp_path: Path) -> None:
    """Unknown positions remain valid and same-name distinct IDs remain review warnings."""
    fields, rows = read_table(SOURCE)
    rows[0].update(latitude="", longitude="", organization="")
    rows[1].update(name=rows[0]["name"], country=rows[0]["country"])
    path, report = tmp_path / "changed.tsv", tmp_path / "report.md"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--dataset", str(path), "--report", str(report))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "organization unknown" in report.read_text() and "same-name duplicate" in report.read_text()
    )


def test_fusion_report_io_failure_refuses(tmp_path: Path) -> None:
    """A report cannot silently disappear when its output parent is a file."""
    parent = tmp_path / "occupied"
    parent.write_text("preserve")
    result = run_cli(SCRIPT, "--dataset", str(SOURCE), "--report", str(parent / "report.md"))
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr and parent.read_text() == "preserve"


def test_fusion_public_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The public entry point uses actual data and an explicitly isolated report."""
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), "--dataset", str(SOURCE), "--report", str(tmp_path / "report.md")],
    )
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_fusion_validator")
    assert module.main() == 0
