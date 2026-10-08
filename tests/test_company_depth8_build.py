# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_company_depth8_build.py

"""Exercise native product generation and preservation of all real source inputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table

ROUND = ROOT / "metadata/company_audit/depth_round8"
INPUTS = ROUND / "reviewed_inputs"
SCRIPT = ROUND / "build.py"

PRODUCTS = [
    "enrichment_overlays.tsv",
    "source_registry.tsv",
    "field_source_bindings.tsv",
    "gap_review.tsv",
]


def test_whole_native_products_reproduce_from_another_cwd(tmp_path: Path) -> None:
    """Reproduce four validated products from another cwd while preserving sources and limitations."""
    protected = [
        *INPUTS.glob("*.tsv"),
        *[
            ROUND.parent / name / "enrichment_overlays.tsv"
            for name in ["depth_round4", "depth_round5", "depth_round6", "depth_round7"]
        ],
    ]
    before = {path: path.read_bytes() for path in protected}
    for optimize in (False, True):
        output = tmp_path / f"output-{optimize}"
        result = run_cli(SCRIPT, "--output-directory", str(output), cwd=tmp_path, optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "10 overlays, 33 sources, 60 field associations" in result.stdout
        for name in PRODUCTS:
            assert (output / name).read_bytes() == (ROUND / name).read_bytes()
        assert not list(output.glob(".depth8-*"))
        checked = run_cli(ROUND / "validate.py", "--directory", str(output), cwd=tmp_path)
        assert checked.returncode == 0, checked.stdout + checked.stderr
        report = json.loads((output / "validation.json").read_text())
        assert (
            report["metadata_gap_fields_reviewed"] == 21
            and "not established" in report["physical_gap_closure"]
        )
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("name", PRODUCTS)
def test_matrix_alias_cannot_be_replaced(tmp_path: Path, name: str) -> None:
    """Reject every product destination aliasing the prior matrix without staging temporary files."""
    matrix = tmp_path / name
    shutil.copy2(ROUND.parent / "depth_round4/gap_matrix.tsv", matrix)
    before = matrix.read_bytes()
    result = run_cli(SCRIPT, "--gap-matrix", str(matrix), "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "replace a source input" in result.stdout
    assert matrix.read_bytes() == before and not list(tmp_path.glob(".depth8-*"))


@pytest.mark.parametrize(
    "kind", ["source_alias", "unrelated_symlink", "directory", "dangling_symlink"]
)
@pytest.mark.parametrize("name", PRODUCTS)
def test_nonregular_and_source_alias_targets_refuse_before_any_write(
    tmp_path: Path, name: str, kind: str
) -> None:
    """Refuse symlink or directory product targets without writing other products or changing a victim."""
    output = tmp_path / "output"
    output.mkdir()
    target = output / name
    victim = tmp_path / "victim.tsv"
    victim.write_text("owned original bytes\n")
    if kind == "source_alias":
        target.symlink_to(INPUTS / "reviewed_profiles.tsv")
    elif kind == "unrelated_symlink":
        target.symlink_to(victim)
    elif kind == "directory":
        target.mkdir()
    else:
        target.symlink_to(tmp_path / "nonexistent")
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert victim.read_text() == "owned original bytes\n"
    assert sorted(p.name for p in output.iterdir()) == [name]
    assert "Traceback" not in result.stderr


def test_output_directory_failure_preserves_existing_file(tmp_path: Path) -> None:
    """Fail an output-directory path occupied by a file while preserving that file."""
    target = tmp_path / "output"
    target.write_text("existing non-directory\n")
    result = run_cli(SCRIPT, "--output-directory", str(target))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert target.read_text() == "existing non-directory\n"


def test_malformed_review_does_not_create_output(tmp_path: Path) -> None:
    """Refuse mismatched reviewed identity before creating the output directory."""
    source = tmp_path / "inputs"
    shutil.copytree(INPUTS, source)
    fields, rows = read_table(source / "reviewed_profiles.tsv")
    rows[0]["source_record_id"] = "AUD-NO-MATCH"
    write_table(source / "reviewed_profiles.tsv", fields, rows)
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--input-directory", str(source), "--output-directory", str(output))
    assert result.returncode == 1 and not output.exists()


def test_atomic_replacement_keeps_hardlinked_real_input_intact(tmp_path: Path) -> None:
    """Replace a hardlinked product atomically without changing the real source inode contents."""
    import os

    output = tmp_path / "output"
    output.mkdir()
    source = INPUTS / "reviewed_sources.tsv"
    before = source.read_bytes()
    os.link(source, output / "gap_review.tsv")
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert source.read_bytes() == before
    assert (output / "gap_review.tsv").read_bytes() == (ROUND / "gap_review.tsv").read_bytes()
