# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — historical taxonomy audit producer conformance

"""Reproduce all original triage while protecting the twelve later audit rows."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/taxonomy_audit/build_audit.py"
SNAPSHOT = SCRIPT.with_name("input-taxonomy-snapshot.tsv")
CHECKS = SCRIPT.with_name("url_checks.json")
OUTPUTS = ("audit.tsv", "summary.json")


def test_complete_historical_projection_preserves_all_later_editorial_rows(tmp_path: Path) -> None:
    paths = [SNAPSHOT, CHECKS, *[SCRIPT.with_name(name) for name in OUTPUTS]]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    fields, maintained = read_table(SCRIPT.with_name("audit.tsv"))
    by_id = {row["id"]: row for row in maintained}
    ordered = [by_id[row["id"]] for row in read_table(SNAPSHOT)[1]]
    golden = tmp_path / "historical.tsv"
    write_table(golden, fields, ordered)
    assert len(ordered) == 123 and len(maintained) == 135
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(SCRIPT, "--output-directory", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (output / "audit.tsv").read_bytes() == golden.read_bytes()
        assert (output / "summary.json").read_bytes() == SCRIPT.with_name(
            "summary.json"
        ).read_bytes()
        assert json.loads(result.stdout)["misassigned_source_entries"] == 24
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )


@pytest.mark.parametrize(
    "damage",
    [
        "header",
        "no_header",
        "empty",
        "short",
        "extra",
        "quote",
        "utf8",
        "missing",
        "duplicate",
        "blank_id",
        "padded_id",
        "name",
        "domain",
        "family",
        "kind",
        "source_urls",
        "blank_reference",
    ],
)
def test_bad_complete_snapshot_preserves_existing_output(tmp_path: Path, damage: str) -> None:
    path = tmp_path / "snapshot.tsv"
    fields, rows = read_table(SNAPSHOT)
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage == "duplicate":
        rows.append(rows[0].copy())
    elif damage == "blank_id":
        rows[0]["id"] = ""
    elif damage == "padded_id":
        rows[0]["id"] += " "
    elif damage in {"name", "domain", "family", "kind", "source_urls"}:
        rows[0][damage] = " "
    elif damage == "blank_reference":
        rows[0]["source_urls"] += " | "
    write_table(path, fields, rows)
    if damage == "no_header":
        path.write_text("")
    elif damage == "short":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif damage == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif damage == "quote":
        path.write_text("\t".join(fields) + '\n"unclosed')
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    output = tmp_path / "output"
    output.mkdir()
    for name in OUTPUTS:
        shutil.copy2(SCRIPT.with_name(name), output / name)
    before = {output / name: (output / name).read_bytes() for name in OUTPUTS}
    result = run_cli(SCRIPT, "--input", str(path), "--output-directory", str(output), optimize=True)
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and all(
        path.read_bytes() == data for path, data in before.items()
    )


@pytest.mark.parametrize(
    "damage",
    [
        "version",
        "envelope_keys",
        "count",
        "boolean_count",
        "records_object",
        "empty",
        "root_number",
        "root_null",
        "record_scalar",
        "url_missing",
        "url_type",
        "url_blank",
        "url_padded",
        "duplicate",
        "access_type",
        "access_blank",
        "title_type",
        "status_null",
        "status_bool",
        "status_low",
        "status_high",
        "status_text",
        "json",
        "utf8",
        "missing",
        "missing_observation",
    ],
)
def test_bad_saved_url_checks_refuse_before_output(tmp_path: Path, damage: str) -> None:
    path = tmp_path / "checks.json"
    document = json.loads(CHECKS.read_text())
    records = document["records"]
    if damage == "version":
        document["schema_version"] = "2.0.0"
    elif damage == "envelope_keys":
        document["extra"] = "unexpected"
    elif damage == "count":
        document["record_count"] -= 1
    elif damage == "boolean_count":
        document["record_count"] = True
    elif damage == "records_object":
        document["records"] = {}
    elif damage == "empty":
        document["records"] = []
        document["record_count"] = 0
    elif damage == "root_number":
        document = 68
    elif damage == "root_null":
        document = None
    elif damage == "record_scalar":
        records[0] = "not a record"
    elif damage == "url_missing":
        records[0].pop("url")
    elif damage == "url_type":
        records[0]["url"] = 42
    elif damage == "url_blank":
        records[0]["url"] = " "
    elif damage == "url_padded":
        records[0]["url"] += " "
    elif damage == "duplicate":
        records[1]["url"] = records[0]["url"]
    elif damage == "access_type":
        records[0]["access"] = None
    elif damage == "access_blank":
        records[0]["access"] = " "
    elif damage == "title_type":
        records[0]["title"] = 42
    elif damage == "status_null":
        records[0]["status"] = None
    elif damage == "status_bool":
        records[0]["status"] = True
    elif damage == "status_low":
        records[0]["status"] = 99
    elif damage == "status_high":
        records[0]["status"] = 600
    elif damage == "status_text":
        records[0]["status"] = "404"
    elif damage == "missing_observation":
        url = read_table(SNAPSHOT)[1][0]["source_urls"].split(" | ")[0]
        document["records"] = [record for record in records if record["url"] != url]
        document["record_count"] = len(document["records"])
    path.write_text(json.dumps(document))
    if damage == "json":
        path.write_text("{")
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    output = tmp_path / "output"
    result = run_cli(
        SCRIPT, "--checks", str(path), "--output-directory", str(output), optimize=True
    )
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert not output.exists() and "Traceback" not in result.stderr


def test_historical_bare_checks_and_absent_optional_title_are_supported(tmp_path: Path) -> None:
    records = json.loads(CHECKS.read_text())["records"]
    for record in records:
        if not record["title"]:
            record.pop("title")
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(records))
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--checks", str(path), "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "summary.json").read_bytes() == SCRIPT.with_name("summary.json").read_bytes()
    expected = {row["id"]: row for row in read_table(SCRIPT.with_name("audit.tsv"))[1]}
    assert all(expected[row["id"]] == row for row in read_table(output / "audit.tsv")[1])


@pytest.mark.parametrize("damage", ["empty", "shape", "duplicate", "missing_check"])
def test_public_audit_rejects_incomplete_actual_snapshot_or_observations(damage: str) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_audit_builder")
    rows = module.read_snapshot(SNAPSHOT)
    checks = module.read_checks(CHECKS)
    if damage == "empty":
        rows.clear()
        diagnostic = "schema mismatch or empty"
    elif damage == "shape":
        rows[0].pop("name")
        diagnostic = "schema mismatch or empty"
    elif damage == "duplicate":
        checks.append(checks[0].copy())
        diagnostic = "duplicate checked URL"
    else:
        checks.clear()
        diagnostic = "no URL check"
    with pytest.raises(ValueError, match=diagnostic):
        module.build_audit(rows, checks)


@pytest.mark.parametrize("name", OUTPUTS)
def test_maintained_audit_is_protected_through_output_symlinks(tmp_path: Path, name: str) -> None:
    original = SCRIPT.with_name(name)
    before = original.read_bytes()
    (tmp_path / name).symlink_to(original)
    result = run_cli(SCRIPT, "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "maintained merged audit" in result.stdout
    assert original.read_bytes() == before


def test_default_maintained_directory_and_directory_alias_are_refused(tmp_path: Path) -> None:
    alias = tmp_path / "maintained"
    alias.symlink_to(SCRIPT.parent, target_is_directory=True)
    for output in (SCRIPT.parent, alias):
        result = run_cli(SCRIPT, "--output-directory", str(output))
        assert result.returncode == 1 and "maintained merged audit" in result.stdout


@pytest.mark.parametrize("source", ["--input", "--checks"])
@pytest.mark.parametrize("name", OUTPUTS)
def test_historical_output_cannot_replace_either_source(
    tmp_path: Path, source: str, name: str
) -> None:
    path = tmp_path / name
    shutil.copy2(SNAPSHOT if source == "--input" else CHECKS, path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, source, str(path), "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "cannot replace audit inputs" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize("failure", ["directory", "audit_file", "summary_file"])
def test_real_output_io_failures_are_controlled(tmp_path: Path, failure: str) -> None:
    output = tmp_path / "output"
    if failure == "directory":
        output.write_text("existing file\n")
    else:
        output.mkdir()
        (output / ("audit.tsv" if failure == "audit_file" else "summary.json")).mkdir()
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr


def test_explicit_output_is_required_to_avoid_destructive_historical_default() -> None:
    result = run_cli(SCRIPT)
    assert result.returncode == 2 and "--output-directory" in result.stderr
    assert "Traceback" not in result.stderr


def test_import_and_public_main_use_actual_inputs_without_mutating_maintained_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = [SNAPSHOT, CHECKS, *[SCRIPT.with_name(name) for name in OUTPUTS]]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_audit_builder")
    audit, summary = module.build_audit(module.read_snapshot(SNAPSHOT), module.read_checks(CHECKS))
    assert len(audit) == 123 and summary == json.loads(SCRIPT.with_name("summary.json").read_text())
    by_id = {row["id"]: row for row in audit}
    assert module.SPH in by_id["spheromak"]["verified_source_url"]
    assert module.FUSION in by_id["field-reversed-configuration-frc"]["verified_source_url"]
    assert module.ZICF in by_id["z-pinch-driven-indirect-icf"]["verified_source_url"]
    assert by_id["polywell"]["classification_ok"] == "evidence-scope-review"
    assert (
        by_id["cavitation-bubble-fusion"]["classification_ok"]
        == "classification-supported-claim-contested"
    )
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-directory", str(tmp_path / "output")])
    assert module.main() == 0
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )


def test_non_electrolysis_404_and_just_a_moment_are_observations_not_endorsement(
    tmp_path: Path,
) -> None:
    records = json.loads(CHECKS.read_text())
    row = read_table(SNAPSHOT)[1][0]
    url = row["source_urls"].split(" | ")[0]
    for record in records["records"]:
        if record["url"] == url:
            record["status"] = 404
            record["title"] = "Just a moment"
    path = tmp_path / "checks.json"
    path.write_text(json.dumps(records))
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--checks", str(path), "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    audit = {record["id"]: record for record in read_table(output / "audit.tsv")[1]}
    assert "Broken source URL (HTTP 404)" in audit[row["id"]]["issue"]
    assert "Access challenge is not substantive article content" in audit[row["id"]]["issue"]
    assert audit[row["id"]]["verified_source_url"] == ""
