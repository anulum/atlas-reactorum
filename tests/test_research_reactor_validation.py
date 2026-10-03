# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research-reactor validator conformance

"""Exercise the real research-reactor catalogue and corrupted copies through its CLI."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "scripts/validate.py"
SOURCE = DIRECTORY / "research_reactors.tsv"


def test_actual_research_catalogue_passes(tmp_path: Path) -> None:
    """The complete source stays unchanged under normal and optimized interpreters."""
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    fields, rows = read_table(SOURCE)
    copy = tmp_path / "research_reactors.tsv"
    write_table(copy, fields, rows)
    for optimize in (False, True):
        result = run_cli(SCRIPT, cwd=tmp_path, optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"records: {len(rows)}" in result.stdout and "validation: PASS" in result.stdout
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("stable_id", "", "invalid stable_id"),
        ("stable_id", "BAD ID", "invalid stable_id"),
        ("name", "", "missing name"),
        ("reactor_type", "", "missing reactor_type"),
        ("status", "invented", "invalid status"),
        ("lat", "91", "coordinate out of range"),
        ("lon", "181", "coordinate out of range"),
        ("lat", "NaN", "coordinate out of range"),
        ("lat", "unknown", "non-numeric coordinate"),
        ("thermal_power_mw", "-1", "thermal power"),
        ("thermal_power_mw", "NaN", "thermal power"),
        ("thermal_power_mw", "inf", "thermal power"),
        ("thermal_power_mw", "unknown", "thermal power"),
        ("first_criticality", "2026-02-30", "invalid first_criticality"),
        ("shutdown_date", "2026-13", "invalid shutdown_date"),
        ("first_criticality", "yesterday", "invalid first_criticality"),
        ("retrieved", "2026", "retrieved must be a full ISO date"),
        ("retrieved", "2026-02-30", "retrieved must be a full ISO date"),
        ("source_url", "file:///source", "https URL"),
        ("source_url", "https:///source", "https URL"),
        ("source_url", "https://[invalid", "https URL"),
    ],
)
def test_research_corrupt_rows_refuse(
    tmp_path: Path, field: str, value: str, diagnostic: str
) -> None:
    """Invalid source facts must not receive a passing catalogue report."""
    fields, rows = read_table(SOURCE)
    rows[0].update(lat="0", lon="0")
    rows[0][field] = value
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, str(path), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption", ["duplicate", "empty", "header", "truncated", "extra", "quote", "utf8", "missing"]
)
def test_research_table_integrity_refuses(tmp_path: Path, corruption: str) -> None:
    """Malformed source tables fail cleanly before row interpretation."""
    fields, rows = read_table(SOURCE)
    path = tmp_path / "changed.tsv"
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
    result = run_cli(SCRIPT, str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "validation: FAIL" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("coordinates", [("", ""), ("0", ""), ("", "0")])
def test_research_coordinate_pair_contract(tmp_path: Path, coordinates: tuple[str, str]) -> None:
    """Unknown positions are allowed; incomplete pairs are refused."""
    fields, rows = read_table(SOURCE)
    rows[0]["lat"], rows[0]["lon"] = coordinates
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, str(path))
    assert result.returncode == (0 if coordinates == ("", "") else 1)
    assert "Traceback" not in result.stderr


def test_research_public_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The importable public entry point validates the same actual source."""
    import sys

    monkeypatch.setattr(sys, "argv", [str(SCRIPT), str(SOURCE)])
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_research_validator")
    module.main()
