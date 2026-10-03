# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — global map GeoJSON export conformance

"""Reproduce the checked-in GeoJSON and reject invalid projection inputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map"
SOURCE = DIRECTORY / "data/reactors.tsv"
PUBLISHED = DIRECTORY / "data/reactors.geojson"
SCRIPT = DIRECTORY / "scripts/export_geojson.py"


def test_actual_wri_rows_reproduce_geojson(tmp_path: Path) -> None:
    """The public exporter preserves exact IDs, coordinates, Unicode and provenance."""
    destination = tmp_path / "nested/reactors.geojson"
    result = run_cli(SCRIPT, "--input", str(SOURCE), "--output", str(destination))
    assert result.returncode == 0, result.stderr
    assert destination.read_bytes() == PUBLISHED.read_bytes()
    assert "wrote 195 features" in result.stdout
    data = json.loads(destination.read_bytes())
    _, rows = read_table(SOURCE)
    assert [f["id"] for f in data["features"]] == [row["id"] for row in rows]
    for feature, row in zip(data["features"], rows, strict=True):
        assert feature["properties"]["source_url"] == row["source_url"]
        assert feature["properties"]["source_license"] == row["source_license"]
        assert feature["properties"]["end_date"] == (row["end_date"] or None)


def test_geojson_default_paths_and_public_absence_api(tmp_path: Path) -> None:
    """The documented native layout and public date-null conversion remain usable."""
    (tmp_path / "data").mkdir()
    shutil.copy2(SOURCE, tmp_path / "data/reactors.tsv")
    result = run_cli(SCRIPT, cwd=tmp_path, optimize=True)
    assert result.returncode == 0
    assert (tmp_path / "data/reactors.geojson").read_bytes() == PUBLISHED.read_bytes()
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_geojson_export")
    _, rows = read_table(SOURCE)
    assert module.null("") is None
    assert module.null(rows[0]["start_date"]) == rows[0]["start_date"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", "NaN"),
        ("longitude", "Infinity"),
        ("latitude", "unknown"),
        ("latitude", "91"),
        ("longitude", "181"),
        ("id", ""),
    ],
)
def test_invalid_geojson_input_never_overwrites_output(
    tmp_path: Path, field: str, value: str
) -> None:
    """Unprojectable positions or absent identities refuse before writing."""
    fields, rows = read_table(SOURCE)
    rows[0][field] = value
    source = tmp_path / SOURCE.name
    write_table(source, fields, rows)
    destination = tmp_path / PUBLISHED.name
    destination.write_bytes(PUBLISHED.read_bytes())
    result = run_cli(SCRIPT, "--input", str(source), "--output", str(destination), optimize=True)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert destination.read_bytes() == PUBLISHED.read_bytes()


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate_id",
        "empty",
        "missing_header",
        "extra_cell",
        "truncated_row",
        "missing_file",
        "invalid_utf8",
        "unterminated_quote",
    ],
)
def test_broken_geojson_source_is_refused(tmp_path: Path, corruption: str) -> None:
    """Table corruption cannot create a partial or falsely empty map."""
    fields, rows = read_table(SOURCE)
    source = tmp_path / SOURCE.name
    if corruption == "duplicate_id":
        rows.append(rows[0].copy())
    elif corruption == "empty":
        rows.clear()
    elif corruption == "missing_header":
        fields.remove("start_date")
        for row in rows:
            row.pop("start_date")
    if corruption != "missing_file":
        write_table(source, fields, rows)
    if corruption in {"extra_cell", "truncated_row"}:
        lines = source.read_text().splitlines()
        lines[1] = lines[1] + "\textra" if corruption == "extra_cell" else lines[1].split("\t")[0]
        source.write_text("\n".join(lines) + "\n")
    elif corruption == "invalid_utf8":
        source.write_bytes(source.read_bytes() + b"\xff")
    elif corruption == "unterminated_quote":
        source.write_text("\t".join(fields) + '\n"unterminated')
    destination = tmp_path / PUBLISHED.name
    result = run_cli(SCRIPT, "--input", str(source), "--output", str(destination))
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert not destination.exists()


def test_geojson_write_error_is_controlled(tmp_path: Path) -> None:
    """An unusable output directory reports an I/O failure rather than a traceback."""
    parent = tmp_path / "not-a-directory"
    parent.write_text("occupied")
    result = run_cli(SCRIPT, "--input", str(SOURCE), "--output", str(parent / "map.geojson"))
    assert result.returncode == 1 and "cannot write GeoJSON" in result.stderr
    assert "Traceback" not in result.stderr
    assert parent.read_text() == "occupied"
