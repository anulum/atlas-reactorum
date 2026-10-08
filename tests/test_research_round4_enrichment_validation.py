# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research round-4 enrichment validator conformance

"""Exercise the round-4 validator and real report generation in isolated catalogue copies."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "enrichment_round4/validate_enrichment_round4.py"
REPORTS = (
    "field_completeness_by_country.tsv",
    "field_completeness_summary.tsv",
    "field_completeness_report.md",
)


@pytest.fixture
def research_copy(tmp_path: Path) -> Path:
    """Copy the complete research catalogue into the caller's temporary directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owned directory for the base, earlier overlays, registry and round-4 reports.

    Returns
    -------
    pathlib.Path
        Round-4 directory within the copied catalogue; canonical sources stay untouched.
    """
    return (
        shutil.copytree(
            DIRECTORY,
            tmp_path / "research",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        / "enrichment_round4"
    )


def test_actual_round4_generates_identical_reports(research_copy: Path) -> None:
    """Reproduce all three reports normally and under -O without changing input hashes."""
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    inputs = [
        research_copy / "research_reactor_enrichment_round4.tsv",
        research_copy / "source_registry.tsv",
        research_copy.parent / "research_reactors.tsv",
    ]
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    for optimize in (False, True):
        result = run_cli(SCRIPT, "--research-root", str(research_copy.parent), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "validation: PASS" in result.stdout
        assert {name: (research_copy / name).read_bytes() for name in REPORTS} == before
    assert hashes == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("stable_id", "", "key absent from base"),
        ("country", "invented", "must not alter"),
        ("lat", "0", "must not alter"),
        ("lon", "0", "must not alter"),
        ("precision", "exact", "must not alter"),
        ("status", "invented", "invalid status"),
        ("source_url", "", "missing"),
        ("source_role", "", "missing"),
        ("verification_notes", "", "missing"),
        ("license", "", "missing"),
        ("source_url", "file:///source", "HTTPS"),
        ("source_url", "https:///source", "HTTPS"),
        ("source_url", "https://[invalid", "HTTPS"),
        ("license", "unknown licence", "undeclared rights basis"),
        ("retrieved", "", "full ISO date"),
        ("retrieved", "2026", "full ISO date"),
        ("first_criticality", "2026-02-30", "invalid first_criticality"),
        ("shutdown_date", "2026-13", "invalid shutdown_date"),
        ("first_criticality", "yesterday", "invalid first_criticality"),
        ("first_criticality", "0000", "invalid first_criticality"),
        ("thermal_power_mw", "NaN", "power"),
        ("thermal_power_mw", "inf", "power"),
        ("thermal_power_mw", "-1", "power"),
        ("thermal_power_mw", "unknown", "power"),
    ],
)
def test_round4_bad_facts_refuse_before_report_generation(
    research_copy: Path, field: str, value: str, diagnostic: str
) -> None:
    """Reject the corrupted fact under -O with its diagnostic and no generated reports."""
    path = research_copy / "research_reactor_enrichment_round4.tsv"
    fields, rows = read_table(path)
    rows[0][field] = value
    write_table(path, fields, rows)
    for name in REPORTS:
        (research_copy / name).unlink()
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout and "Traceback" not in result.stderr
    assert all(not (research_copy / name).exists() for name in REPORTS)


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate_patch",
        "duplicate_base",
        "no_fact",
        "empty",
        "empty_file",
        "header",
        "truncated",
        "extra",
        "utf8",
        "quote",
        "missing",
    ],
)
def test_round4_integrity_refuses(research_copy: Path, corruption: str) -> None:
    """Reject malformed, duplicate, absent or ineffective overlay data without a traceback."""
    path = research_copy / "research_reactor_enrichment_round4.tsv"
    fields, rows = read_table(path)
    base = research_copy.parent / "research_reactors.tsv"
    base_fields, base_rows = read_table(base)
    if corruption == "duplicate_patch":
        rows.append(rows[0].copy())
    elif corruption == "duplicate_base":
        base_rows.append(base_rows[0].copy())
    elif corruption == "no_fact":
        original = next(r for r in base_rows if r["stable_id"] == rows[0]["stable_id"])
        for field in fields[1:14]:
            rows[0][field] = (
                "" if field in ("country", "lat", "lon", "precision") else original[field]
            )
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
    elif corruption == "empty_file":
        path.write_bytes(b"")
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "validation: FAIL" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize("date", ["1957", "1957-09", "1957-09-01"])
def test_round4_preserves_source_date_precision(research_copy: Path, date: str) -> None:
    """Accept year, month and full-date precision for the source criticality date."""
    path = research_copy / "research_reactor_enrichment_round4.tsv"
    fields, rows = read_table(path)
    rows[0]["first_criticality"] = date
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "excluded_patch_source",
        "missing_included_source",
        "duplicate_source_id",
        "empty_source_id",
        "blank_required_field",
        "broken_url",
        "file_url",
        "empty_registry",
        "registry_header",
        "registry_truncated",
        "registry_missing",
    ],
)
def test_round4_source_registry_refuses(research_copy: Path, corruption: str) -> None:
    """Refuse corrupted or excluded provenance registry entries under optimized execution."""
    path = research_copy / "source_registry.tsv"
    fields, rows = read_table(path)
    _, patches = read_table(research_copy / "research_reactor_enrichment_round4.tsv")
    included = next(
        r
        for r in rows
        if r["url"] == patches[0]["source_url"] and r["use_decision"].startswith("Included")
    )
    if corruption == "excluded_patch_source":
        included["use_decision"] = "Excluded"
    elif corruption == "missing_included_source":
        rows.remove(included)
    elif corruption == "duplicate_source_id":
        rows.append(rows[0].copy())
    elif corruption == "empty_source_id":
        rows[0]["source_id"] = ""
    elif corruption == "blank_required_field":
        rows[0]["publisher"] = ""
    elif corruption == "broken_url":
        rows[0]["url"] = "https://[invalid"
    elif corruption == "file_url":
        rows[0]["url"] = "file:///source"
    elif corruption == "empty_registry":
        rows.clear()
    elif corruption == "registry_header":
        fields = fields[::-1]
    write_table(path, fields, rows)
    if corruption == "registry_truncated":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif corruption == "registry_missing":
        path.unlink()
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "validation: FAIL" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "country_header",
        "summary_header",
        "country_stages",
        "summary_rows",
        "missing_country",
        "empty_summary",
        "truncated_country",
        "previous_overlay_missing",
    ],
)
def test_round4_report_boundary_refuses(research_copy: Path, corruption: str) -> None:
    """Refuse malformed existing reports or a missing prior overlay through the CLI."""
    country = research_copy / REPORTS[0]
    summary = research_copy / REPORTS[1]
    cf, cr = read_table(country)
    sf, sr = read_table(summary)
    if corruption == "country_header":
        cf = cf[::-1]
    elif corruption == "summary_header":
        sf = sf[::-1]
    elif corruption == "country_stages":
        cr = [r for r in cr if r["stage"] == "after_round3"]
    elif corruption == "summary_rows":
        sr.pop()
    elif corruption == "empty_summary":
        sr.clear()
    write_table(country, cf, cr)
    write_table(summary, sf, sr)
    if corruption == "missing_country":
        country.unlink()
    elif corruption == "truncated_country":
        country.write_text("\t".join(cf) + "\nonly-stage\n")
    elif corruption == "previous_overlay_missing":
        (research_copy.parent / "enrichment/research_reactor_enrichment.tsv").unlink()
    regenerate = corruption in {"previous_overlay_missing"}
    result = run_cli(
        SCRIPT,
        "--research-root",
        str(research_copy.parent),
        *([] if regenerate else ["--check-reports"]),
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "validation: FAIL" in result.stdout and "Traceback" not in result.stderr


def test_round4_public_entry_point_checks_existing_reports(
    research_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Load the real overlay through the public API and check reports without rewriting them."""
    script = SCRIPT
    spec = importlib.util.spec_from_file_location("atlas_research_round4", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(script), "--research-root", str(research_copy.parent), "--check-reports"],
    )
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    fields, rows = module.load(research_copy / "research_reactor_enrichment_round4.tsv")
    assert (fields, rows) == read_table(research_copy / "research_reactor_enrichment_round4.tsv")
    module.main()
    assert before == {name: (research_copy / name).read_bytes() for name in REPORTS}


