# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — reviewed research-supplement merge conformance

"""Rebuild the preserved catalogue from its actual discovery and regulator records."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "scripts/merge_supplements.py"
CATALOGUE = DIRECTORY / "research_reactors.tsv"
SUPPLEMENT = DIRECTORY / "supplements/cnsc_official.tsv"


@pytest.fixture
def source_partition(tmp_path: Path) -> tuple[Path, Path]:
    fields, rows = read_table(CATALOGUE)
    supplement_fields, supplements = read_table(SUPPLEMENT)
    ids = {row["stable_id"] for row in supplements}
    base = [row for row in rows if row["stable_id"] not in ids]
    assert len(base) == 161 and len(supplements) == 11
    assert all(next(r for r in rows if r["stable_id"] == s["stable_id"]) == s for s in supplements)
    base_path, supplement_path = tmp_path / "base.tsv", tmp_path / "official.tsv"
    write_table(base_path, fields, base)
    write_table(supplement_path, supplement_fields, supplements)
    return base_path, supplement_path


def test_actual_supplement_merge_reproduces_catalogue(
    source_partition: tuple[Path, Path], tmp_path: Path
) -> None:
    base, supplement = source_partition
    source_hashes = {
        p: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (CATALOGUE, SUPPLEMENT, base, supplement)
    }
    output = tmp_path / "output.tsv"
    for optimized in (False, True):
        result = run_cli(
            SCRIPT, str(base), str(supplement), "--out", str(output), optimize=optimized
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "wrote 172 records" in result.stdout
        assert output.read_bytes() == CATALOGUE.read_bytes()
    assert source_hashes == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_hashes}
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize("target", ["base", "supplement"])
@pytest.mark.parametrize(
    "corruption",
    [
        "empty_file",
        "empty_table",
        "header",
        "truncated",
        "extra",
        "utf8",
        "quote",
        "blank_id",
        "whitespace_id",
        "duplicate_id",
        "missing",
    ],
)
def test_corrupt_merge_source_preserves_output(
    source_partition: tuple[Path, Path], tmp_path: Path, target: str, corruption: str
) -> None:
    base, supplement = source_partition
    path = base if target == "base" else supplement
    fields, rows = read_table(path)
    if corruption == "empty_table":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    elif corruption == "blank_id":
        rows[0]["stable_id"] = ""
    elif corruption == "whitespace_id":
        rows[0]["stable_id"] = " "
    elif corruption == "duplicate_id":
        rows.append(rows[0].copy())
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
    output = tmp_path / "output.tsv"
    output.write_bytes(CATALOGUE.read_bytes())
    before = output.read_bytes()
    result = run_cli(SCRIPT, str(base), str(supplement), "--out", str(output), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "merge: FAIL" in result.stderr and "Traceback" not in result.stderr
    assert output.read_bytes() == before
    assert not list(tmp_path.glob(".*.tmp"))


def test_duplicate_across_sources_preserves_output(
    source_partition: tuple[Path, Path], tmp_path: Path
) -> None:
    base, supplement = source_partition
    fields, rows = read_table(supplement)
    _, original = read_table(base)
    rows.append(original[0].copy())
    write_table(supplement, fields, rows)
    output = tmp_path / "output.tsv"
    output.write_bytes(CATALOGUE.read_bytes())
    result = run_cli(SCRIPT, str(base), str(supplement), "--out", str(output))
    assert result.returncode == 1 and "duplicate stable_id" in result.stderr
    assert output.read_bytes() == CATALOGUE.read_bytes()


def test_multiple_regulator_supplements_preserve_sort_and_licences(
    source_partition: tuple[Path, Path], tmp_path: Path
) -> None:
    base, supplement = source_partition
    fields, rows = read_table(supplement)
    second = tmp_path / "second.tsv"
    write_table(supplement, fields, rows[:5][::-1])
    write_table(second, fields, rows[5:][::-1])
    output = tmp_path / "output.tsv"
    result = run_cli(SCRIPT, str(base), str(second), str(supplement), "--out", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes() == CATALOGUE.read_bytes()


@pytest.mark.parametrize("destination", ["missing_parent", "directory"])
def test_output_failure_cleans_temporary_file(
    source_partition: tuple[Path, Path], tmp_path: Path, destination: str
) -> None:
    base, supplement = source_partition
    output = (
        tmp_path / "missing/output.tsv"
        if destination == "missing_parent"
        else tmp_path / "output.tsv"
    )
    if destination == "directory":
        output.mkdir()
        (output / "existing.tsv").write_bytes(CATALOGUE.read_bytes())
    result = run_cli(SCRIPT, str(base), str(supplement), "--out", str(output))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "merge: FAIL" in result.stderr and "Traceback" not in result.stderr
    if destination == "directory":
        assert (output / "existing.tsv").read_bytes() == CATALOGUE.read_bytes()
    else:
        assert not output.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_merge_can_safely_replace_selected_base(
    source_partition: tuple[Path, Path],
) -> None:
    base, supplement = source_partition
    result = run_cli(SCRIPT, str(base), str(supplement), "--out", str(base))
    assert result.returncode == 0, result.stdout + result.stderr
    assert base.read_bytes() == CATALOGUE.read_bytes()


def test_merge_public_read_and_default_output(
    source_partition: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base, supplement = source_partition
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_research_supplement_merge")
    assert module.read(base) == read_table(base)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), str(base), str(supplement)])
    monkeypatch.chdir(tmp_path)
    module.main()
    assert (tmp_path / "research_reactors.tsv").read_bytes() == CATALOGUE.read_bytes()
