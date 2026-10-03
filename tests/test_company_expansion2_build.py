# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — second company expansion producer conformance

"""Generate actual discovery outputs only after checking both protected catalogs."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/expansion_round2/build.py"
AUDIT = SCRIPT.parent.parent
PROTECTED = ["audited_companies.tsv", "expansion_candidates.tsv"]
OUTPUTS = ["candidates.tsv", "source_registry.tsv"]


@pytest.fixture
def audit_copy(tmp_path: Path) -> Path:
    directory = tmp_path / "audit"
    directory.mkdir()
    for name in PROTECTED:
        shutil.copy2(AUDIT / name, directory / name)
    return directory


def test_real_curated_outputs_reproduce_every_byte(tmp_path: Path) -> None:
    paths = [AUDIT / name for name in PROTECTED]
    paths.extend(SCRIPT.with_name(name) for name in [*OUTPUTS, "validation.json"])
    before = {path: path.read_bytes() for path in paths}
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(SCRIPT, "--output-directory", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "15 candidates and 30 source records" in result.stdout
        for name in OUTPUTS:
            assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
        check = run_cli(SCRIPT.with_name("validate.py"), "--directory", str(output))
        assert check.returncode == 0, check.stdout + check.stderr
    assert all(path.read_bytes() == content for path, content in before.items())


@pytest.mark.parametrize("name", PROTECTED)
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
def test_bad_protected_catalog_preserves_existing_outputs(
    audit_copy: Path, tmp_path: Path, name: str, damage: str
) -> None:
    path = audit_copy / name
    fields, rows = read_table(path)
    key = "company" if name == PROTECTED[0] else "organization"
    candidates = read_table(SCRIPT.with_name(OUTPUTS[0]))[1]
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage == "duplicate":
        rows.append(rows[0].copy())
    elif damage == "blank":
        rows[0][key] = " "
    elif damage == "punctuation":
        rows[0][key] = "!!!"
    elif damage == "invalid_alias":
        rows[0]["aliases"] = "!!!"
    elif damage == "name_collision":
        rows[0][key] = candidates[0]["organization"]
    elif damage == "alias_collision":
        rows[0]["aliases"] = candidates[0]["aliases"].split(";")[0]
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
    for filename in OUTPUTS:
        shutil.copy2(SCRIPT.with_name(filename), output / filename)
    before = {output / filename: (output / filename).read_bytes() for filename in OUTPUTS}
    result = run_cli(
        SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output), optimize=True
    )
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr
    assert all(p.read_bytes() == data for p, data in before.items())
    if damage in {"name_collision", "alias_collision"}:
        assert "protected identity collision" in result.stdout
    elif damage == "invalid_alias":
        assert "invalid alias" in result.stdout


@pytest.mark.parametrize(
    "damage",
    [
        "empty",
        "row_shape",
        "duplicate_id",
        "blank_id",
        "blank_name",
        "punctuation",
        "invalid_alias",
        "protected_name",
        "protected_alias",
        "duplicate_name",
        "cross_alias",
    ],
)
def test_public_identity_checks_refuse_damaged_actual_candidates(damage: str) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion2_builder")
    rows = read_table(SCRIPT.with_name(OUTPUTS[0]))[1]
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
    elif damage in {"blank_name", "punctuation", "invalid_alias"}:
        field = "aliases" if damage == "invalid_alias" else "organization"
        rows[0][field] = " " if damage == "blank_name" else "!!!"
        diagnostic = "invalid normalized candidate identity"
    elif damage in {"protected_name", "protected_alias"}:
        rows[0]["organization" if damage == "protected_name" else "aliases"] = read_table(
            AUDIT / PROTECTED[0]
        )[1][0]["company"]
        diagnostic = "protected identity collision"
    elif damage == "duplicate_name":
        rows[1]["organization"] = rows[0]["organization"]
        diagnostic = "duplicate candidate name or alias"
    else:
        rows[1]["aliases"] = rows[0]["aliases"].split(";")[0]
        diagnostic = "duplicate candidate name or alias"
    with pytest.raises(ValueError, match=diagnostic):
        module.check_identities(rows, protected)


@pytest.mark.parametrize("name", PROTECTED)
@pytest.mark.parametrize("output_name", OUTPUTS)
def test_output_symlink_cannot_replace_protected_catalog(
    audit_copy: Path, tmp_path: Path, name: str, output_name: str
) -> None:
    path = audit_copy / name
    before = path.read_bytes()
    output = tmp_path / "output"
    output.mkdir()
    (output / output_name).symlink_to(path)
    result = run_cli(SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output))
    assert result.returncode == 1 and "replace a protected input" in result.stdout
    assert path.read_bytes() == before


def test_missing_protected_directory_creates_no_outputs(tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = run_cli(
        SCRIPT, "--audit-root", str(tmp_path / "missing"), "--output-directory", str(output)
    )
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and not output.exists()


def test_output_directory_failure_is_controlled(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.write_text("existing non-directory\n")
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr and output.read_text() == "existing non-directory\n"


def test_public_read_check_and_main_preserve_imported_catalogs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = [SCRIPT.with_name(name) for name in OUTPUTS]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion2_builder")
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
    rows = read_table(SCRIPT.with_name(OUTPUTS[0]))[1]
    assert module.C == rows
    protected = module.read_protected(AUDIT)
    module.check_identities(rows, protected)
    output = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-directory", str(output)])
    module.main()
    for name in OUTPUTS:
        assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )


@pytest.mark.parametrize("name", PROTECTED)
def test_empty_alias_tokens_do_not_create_protected_identities(
    audit_copy: Path, tmp_path: Path, name: str
) -> None:
    path = audit_copy / name
    fields, rows = read_table(path)
    rows[0]["aliases"] += "; ;"
    write_table(path, fields, rows)
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_expansion2_builder")
    assert module.read_protected(audit_copy) == module.read_protected(AUDIT)
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    for filename in OUTPUTS:
        assert (output / filename).read_bytes() == SCRIPT.with_name(filename).read_bytes()
    check = run_cli(
        SCRIPT.with_name("validate.py"), "--directory", str(output), "--audit-root", str(audit_copy)
    )
    assert check.returncode == 0, check.stdout + check.stderr
