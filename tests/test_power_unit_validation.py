# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — power-unit validation conformance

"""Validate real GEM rows and refuse corrupt copies through the public CLI."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SOURCE = ROOT / "05_global_reactor_map/imports/power_units/power_reactor_units.tsv"
SCRIPT = ROOT / "05_global_reactor_map/imports/power_units/scripts/validate.py"


def test_canonical_power_units_are_accepted_without_mutation() -> None:
    """The actual complete layer passes under ordinary and optimized Python."""
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    for optimize in (False, True):
        result = run_cli(SCRIPT, str(SOURCE), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VALIDATION PASSED" in result.stdout
        assert "records\t1823" in result.stdout
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("stable_id", "", "missing stable_id"),
        ("country", "", "missing country"),
        ("status", "operational-maybe", "invalid status"),
        ("reactor_type", "fusion", "fusion record in fission layer"),
        ("lat", "91", "coordinates out of range"),
        ("lon", "181", "coordinates out of range"),
        ("lat", "NaN", "coordinates out of range"),
        ("lat", "unknown", "non-numeric coordinates"),
        ("nameplate_mw", "-1", "negative nameplate_mw"),
        ("nameplate_mw", "unspecified", "non-numeric nameplate_mw"),
        ("nameplate_mw", "NaN", "non-finite nameplate_mw"),
        ("thermal_mw", "Infinity", "non-finite thermal_mw"),
        ("commercial_operation", "2026-02-30", "invalid date"),
        ("construction_start", "2026-13", "invalid date"),
        ("construction_start", "0000", "invalid date"),
        ("source_url", "http://globalenergymonitor.org/", "non-HTTPS source URL"),
        ("source_url", "https:missing-host", "malformed source URL"),
        ("source_url", "extra-source", "count mismatch"),
    ],
)
def test_corrupt_power_unit_fields_refuse(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    """Field corruption is refused with an actionable diagnostic and no traceback."""
    fields, rows = read_table(SOURCE)
    rows[0][field] = (
        rows[0][field] + "|" + rows[0][field].split("|")[0] if value == "extra-source" else value
    )
    destination = tmp_path / SOURCE.name
    write_table(destination, fields, rows)
    result = run_cli(SCRIPT, str(destination), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert message in result.stdout + result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption", ["duplicate", "reordered_header", "missing_header", "empty", "truncated_row"]
)
def test_power_unit_table_structure_refuses(tmp_path: Path, corruption: str) -> None:
    """Broken table structure cannot produce success or an incidental KeyError."""
    fields, rows = read_table(SOURCE)
    destination = tmp_path / SOURCE.name
    if corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "reordered_header":
        fields.reverse()
    elif corruption == "missing_header":
        fields.remove("stable_id")
        for row in rows:
            row.pop("stable_id")
    elif corruption == "empty":
        rows.clear()
    write_table(destination, fields, rows)
    if corruption == "truncated_row":
        lines = destination.read_text().splitlines()
        lines[1] = lines[1].split("\t")[0]
        destination.write_text("\n".join(lines) + "\n")
    result = run_cli(SCRIPT, str(destination), optimize=True)
    assert result.returncode == 1
    assert "VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr


def test_power_unit_calendar_precision_contract() -> None:
    """Public date validation accepts declared precisions and rejects impossible dates."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_power_unit_validator")
    for value in ("", "2026", "2026-09", "2026-09-27"):
        assert module.valid_date(value)
    for value in ("0000", "2026-13", "2026-02-30", "invalid"):
        assert not module.valid_date(value)


@pytest.mark.parametrize(
    "corruption", ["missing_file", "invalid_utf8", "unterminated_quote", "extra_cell"]
)
def test_power_unit_read_failures_are_controlled(tmp_path: Path, corruption: str) -> None:
    """Unreadable or malformed CSV input is rejected without partial validation."""
    fields, rows = read_table(SOURCE)
    destination = tmp_path / SOURCE.name
    if corruption != "missing_file":
        write_table(destination, fields, rows)
    if corruption == "invalid_utf8":
        destination.write_bytes(destination.read_bytes() + b"\xff")
    elif corruption == "unterminated_quote":
        destination.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "extra_cell":
        lines = destination.read_text().splitlines()
        lines[1] += "\textra"
        destination.write_text("\n".join(lines) + "\n")
    result = run_cli(SCRIPT, str(destination))
    assert result.returncode == 1
    assert "VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr
