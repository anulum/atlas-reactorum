# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — third company expansion conformance

"""Validate actual discovery records, protected audits and their evidence joins."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/expansion_round3/validate.py"
NAMES = [
    "candidates.tsv",
    "source_registry.tsv",
    "audited_companies.tsv",
    "expansion_candidates.tsv",
    "expansion_round2/candidates.tsv",
]


@pytest.fixture
def inputs(tmp_path: Path) -> Path:
    """Copy current discovery and all three protected company catalogues into owned storage.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for candidate, registry and historical catalogue copies.

    Returns
    -------
    Path
        Complete discovery directory also usable as the native audit root.
    """
    folder = tmp_path / "round2"
    folder.mkdir()
    for name in NAMES:
        source = SCRIPT.with_name(name) if name in NAMES[:2] else SCRIPT.parent.parent / name
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return folder


def test_original_discovery_reproduces_golden_report(tmp_path: Path) -> None:
    """Reproduce the exact accepted report in both CLI modes while preserving all source bytes."""
    paths = (
        [SCRIPT.with_name(name) for name in NAMES[:2]]
        + [SCRIPT.parent.parent / name for name in NAMES[2:]]
        + [SCRIPT.with_name("validation.json")]
    )
    before = {path: path.read_bytes() for path in paths}
    report = tmp_path / "report.json"
    for optimized in (False, True):
        result = run_cli(SCRIPT, "--report", str(report), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert report.read_bytes() == SCRIPT.with_name("validation.json").read_bytes()
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "damage", ["header", "empty", "short", "extra", "quote", "utf8", "missing"]
)
def test_bad_source_shape_does_not_replace_report(inputs: Path, name: str, damage: str) -> None:
    """Reject malformed current or protected tables without replacing the existing report."""
    path = inputs / name
    fields, rows = read_table(path)
    if damage == "header":
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
    report = inputs / "validation.json"
    report.write_text("old report\n")
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs), optimize=True)
    assert result.returncode == 1 and "VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr and report.read_text() == "old report\n"


@pytest.mark.parametrize("name", NAMES[:2])
def test_all_mandatory_facts_refuse_blank_values(inputs: Path, name: str) -> None:
    """Reject blank values in every candidate and source-registry field."""
    path = inputs / name
    fields, original = read_table(path)
    for field in fields:
        rows = [row.copy() for row in original]
        rows[0][field] = " "
        write_table(path, fields, rows)
        result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
        assert result.returncode == 1 and "blank" in result.stdout, (
            f"{field}: {result.stdout}{result.stderr}"
        )
        assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "case",
    [
        "count",
        "duplicate_id",
        "duplicate_name",
        "cross_alias",
        "cross_name_alias",
        "protected_name",
        "protected_alias",
        "punctuation_name",
        "punctuation_alias",
        "date",
        "confidence",
        "single_ref",
        "duplicate_ref",
        "unknown_ref",
        "foreign_refs",
        "registry_url",
        "source_count",
        "source_duplicate",
        "source_blank_id",
        "source_date",
    ],
)
def test_identity_and_source_association_refusals(inputs: Path, case: str) -> None:
    """Reject changed identities, aliases, dates and reference joins with the expected diagnostics."""
    cp, sp = inputs / NAMES[0], inputs / NAMES[1]
    cf, rows = read_table(cp)
    sf, sources = read_table(sp)
    diagnostic = ""
    if case == "count":
        rows.pop()
        diagnostic = "14 candidate"
    elif case == "duplicate_id":
        rows[1]["candidate_id"] = rows[0]["candidate_id"]
        diagnostic = "duplicate candidate_id"
    elif case == "duplicate_name":
        rows[1]["organization"] = rows[0]["organization"]
        diagnostic = "duplicate candidate name or alias"
    elif case == "cross_alias":
        rows[1]["aliases"] = rows[0]["aliases"]
        diagnostic = "duplicate candidate name or alias"
    elif case == "cross_name_alias":
        rows[1]["organization"] = rows[0]["aliases"].split(";")[0]
        diagnostic = "duplicate candidate name or alias"
    elif case == "protected_name":
        rows[0]["organization"] = read_table(inputs / NAMES[2])[1][0]["company"]
        diagnostic = "protected identity collision"
    elif case == "protected_alias":
        rows[0]["aliases"] = read_table(inputs / NAMES[3])[1][0]["organization"]
        diagnostic = "protected identity collision"
    elif case == "punctuation_name":
        rows[0]["organization"] = "---"
        diagnostic = "invalid normalized identity"
    elif case == "punctuation_alias":
        rows[0]["aliases"] = "---"
        diagnostic = "invalid normalized identity"
    elif case == "date":
        rows[0]["audit_date"] = "2026-02-30"
        diagnostic = "wrong audit date"
    elif case == "confidence":
        rows[0]["confidence"] = "certain"
        diagnostic = "invalid confidence"
    elif case == "single_ref":
        rows[0]["source_ids"] = "R3S001"
        diagnostic = "invalid source references"
    elif case == "duplicate_ref":
        rows[0]["source_ids"] = "R3S001;R3S001"
        diagnostic = "invalid source references"
    elif case == "unknown_ref":
        rows[0]["source_ids"] = "R3S001;UNKNOWN"
        diagnostic = "invalid source references"
    elif case == "foreign_refs":
        rows[0]["source_ids"] = rows[1]["source_ids"]
        diagnostic = "source URLs do not match"
    elif case == "registry_url":
        sources[0]["url"] = "https://example.org/unrelated"
        diagnostic = "source URLs do not match"
    elif case == "source_count":
        sources.pop()
        diagnostic = "28 unique"
    elif case == "source_duplicate":
        sources[1] = sources[0].copy()
        diagnostic = "28 unique"
    elif case == "source_blank_id":
        sources[0]["source_id"] = " "
        diagnostic = "nonempty sources"
    else:
        sources[0]["accessed_on"] = "2026-02-30"
        diagnostic = "date or URL"
    write_table(cp, cf, rows)
    write_table(sp, sf, sources)
    before = {path: path.read_bytes() for path in (cp, sp)}
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize(
    "name,key", [(NAMES[2], "company"), (NAMES[3], "organization"), (NAMES[4], "organization")]
)
@pytest.mark.parametrize("case", ["duplicate", "blank", "punctuation", "alias"])
def test_invalid_protected_identities_refuse_before_report(
    inputs: Path, name: str, key: str, case: str
) -> None:
    """Reject invalid protected identities before replacing the accepted report."""
    path = inputs / name
    fields, rows = read_table(path)
    if case == "duplicate":
        rows[1][key] = rows[0][key]
    elif case == "blank":
        rows[0][key] = " "
    elif case == "punctuation":
        rows[0][key] = "---"
    else:
        rows[0]["aliases"] = "---"
    write_table(path, fields, rows)
    report = inputs / "validation.json"
    report.write_text("old report\n")
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 1 and "protected catalog" in result.stdout
    assert "Traceback" not in result.stderr and report.read_text() == "old report\n"


@pytest.mark.parametrize(
    "table,field", [(NAMES[0], "primary_url"), (NAMES[0], "independent_urls"), (NAMES[1], "url")]
)
@pytest.mark.parametrize(
    "url", ["http://example.org", "https:///no-host", "https://[broken", "https://exa mple.org"]
)
def test_provenance_urls_require_https_authority(
    inputs: Path, table: str, field: str, url: str
) -> None:
    """Reject malformed HTTPS links in primary, independent and source-registry references."""
    path = inputs / table
    fields, rows = read_table(path)
    rows[0][field] = "https://example.org;" + url if field == "independent_urls" else url
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 1 and "URL" in result.stdout


@pytest.mark.parametrize("name", NAMES)
def test_report_cannot_replace_candidate_or_protected_inputs(inputs: Path, name: str) -> None:
    """Refuse report destinations that alias current candidates or any protected input."""
    path = inputs / name
    before = path.read_bytes()
    result = run_cli(
        SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs), "--report", str(path)
    )
    assert result.returncode == 1 and "report would replace" in result.stdout
    assert path.read_bytes() == before


def test_optional_protected_alias_remains_unknown(inputs: Path) -> None:
    """Accept an absent optional alias without inferring a replacement identity."""
    path = inputs / NAMES[2]
    fields, rows = read_table(path)
    rows[0]["aliases"] = ""
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 0, result.stdout + result.stderr


def test_report_directory_failure_is_controlled(inputs: Path) -> None:
    """Report an unwritable directory destination without a native traceback."""
    result = run_cli(
        SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs), "--report", str(inputs)
    )
    assert result.returncode == 1 and "cannot write report" in result.stdout
    assert "Traceback" not in result.stderr


def test_public_read_and_main_use_original_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read original candidates and validate them through the public main entry point."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion3_validator")
    assert (
        module.read(SCRIPT.with_name(NAMES[0]), module.CF)
        == read_table(SCRIPT.with_name(NAMES[0]))[1]
    )
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--report", str(tmp_path / "report.json")])
    module.main()
    assert not json.loads((tmp_path / "report.json").read_text())["errors"]


@pytest.mark.parametrize("name", NAMES[2:])
def test_each_historical_baseline_count_is_required(inputs: Path, name: str) -> None:
    """Reject a changed count in each protected catalogue while preserving the prior report."""
    path = inputs / name
    fields, rows = read_table(path)
    rows.pop()
    write_table(path, fields, rows)
    report = inputs / "validation.json"
    report.write_text("old report\n")
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 1 and "baseline file counts" in result.stdout
    assert report.read_text() == "old report\n"


def test_compensating_baseline_counts_cannot_hide_a_changed_catalog(inputs: Path) -> None:
    """Reject changed individual catalogue counts even when their combined total remains 84."""
    audit = inputs / NAMES[2]
    expansion = inputs / NAMES[3]
    af, a = read_table(audit)
    ef, e = read_table(expansion)
    a.pop()
    e.append(e[0].copy())
    write_table(audit, af, a)
    write_table(expansion, ef, e)
    # The old summed check would still see84; independent schemas/counts matter.
    assert len(a) + len(e) + len(read_table(inputs / NAMES[4])[1]) == 84
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 1 and "baseline file counts" in result.stdout


def test_shared_iaea_source_and_three_reference_record_remain_valid(inputs: Path) -> None:
    """Accept shared and three-reference sources while preserving the 84-to-98 record totals."""
    rows = read_table(inputs / NAMES[0])[1]
    shared = [row for row in rows if "R3S012" in row["source_ids"].split(";")]
    assert len(shared) == 3
    assert any(len(row["source_ids"].split(";")) == 3 for row in shared)
    rows[0]["aliases"] += "; "
    fields = read_table(inputs / NAMES[0])[0]
    write_table(inputs / NAMES[0], fields, rows)
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((inputs / "validation.json").read_text())
    assert report["baseline_records"] == 84 and report["combined_records_after_round3"] == 98


def test_third_protected_catalog_names_are_not_new_candidates(inputs: Path) -> None:
    """Reject a new candidate alias that collides with the third protected catalogue."""
    path = inputs / NAMES[0]
    fields, rows = read_table(path)
    rows[0]["aliases"] = read_table(inputs / NAMES[4])[1][0]["organization"]
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--directory", str(inputs), "--audit-root", str(inputs))
    assert result.returncode == 1 and "protected identity collision" in result.stdout