def test_round4_runs_canonical_generator_for_alternate_data_root(
    research_copy: Path,
) -> None:
    """Generate reports with the canonical script when the copied generator is absent."""
    (research_copy / "generate_completeness_report.py").unlink()
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validation: PASS" in result.stdout


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf", "1e308", "3600.0001"])
def test_round4_invalid_report_deadline_preserves_inputs(research_copy: Path, timeout: str) -> None:
    """Reject unsupported deadlines as CLI errors while preserving existing report bytes."""
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    result = run_cli(
        SCRIPT,
        "--research-root",
        str(research_copy.parent),
        "--report-timeout",
        timeout,
    )
    assert result.returncode == 2
    assert "positive and finite" in result.stderr
    assert "Traceback" not in result.stderr
    assert before == {name: (research_copy / name).read_bytes() for name in REPORTS}


def test_round4_actual_reporter_timeout_preserves_existing_reports(
    research_copy: Path,
) -> None:
    """Time out the real reporter normally and under -O without changing reports or source."""
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    source = research_copy / "research_reactor_enrichment_round4.tsv"
    original = source.read_bytes()
    for optimize in (False, True):
        result = run_cli(
            SCRIPT,
            "--research-root",
            str(research_copy.parent),
            "--report-timeout",
            "1e-9",
            optimize=optimize,
        )
        assert result.returncode == 1
        assert "completeness reports: reporter timed out" in result.stdout
        assert "Traceback" not in result.stderr
        assert before == {name: (research_copy / name).read_bytes() for name in REPORTS}
        assert source.read_bytes() == original


def test_round4_documented_upper_deadline_runs_real_reporter(
    research_copy: Path,
) -> None:
    """Accept the inclusive supported wait without changing original reports."""
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    source = research_copy / "research_reactor_enrichment_round4.tsv"
    original = source.read_bytes()
    for optimize in (False, True):
        result = run_cli(
            SCRIPT,
            "--research-root",
            str(research_copy.parent),
            "--report-timeout",
            "3600",
            optimize=optimize,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "validation: PASS" in result.stdout
        assert "Traceback" not in result.stderr and "OverflowError" not in result.stderr
        assert before == {name: (research_copy / name).read_bytes() for name in REPORTS}
        assert source.read_bytes() == original
