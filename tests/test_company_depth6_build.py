# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — sixth company depth producer conformance

"""Generate actual curated depth outputs and verify previous-matrix refusal boundaries."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/depth_round6/build.py"
MATRIX = SCRIPT.parent.parent / "depth_round4/gap_matrix.tsv"
OUTPUTS = ["enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv"]


def test_real_curated_outputs_reproduce_every_byte(tmp_path: Path) -> None:
    before = {p: p.read_bytes() for p in [MATRIX, *[SCRIPT.with_name(name) for name in OUTPUTS]]}
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(SCRIPT, "--output-directory", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "10 overlays, 30 sources and 10 closure rows" in result.stdout
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
        "priority",
        "record_id",
        "gaps",
    ],
)
def test_bad_previous_matrix_preserves_existing_outputs(tmp_path: Path, damage: str) -> None:
    path = tmp_path / "previous.tsv"
    fields, rows = read_table(MATRIX)
    target = next(row for row in rows if row["organization"] == "Helion Energy")
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
    elif damage == "priority":
        target["priority_score"] = "4"
    elif damage == "gaps":
        target["gap_fields"] = "fuel_cycle;source_date;unavailable_measurement"
    elif damage == "record_id":
        target["record_id"] = "AUD-UNKNOWN"
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
    diagnostic = {
        "header": "header mismatch",
        "empty": "empty or malformed",
        "short": "empty or malformed",
        "extra": "empty or malformed",
        "duplicate": "duplicate or blank",
        "blank": "duplicate or blank",
        "target": "missing overlay target",
        "priority": "identity, score5 or fuel/date gaps",
        "record_id": "identity, score5 or fuel/date gaps",
        "gaps": "identity, score5 or fuel/date gaps",
    }
    if damage in diagnostic:
        assert diagnostic[damage] in result.stdout


@pytest.mark.parametrize(
    "damage",
    [
        "row_shape",
        "missing_row",
        "duplicate_target",
        "missing_target",
        "record_id",
        "priority",
        "gaps",
        "enriched_fuel",
        "enriched_dates",
    ],
)
def test_public_closure_derivation_refuses_damaged_reviewed_rows(damage: str) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth6_builder")
    fields, records = read_table(SCRIPT.with_name(OUTPUTS[0]))
    overlays = [[record[field] for field in fields] for record in records]
    old = module.read_matrix(MATRIX)
    diagnostic = ""
    if damage == "row_shape":
        overlays[0].pop()
        diagnostic = "row shape"
    elif damage == "missing_row":
        overlays.pop()
        diagnostic = "ten unique"
    elif damage == "duplicate_target":
        overlays[1] = overlays[0].copy()
        diagnostic = "ten unique"
    elif damage == "missing_target":
        old.pop(overlays[0][0])
        diagnostic = "missing overlay target"
    elif damage == "record_id":
        old[overlays[0][0]]["record_id"] = "AUD-UNKNOWN"
        diagnostic = "identity, score5 or fuel/date gaps"
    elif damage == "gaps":
        old[overlays[0][0]]["gap_fields"] = "fuel_cycle"
        diagnostic = "identity, score5 or fuel/date gaps"
    elif damage in {"enriched_fuel", "enriched_dates"}:
        field = "fuel_cycle" if damage == "enriched_fuel" else "source_dates"
        overlays[0][3] = ";".join(key for key in overlays[0][3].split(";") if key != field)
        diagnostic = "document both"
    else:
        old[overlays[0][0]]["priority_score"] = "4"
        diagnostic = "identity, score5 or fuel/date gaps"
    with pytest.raises(ValueError, match=diagnostic):
        module.build_closures(overlays, old)


@pytest.mark.parametrize("name", OUTPUTS)
def test_output_cannot_replace_previous_input_matrix(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    shutil.copy2(MATRIX, path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--gap-matrix", str(path), "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "output would replace previous matrix" in result.stdout
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
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth6_builder")
    fields, records = read_table(SCRIPT.with_name(OUTPUTS[0]))
    overlays = [[record[field] for field in fields] for record in records]
    closures = module.build_closures(overlays, module.read_matrix(MATRIX))
    cf, expected = read_table(SCRIPT.with_name(OUTPUTS[2]))
    assert closures == [[record[field] for field in cf] for record in expected]
    output = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-directory", str(output)])
    module.main()
    for name in OUTPUTS:
        assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
