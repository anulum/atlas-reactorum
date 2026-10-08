# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research round-4 completeness report generation

"""Check generated reports against the preserved actual research catalogue and overlays."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "enrichment_round4/generate_completeness_report.py"
REPORTS = (
    "field_completeness_by_country.tsv",
    "field_completeness_summary.tsv",
    "field_completeness_report.md",
)


@pytest.fixture
def research_catalogue(tmp_path: Path) -> Path:
    """Copy the complete research catalogue for isolated report generation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owned parent directory for the copied base catalogue and all overlays.

    Returns
    -------
    pathlib.Path
        Complete copied research root with interpreter caches omitted.
    """
    return shutil.copytree(
        DIRECTORY, tmp_path / "research", ignore=shutil.ignore_patterns("__pycache__")
    )


def test_actual_round4_completeness_report_bytes(research_catalogue: Path) -> None:
    """Reproduce all three canonical completeness reports normally and under -O."""
    output = research_catalogue / "enrichment_round4"
    expected = {name: (SCRIPT.parent / name).read_bytes() for name in REPORTS}
    for name in REPORTS:
        (output / name).unlink()
    for optimized in (False, True):
        result = run_cli(
            SCRIPT,
            "--research-root",
            str(research_catalogue),
            "--output-dir",
            str(output),
            optimize=optimized,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert expected == {name: (output / name).read_bytes() for name in REPORTS}


def test_round4_completeness_country_and_placeholder_semantics(
    research_catalogue: Path,
) -> None:
    """Count unknown-country placeholders at both stages and reconcile all 14 field-summary rows."""
    output = research_catalogue / "enrichment_round4"
    _, original_countries = read_table(output / REPORTS[0])
    original_unknown = {
        r["stage"]: r for r in original_countries if r["country"] == "(unknown country)"
    }
    base = research_catalogue / "research_reactors.tsv"
    fields, rows = read_table(base)
    overlays = [
        research_catalogue / "enrichment/research_reactor_enrichment.tsv",
        research_catalogue / "enrichment_round2/research_reactor_enrichment_round2.tsv",
        research_catalogue / "enrichment_round3/research_reactor_enrichment_round3.tsv",
        output / "research_reactor_enrichment_round4.tsv",
    ]
    overlay_ids = {r["stable_id"] for path in overlays for r in read_table(path)[1]}
    row = next(r for r in rows if r["stable_id"] not in overlay_ids and bool(r["country"]))
    row.update(
        country="",
        status="unknown",
        reactor_type="Research Reactor",
        thermal_power_mw="unknown",
        operator="",
        purpose="unknown",
        first_criticality="",
        shutdown_date="",
    )
    write_table(base, fields, rows)
    result = run_cli(
        SCRIPT, "--research-root", str(research_catalogue), "--output-dir", str(output)
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _, country_rows = read_table(output / REPORTS[0])
    unknown = [r for r in country_rows if r["country"] == "(unknown country)"]
    assert len(unknown) == 2
    assert {r["stage"] for r in unknown} == {"after_round3", "after_round4"}
    assert all(
        int(r[k]) == int(original_unknown.get(r["stage"], {}).get(k, "0")) + 1
        for r in unknown
        for k in r
        if k not in {"stage", "country"}
    )
    _, summary = read_table(output / REPORTS[1])
    assert len(summary) == 14
    assert all(int(r["records"]) == len(rows) for r in summary)
    assert all(int(r["known"]) + int(r["unknown_or_unpopulated"]) == len(rows) for r in summary)


def test_round4_completeness_public_api_and_entrypoint(
    research_catalogue: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reconcile public aggregation with source counts and reproduce report bytes through main."""
    output = research_catalogue / "enrichment_round4"
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_research_round4_reports")
    base = module.load(research_catalogue / "research_reactors.tsv")
    assert base == read_table(research_catalogue / "research_reactors.tsv")[1]
    patches = [research_catalogue / path.relative_to(DIRECTORY) for path in module.ROUND_FILES]
    effective = module.effective(base, patches)
    aggregates = module.aggregate(effective)
    _, summary = read_table(output / REPORTS[1])
    assert sum(country["records"] for country in aggregates.values()) == len(base)
    for row in summary:
        if row["stage"] == "after_round4":
            assert sum(country[row["field"]] for country in aggregates.values()) == int(
                row["unknown_or_unpopulated"]
            )
    before = {name: (output / name).read_bytes() for name in REPORTS}
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--research-root",
            str(research_catalogue),
            "--output-dir",
            str(output),
        ],
    )
    module.main()
    assert before == {name: (output / name).read_bytes() for name in REPORTS}
