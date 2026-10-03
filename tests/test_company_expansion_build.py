# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — first company expansion producer conformance

"""Generate actual discovery rows against the required original company audit."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/build_expansion.py"
AUDIT = SCRIPT.with_name("audited_companies.tsv")
OUTPUT = SCRIPT.with_name("expansion_candidates.tsv")


def test_actual_curated_expansion_is_byte_exact(tmp_path: Path) -> None:
    before = {
        path: path.read_bytes()
        for path in [AUDIT, OUTPUT, SCRIPT.with_name("expansion_validation.json")]
    }
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}/expansion.tsv"
        result = run_cli(SCRIPT, "--output", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "wrote 18 rows" in result.stdout and output.read_bytes() == OUTPUT.read_bytes()
        check = run_cli(
            SCRIPT.with_name("validate_expansion.py"),
            "--input",
            str(output),
            "--report",
            str(tmp_path / "report.json"),
        )
        assert check.returncode == 0, check.stdout + check.stderr
        assert (tmp_path / "report.json").read_bytes() == SCRIPT.with_name(
            "expansion_validation.json"
        ).read_bytes()
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
        "punctuation",
        "invalid_alias",
        "name_collision",
        "alias_collision",
    ],
)
def test_bad_required_audit_preserves_existing_expansion(tmp_path: Path, damage: str) -> None:
    path = tmp_path / "audited.tsv"
    fields, rows = read_table(AUDIT)
    candidates = read_table(OUTPUT)[1]
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage == "duplicate":
        rows.append(rows[0].copy())
    elif damage == "blank":
        rows[0]["company"] = " "
    elif damage == "punctuation":
        rows[0]["company"] = "!!!"
    elif damage == "invalid_alias":
        rows[0]["aliases"] = "!!!"
    elif damage == "name_collision":
        rows[0]["company"] = candidates[0]["organization"]
    elif damage == "alias_collision":
        rows[0]["aliases"] = candidates[0]["aliases"]
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
    output = tmp_path / "expansion.tsv"
    shutil.copy2(OUTPUT, output)
    before = output.read_bytes()
    result = run_cli(SCRIPT, "--audited", str(path), "--output", str(output), optimize=True)
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and output.read_bytes() == before
    if damage in {"name_collision", "alias_collision"}:
        assert "protected identity collision" in result.stdout


@pytest.mark.parametrize(
    "damage",
    [
        "empty",
        "row_shape",
        "duplicate_id",
        "blank_id",
        "blank_name",
        "invalid_alias",
        "protected_name",
        "protected_alias",
        "duplicate_name",
        "cross_alias",
    ],
)
def test_public_identity_checks_use_full_reviewed_records(damage: str) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion_builder")
    rows = read_table(OUTPUT)[1]
    protected = module.read_protected(AUDIT)
    if damage == "empty":
        rows.clear()
        diagnostic = "empty or row schema"
    elif damage == "row_shape":
        rows[0].pop("country")
        diagnostic = "empty or row schema"
    elif damage == "duplicate_id":
        rows[1]["candidate_id"] = rows[0]["candidate_id"]
        diagnostic = "duplicate or blank candidate_id"
    elif damage == "blank_id":
        rows[0]["candidate_id"] = " "
        diagnostic = "duplicate or blank candidate_id"
    elif damage in {"blank_name", "invalid_alias"}:
        rows[0]["organization" if damage == "blank_name" else "aliases"] = (
            " " if damage == "blank_name" else "!!!"
        )
        diagnostic = "invalid normalized candidate identity"
    elif damage in {"protected_name", "protected_alias"}:
        rows[0]["organization" if damage == "protected_name" else "aliases"] = read_table(AUDIT)[1][
            0
        ]["company"]
        diagnostic = "protected identity collision"
    elif damage == "duplicate_name":
        rows[1]["organization"] = rows[0]["organization"]
        diagnostic = "duplicate candidate name or alias"
    else:
        rows[1]["aliases"] = rows[0]["aliases"].split(";")[0]
        diagnostic = "duplicate candidate name or alias"
    with pytest.raises(ValueError, match=diagnostic):
        module.check_identities(rows, protected)


@pytest.mark.parametrize("symlink", [False, True])
def test_expansion_cannot_replace_selected_audit(tmp_path: Path, symlink: bool) -> None:
    path = tmp_path / "audit.tsv"
    shutil.copy2(AUDIT, path)
    output = tmp_path / "expansion.tsv" if symlink else path
    if symlink:
        output.symlink_to(path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--audited", str(path), "--output", str(output))
    assert result.returncode == 1 and "replace protected audit" in result.stdout
    assert path.read_bytes() == before


def test_missing_audit_creates_no_output(tmp_path: Path) -> None:
    output = tmp_path / "new/expansion.tsv"
    result = run_cli(SCRIPT, "--audited", str(tmp_path / "missing"), "--output", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and not output.parent.exists()


def test_output_error_is_controlled(tmp_path: Path) -> None:
    output = tmp_path / "expansion.tsv"
    output.mkdir()
    result = run_cli(SCRIPT, "--output", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and not list(output.iterdir())


def test_legal_empty_alias_tokens_preserve_protection_and_generation(tmp_path: Path) -> None:
    path = tmp_path / "audit.tsv"
    fields, rows = read_table(AUDIT)
    rows[0]["aliases"] += "; ;"
    write_table(path, fields, rows)
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion_builder")
    assert module.read_protected(path) == module.read_protected(AUDIT)
    output = tmp_path / "expansion.tsv"
    result = run_cli(SCRIPT, "--audited", str(path), "--output", str(output))
    assert result.returncode == 0 and output.read_bytes() == OUTPUT.read_bytes()
    check = run_cli(
        SCRIPT.with_name("validate_expansion.py"),
        "--input",
        str(output),
        "--audit",
        str(path),
        "--report",
        str(tmp_path / "report.json"),
    )
    assert check.returncode == 0, check.stdout + check.stderr


def test_public_generation_preserves_imported_catalog_bytes_and_mtimes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in [AUDIT, OUTPUT]}
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion_builder")
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
    rows = read_table(OUTPUT)[1]
    assert module.R == rows
    module.check_identities(rows, module.read_protected(AUDIT))
    fpc = next(row for row in rows if row["candidate_id"] == "FCX-015")
    assert fpc["normalized_status"] == "dormant or inactive; website retained"
    output = tmp_path / "expansion.tsv"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output", str(output)])
    module.main()
    assert output.read_bytes() == OUTPUT.read_bytes()
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
