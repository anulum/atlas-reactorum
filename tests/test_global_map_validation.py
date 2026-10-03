# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — global map validation conformance

"""Check real WRI TSV/GeoJSON pairs and refuse corrupt copies through the CLI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map"
SCRIPT = DIRECTORY / "scripts/validate.py"


@pytest.fixture
def map_inputs(tmp_path: Path) -> Path:
    """Copy the actual paired data into an isolated native directory layout."""
    (tmp_path / "data").mkdir()
    for name in ("reactors.tsv", "reactors.geojson"):
        shutil.copy2(DIRECTORY / "data" / name, tmp_path / "data" / name)
    return tmp_path


def test_actual_global_map_pair_passes(map_inputs: Path) -> None:
    """The complete 195-plant WRI layer is accepted and its report pins exact inputs."""
    for optimize in (False, True):
        result = run_cli(SCRIPT, cwd=map_inputs, optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        report = (map_inputs / "VALIDATION.md").read_text()
        assert "Records: 195" in report and "Errors: 0" in report
        assert "SHA-256" in report


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("name", "", "missing name"),
        ("domain", "unclassified", "bad domain"),
        ("latitude", "91", "coordinate range"),
        ("longitude", "181", "coordinate range"),
        ("latitude", "NaN", "coordinate range"),
        ("latitude", "unknown", "invalid coordinate"),
        ("country_code", "arm", "country_code"),
        ("source_url", "file:///article", "source_url"),
        ("last_verified", "yesterday", "last_verified"),
        ("last_verified", "2026-02-30", "last_verified"),
    ],
)
def test_invalid_global_map_rows_are_reported(
    map_inputs: Path, field: str, value: str, diagnostic: str
) -> None:
    """Source corruption is refused and recorded rather than silently projected."""
    path = map_inputs / "data/reactors.tsv"
    fields, rows = read_table(path)
    rows[0][field] = value
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, cwd=map_inputs, optimize=True)
    assert result.returncode == 1
    assert diagnostic in (map_inputs / "VALIDATION.md").read_text()
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption", ["duplicate", "empty", "missing_header", "truncated_row", "extra_cell"]
)
def test_global_map_table_integrity_refuses(map_inputs: Path, corruption: str) -> None:
    """A complete-looking GeoJSON file cannot conceal broken TSV structure."""
    path = map_inputs / "data/reactors.tsv"
    fields, rows = read_table(path)
    if corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "empty":
        rows.clear()
    elif corruption == "missing_header":
        fields.remove("country_code")
        for row in rows:
            row.pop("country_code")
    write_table(path, fields, rows)
    if corruption in {"truncated_row", "extra_cell"}:
        lines = path.read_text().splitlines()
        lines[1] = (
            lines[1].split("\t")[0] if corruption == "truncated_row" else lines[1] + "\textra"
        )
        path.write_text("\n".join(lines) + "\n")
    result = run_cli(SCRIPT, cwd=map_inputs, optimize=True)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_feature",
        "unknown_id",
        "duplicate_id",
        "wrong_coordinates",
        "non_object_feature",
        "invalid_geometry",
        "bad_json",
        "wrong_collection",
    ],
)
def test_global_map_geojson_parity_refuses(map_inputs: Path, corruption: str) -> None:
    """Equal counts alone cannot establish identity or coordinate agreement."""
    path = map_inputs / "data/reactors.geojson"
    data = json.loads(path.read_bytes())
    if corruption == "missing_feature":
        data["features"].pop()
    elif corruption == "unknown_id":
        data["features"][0]["id"] += "-changed"
    elif corruption == "duplicate_id":
        data["features"][0]["id"] = data["features"][1]["id"]
    elif corruption == "wrong_coordinates":
        data["features"][0]["geometry"]["coordinates"][0] += 1
    elif corruption == "non_object_feature":
        data["features"][0] = None
    elif corruption == "invalid_geometry":
        data["features"][0]["geometry"] = None
    elif corruption == "wrong_collection":
        data = []
    path.write_bytes(b"{" if corruption == "bad_json" else json.dumps(data).encode())
    result = run_cli(SCRIPT, cwd=map_inputs, optimize=True)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_global_map_read_failure_refuses(map_inputs: Path) -> None:
    """A missing source is an explicit validation failure."""
    (map_inputs / "data/reactors.tsv").unlink()
    result = run_cli(SCRIPT, cwd=map_inputs)
    assert result.returncode == 1 and "Traceback" not in result.stderr


def test_global_map_public_report_api(map_inputs: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The public report API returns whether the actual pair has errors."""
    monkeypatch.chdir(map_inputs)
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_global_map_validator")
    assert module.main() is False
    assert (map_inputs / "VALIDATION.md").is_file()
