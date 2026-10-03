# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research round-2 enrichment validator conformance

"""Exercise the actual official-source round-2 research enrichment layer through its CLI."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "enrichment_round2/validate_enrichment_round2.py"
BASE = DIRECTORY / "research_reactors.tsv"
PATCH = DIRECTORY / "enrichment_round2/research_reactor_enrichment_round2.tsv"


def test_actual_research_round2_enrichment_passes() -> None:
    """The complete official-source patch validates without modifying either layer."""
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE, PATCH)}
    for optimize in (False, True):
        result = run_cli(SCRIPT, optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "patch records: 12" in result.stdout and "validation: PASS" in result.stdout
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE, PATCH)}


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("stable_id", "", "key absent from base"),
        ("status", "invented", "invalid status"),
        ("source_url", "", "missing"),
        ("source_role", "", "missing"),
        ("verification_notes", "", "missing"),
        ("source_url", "file:///source", "source URL must be HTTPS"),
        ("source_url", "https:///source", "source URL must be HTTPS"),
        ("source_url", "https://[invalid", "source URL must be HTTPS"),
        ("license", "unknown licence", "undeclared rights basis"),
        ("retrieved", "", "full ISO date"),
        ("retrieved", "2026", "full ISO date"),
        ("first_criticality", "2026-02-30", "invalid first_criticality"),
        ("shutdown_date", "2026-13", "invalid shutdown_date"),
        ("first_criticality", "yesterday", "invalid first_criticality"),
        ("thermal_power_mw", "NaN", "power"),
        ("thermal_power_mw", "inf", "power"),
        ("thermal_power_mw", "-1", "power"),
        ("thermal_power_mw", "unknown", "power"),
        ("lat", "91", "coordinates out of range"),
        ("lon", "181", "coordinates out of range"),
        ("lat", "unknown", "non-numeric coordinates"),
        ("lat", "", "unpaired coordinates"),
        ("lon", "", "unpaired coordinates"),
    ],
)
def test_research_round2_enrichment_corrupt_facts_refuse(
    tmp_path: Path, field: str, value: str, diagnostic: str
) -> None:
    """Corrupted copies must not receive a successful provenance report."""
    fields, rows = read_table(PATCH)
    rows[0].update(lat="0", lon="0")
    rows[0][field] = value
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--patch", str(path), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate_patch",
        "duplicate_base",
        "no_fact",
        "empty",
        "header",
        "truncated",
        "extra",
        "utf8",
        "quote",
        "missing",
    ],
)
def test_research_round2_enrichment_integrity_refuses(tmp_path: Path, corruption: str) -> None:
    """Identity, factual changes, structure and I/O are checked before success."""
    fields, rows = read_table(PATCH)
    base_fields, base_rows = read_table(BASE)
    path, base = tmp_path / "patch.tsv", tmp_path / "base.tsv"
    if corruption == "duplicate_patch":
        rows.append(rows[0].copy())
    elif corruption == "duplicate_base":
        base_rows.append(base_rows[0].copy())
    elif corruption == "no_fact":
        original = next(row for row in base_rows if row["stable_id"] == rows[0]["stable_id"])
        provenance = {
            k: rows[0][k]
            for k in (
                "source_url",
                "source_role",
                "retrieved",
                "license",
                "verification_notes",
            )
        }
        rows[0] = original.copy()
        rows[0].update(provenance)
    elif corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    write_table(path, fields, rows)
    write_table(base, base_fields, base_rows)
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
    result = run_cli(SCRIPT, "--base", str(base), "--patch", str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "validation: FAIL" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize("date", ["1957", "1957-09", "1957-09-01"])
def test_research_round2_enrichment_source_date_precision(tmp_path: Path, date: str) -> None:
    """Source date precision is preserved without demanding invented day information."""
    fields, rows = read_table(PATCH)
    rows[0]["first_criticality"] = date
    path = tmp_path / "patch.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--patch", str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_research_round2_enrichment_public_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public imported entry point validates the actual accepted layer."""
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_research_round2_enrichment")
    fields, rows = module.load(PATCH)
    expected_fields, expected_rows = read_table(PATCH)
    assert fields == expected_fields and rows == expected_rows
    module.main()
