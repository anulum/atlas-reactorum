# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — industrial facility validator conformance

"""Exercise the complete 6,550-site discovery layer and corrupted copies."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities"
SCRIPT = DIRECTORY / "validate.py"
SOURCE = DIRECTORY / "industrial_facilities.tsv"


def test_full_industrial_catalogue_native_and_optimized() -> None:
    """Validate the exact 6,550-site discovery summary normally and under -O without source changes."""
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    for optimize in (False, True):
        result = run_cli(SCRIPT, optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout == (
            "VALIDATION PASSED\nrecords\t6550\ncountries\t26\ncoordinates\t6550\n"
            "sources\teea-ied-site=6150; epa-agstar=400\nexplicit_reactor_type\t400\n"
        )
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    "field",
    [
        "stable_id",
        "facility_name",
        "country",
        "lat",
        "lon",
        "precision",
        "sector",
        "status",
        "source_url",
        "source_role",
        "retrieved",
        "license",
        "verification_notes",
    ],
)
def test_required_observations_refuse_full_copy(tmp_path: Path, field: str) -> None:
    """Reject each blank required observation in the full copied source catalogue under -O."""
    fields, rows = read_table(SOURCE)
    rows[0][field] = "   "
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--dataset", str(path), optimize=True)
    assert result.returncode == 1 and f"missing {field}" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("lat", "91", "coordinate out of range"),
        ("lon", "-181", "coordinate out of range"),
        ("lat", "NaN", "coordinate out of range"),
        ("lon", "inf", "coordinate out of range"),
        ("lat", "unknown", "invalid coordinate"),
        ("source_url", "http://www.eea.europa.eu/data", "valid anonymous HTTPS"),
        ("source_url", "https:///data", "valid anonymous HTTPS"),
        ("source_url", "https://user:password@www.eea.europa.eu/data", "valid anonymous HTTPS"),
        ("source_url", "https://www.eea.europa.eu:0/data", "valid anonymous HTTPS"),
        ("source_url", "https://www.eea.europa.eu:65536/data", "valid anonymous HTTPS"),
        ("source_url", "https://[invalid/data", "valid anonymous HTTPS"),
        ("source_url", "https://www.eea.europa.eu/with space", "valid anonymous HTTPS"),
        ("retrieved", "2026-02-30", "invalid ISO retrieval date"),
        ("retrieved", "20260927", "invalid ISO retrieval date"),
        ("reactor_type_if_explicit", "inferred stirred tank", "must not imply"),
    ],
)
def test_corrupt_facts_refuse_full_copy(
    tmp_path: Path, field: str, value: str, diagnostic: str
) -> None:
    """Refuse corrupt coordinates, provenance, dates or inferred reactor types with specific diagnostics."""
    fields, rows = read_table(SOURCE)
    assert rows[0]["stable_id"].startswith("eea-")
    rows[0][field] = value
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    for optimize in (False, True):
        result = run_cli(SCRIPT, "--dataset", str(path), optimize=optimize)
        assert result.returncode == 1 and diagnostic in result.stdout
        assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate",
        "empty_id",
        "empty",
        "header",
        "truncated",
        "extra",
        "quote",
        "utf8",
        "missing",
    ],
)
def test_table_integrity_refuses(tmp_path: Path, corruption: str) -> None:
    """Reject duplicate, malformed or unreadable source tables under -O without a traceback."""
    fields, rows = read_table(SOURCE)
    path = tmp_path / "changed.tsv"
    if corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "empty_id":
        rows[0]["stable_id"] = ""
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
    result = run_cli(SCRIPT, "--dataset", str(path), optimize=True)
    assert result.returncode == 1 and "VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr


def test_public_runtime_api_preserves_scope(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate the complete public API schema, optional absences and inclusive coordinate boundaries."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_validator")
    assert capsys.readouterr().out == ""
    rows = module.read_rows(SOURCE)
    assert len(rows) == 6550 and module.validate_rows(rows) == []
    assert module.main(["--dataset", str(SOURCE)]) == 0
    assert "records\t6550" in capsys.readouterr().out
    assert module.validate_rows([]) == ["industrial table contains no records"]
    fields, changed = read_table(SOURCE)
    changed[0].pop("facility_name")
    assert "string schema" in module.validate_rows(changed)[0]
    invalid = json.loads(json.dumps(rows))
    invalid[0]["facility_name"] = None
    assert "string schema" in module.validate_rows(invalid)[0]
    for row in rows:
        row["operator"] = row["capacity"] = row["process_or_activity"] = ""
    rows[0].update(lat="-90", lon="180", reactor_type_if_explicit="   ")
    assert module.validate_rows(rows) == []
    path = tmp_path / "valid-boundaries.tsv"
    write_table(path, fields, rows)
    assert module.main(["--dataset", str(path)]) == 0
    assert "VALIDATION PASSED" in capsys.readouterr().out


def test_many_errors_keep_original_console_limit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Limit 150 source errors to the original 100 displayed diagnostics and one failure line."""
    fields, rows = read_table(SOURCE)
    for row in rows[:150]:
        row["facility_name"] = ""
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_validator_errors")
    assert module.main(["--dataset", str(path)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 101 and sum("missing facility_name" in s for s in lines) == 100
