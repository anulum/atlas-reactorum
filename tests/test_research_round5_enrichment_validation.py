# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research round-5 enrichment validator conformance

"""Exercise the round-5 validator and real report generation in isolated catalogue copies."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "enrichment_round5/validate_enrichment_round5.py"
REPORTS = (
    "field_completeness_by_country.tsv",
    "field_completeness_summary.tsv",
    "field_completeness_report.md",
)


@pytest.fixture
def research_copy(tmp_path: Path) -> Path:
    """Preserve the real base, previous overlays, current registry and sibling generator."""
    return (
        shutil.copytree(
            DIRECTORY,
            tmp_path / "research",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        / "enrichment_round5"
    )


def test_actual_round5_generates_identical_reports(research_copy: Path) -> None:
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    inputs = [
        research_copy / "research_reactor_enrichment_round5.tsv",
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
def test_round5_bad_facts_refuse_before_report_generation(
    research_copy: Path, field: str, value: str, diagnostic: str
) -> None:
    path = research_copy / "research_reactor_enrichment_round5.tsv"
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
def test_round5_integrity_refuses(research_copy: Path, corruption: str) -> None:
    path = research_copy / "research_reactor_enrichment_round5.tsv"
    fields, rows = read_table(path)
    base = research_copy.parent / "research_reactors.tsv"
    base_fields, base_rows = read_table(base)
    if corruption == "duplicate_patch":
        rows.append(rows[0].copy())
    elif corruption == "duplicate_base":
        base_rows.append(base_rows[0].copy())
    elif corruption == "no_fact":
        before = {r["stable_id"]: r.copy() for r in base_rows}
        for prior in [
            research_copy.parent / "enrichment/research_reactor_enrichment.tsv",
            research_copy.parent / "enrichment_round2/research_reactor_enrichment_round2.tsv",
            research_copy.parent / "enrichment_round3/research_reactor_enrichment_round3.tsv",
            research_copy.parent / "enrichment_round4/research_reactor_enrichment_round4.tsv",
        ]:
            for patch in read_table(prior)[1]:
                before[patch["stable_id"]].update(
                    {k: v for k, v in patch.items() if v and k in fields[1:14]}
                )
        original = before[rows[0]["stable_id"]]
        for field in fields[1:14]:
            rows[0][field] = (
                "" if field in ("country", "lat", "lon", "precision") else original[field]
            )
    elif corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    write_table(path, fields, rows)
    if corruption == "duplicate_base":
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
    if corruption != "duplicate_base":
        assert "immutable input changed" not in result.stdout
    if corruption == "duplicate_patch":
        assert "duplicate key" in result.stdout
    if corruption == "no_fact":
        assert "no effective factual change" in result.stdout


@pytest.mark.parametrize("date", ["1957", "1957-09", "1957-09-01"])
def test_round5_preserves_source_date_precision(research_copy: Path, date: str) -> None:
    path = research_copy / "research_reactor_enrichment_round5.tsv"
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
def test_round5_source_registry_refuses(research_copy: Path, corruption: str) -> None:
    path = research_copy / "source_registry.tsv"
    fields, rows = read_table(path)
    _, patches = read_table(research_copy / "research_reactor_enrichment_round5.tsv")
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
        "summary_records",
        "summary_noninteger",
        "report_output_directory",
    ],
)
def test_round5_report_boundary_refuses(research_copy: Path, corruption: str) -> None:
    country = research_copy / REPORTS[0]
    summary = research_copy / REPORTS[1]
    cf, cr = read_table(country)
    sf, sr = read_table(summary)
    if corruption == "country_header":
        cf = cf[::-1]
    elif corruption == "summary_header":
        sf = sf[::-1]
    elif corruption == "country_stages":
        cr = [r for r in cr if r["stage"] == "before_round5"]
    elif corruption == "summary_rows":
        sr.pop()
    elif corruption == "summary_records":
        sr[0]["records"] = "999"
    elif corruption == "summary_noninteger":
        sr[0]["records"] = "not-an-integer"
    elif corruption == "empty_summary":
        sr.clear()
    write_table(country, cf, cr)
    write_table(summary, sf, sr)
    if corruption == "missing_country":
        country.unlink()
    elif corruption == "truncated_country":
        country.write_text("\t".join(cf) + "\nonly-stage\n")
    elif corruption == "report_output_directory":
        country.unlink()
        country.mkdir()
    elif corruption == "previous_overlay_missing":
        (research_copy.parent / "enrichment/research_reactor_enrichment.tsv").unlink()
    regenerate = corruption in {"previous_overlay_missing", "report_output_directory"}
    result = run_cli(
        SCRIPT,
        "--research-root",
        str(research_copy.parent),
        *([] if regenerate else ["--check-reports"]),
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "validation: FAIL" in result.stdout and "Traceback" not in result.stderr


def test_round5_public_entry_point_checks_existing_reports(
    research_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = SCRIPT
    spec = importlib.util.spec_from_file_location("atlas_research_round5", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(script), "--research-root", str(research_copy.parent), "--check-reports"],
    )
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    fields, rows = module.load(research_copy / "research_reactor_enrichment_round5.tsv")
    assert (fields, rows) == read_table(research_copy / "research_reactor_enrichment_round5.tsv")
    module.main()
    assert before == {name: (research_copy / name).read_bytes() for name in REPORTS}


def test_round5_runs_canonical_generator_for_alternate_data_root(
    research_copy: Path,
) -> None:
    (research_copy / "generate_gap_report.py").unlink()
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validation: PASS" in result.stdout


@pytest.mark.parametrize(
    "relative",
    [
        "research_reactors.tsv",
        "enrichment/research_reactor_enrichment.tsv",
        "enrichment_round2/research_reactor_enrichment_round2.tsv",
        "enrichment_round3/research_reactor_enrichment_round3.tsv",
        "enrichment_round4/research_reactor_enrichment_round4.tsv",
    ],
)
def test_round5_preserves_each_immutable_input(research_copy: Path, relative: str) -> None:
    path = research_copy.parent / relative
    path.write_bytes(path.read_bytes() + b"\n")
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "immutable input changed" in result.stdout and "Traceback" not in result.stderr


def test_round5_refuses_changes_without_a_requested_gap(research_copy: Path) -> None:
    path = research_copy / "research_reactor_enrichment_round5.tsv"
    fields, rows = read_table(path)
    for field in fields[1:14]:
        rows[0][field] = ""
    rows[0]["name"] = rows[0]["stable_id"] + " corrected name"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--research-root", str(research_copy.parent))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "does not fill a requested priority gap" in result.stdout
    assert "Traceback" not in result.stderr


def test_round5_public_missing_predicate_matches_actual_type_gaps(
    research_copy: Path,
) -> None:
    spec = importlib.util.spec_from_file_location("atlas_research_round5_missing", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = read_table(research_copy.parent / "research_reactors.tsv")[1]
    generic = next(r for r in rows if r["reactor_type"].lower() == "research reactor")
    assert module.is_missing("reactor_type", generic["reactor_type"])


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf", "1e308", "3600.0001"])
def test_round5_invalid_report_deadline_preserves_inputs(research_copy: Path, timeout: str) -> None:
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


def test_round5_actual_reporter_timeout_preserves_existing_reports(
    research_copy: Path,
) -> None:
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    source = research_copy / "research_reactor_enrichment_round5.tsv"
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


def test_round5_documented_upper_deadline_runs_real_reporter(
    research_copy: Path,
) -> None:
    """Accept the inclusive supported wait without changing original reports."""
    before = {name: (research_copy / name).read_bytes() for name in REPORTS}
    source = research_copy / "research_reactor_enrichment_round5.tsv"
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
