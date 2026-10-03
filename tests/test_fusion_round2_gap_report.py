# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — fusion round-2 gap report conformance

"""Reproduce the published round-2 reports from actual native fusion layer copies."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from ._fusion_layers import DIRECTORY, copy_fusion_layers
from .conftest import load_module

SCRIPT = DIRECTORY / "enrichment_round2/generate_gap_report.py"
REPORTS = ("gap_report_summary.tsv", "gap_report_by_country.tsv", "GAP_REPORT.md")


def test_round2_actual_reports_reproduce(tmp_path: Path) -> None:
    """All three outputs reproduce exactly under normal and optimized CLI runs."""
    copy_fusion_layers(tmp_path)
    for optimize in (False, True):
        result = run_cli(SCRIPT, "--fusion-root", str(tmp_path), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        for name in REPORTS:
            assert (tmp_path / "enrichment_round2" / name).read_bytes() == (
                DIRECTORY / "enrichment_round2" / name
            ).read_bytes()


@pytest.mark.parametrize(
    "corruption",
    [
        "new_collision",
        "unknown_overlay_id",
        "blank_id",
        "duplicate_id",
        "empty_base",
        "header",
        "truncated",
        "extra",
        "quote",
        "utf8",
        "missing",
        "output_blocked",
    ],
)
def test_round2_report_corrupt_sources_refuse(tmp_path: Path, corruption: str) -> None:
    """Invalid source identity and I/O cannot silently produce successful reports."""
    copy_fusion_layers(tmp_path)
    path = tmp_path / "enrichment_round2/enrichment_round2.tsv"
    fields, rows = read_table(path)
    if corruption == "new_collision":
        new_path = tmp_path / "enrichment/new_facilities.tsv"
        columns, new = read_table(new_path)
        _, base = read_table(tmp_path / "fusion_facilities.tsv")
        new[0]["stable_id"] = base[0]["stable_id"]
        write_table(new_path, columns, new)
    elif corruption == "unknown_overlay_id":
        rows[0]["stable_id"] = "missing-base-identity"
    elif corruption == "blank_id":
        rows[0]["stable_id"] = ""
    elif corruption == "duplicate_id":
        rows.append(rows[0].copy())
    elif corruption == "empty_base":
        columns, _ = read_table(tmp_path / "fusion_facilities.tsv")
        write_table(tmp_path / "fusion_facilities.tsv", columns, [])
    elif corruption == "header":
        fields = fields[::-1]
    write_table(path, fields, rows)
    if corruption == "truncated":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "missing":
        path.unlink()
    elif corruption == "output_blocked":
        (tmp_path / "enrichment_round2/GAP_REPORT.md").mkdir()
    result = run_cli(SCRIPT, "--fusion-root", str(tmp_path), optimize=True)
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr


def test_round2_report_import_and_public_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Importing does not generate reports; the public entry point uses the chosen source root."""
    copy_fusion_layers(tmp_path)
    before = {name: (DIRECTORY / "enrichment_round2" / name).read_bytes() for name in REPORTS}
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_fusion_round2_gap")
    assert before == {
        name: (DIRECTORY / "enrichment_round2" / name).read_bytes() for name in REPORTS
    }
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--fusion-root", str(tmp_path)])
    module.main()
    for name in REPORTS:
        assert (tmp_path / "enrichment_round2" / name).read_bytes() == before[name]
