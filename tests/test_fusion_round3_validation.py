# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — fusion round-3 validation conformance

"""Validate genuine exact-ID overlays and their actual generated completeness reports."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from ._fusion_layers import DIRECTORY, copy_fusion_layers
from .conftest import load_module

SCRIPT = DIRECTORY / "enrichment_round3/validate_enrichment_round3.py"


@pytest.mark.parametrize("optimize", [False, True])
def test_public_validation_writes_separate_reports_and_preserves_every_input(
    tmp_path: Path, optimize: bool
) -> None:
    """The original validator and child generator honour an explicit report directory."""
    source = tmp_path / "inputs"
    source.mkdir()
    copy_fusion_layers(source)
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.rglob("*.tsv")}
    reports = tmp_path / "reports"
    result = run_cli(
        SCRIPT,
        "--fusion-root",
        str(source),
        "--base-selection",
        "public",
        "--report-root",
        str(reports),
        optimize=optimize,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "157 effective records" in result.stdout
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before} == before
    for name in ("gap_report_summary.tsv", "gap_report_by_country.tsv", "GAP_REPORT.md"):
        assert (reports / name).read_bytes() == (SCRIPT.parent / name).read_bytes()


@pytest.mark.parametrize("optimize", [False, True])
def test_child_report_failure_has_fixed_output_without_interpreter_details(
    tmp_path: Path, optimize: bool
) -> None:
    """Actual child I/O failure cannot forward exception text through the validator."""
    source = tmp_path / "inputs"
    source.mkdir()
    copy_fusion_layers(source)
    reports = tmp_path / "CALLER_REPORT_SENTINEL"
    reports.write_text("preserve")
    result = run_cli(
        SCRIPT,
        "--fusion-root",
        str(source),
        "--report-root",
        str(reports),
        optimize=optimize,
    )
    assert result.returncode == 1
    assert result.stdout == "FAIL: source inputs or report outputs are invalid or unavailable\n"
    assert not result.stderr and reports.read_text() == "preserve"


@pytest.mark.parametrize("optimize", [False, True])
def test_registry_observation_date_refuses_with_its_specific_failure(
    tmp_path: Path, optimize: bool
) -> None:
    """An altered registry date reaches the date guard before any report is written."""
    copy_fusion_layers(tmp_path)
    path = tmp_path / "enrichment_round3/source_registry.tsv"
    fields, rows = read_table(path)
    rows[0]["retrieved_date"] = "2000-01-01"
    write_table(path, fields, rows)
    result = run_cli(
        SCRIPT,
        "--fusion-root",
        str(tmp_path),
        "--base-selection",
        "public",
        optimize=optimize,
    )
    assert result.returncode == 1
    assert "wrong source-registry retrieval date" in result.stdout
    assert not result.stderr and not (tmp_path / "enrichment_round3/GAP_REPORT.md").exists()


def test_actual_round3_validation(tmp_path: Path) -> None:
    """The complete layer passes and its generated counts match the published report."""
    copy_fusion_layers(tmp_path)
    for optimize in (False, True):
        result = run_cli(SCRIPT, "--fusion-root", str(tmp_path), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "157 effective records" in result.stdout
        assert (tmp_path / "enrichment_round3/gap_report_summary.tsv").read_bytes() == (
            DIRECTORY / "enrichment_round3/gap_report_summary.tsv"
        ).read_bytes()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stable_id", ""),
        ("stable_id", "absent-from-base"),
        ("retrieved_date", ""),
        ("source_url", ""),
        ("source_role", ""),
        ("license", ""),
        ("verification_evidence_notes", ""),
        ("source_url", "https://[invalid"),
        ("source_url", "file:///source"),
        ("first_operation_date", "2026-02-30"),
        ("last_operation_date", "yesterday"),
        ("latitude", "91"),
        ("longitude", "181"),
        ("latitude", "unknown"),
        ("latitude", "0"),
        ("longitude", "0"),
    ],
)
def test_round3_invalid_facts_refuse(tmp_path: Path, field: str, value: str) -> None:
    """Malformed copied facts refuse before report generation even with -O."""
    copy_fusion_layers(tmp_path)
    path = tmp_path / "enrichment_round3/enrichment_round3.tsv"
    fields, rows = read_table(path)
    rows[0].update(latitude="", longitude="")
    rows[0][field] = value
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--fusion-root", str(tmp_path), optimize=True)
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "enrichment_round3/GAP_REPORT.md").exists()


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate",
        "header",
        "truncated",
        "extra",
        "empty_file",
        "missing",
        "registry_exclusion",
        "registry_date",
        "base_hash",
        "generator_input",
        "coordinate_count",
        "effective_count",
    ],
)
def test_round3_integrity_and_generated_count_refuse(tmp_path: Path, corruption: str) -> None:
    """Read failures, exclusion provenance, source pins and regenerated metrics are enforced."""
    copy_fusion_layers(tmp_path)
    path = tmp_path / "enrichment_round3/enrichment_round3.tsv"
    fields, rows = read_table(path)
    if corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "header":
        fields = fields[::-1]
    elif corruption == "base_hash":
        base = tmp_path / "fusion_facilities.tsv"
        base.write_bytes(base.read_bytes() + b"\n")
    elif corruption in {"registry_exclusion", "registry_date"}:
        registry_path = tmp_path / "enrichment_round3/source_registry.tsv"
        columns, registry = read_table(registry_path)
        if corruption == "registry_exclusion":
            registry = [row for row in registry if row["source_id"] != "excluded-iaea-fusdis"]
        else:
            registry[0]["retrieved_date"] = ""
        write_table(registry_path, columns, registry)
    elif corruption == "generator_input":
        (tmp_path / "enrichment/enrichment.tsv").unlink()
    elif corruption == "coordinate_count":
        next(row for row in rows if row["first_operation_date"])["first_operation_date"] = ""
    elif corruption == "effective_count":
        new_path = tmp_path / "enrichment/new_facilities.tsv"
        columns, new = read_table(new_path)
        patch_ids = {row["stable_id"] for row in rows}
        _, prior = read_table(tmp_path / "enrichment_round2/enrichment_round2.tsv")
        patch_ids.update(row["stable_id"] for row in prior)
        target = next(row for row in new if row["stable_id"] not in patch_ids)
        new.remove(target)
        write_table(new_path, columns, new)
    write_table(path, fields, rows)
    if corruption == "truncated":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "empty_file":
        path.write_bytes(b"")
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, "--fusion-root", str(tmp_path))
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("date", ["1957", "1957-09", "1957-09-01"])
def test_round3_calendar_precision(tmp_path: Path, date: str) -> None:
    """A field with an existing date can retain any allowed source precision."""
    copy_fusion_layers(tmp_path)
    path = tmp_path / "enrichment_round3/enrichment_round3.tsv"
    fields, rows = read_table(path)
    next(row for row in rows if row["first_operation_date"])["first_operation_date"] = date
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, "--fusion-root", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_round3_validator_public_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The imported entry point runs the same native validation and actual generator."""
    copy_fusion_layers(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--fusion-root", str(tmp_path)])
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_fusion_round3_validator")
    module.main()
