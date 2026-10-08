# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — UK industrial validator conformance

"""Validate all UK facilities, source provenance and actual prior import layers."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round3"
SCRIPT = DIRECTORY / "validate.py"
NAMES = {
    "data": "industrial_facilities_round3.tsv",
    "snapshot": "selected_source_snapshot.tsv",
    "manifest": "source_snapshot_manifest.tsv",
    "registry": "source_registry.tsv",
}
PRIOR = DIRECTORY.parent / "industrial_facilities.tsv"


@pytest.fixture
def validator() -> ModuleType:
    """Load the UK industrial validator through its repository module path.

    Returns
    -------
    ModuleType
        Validator exposing native read-only record, prior-layer and rebuild checks.
    """
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round3_validator")


@pytest.fixture
def bundle(tmp_path: Path) -> dict[str, Path]:
    """Copy the complete accepted four-table bundle into owned test storage.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for dataset, snapshot, manifest and source-registry copies.

    Returns
    -------
    dict[str, Path]
        All four table paths indexed by their native CLI argument names.
    """
    paths = {key: tmp_path / name for key, name in NAMES.items()}
    for key, path in paths.items():
        path.write_bytes((DIRECTORY / NAMES[key]).read_bytes())
    return paths


def arguments(bundle: dict[str, Path]) -> list[str]:
    """Construct native validation arguments for all four complete source tables.

    Parameters
    ----------
    bundle : dict[str, Path]
        Dataset, snapshot, manifest and source-registry paths.

    Returns
    -------
    list[str]
        Alternating option names and paths for the read-only native validator.
    """
    return [value for key, path in bundle.items() for value in ("--" + key, str(path))]


def test_native_complete_validation_preserves_all_layers(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Validate all 722 UK facilities in both CLI modes while preserving current and prior source bytes."""
    before = {key: path.read_bytes() for key, path in bundle.items()}
    prior = {p: p.read_bytes() for p in validator.OTHER_LAYERS}
    for optimize in (False, True):
        result = run_cli(SCRIPT, *arguments(bundle), optimize=optimize)
        assert result.returncode == 0 and result.stdout.startswith("PASS: 722"), (
            result.stdout + result.stderr
        )
    assert validator.main(arguments(bundle)) == 0
    assert before == {key: path.read_bytes() for key, path in bundle.items()}
    assert prior == {p: p.read_bytes() for p in prior}
    assert run_cli(SCRIPT).returncode == 0


@pytest.mark.parametrize(
    "field",
    [
        "facility_name",
        "country",
        "lat",
        "lon",
        "precision",
        "sector",
        "process_or_activity",
        "status",
        "operator",
        "source_url",
        "source_role",
        "license",
        "verification_notes",
    ],
)
def test_required_observations_refuse(bundle: dict[str, Path], field: str) -> None:
    """Reject blank required observations under optimized execution without modifying candidate bytes."""
    fields, rows = read_table(bundle["data"])
    rows[0][field] = " "
    write_table(bundle["data"], fields, rows)
    before = bundle["data"].read_bytes()
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and f"missing {field}" in result.stdout
    assert "Traceback" not in result.stderr and bundle["data"].read_bytes() == before


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("lat", "91", "coordinate out of range"),
        ("lon", "181", "coordinate out of range"),
        ("lat", "NaN", "coordinate out of range"),
        ("lat", "unknown", "non-numeric coordinate"),
        ("country", "unknown", "unexpected country"),
        ("reactor_type_if_explicit", "inferred stirred tank", "must remain empty"),
        ("capacity", "inferred 1 MW", "must remain empty"),
        ("retrieved", "2026-09-30", "wrong retrieval date"),
        ("status", "operating", "status overclaims"),
        ("source_url", "http://source.example/data", "valid anonymous HTTPS"),
        ("source_url", "https:///data", "valid anonymous HTTPS"),
        ("source_url", "https://user:password@source.example/data", "valid anonymous HTTPS"),
        ("source_url", "https://source.example:0/data", "valid anonymous HTTPS"),
        ("source_url", "https://source.example:99999/data", "valid anonymous HTTPS"),
        ("source_url", "https://[invalid/data", "valid anonymous HTTPS"),
        ("source_url", "https://source.example/white space", "valid anonymous HTTPS"),
    ],
)
def test_full_data_fact_refusals(
    bundle: dict[str, Path], field: str, value: str, diagnostic: str
) -> None:
    """Reject invalid geography, inferred facts, status overclaims and unsafe provenance URLs."""
    fields, rows = read_table(bundle["data"])
    rows[0][field] = value
    write_table(bundle["data"], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("which", "field", "value", "diagnostic"),
    [
        ("snapshot", "source", "unknown", "unexpected source/year"),
        ("snapshot", "reporting_year", "2023", "unexpected source/year"),
        ("snapshot", "nace_code", "99", "outside documented filter"),
        ("snapshot", "source_record_id", "", "duplicate/empty source_record_id"),
        ("manifest", "source", "unknown", "exactly the UK PRTR"),
        ("manifest", "sha256", "short", "invalid SHA-256"),
        ("manifest", "sha256", "g" * 64, "invalid SHA-256"),
        ("manifest", "retrieved", "2026-09-30", "unexpected retrieval/report year"),
        ("manifest", "reporting_year", "2023", "unexpected retrieval/report year"),
        ("manifest", "selected_rows", "wrong", "count mismatch"),
        ("manifest", "selected_rows", "1", "count mismatch"),
        ("manifest", "raw_rows", "1", "count mismatch"),
        ("manifest", "bytes", "0", "count mismatch"),
        ("manifest", "url", "http://source.example", "valid anonymous HTTPS"),
        ("registry", "retrieved", "2026-09-30", "invalid record"),
        ("registry", "url", "http://source.example", "invalid record"),
        ("registry", "source_id", "", "nonempty and unique"),
        ("registry", "license", "", "missing provenance"),
    ],
)
def test_source_identity_and_provenance_refuse(
    bundle: dict[str, Path], which: str, field: str, value: str, diagnostic: str
) -> None:
    """Reject changed source/year/filter identity, counts, hashes, dates and missing provenance fields."""
    fields, rows = read_table(bundle[which])
    rows[0][field] = value
    write_table(bundle[which], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate_data",
        "empty_id",
        "data_count",
        "snapshot_count",
        "source_id",
        "manifest_count",
        "registry_count",
        "registry_id",
    ],
)
def test_historical_counts_and_ids_refuse(bundle: dict[str, Path], corruption: str) -> None:
    """Reject altered accepted table counts and empty or duplicate record identities."""
    which = (
        "data"
        if corruption in {"duplicate_data", "empty_id", "data_count"}
        else "snapshot"
        if corruption in {"snapshot_count", "source_id"}
        else "manifest"
        if corruption == "manifest_count"
        else "registry"
    )
    fields, rows = read_table(bundle[which])
    if corruption == "duplicate_data":
        rows[1]["stable_id"] = rows[0]["stable_id"]
    elif corruption == "empty_id":
        rows[0]["stable_id"] = ""
    elif corruption == "source_id":
        rows[1]["source_record_id"] = rows[0]["source_record_id"]
    elif corruption == "manifest_count":
        rows.append(rows[0].copy())
    elif corruption == "registry_count":
        rows = rows[:2]
    elif corruption == "registry_id":
        rows[1]["source_id"] = rows[0]["source_id"]
    else:
        rows.pop()
    write_table(bundle[which], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle))
    assert result.returncode == 1 and "FAIL" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize("which", ["data", "snapshot", "manifest", "registry"])
