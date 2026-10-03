# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — reviewed company expansion identity validation

"""Validate actual expansion identities against the protected company audit and golden report."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "metadata/company_audit"
SCRIPT = DIRECTORY / "validate_expansion.py"
EXPANSION = DIRECTORY / "expansion_candidates.tsv"
AUDIT = DIRECTORY / "audited_companies.tsv"
REPORT = DIRECTORY / "expansion_validation.json"


def test_actual_company_expansion_reproduces_report(tmp_path: Path) -> None:
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (EXPANSION, AUDIT, REPORT)}
    report = tmp_path / "validation.json"
    for optimized in (False, True):
        result = run_cli(SCRIPT, "--report", str(report), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert report.read_bytes() == REPORT.read_bytes()
        assert json.loads(result.stdout)["errors"] == []
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before}


@pytest.mark.parametrize(
    "corruption",
    [
        "blank",
        "duplicate_id",
        "duplicate_organization",
        "existing_name",
        "existing_alias",
        "cross_alias",
        "punctuation_identity",
        "punctuation_alias",
        "wrong_date",
        "confidence",
        "no_host",
        "file_url",
        "broken_url",
        "independent_no_host",
        "independent_broken",
        "compact_list_bad_url",
    ],
)
def test_company_expansion_identity_and_sources_refuse(tmp_path: Path, corruption: str) -> None:
    fields, rows = read_table(EXPANSION)
    _, audited = read_table(AUDIT)
    if corruption == "blank":
        rows[0]["inclusion_rationale"] = " "
    elif corruption == "duplicate_id":
        rows[1]["candidate_id"] = rows[0]["candidate_id"]
    elif corruption == "duplicate_organization":
        rows[1]["organization"] = rows[0]["organization"].upper()
    elif corruption == "existing_name":
        rows[0]["organization"] = audited[0]["company"]
    elif corruption == "existing_alias":
        existing = next(r for r in audited if r["aliases"].strip())
        rows[0]["aliases"] = existing["aliases"].split(";")[0]
    elif corruption == "cross_alias":
        rows[1]["aliases"] = rows[0]["aliases"]
    elif corruption == "punctuation_identity":
        rows[0]["organization"] = "---"
    elif corruption == "punctuation_alias":
        rows[0]["aliases"] = "---"
    elif corruption == "wrong_date":
        rows[0]["audit_date"] = "2026-09-28"
    elif corruption == "confidence":
        rows[0]["confidence"] = "certain"
    elif corruption == "no_host":
        rows[0]["official_url"] = "https:///source"
    elif corruption == "file_url":
        rows[0]["official_url"] = "file:///source"
    elif corruption == "broken_url":
        rows[0]["official_url"] = "https://[broken"
    elif corruption == "independent_no_host":
        rows[0]["independent_urls"] = "https:///source"
    elif corruption == "independent_broken":
        rows[0]["independent_urls"] = "https://[broken"
    elif corruption == "compact_list_bad_url":
        rows[0]["independent_urls"] += ";file:///source"
    path, report = tmp_path / "candidates.tsv", tmp_path / "validation.json"
    write_table(path, fields, rows)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--input", str(path), "--report", str(report), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    errors = json.loads(report.read_text())["errors"]
    assert errors and "Traceback" not in result.stderr
    assert path.read_bytes() == before
    if corruption == "duplicate_id":
        assert any("duplicate candidate_id" in error for error in errors)
    elif corruption in {"existing_name", "existing_alias"}:
        assert any("audited identity" in error for error in errors)
    elif corruption == "cross_alias":
        assert any("alias identity collides" in error for error in errors)
    elif corruption == "duplicate_organization":
        assert any("duplicate normalized organization" in error for error in errors)


@pytest.mark.parametrize("target", ["expansion", "audit"])
@pytest.mark.parametrize(
    "corruption",
    ["empty", "empty_file", "header", "truncated", "extra", "utf8", "quote", "missing"],
)
def test_company_expansion_bad_tables_preserve_report(
    tmp_path: Path, target: str, corruption: str
) -> None:
    source = EXPANSION if target == "expansion" else AUDIT
    fields, rows = read_table(source)
    if corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    path = tmp_path / "table.tsv"
    write_table(path, fields, rows)
    if corruption == "empty_file":
        path.write_bytes(b"")
    elif corruption == "truncated":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "missing":
        path.unlink()
    report = tmp_path / "validation.json"
    report.write_bytes(REPORT.read_bytes())
    argument = "--input" if target == "expansion" else "--audit"
    result = run_cli(SCRIPT, argument, str(path), "--report", str(report))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "VALIDATION FAILED" in result.stdout and "Traceback" not in result.stderr
    assert report.read_bytes() == REPORT.read_bytes()


@pytest.mark.parametrize("target", ["expansion", "audit"])
def test_company_expansion_report_cannot_replace_input(tmp_path: Path, target: str) -> None:
    path = tmp_path / "input.tsv"
    source = EXPANSION if target == "expansion" else AUDIT
    path.write_bytes(source.read_bytes())
    argument = "--input" if target == "expansion" else "--audit"
    result = run_cli(SCRIPT, argument, str(path), "--report", str(path))
    assert result.returncode == 1 and "report path must differ" in result.stdout
    assert path.read_bytes() == source.read_bytes()


def test_company_expansion_output_failure_preserves_directory(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.mkdir()
    (report / "existing.json").write_bytes(REPORT.read_bytes())
    result = run_cli(SCRIPT, "--report", str(report))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "VALIDATION FAILED" in result.stdout and "Traceback" not in result.stderr
    assert (report / "existing.json").read_bytes() == REPORT.read_bytes()


def test_company_expansion_public_api_and_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion_validator")
    assert module.load(EXPANSION, module.EXPECTED) == read_table(EXPANSION)[1]
    report = tmp_path / "validation.json"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--report", str(report)])
    module.main()
    assert report.read_bytes() == REPORT.read_bytes()


@pytest.mark.parametrize(
    "corruption", ["blank_company", "punctuation_company", "duplicate_company"]
)
def test_protected_audit_requires_valid_unique_identities(tmp_path: Path, corruption: str) -> None:
    fields, rows = read_table(AUDIT)
    if corruption == "blank_company":
        rows[0]["company"] = ""
    elif corruption == "punctuation_company":
        rows[0]["company"] = "---"
    else:
        rows[1]["company"] = rows[0]["company"].upper()
    audit, report = tmp_path / "audit.tsv", tmp_path / "report.json"
    write_table(audit, fields, rows)
    report.write_bytes(REPORT.read_bytes())
    result = run_cli(SCRIPT, "--audit", str(audit), "--report", str(report))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "normalized audited identity" in result.stdout and "Traceback" not in result.stderr
    assert report.read_bytes() == REPORT.read_bytes()


def test_protected_audit_optional_alias_can_remain_unknown(tmp_path: Path) -> None:
    fields, rows = read_table(AUDIT)
    rows[0]["aliases"] = ""
    audit, report = tmp_path / "audit.tsv", tmp_path / "report.json"
    write_table(audit, fields, rows)
    result = run_cli(SCRIPT, "--audit", str(audit), "--report", str(report))
    assert result.returncode == 0, result.stdout + result.stderr
    assert report.read_bytes() == REPORT.read_bytes()


def test_cross_identity_error_report_is_deterministic(tmp_path: Path) -> None:
    fields, rows = read_table(EXPANSION)
    rows[2]["aliases"] = rows[0]["organization"] + "; " + rows[1]["organization"]
    path = tmp_path / "candidates.tsv"
    write_table(path, fields, rows)
    reports = [tmp_path / "normal.json", tmp_path / "optimized.json"]
    for optimized, report in zip((False, True), reports, strict=True):
        result = run_cli(SCRIPT, "--input", str(path), "--report", str(report), optimize=optimized)
        assert result.returncode == 1, result.stdout + result.stderr
        errors = json.loads(report.read_text())["errors"]
        assert any(rows[0]["organization"] in error for error in errors)
        assert any(rows[1]["organization"] in error for error in errors)
    assert reports[0].read_bytes() == reports[1].read_bytes()
