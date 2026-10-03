# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_company_depth8_review.py

"""Verify actual priority history, exact identities and dated field-source associations."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table

ROUND = ROOT / "metadata/company_audit/depth_round8"
INPUTS = ROUND / "reviewed_inputs"
SCRIPT = ROUND / "review.py"


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate_name",
        "blank_name",
        "duplicate_id",
        "blank_id",
        "priority_negative",
        "priority_text",
        "source_row_zero",
        "source_row_text",
        "ineligible",
        "swapped_rank",
        "record_id",
    ],
)
def test_actual_full_matrix_refuses_identity_and_ranking_damage(
    tmp_path: Path, damage: str
) -> None:
    path = tmp_path / "matrix.tsv"
    fields, rows = read_table(ROUND.parent / "depth_round4/gap_matrix.tsv")
    if damage == "duplicate_name":
        rows[1]["organization"] = rows[0]["organization"]
    elif damage == "blank_name":
        rows[0]["organization"] = " "
    elif damage == "duplicate_id":
        rows[1]["record_id"] = rows[0]["record_id"]
    elif damage == "blank_id":
        rows[0]["record_id"] = " "
    elif damage.startswith("priority"):
        rows[0]["priority_score"] = "-1" if damage.endswith("negative") else "invalid"
    elif damage.startswith("source_row"):
        rows[0]["source_row"] = "0" if damage.endswith("zero") else "invalid"
    elif damage == "ineligible":
        for row in rows:
            row["gap_fields"] = "source_date"
    else:
        row = next(row for row in rows if row["organization"] == "NearStar Fusion")
        row["priority_score" if damage == "swapped_rank" else "record_id"] = (
            "0" if damage == "swapped_rank" else "AUD-NO-MATCH"
        )
    write_table(path, fields, rows)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--gap-matrix", str(path))
    assert result.returncode == 1 and "REVIEW FAILED" in result.stdout
    assert path.read_bytes() == before and "Traceback" not in result.stderr


@pytest.mark.parametrize("layer", ["depth_round4", "depth_round5", "depth_round6", "depth_round7"])
@pytest.mark.parametrize(
    "damage",
    [
        "header",
        "empty",
        "duplicate",
        "blank",
        "overlap",
        "unknown",
        "record_id",
        "selected",
        "missing",
    ],
)
def test_complete_actual_history_refuses_drift(tmp_path: Path, layer: str, damage: str) -> None:
    history = tmp_path / "history"
    layers = ["depth_round4", "depth_round5", "depth_round6", "depth_round7"]
    for name in layers:
        (history / name).mkdir(parents=True)
        shutil.copy2(
            ROUND.parent / name / "enrichment_overlays.tsv",
            history / name / "enrichment_overlays.tsv",
        )
    path = history / layer / "enrichment_overlays.tsv"
    fields, rows = read_table(path)
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage == "duplicate":
        rows.append(rows[0].copy())
    elif damage == "blank":
        rows[0]["organization"] = " "
    elif damage == "overlap":
        other = next(name for name in layers if name != layer)
        rows[0]["organization"] = read_table(history / other / "enrichment_overlays.tsv")[1][0][
            "organization"
        ]
        _, matrix = read_table(ROUND.parent / "depth_round4/gap_matrix.tsv")
        rows[0]["source_record_id"] = next(
            row["record_id"] for row in matrix if row["organization"] == rows[0]["organization"]
        )
    elif damage == "unknown":
        rows[0]["organization"] = "Unknown organisation"
    elif damage == "record_id":
        rows[0]["source_record_id"] = "AUD-NO-MATCH"
    elif damage == "selected":
        rows[0]["organization"] = "NearStar Fusion"
        rows[0]["source_record_id"] = "AUD-024"
    write_table(path, fields, rows)
    if damage == "missing":
        path.unlink()
    result = run_cli(SCRIPT, "--history-directory", str(history))
    assert result.returncode == 1 and "REVIEW FAILED" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("column", read_table(INPUTS / "reviewed_profiles.tsv")[0])
def test_blank_actual_profile_fields_are_refused(tmp_path: Path, column: str) -> None:
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / "reviewed_profiles.tsv"
    fields, rows = read_table(path)
    rows[0][column] = " "
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input-directory", str(source))
    assert result.returncode == 1 and "REVIEW FAILED" in result.stdout


@pytest.mark.parametrize(
    "table,column,value",
    [
        ("reviewed_profiles.tsv", "source_record_id", "AUD-NO-MATCH"),
        ("reviewed_profiles.tsv", "match_rule", "fuzzy match"),
        ("reviewed_profiles.tsv", "audit_date", "2026-09-28"),
        ("reviewed_profiles.tsv", "fields_enriched", "fuel_cycle"),
        ("reviewed_profiles.tsv", "source_ids", "N01;N01;N03"),
        ("reviewed_profiles.tsv", "source_dates", "undated"),
        ("reviewed_profiles.tsv", "enriched_independent_urls", "https://example.org/unbound"),
        ("reviewed_sources.tsv", "source_id", "N02"),
        ("reviewed_sources.tsv", "organization", "Longview Fusion Energy Systems"),
        ("reviewed_sources.tsv", "accessed_on", "2026-09-28"),
        ("field_source_bindings.tsv", "field", "unbound-field"),
        ("field_source_bindings.tsv", "source_ids", "not-registered"),
        ("field_source_bindings.tsv", "source_ids", "L02"),
        ("field_source_bindings.tsv", "source_ids", "N01;N01"),
        ("field_source_bindings.tsv", "reviewed_on", "2026-09-28"),
    ],
)
def test_actual_provenance_refuses_changed_association(
    tmp_path: Path, table: str, column: str, value: str
) -> None:
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / table
    fields, rows = read_table(path)
    rows[0][column] = value
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input-directory", str(source))
    assert result.returncode == 1 and "REVIEW FAILED" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("column", read_table(INPUTS / "reviewed_sources.tsv")[0])
def test_blank_actual_source_provenance_is_refused(tmp_path: Path, column: str) -> None:
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / "reviewed_sources.tsv"
    fields, rows = read_table(path)
    rows[0][column] = " "
    write_table(path, fields, rows)
    assert run_cli(SCRIPT, "--input-directory", str(source)).returncode == 1


@pytest.mark.parametrize(
    "table,column",
    [
        ("reviewed_sources.tsv", "url"),
        ("reviewed_profiles.tsv", "enriched_official_url"),
        ("reviewed_profiles.tsv", "enriched_independent_urls"),
    ],
)
@pytest.mark.parametrize(
    "url",
    [
        "http://example.org/",
        "https:///missing-host",
        "https://user@example.org/",
        "https://:password@example.org/",
        "https://[",
    ],
)
def test_bad_source_or_profile_urls_are_refused(
    tmp_path: Path, table: str, column: str, url: str
) -> None:
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / table
    fields, rows = read_table(path)
    rows[0][column] = url
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input-directory", str(source))
    assert (result.returncode == 1 and "HTTPS" in result.stdout) or (
        result.returncode == 1 and "IPv6" in result.stdout
    )
    assert "Traceback" not in result.stderr


def test_extra_unassociated_actual_source_cannot_be_admitted(tmp_path: Path) -> None:
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / "reviewed_sources.tsv"
    fields, rows = read_table(path)
    extra = rows[0].copy()
    extra.update(source_id="UNASSOCIATED", organization="Unknown organisation")
    rows.append(extra)
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input-directory", str(source))
    assert result.returncode == 1 and "unassociated source" in result.stdout


def test_actual_profile_selection_order_is_required(tmp_path: Path) -> None:
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    path = source / "reviewed_profiles.tsv"
    fields, rows = read_table(path)
    rows[0], rows[1] = rows[1], rows[0]
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--input-directory", str(source), optimize=True)
    assert result.returncode == 1 and "deterministic rule" in result.stdout
