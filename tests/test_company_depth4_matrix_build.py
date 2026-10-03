# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — company completeness matrix generation

"""Build real source audits and verify documentation priorities and derived summaries."""

from __future__ import annotations

import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/depth_round4/build.py"
AUDIT = SCRIPT.parent.parent
INPUTS = [
    "audited_companies.tsv",
    "expansion_candidates.tsv",
    "expansion_round2/candidates.tsv",
    "expansion_round3/candidates.tsv",
]


@pytest.fixture
def audit_copy(tmp_path: Path) -> Path:
    root = tmp_path / "audit"
    for name in INPUTS:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUDIT / name, target)
    return root


def test_real_matrix_corrects_only_inactive_company_priority(tmp_path: Path) -> None:
    before = {(AUDIT / name): (AUDIT / name).read_bytes() for name in INPUTS}
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(SCRIPT, "--output-directory", str(output), optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "98 matrix records" in result.stdout
        fields, expected = read_table(SCRIPT.with_name("gap_matrix.tsv"))
        for row in expected:
            if row["organization"] == "Fusion Power Corporation":
                assert row["normalized_status"] == "dormant or inactive; website retained"
                row.update(priority_score="1", priority_band="low")
        assert read_table(output / "gap_matrix.tsv") == (fields, expected)
        for name in ["enrichment_overlays.tsv", "overlay_sources.tsv"]:
            assert (output / name).read_bytes() == SCRIPT.with_name(name).read_bytes()
        for filename, key in [
            ("summary_by_country.tsv", "country"),
            ("summary_by_identity.tsv", "identity_class"),
            ("summary_by_evidence_tier.tsv", "evidence_tier"),
        ]:
            _, summaries = read_table(output / filename)
            assert sum(int(r["records"]) for r in summaries) == 98
            assert {r[key]: int(r["records"]) for r in summaries} == Counter(
                r[key] for r in expected
            )
            for row in summaries:
                records = [r for r in expected if r[key] == row[key]]
                assert int(row["complete_records"]) == sum(r["gap_count"] == "0" for r in records)
                assert int(row["records_with_gaps"]) == sum(r["gap_count"] != "0" for r in records)
                for band in ["high", "medium", "low"]:
                    assert int(row[f"{band}_priority"]) == sum(
                        r["priority_band"] == band for r in records
                    )
                for field in ["fuel_cycle", "official_url"]:
                    assert int(row[f"missing_{field}"]) == sum(
                        r[f"{field}_completeness"].startswith("missing") for r in records
                    )
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize(
    "status,bonus",
    [
        ("active; current development", 3),
        ("current activity plausible", 3),
        ("inactive", 0),
        ("dormant or inactive; website retained", 0),
    ],
)
def test_active_developer_bonus_does_not_match_inactive(
    audit_copy: Path, tmp_path: Path, status: str, bonus: int
) -> None:
    path = audit_copy / INPUTS[1]
    fields, rows = read_table(path)
    target = next(r for r in rows if r["organization"] == "Fusion Power Corporation")
    target["normalized_status"] = status
    write_table(path, fields, rows)
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    row = next(
        r
        for r in read_table(output / "gap_matrix.tsv")[1]
        if r["organization"] == target["organization"]
    )
    assert (
        int(row["priority_score"])
        == sum(
            {
                "status": 2,
                "identity": 2,
                "approach": 2,
                "device": 2,
                "fuel_cycle": 1,
                "milestone": 3,
                "unsupported_claims": 2,
                "official_url": 2,
                "independent_source": 3,
                "source_date": 1,
                "country": 2,
                "confidence": 1,
            }[field]
            for field in row["gap_fields"].split(";")
            if field
        )
        + bonus
    )


@pytest.mark.parametrize(
    "tier,band",
    [
        ("A/B scoped", "A/B"),
        ("B/C scoped", "B/C"),
        ("C-H historical", "C-H"),
        ("A measured", "A"),
        ("B experimental", "B"),
        ("C bounded", "C"),
        ("D conceptual", "D"),
        ("unclassified", "other"),
    ],
)
def test_evidence_tier_qualifiers_are_preserved_in_source_and_grouped(
    audit_copy: Path, tmp_path: Path, tier: str, band: str
) -> None:
    path = audit_copy / INPUTS[0]
    fields, rows = read_table(path)
    rows[0]["evidence_tier"] = tier
    write_table(path, fields, rows)
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert read_table(output / "gap_matrix.tsv")[1][0]["evidence_tier"] == band
    assert read_table(path)[1][0]["evidence_tier"] == tier
    assert any(
        r["evidence_tier"] == band for r in read_table(output / "summary_by_evidence_tier.tsv")[1]
    )


@pytest.mark.parametrize("name", INPUTS)
@pytest.mark.parametrize(
    "damage", ["schema", "empty", "short", "extra", "quote", "utf8", "missing"]
)
def test_source_input_failures_do_not_replace_existing_outputs(
    audit_copy: Path, tmp_path: Path, name: str, damage: str
) -> None:
    path = audit_copy / name
    fields, rows = read_table(path)
    if damage == "schema":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    write_table(path, fields, rows)
    if damage == "short":
        path.write_text("\t".join(fields) + "\nonly-company\n")
    elif damage == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif damage == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "gap_matrix.tsv"
    sentinel.write_text("existing matrix\n")
    result = run_cli(
        SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output), optimize=True
    )
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr
    assert sentinel.read_text() == "existing matrix\n"
    assert list(output.iterdir()) == [sentinel]


def test_output_write_failure_is_controlled(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.write_text("existing non-directory\n")
    result = run_cli(SCRIPT, "--output-directory", str(output))
    assert result.returncode == 1 and "BUILD FAILED" in result.stdout
    assert "Traceback" not in result.stderr
    assert output.read_text() == "existing non-directory\n"


def test_unspecified_aneutronic_isotope_is_retained_as_a_claim(
    audit_copy: Path, tmp_path: Path
) -> None:
    path = audit_copy / INPUTS[1]
    fields, rows = read_table(path)
    target = next(r for r in rows if r["organization"] == "Fusion Power Corporation")
    target["approach_family"] = "aneutronic configuration; isotope not explicit"
    write_table(path, fields, rows)
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--audit-root", str(audit_copy), "--output-directory", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    row = next(
        r
        for r in read_table(output / "gap_matrix.tsv")[1]
        if r["organization"] == target["organization"]
    )
    assert row["fuel_cycle"] == "aneutronic fuel claimed; isotope not explicit"
    assert row["unsupported_or_ambiguous_claims"] == target["unsupported_or_ambiguous_claims"]


def test_public_matrix_and_main_use_real_audit_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_company_depth4_builder")
    rows = module.build_matrix(AUDIT)
    assert len(rows) == 98
    target = next(r for r in rows if r["organization"] == "Fusion Power Corporation")
    assert target["priority_score"] == "1" and target["priority_band"] == "low"
    output = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-directory", str(output)])
    module.main()
    assert read_table(output / "gap_matrix.tsv")[1] == rows
