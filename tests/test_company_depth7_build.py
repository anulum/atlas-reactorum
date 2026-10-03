# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — seventh company depth producer conformance

"""Exercise actual reviewed generation, previous-layer selection and refusal boundaries."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/depth_round7/build.py"
AUDIT = SCRIPT.parent.parent
MATRIX = AUDIT / "depth_round4/gap_matrix.tsv"
OUTPUTS = ["enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv"]
LAYERS = ["depth_round4", "depth_round5", "depth_round6"]


def test_real_curated_outputs_reproduce_every_byte(tmp_path: Path) -> None:
    inputs = [MATRIX, *[AUDIT / name / OUTPUTS[0] for name in LAYERS]]
    inputs.extend(SCRIPT.with_name(name) for name in [*OUTPUTS, "validation.json"])
    before = {p: p.read_bytes() for p in inputs}
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(SCRIPT, "--output-directory", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (
            "10 overlays, 30 sources, 10 closure rows; resolved 24 gap instances" in result.stdout
        )
        for name in OUTPUTS:
            assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
        check = run_cli(SCRIPT.with_name("validate.py"), "--directory", str(output))
        assert check.returncode == 0, check.stdout + check.stderr
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize(
    "damage",
    [
        "header",
        "empty",
        "short",
        "extra",
        "quote",
        "utf8",
        "missing",
        "duplicate",
        "blank",
        "target",
        "record_id",
        "negative_score",
        "zero_source_row",
        "nonnumeric",
        "rank_order",
        "tie_order",
        "eligibility",
    ],
)
def test_bad_previous_matrix_preserves_existing_outputs(tmp_path: Path, damage: str) -> None:
    path = tmp_path / "previous.tsv"
    fields, rows = read_table(MATRIX)
    target = next(row for row in rows if row["organization"] == "Marvel Fusion")
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage == "duplicate":
        rows.append(rows[0].copy())
    elif damage == "blank":
        rows[0]["organization"] = " "
    elif damage == "target":
        rows.remove(target)
    elif damage == "record_id":
        target["record_id"] = "AUD-UNKNOWN"
    elif damage == "negative_score":
        rows[-1]["priority_score"] = "-1"
    elif damage == "zero_source_row":
        rows[-1]["source_row"] = "0"
    elif damage == "nonnumeric":
        rows[-1]["priority_score"] = "NaN"
    elif damage == "rank_order":
        target["priority_score"] = "100"
    elif damage == "tie_order":
        target["source_row"] = "999999"
    elif damage == "eligibility":
        target["gap_fields"] = "source_date"
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
    output = tmp_path / "output"
    output.mkdir()
    for name in OUTPUTS:
        shutil.copy2(SCRIPT.with_name(name), output / name)
    before = {output / name: (output / name).read_bytes() for name in OUTPUTS}
    result = run_cli(
        SCRIPT, "--gap-matrix", str(path), "--output-directory", str(output), optimize=True
    )
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr
    assert all(p.read_bytes() == data for p, data in before.items())
    if damage in {"rank_order", "tie_order", "eligibility"}:
        assert "deterministic rule" in result.stdout
    elif damage in {"zero_source_row", "negative_score"}:
        assert "invalid previous matrix ranking" in result.stdout


@pytest.mark.parametrize("layer", LAYERS)
@pytest.mark.parametrize(
    "damage", ["header", "empty", "duplicate", "blank", "overlap", "selected", "missing"]
)
def test_damaged_actual_history_refuses_before_outputs(
    tmp_path: Path, layer: str, damage: str
) -> None:
    history = tmp_path / "history"
    for name in LAYERS:
        (history / name).mkdir(parents=True)
        shutil.copy2(AUDIT / name / OUTPUTS[0], history / name / OUTPUTS[0])
    path = history / layer / OUTPUTS[0]
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
        other = next(name for name in LAYERS if name != layer)
        rows[0]["organization"] = read_table(history / other / OUTPUTS[0])[1][0]["organization"]
    elif damage == "selected":
        rows[0]["organization"] = "Marvel Fusion"
    write_table(path, fields, rows)
    if damage == "missing":
        path.unlink()
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--history-directory", str(history), "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and not output.exists()
    if damage == "selected":
        assert "deterministic rule" in result.stdout
    elif damage == "overlap":
        assert "overlap across layers" in result.stdout


@pytest.mark.parametrize(
    "damage",
    ["row_shape", "missing_row", "duplicate", "target", "record_id", "selection", "incomplete"],
)
def test_public_closure_refusal_uses_complete_reviewed_tables(damage: str) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth7_builder")
    fields, records = read_table(SCRIPT.with_name(OUTPUTS[0]))
    overlays = [[record[field] for field in fields] for record in records]
    old = module.read_matrix(MATRIX)
    excluded = module.read_history(AUDIT)
    if damage == "row_shape":
        overlays[0].pop()
        diagnostic = "row shape"
    elif damage == "missing_row":
        overlays.pop()
        diagnostic = "ten unique"
    elif damage == "duplicate":
        overlays[1] = overlays[0].copy()
        diagnostic = "ten unique"
    elif damage == "target":
        old.pop(overlays[0][0])
        diagnostic = "missing overlay target"
    elif damage == "record_id":
        old[overlays[0][0]]["record_id"] = "AUD-UNKNOWN"
        diagnostic = "record identity"
    elif damage == "selection":
        overlays[0], overlays[1] = overlays[1], overlays[0]
        diagnostic = "deterministic rule"
    else:
        overlays[0][3] = ";".join(
            field for field in overlays[0][3].split(";") if field != "fuel_cycle"
        )
        diagnostic = "incomplete bounded closure"
    with pytest.raises(ValueError, match=diagnostic):
        module.build_closures(overlays, old, excluded)


@pytest.mark.parametrize("name", OUTPUTS)
def test_output_cannot_replace_previous_matrix(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    shutil.copy2(MATRIX, path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--gap-matrix", str(path), "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "replace a source input" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize("layer", LAYERS)
def test_output_cannot_replace_historical_overlay(tmp_path: Path, layer: str) -> None:
    history = tmp_path / "history"
    for name in LAYERS:
        (history / name).mkdir(parents=True)
        shutil.copy2(AUDIT / name / OUTPUTS[0], history / name / OUTPUTS[0])
    path = history / layer / OUTPUTS[0]
    before = path.read_bytes()
    result = run_cli(
        SCRIPT, "--history-directory", str(history), "--output-directory", str(path.parent)
    )
    assert result.returncode == 1 and "replace a source input" in result.stdout
    assert path.read_bytes() == before


def test_output_directory_failure_is_controlled(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.write_text("existing non-directory\n")
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr
    assert output.read_text() == "existing non-directory\n"


def test_public_derivation_and_main_use_actual_reviewed_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth7_builder")
    fields, records = read_table(SCRIPT.with_name(OUTPUTS[0]))
    overlays = [[record[field] for field in fields] for record in records]
    excluded = module.read_history(AUDIT)
    assert len(excluded) == 19
    closures = module.build_closures(overlays, module.read_matrix(MATRIX), excluded)
    cf, expected = read_table(SCRIPT.with_name(OUTPUTS[2]))
    assert closures == [[record[field] for field in cf] for record in expected]
    assert sum(int(row[5]) for row in closures) == 24
    output = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-directory", str(output)])
    module.main()
    for name in OUTPUTS:
        assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
