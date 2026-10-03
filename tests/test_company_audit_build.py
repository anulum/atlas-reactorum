# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — company audit producer conformance

"""Generate the actual fifty-one-row review and its original deterministic summary."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/build_audit.py"
SOURCE = ROOT / "metadata/discovery_audit/fusion_companies_candidates.tsv"
OUTPUTS = ["audited_companies.tsv", "summary.json"]


def test_original_review_and_summary_are_byte_exact(tmp_path: Path) -> None:
    paths = [SOURCE, *[SCRIPT.with_name(name) for name in OUTPUTS]]
    before = {path: path.read_bytes() for path in paths}
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(SCRIPT, "--output-directory", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        for name in OUTPUTS:
            assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
            assert name in result.stdout
        check = run_cli(SCRIPT.with_name("validate.py"), "--input", str(output / OUTPUTS[0]))
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
        "case_duplicate",
        "blank",
        "punctuation",
        "padded",
    ],
)
def test_bad_discovery_preserves_existing_review_outputs(tmp_path: Path, damage: str) -> None:
    path = tmp_path / "discovery.tsv"
    fields, rows = read_table(SOURCE)
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage == "duplicate":
        rows.append(rows[0].copy())
    elif damage == "case_duplicate":
        rows[1]["company"] = rows[0]["company"].swapcase()
    elif damage == "blank":
        rows[0]["company"] = " "
    elif damage == "punctuation":
        rows[0]["company"] = "!!!"
    elif damage == "padded":
        rows[0]["company"] += " "
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
    result = run_cli(SCRIPT, "--input", str(path), "--output-directory", str(output), optimize=True)
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and all(
        p.read_bytes() == data for p, data in before.items()
    )


@pytest.mark.parametrize(
    "field", ["country", "approach", "claimed_milestones", "evidence_maturity"]
)
def test_blank_required_discovery_context_refuses_before_outputs(
    tmp_path: Path, field: str
) -> None:
    path = tmp_path / "discovery.tsv"
    fields, rows = read_table(SOURCE)
    rows[0][field] = " "
    write_table(path, fields, rows)
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--input", str(path), "--output-directory", str(output))
    assert result.returncode == 1 and "required discovery claim context" in result.stdout
    assert not output.exists() and "Traceback" not in result.stderr


@pytest.mark.parametrize("damage", ["empty", "row_shape", "duplicate", "padded", "blank_context"])
def test_public_projection_refuses_damaged_complete_discovery_records(damage: str) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_audit_builder")
    rows = read_table(SOURCE)[1]
    if damage == "empty":
        rows.clear()
        diagnostic = "schema mismatch or empty"
    elif damage == "row_shape":
        rows[0].pop("country")
        diagnostic = "schema mismatch or empty"
    elif damage == "duplicate":
        rows[1]["company"] = rows[0]["company"]
        diagnostic = "discovery identity"
    elif damage == "padded":
        rows[0]["company"] += " "
        diagnostic = "discovery identity"
    else:
        rows[0]["evidence_maturity"] = " "
        diagnostic = "required discovery claim context"
    with pytest.raises(ValueError, match=diagnostic):
        module.build_rows(rows)


@pytest.mark.parametrize("name", OUTPUTS)
def test_output_cannot_replace_discovery_input(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    shutil.copy2(SOURCE, path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--input", str(path), "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "replace discovery input" in result.stdout
    assert path.read_bytes() == before


def test_output_directory_failure_is_controlled(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.write_text("existing non-directory\n")
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and output.read_text() == "existing non-directory\n"


def test_public_derivation_summary_and_main_preserve_imported_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = [SOURCE, *[SCRIPT.with_name(name) for name in OUTPUTS]]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_audit_builder")
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
    candidates = module.read_candidates(SOURCE)
    rows = module.build_rows(candidates)
    assert rows == read_table(SCRIPT.with_name(OUTPUTS[0]))[1]
    assert module.summarize(rows) == json.loads(SCRIPT.with_name(OUTPUTS[1]).read_text())
    assert len(rows) == 51
    output = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-directory", str(output)])
    module.main()
    for name in OUTPUTS:
        assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
