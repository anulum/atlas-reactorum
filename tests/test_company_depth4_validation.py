# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — persisted company depth matrix verification

"""Check real persisted outputs against source audits and all grouped statistics."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/depth_round4/validate.py"
TABLES = [
    "gap_matrix.tsv",
    "enrichment_overlays.tsv",
    "overlay_sources.tsv",
    "summary_by_country.tsv",
    "summary_by_identity.tsv",
    "summary_by_evidence_tier.tsv",
]
COLUMNS = [
    "records",
    "complete_records",
    "records_with_gaps",
    "high_priority",
    "medium_priority",
    "low_priority",
    "missing_fuel_cycle",
    "missing_official_url",
]


@pytest.fixture
def outputs(tmp_path: Path) -> Path:
    folder = tmp_path / "outputs"
    folder.mkdir()
    for name in TABLES:
        shutil.copy2(SCRIPT.with_name(name), folder / name)
    return folder


def test_original_corrected_matrix_reproduces_report_without_mutating_inputs(
    tmp_path: Path,
) -> None:
    before = {
        p: p.read_bytes()
        for p in [*[SCRIPT.with_name(name) for name in TABLES], SCRIPT.with_name("validation.json")]
    }
    report = tmp_path / "report.json"
    for optimized in (False, True):
        result = run_cli(SCRIPT, "--report", str(report), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert report.read_bytes() == SCRIPT.with_name("validation.json").read_bytes()
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize("name", TABLES)
@pytest.mark.parametrize(
    "damage", ["schema", "empty", "short", "extra", "quote", "utf8", "missing"]
)
def test_invalid_persisted_structure_preserves_report(
    outputs: Path, name: str, damage: str
) -> None:
    path = outputs / name
    fields, rows = read_table(path)
    if damage == "schema":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    write_table(path, fields, rows)
    if damage == "short":
        path.write_text("\t".join(fields) + "\nonly-name\n")
    elif damage == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif damage == "quote":
        path.write_text("\t".join(fields) + '\n"unclosed')
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    report = outputs / "validation.json"
    report.write_text("previous report\n")
    result = run_cli(SCRIPT, "--directory", str(outputs), optimize=True)
    assert result.returncode == 1 and "VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr and report.read_text() == "previous report\n"


@pytest.mark.parametrize(
    "field",
    [
        "priority_score",
        "priority_band",
        "gap_count",
        "gap_fields",
        "fuel_cycle_completeness",
        "normalized_status",
        "organization",
        "source_row",
    ],
)
def test_entire_matrix_matches_actual_source_derivation(outputs: Path, field: str) -> None:
    path = outputs / TABLES[0]
    fields, rows = read_table(path)
    rows[0][field] = "wrong persisted value"
    write_table(path, fields, rows)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--directory", str(outputs))
    assert result.returncode == 1 and "matrix differs" in result.stdout
    assert "Traceback" not in result.stderr and path.read_bytes() == before


@pytest.mark.parametrize(
    "case",
    [
        "matrix_duplicate",
        "matrix_blank",
        "matrix_count",
        "overlay_count",
        "overlay_foreign",
        "overlay_blank",
        "overlay_date",
        "overlay_match",
        "overlay_id",
        "overlay_owner",
        "refs_single",
        "refs_duplicate",
        "refs_unknown",
        "refs_foreign",
        "source_count",
        "source_duplicate",
        "source_blank_id",
        "source_blank",
        "source_date",
    ],
)
def test_record_and_evidence_refusals(outputs: Path, case: str) -> None:
    paths = [outputs / name for name in TABLES[:3]]
    mf, m = read_table(paths[0])
    of, o = read_table(paths[1])
    sf, s = read_table(paths[2])
    diagnostic = ""
    if case == "matrix_duplicate":
        m[1] = m[0].copy()
        diagnostic = "duplicate or blank matrix"
    elif case == "matrix_blank":
        m[0]["record_id"] = " "
        diagnostic = "duplicate or blank matrix"
    elif case == "matrix_count":
        m.pop()
        diagnostic = "matrix differs"
    elif case == "overlay_count":
        o.pop()
        diagnostic = "three exact overlay"
    elif case == "overlay_foreign":
        o[0]["organization"] = "Wrong identity"
        diagnostic = "three exact overlay"
    elif case == "overlay_blank":
        o[0]["overlay_note"] = " "
        diagnostic = "blank required field"
    elif case == "overlay_date":
        o[0]["audit_date"] = "2026-02-30"
        diagnostic = "date or match rule"
    elif case == "overlay_match":
        o[0]["match_rule"] = "fuzzy"
        diagnostic = "date or match rule"
    elif case == "overlay_id":
        o[0]["source_record_id"] = "UNKNOWN"
        diagnostic = "exact-name/record mismatch"
    elif case == "overlay_owner":
        o[0]["source_record_id"] = o[1]["source_record_id"]
        diagnostic = "exact-name/record mismatch"
    elif case == "refs_single":
        o[0]["source_ids"] = "N01"
        diagnostic = "source reference problem"
    elif case == "refs_duplicate":
        o[0]["source_ids"] = "N01;N01"
        diagnostic = "source reference problem"
    elif case == "refs_unknown":
        o[0]["source_ids"] = "N01;UNKNOWN"
        diagnostic = "source reference problem"
    elif case == "refs_foreign":
        o[0]["source_ids"] = o[1]["source_ids"]
        diagnostic = "source reference problem"
    elif case == "source_count":
        s.pop()
        diagnostic = "nine unique source"
    elif case == "source_duplicate":
        s[1] = s[0].copy()
        diagnostic = "nine unique source"
    elif case == "source_blank_id":
        s[0]["source_id"] = " "
        diagnostic = "nine unique source"
    elif case == "source_blank":
        s[0]["scope_and_limitations"] = " "
        diagnostic = "blank field"
    else:
        s[0]["accessed_on"] = "2026-02-30"
        diagnostic = "date or URL"
    for path, fields, rows in zip(paths, [mf, of, sf], [m, o, s], strict=True):
        write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(outputs), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout, result.stdout + result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("name", TABLES[3:])
@pytest.mark.parametrize("field", COLUMNS)
def test_every_summary_count_matches_derived_rows(outputs: Path, name: str, field: str) -> None:
    path = outputs / name
    fields, rows = read_table(path)
    rows[0][field] = str(int(rows[0][field]) + 1)
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(outputs))
    assert result.returncode == 1 and "derived summary counts mismatch" in result.stdout


@pytest.mark.parametrize("case", ["duplicate", "missing", "foreign", "negative", "nonnumeric"])
def test_summary_groupings_and_numeric_refusals(outputs: Path, case: str) -> None:
    path = outputs / TABLES[3]
    fields, rows = read_table(path)
    if case == "duplicate":
        rows.append(rows[0].copy())
    elif case == "missing":
        rows.pop()
    elif case == "foreign":
        rows[0]["country"] = "Unknown grouping"
    elif case == "negative":
        rows[0]["records"] = "-1"
    else:
        rows[0]["records"] = "not a number"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(outputs))
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert (
        "VALIDATION FAILED" if case in {"negative", "nonnumeric"} else "foreign grouping"
    ) in result.stdout


@pytest.mark.parametrize(
    "table,field",
    [
        (TABLES[1], "enriched_official_url"),
        (TABLES[1], "enriched_independent_urls"),
        (TABLES[2], "url"),
    ],
)
@pytest.mark.parametrize("url", ["http://example.org", "https:///no-host", "https://[broken"])
def test_source_links_require_https_authority(
    outputs: Path, table: str, field: str, url: str
) -> None:
    path = outputs / table
    fields, rows = read_table(path)
    rows[0][field] = "https://example.org;" + url if field == "enriched_independent_urls" else url
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(outputs))
    assert result.returncode == 1 and ("URL" in result.stdout), result.stdout + result.stderr


@pytest.mark.parametrize("name", TABLES)
def test_report_cannot_replace_persisted_input(outputs: Path, name: str) -> None:
    path = outputs / name
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--directory", str(outputs), "--report", str(path))
    assert result.returncode == 1 and "report would replace" in result.stdout
    assert path.read_bytes() == before


def test_source_audit_read_failure_and_protection(outputs: Path, tmp_path: Path) -> None:
    root = tmp_path / "audit"
    root.mkdir()
    report = outputs / "validation.json"
    report.write_text("existing report\n")
    result = run_cli(SCRIPT, "--directory", str(outputs), "--audit-root", str(root))
    assert result.returncode == 1 and "VALIDATION FAILED" in result.stdout
    assert report.read_text() == "existing report\n"
    path = SCRIPT.parent.parent / "audited_companies.tsv"
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--directory", str(outputs), "--report", str(path))
    assert result.returncode == 1 and "report would replace" in result.stdout
    assert path.read_bytes() == before


def test_report_directory_failure_is_controlled(outputs: Path) -> None:
    result = run_cli(SCRIPT, "--directory", str(outputs), "--report", str(outputs))
    assert result.returncode == 1 and "cannot write report" in result.stdout
    assert "Traceback" not in result.stderr


def test_public_read_and_main_use_persisted_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth4_validator")
    assert (
        module.read(SCRIPT.with_name(TABLES[0]), module.MATRIX_FIELDS)
        == read_table(SCRIPT.with_name(TABLES[0]))[1]
    )
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--report", str(tmp_path / "report.json")])
    module.main()
    assert not json.loads((tmp_path / "report.json").read_text())["errors"]


def test_source_matching_cannot_accept_blank_required_matrix_facts(
    outputs: Path, tmp_path: Path
) -> None:
    audit = tmp_path / "audit"
    names = [
        "audited_companies.tsv",
        "expansion_candidates.tsv",
        "expansion_round2/candidates.tsv",
        "expansion_round3/candidates.tsv",
    ]
    for name in names:
        target = audit / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SCRIPT.parent.parent / name, target)
    path = audit / names[0]
    fields, rows = read_table(path)
    rows[0]["country"] = ""
    write_table(path, fields, rows)
    build = run_cli(
        SCRIPT.with_name("build.py"), "--audit-root", str(audit), "--output-directory", str(outputs)
    )
    assert build.returncode == 0, build.stdout + build.stderr
    result = run_cli(SCRIPT, "--directory", str(outputs), "--audit-root", str(audit))
    assert result.returncode == 1 and "blank required field" in result.stdout
    assert "matrix differs" not in result.stdout


def test_data_directory_cannot_supply_executable_builder(outputs: Path) -> None:
    (outputs / "build.py").write_text(
        "raise RuntimeError('data directory is not executable code')\n"
    )
    result = run_cli(SCRIPT, "--directory", str(outputs))
    assert result.returncode == 0, result.stdout + result.stderr
    assert not json.loads((outputs / "validation.json").read_text())["errors"]