@pytest.mark.parametrize(
    "corruption", ["header", "empty", "extra", "short", "quote", "utf8", "missing"]
)
def test_all_table_boundaries_refuse(bundle: dict[str, Path], which: str, corruption: str) -> None:
    """Reject malformed or missing inputs for each of the four native table roles."""
    path = bundle[which]
    fields, rows = read_table(path)
    if corruption == "header":
        fields = fields[::-1]
    elif corruption == "empty":
        rows.clear()
    write_table(path, fields, rows)
    if corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "short":
        path.write_text("\t".join(fields) + "\nonly-one-cell\n")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and "Traceback" not in result.stderr


@pytest.mark.parametrize("corruption", ["overlap", "duplicate", "empty_id", "missing", "schema"])
def test_actual_prior_layers_must_be_readable_and_disjoint(
    tmp_path: Path, bundle: dict[str, Path], corruption: str
) -> None:
    """Reject unreadable, malformed or overlapping prior layers without rewriting them."""
    fields, rows = read_table(PRIOR)
    path = tmp_path / "prior.tsv"
    if corruption == "overlap":
        rows[0]["stable_id"] = read_table(bundle["data"])[1][0]["stable_id"]
    elif corruption == "duplicate":
        rows[1]["stable_id"] = rows[0]["stable_id"]
    elif corruption == "empty_id":
        rows[0]["stable_id"] = ""
    elif corruption == "schema":
        fields = fields[::-1]
    write_table(path, fields, rows)
    if corruption == "missing":
        path.unlink()
    before = path.read_bytes() if path.exists() else None
    result = run_cli(SCRIPT, *arguments(bundle), "--other-layer", str(path))
    assert result.returncode == 1 and "FAIL" in result.stdout and "Traceback" not in result.stderr
    assert before == (path.read_bytes() if path.exists() else None)


def test_real_native_rebuild_failure_mismatch_and_deadline(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Reject actual rebuild mismatches, invalid snapshots and expired or invalid time limits."""
    fields, rows = read_table(bundle["data"])
    rows[0]["facility_name"] += " changed"
    write_table(bundle["data"], fields, rows)
    before = bundle["data"].read_bytes()
    result = run_cli(SCRIPT, *arguments(bundle))
    assert result.returncode == 1 and "not deterministic" in result.stdout
    assert bundle["data"].read_bytes() == before
    assert not validator.verify_rebuild(bundle["data"], bundle["snapshot"])
    fields, rows = read_table(bundle["snapshot"])
    rows[0]["nace_code"] = "99"
    write_table(bundle["snapshot"], fields, rows)
    assert not validator.verify_rebuild(bundle["data"], bundle["snapshot"])
    assert not validator.verify_rebuild(
        bundle["data"], DIRECTORY / NAMES["snapshot"], timeout=0.000001
    )
    for timeout in [0, float("inf")]:
        with pytest.raises(ValueError, match="positive and finite"):
            validator.verify_rebuild(bundle["data"], bundle["snapshot"], timeout=timeout)
        assert validator.main([*arguments(bundle), "--timeout", str(timeout)]) == 1
    assert bundle["data"].read_bytes() == before


def test_public_runtime_schema_and_prior_layer_contract(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Require complete string schemas and at least one readable prior layer for stable-ID checking."""
    tables = [read_table(bundle[k])[1] for k in NAMES]
    assert validator.validate_records(*tables) == []
    broken = json.loads(json.dumps(tables))
    broken[0][0]["facility_name"] = None
    assert validator.validate_records(*broken) == ["record differs from its required string schema"]
    tables[1][0].pop("country")
    assert "string schema" in validator.validate_records(*tables)[0]
    assert validator.check_other_layers(tables[0], []) == [
        "at least one prior layer is required for stable-ID checking"
    ]
    assert validator.check_other_layers(tables[0], [PRIOR]) == []
