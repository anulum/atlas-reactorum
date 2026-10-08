# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_company_depth8_tables.py

"""Exercise complete TSV contracts through the real read-only packet CLI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table

ROUND = ROOT / "metadata/company_audit/depth_round8"
INPUTS = ROUND / "reviewed_inputs"
SCRIPT = ROUND / "review.py"


@pytest.mark.parametrize(
    "name", ["reviewed_profiles.tsv", "reviewed_sources.tsv", "field_source_bindings.tsv"]
)
@pytest.mark.parametrize(
    "damage", ["header", "no_header", "empty", "short", "extra", "quote", "utf8", "missing"]
)
def test_actual_complete_input_tables_fail_closed(tmp_path: Path, name: str, damage: str) -> None:
    """Refuse corrupt copied TSV contracts under -O without modifying any surviving input."""
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / name
    fields, rows = read_table(path)
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    write_table(path, fields, rows)
    data = path.read_bytes()
    lines = data.splitlines(keepends=True)
    if damage == "no_header":
        path.write_bytes(b"")
    elif damage == "short":
        lines[1] = b"\t".join(lines[1].rstrip(b"\r\n").split(b"\t")[:-1]) + b"\n"
        path.write_bytes(b"".join(lines))
    elif damage == "extra":
        lines[1] = lines[1].rstrip(b"\r\n") + b"\textra-cell\n"
        path.write_bytes(b"".join(lines))
    elif damage == "quote":
        path.write_bytes(data + b'"unterminated\n')
    elif damage == "utf8":
        path.write_bytes(b"\xff" + data)
    elif damage == "missing":
        path.unlink()
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    result = run_cli(SCRIPT, "--input-directory", str(source), cwd=tmp_path, optimize=True)
    assert result.returncode == 1 and "REVIEW FAILED" in result.stdout
    assert "Traceback" not in result.stderr
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before


def test_all_actual_tsv_contracts_are_exercised_without_writing(tmp_path: Path) -> None:
    """Review all actual input tables with exact counts while preserving their source bytes."""
    before = {p: p.read_bytes() for p in INPUTS.glob("*.tsv")}
    result = run_cli(SCRIPT, cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert (report["profile_count"], report["source_count"]) == (10, 33)
    assert report["metadata_gap_fields_reviewed"] == 21
    assert "not established" in report["physical_gap_closure"]
    assert all(p.read_bytes() == value for p, value in before.items())
