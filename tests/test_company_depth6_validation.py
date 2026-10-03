# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — persisted company depth round6 validation

"""Exercise real depth tables, damaged copies and the production validation CLI."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/depth_round6/validate.py"
GAPS = SCRIPT.parent.parent / "depth_round4/gap_matrix.tsv"
TABLES = ["enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv"]


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[Path, Path]:
    folder = tmp_path / "round6"
    folder.mkdir()
    for name in TABLES:
        shutil.copy2(SCRIPT.with_name(name), folder / name)
    gap = tmp_path / "gap_matrix.tsv"
    shutil.copy2(GAPS, gap)
    return folder, gap


def test_original_snapshot_preserves_inputs_and_report(tmp_path: Path) -> None:
    before = {
        p: p.read_bytes()
        for p in [GAPS, *[SCRIPT.with_name(n) for n in TABLES], SCRIPT.with_name("validation.json")]
    }
    report = tmp_path / "validation.json"
    for optimized in (False, True):
        result = run_cli(SCRIPT, "--report", str(report), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert report.read_bytes() == SCRIPT.with_name("validation.json").read_bytes()
        assert json.loads(result.stdout)["valid"] is True
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize("name", [*TABLES, "gap_matrix.tsv"])
@pytest.mark.parametrize(
    "damage", ["header", "empty", "short", "extra", "quote", "utf8", "missing"]
)
def test_structural_input_failures_preserve_previous_report(
    inputs: tuple[Path, Path], name: str, damage: str
) -> None:
    folder, gap = inputs
    path = gap if name == "gap_matrix.tsv" else folder / name
    fields, rows = read_table(path)
    if damage == "header":
        write_table(path, fields[::-1], rows)
    elif damage == "empty":
        write_table(path, fields, [])
    elif damage == "short":
        path.write_text("\t".join(fields) + "\nonly-name\n")
    elif damage == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif damage == "quote":
        path.write_text("\t".join(fields) + '\n"unclosed')
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    else:
        path.unlink()
    report = folder / "validation.json"
    report.write_text("previous report\n")
    result = run_cli(SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "VALIDATION FAILED" in result.stdout and "Traceback" not in result.stderr
    assert report.read_text() == "previous report\n"


@pytest.mark.parametrize(
    "field",
    [
        "enriched_status",
        "enriched_named_devices_projects",
        "enriched_fuel_cycle",
        "enriched_highest_independently_supported_milestone",
        "enriched_unsupported_or_ambiguous_claims",
        "source_dates",
        "source_record_id",
        "fields_enriched",
        "overlay_note",
    ],
)
def test_blank_overlay_facts_are_not_repaired(inputs: tuple[Path, Path], field: str) -> None:
    folder, gap = inputs
    path = folder / TABLES[0]
    fields, rows = read_table(path)
    rows[0][field] = " "
    write_table(path, fields, rows)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap))
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"blank {field}" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "case",
    [
        "overlay_duplicate",
        "overlay_missing",
        "overlay_foreign",
        "closure_duplicate",
        "closure_missing",
        "closure_foreign",
        "source_count",
        "source_duplicate",
        "source_blank_id",
        "source_foreign",
        "source_wrong_org",
        "source_unknown",
        "source_repeated",
        "source_blank",
        "source_insufficient",
        "match_rule",
        "audit_date",
        "previous_duplicate",
        "previous_blank",
        "previous_missing",
        "previous_priority",
        "previous_gap",
        "missing_enriched_fuel",
        "missing_enriched_date",
        "previous_id",
        "source_limit",
        "source_date",
    ],
)
def test_identity_and_provenance_association_refusals(inputs: tuple[Path, Path], case: str) -> None:
    folder, gap = inputs
    op, sp, cp = [folder / name for name in TABLES]
    of, o = read_table(op)
    sf, s = read_table(sp)
    cf, c = read_table(cp)
    gf, g = read_table(gap)
    previous = next(row for row in g if row["organization"] == o[0]["organization"])
    if case == "overlay_duplicate":
        o[1] = o[0].copy()
    elif case == "overlay_missing":
        o.pop(0)
    elif case == "overlay_foreign":
        o[0]["organization"] = "Wrong identity"
    elif case == "closure_duplicate":
        c[1] = c[0].copy()
    elif case == "closure_missing":
        c.pop(0)
    elif case == "closure_foreign":
        c[0]["organization"] = "Wrong identity"
    elif case == "source_count":
        s.pop()
    elif case == "source_duplicate":
        s[1] = s[0].copy()
    elif case == "source_blank_id":
        s[0]["source_id"] = " "
    elif case == "source_foreign":
        s[0]["organization"] = "Wrong identity"
    elif case == "source_wrong_org":
        o[0]["source_ids"] = o[1]["source_ids"]
    elif case == "source_unknown":
        o[0]["source_ids"] = "UNKNOWN;H02;H03"
    elif case == "source_repeated":
        o[0]["source_ids"] = "H01;H01;H03"
    elif case == "source_blank":
        o[0]["source_ids"] = ";;"
    elif case == "source_insufficient":
        o[0]["source_ids"] = "H01"
    elif case == "match_rule":
        o[0]["match_rule"] = "fuzzy"
    elif case == "audit_date":
        o[0]["audit_date"] = "2026-02-30"
    elif case == "previous_duplicate":
        g.append(previous.copy())
    elif case == "previous_blank":
        g[0]["organization"] = " "
    elif case == "previous_missing":
        g.remove(previous)
    elif case == "previous_priority":
        previous["priority_score"] = "0"
    elif case == "previous_gap":
        previous["gap_fields"] = "source_date"
    elif case == "missing_enriched_fuel":
        o[0]["fields_enriched"] = o[0]["fields_enriched"].replace("fuel_cycle;", "")
    elif case == "missing_enriched_date":
        o[0]["fields_enriched"] = o[0]["fields_enriched"].replace(";source_dates", "")
    elif case == "previous_id":
        previous["record_id"] = "AUD-UNKNOWN"
    elif case == "source_limit":
        s[0]["scope_and_limitations"] = " "
    else:
        s[0]["accessed_on"] = "2026-02-30"
    for path, fields, rows in [(op, of, o), (sp, sf, s), (cp, cf, c), (gap, gf, g)]:
        write_table(path, fields, rows)
    before = {p: p.read_bytes() for p in [op, sp, cp, gap]}
    result = run_cli(SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    report = json.loads((folder / "validation.json").read_text())
    assert report["valid"] is False and report["errors"]
    diagnostic = {
        "overlay_duplicate": "ten unique overlay",
        "overlay_missing": "ten unique overlay",
        "overlay_foreign": "ten unique overlay",
        "closure_duplicate": "ten unique closure",
        "closure_missing": "ten unique closure",
        "closure_foreign": "ten unique closure",
        "source_count": "30 unique",
        "source_duplicate": "30 unique",
        "source_blank_id": "nonempty sources",
        "source_foreign": "three sources per target",
        "source_wrong_org": "invalid source association",
        "source_unknown": "invalid source association",
        "source_repeated": "invalid source association",
        "source_blank": "invalid source association",
        "source_insufficient": "invalid source association",
        "match_rule": "non-exact match",
        "audit_date": "bad audit date",
        "previous_duplicate": "duplicate or blank identities",
        "previous_blank": "duplicate or blank identities",
        "previous_missing": "missing previous target",
        "previous_priority": "selection/identity mismatch",
        "previous_id": "selection/identity mismatch",
        "previous_gap": "selection/identity mismatch",
        "missing_enriched_fuel": "required closure fields not enriched",
        "missing_enriched_date": "required closure fields not enriched",
        "source_limit": "missing source limitation",
        "source_date": "bad source access date",
    }[case]
    assert any(diagnostic in error for error in report["errors"])
    assert "Traceback" not in result.stderr
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize(
    "field",
    [
        "source_record_id",
        "round4_priority_score",
        "round4_gap_fields",
        "fields_closed",
        "remaining_negative_findings",
        "round6_disposition",
        "audit_date",
    ],
)
def test_each_closure_fact_matches_previous_gaps_and_bounded_overlay(
    inputs: tuple[Path, Path], field: str
) -> None:
    folder, gap = inputs
    path = folder / TABLES[2]
    fields, rows = read_table(path)
    rows[0][field] = "fabricated closure"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "closure differs" in result.stdout
    assert read_table(path)[1][0][field] == "fabricated closure"


@pytest.mark.parametrize(
    "table,field",
    [
        (TABLES[0], "enriched_official_url"),
        (TABLES[0], "enriched_independent_urls"),
        (TABLES[1], "url"),
    ],
)
@pytest.mark.parametrize("url", ["http://example.org", "https:///no-host", "https://[broken", ""])
def test_links_require_https_authority(
    inputs: tuple[Path, Path], table: str, field: str, url: str
) -> None:
    folder, gap = inputs
    path = folder / table
    fields, rows = read_table(path)
    # Independent URLs are optional; a compact malformed second link must still refuse.
    rows[0][field] = (
        "https://example.org;" + (url or "https:///")
        if field == "enriched_independent_urls"
        else url
    )
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "URL" in result.stdout


@pytest.mark.parametrize("name", [*TABLES, "gap_matrix.tsv"])
def test_report_cannot_replace_inputs(inputs: tuple[Path, Path], name: str) -> None:
    folder, gap = inputs
    target = gap if name == "gap_matrix.tsv" else folder / name
    before = target.read_bytes()
    result = run_cli(
        SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap), "--report", str(target)
    )
    assert result.returncode == 1 and "report would replace" in result.stdout
    assert target.read_bytes() == before


def test_report_write_failure_is_controlled(inputs: tuple[Path, Path]) -> None:
    folder, gap = inputs
    result = run_cli(
        SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap), "--report", str(folder)
    )
    assert result.returncode == 1 and "cannot write report" in result.stdout
    assert "Traceback" not in result.stderr and folder.is_dir()


def test_optional_independent_links_do_not_erase_claim_limits(inputs: tuple[Path, Path]) -> None:
    folder, gap = inputs
    path = folder / TABLES[0]
    fields, rows = read_table(path)
    note = rows[0]["overlay_note"]
    rows[0]["enriched_independent_urls"] = ""
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(folder), "--gap-matrix", str(gap))
    assert result.returncode == 0, result.stdout + result.stderr
    assert read_table(folder / TABLES[2])[1][0]["remaining_negative_findings"] == note


def test_public_read_and_main_check_original_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth6_validator")
    assert (
        module.read(SCRIPT.with_name(TABLES[0]), module.OVERLAY_FIELDS)
        == read_table(SCRIPT.with_name(TABLES[0]))[1]
    )
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--report", str(tmp_path / "report.json")])
    module.main()
    assert json.loads((tmp_path / "report.json").read_text())["valid"] is True
