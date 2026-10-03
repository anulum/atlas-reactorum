# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — company identity and evidence audit conformance

"""Check the actual company audit and damaged copies through its production CLI."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/validate.py"
AUDIT = SCRIPT.with_name("audited_companies.tsv")
REQUIRED = [
    "company",
    "identity_class",
    "normalized_status",
    "country",
    "approach_family",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "source_dates",
    "audit_date",
    "confidence",
]


def test_actual_company_audit_preserves_claims_and_sources() -> None:
    before = hashlib.sha256(AUDIT.read_bytes()).hexdigest()
    for optimized in (False, True):
        result = run_cli(SCRIPT, optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VALIDATION PASSED" in result.stdout and "records\t51" in result.stdout
        assert "evidence_tiers\t" in result.stdout
    assert before == hashlib.sha256(AUDIT.read_bytes()).hexdigest()


@pytest.mark.parametrize("field", REQUIRED)
@pytest.mark.parametrize("value", ["", " "])
def test_required_evidence_fields_refuse_blank_values(
    tmp_path: Path, field: str, value: str
) -> None:
    fields, rows = read_table(AUDIT)
    rows[0][field] = value
    path = tmp_path / "audit.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input", str(path), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"missing {field}" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize("field", ["official_url", "independent_urls"])
@pytest.mark.parametrize(
    "value",
    [
        "file:///source",
        "http://example.org/source",
        "https:///source",
        "https://[broken",
    ],
)
def test_company_source_url_refuses_malformed_or_non_https(
    tmp_path: Path, field: str, value: str
) -> None:
    fields, rows = read_table(AUDIT)
    rows[0][field] = value
    path = tmp_path / "audit.tsv"
    write_table(path, fields, rows)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--input", str(path), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "invalid source URL" in result.stdout and "Traceback" not in result.stderr
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "corruption",
    [
        "empty",
        "empty_file",
        "header",
        "truncated",
        "extra",
        "utf8",
        "quote",
        "missing",
        "duplicate",
        "no_sources",
        "confidence",
        "calendar",
        "partial_date",
    ],
)
def test_company_audit_structure_identity_and_provenance_refuse(
    tmp_path: Path, corruption: str
) -> None:
    fields, rows = read_table(AUDIT)
    if corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    elif corruption == "duplicate":
        rows[1] = rows[0].copy()
    elif corruption == "no_sources":
        rows[0].update(official_url="", independent_urls=" ; ")
    elif corruption == "confidence":
        rows[0]["confidence"] = "certain"
    elif corruption == "calendar":
        rows[0]["audit_date"] = "2026-02-30"
    elif corruption == "partial_date":
        rows[0]["audit_date"] = "2026"
    path = tmp_path / "audit.tsv"
    write_table(path, fields, rows)
    if corruption == "empty_file":
        path.write_bytes(b"")
    elif corruption == "truncated":
        path.write_text("\t".join(fields) + "\nonly-company\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, "--input", str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "VALIDATION FAILED" in result.stdout and "Traceback" not in result.stderr
    if corruption == "duplicate":
        assert "occurs 2 times" in result.stdout
    elif corruption == "no_sources":
        assert "no source URL" in result.stdout
    elif corruption == "confidence":
        assert "invalid confidence" in result.stdout
    elif corruption in {"calendar", "partial_date"}:
        assert "full ISO date" in result.stdout


def test_independent_sources_can_support_missing_official_site(tmp_path: Path) -> None:
    fields, rows = read_table(AUDIT)
    source = next(row for row in rows if not row["official_url"] and row["independent_urls"])
    assert source["company"]
    with_independent = next(row for row in rows if row["official_url"] and row["independent_urls"])
    with_independent["official_url"] = ""
    path = tmp_path / "audit.tsv"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input", str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_company_validator_public_read_and_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_audit_validator")
    assert module.load(AUDIT) == read_table(AUDIT)[1]
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    module.main()
