# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Canadian and Australian industrial validator conformance

"""Validate all actual round-two records without rewriting any requested input."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round2"
SCRIPT = DIRECTORY / "validate.py"
NAMES = {
    "data": "industrial_facilities_round2.tsv",
    "snapshot": "selected_source_snapshot.tsv",
    "manifest": "source_snapshot_manifest.tsv",
    "registry": "source_registry.tsv",
}


@pytest.fixture
def validator() -> ModuleType:
    """Load the Canadian and Australian validator through its repository module path.

    Returns
    -------
    ModuleType
        Validator exposing native read-only record and rebuild checks.
    """
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round2_validator")


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


def test_full_native_validation_preserves_all_inputs(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Validate all 1,776 facilities in both CLI modes and through API without changing source bytes."""
    before = {key: path.read_bytes() for key, path in bundle.items()}
    for optimize in (False, True):
        result = run_cli(SCRIPT, *arguments(bundle), optimize=optimize)
        assert result.returncode == 0 and result.stdout.startswith("PASS: 1,776"), (
            result.stdout + result.stderr
        )
    assert validator.main(arguments(bundle)) == 0
    assert before == {key: path.read_bytes() for key, path in bundle.items()}
    result = run_cli(SCRIPT)
    assert result.returncode == 0 and "deterministic offline rebuild" in result.stdout


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
def test_required_source_observations_refuse(bundle: dict[str, Path], field: str) -> None:
    """Reject blank required source observations in optimized mode without modifying candidate bytes."""
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
        ("reactor_type_if_explicit", "inferred stirred tank", "reactor type must remain empty"),
        ("capacity", "inferred 1 MW", "capacity must remain empty"),
        ("retrieved", "2026-09-30", "wrong retrieval date"),
        ("source_url", "http://source.example/data", "invalid HTTPS"),
        ("source_url", "https:///data", "invalid HTTPS"),
        ("source_url", "https://user:password@source.example/data", "invalid HTTPS"),
        ("source_url", "https://source.example:0/data", "invalid HTTPS"),
        ("source_url", "https://source.example:99999/data", "invalid HTTPS"),
        ("source_url", "https://[invalid/data", "invalid HTTPS"),
        ("source_url", "https://source.example/white space", "invalid HTTPS"),
        ("status", "operating", "status overclaims"),
        ("country", "unknown", "unexpected country counts"),
    ],
)
def test_full_data_facts_refuse(
    bundle: dict[str, Path], field: str, value: str, diagnostic: str
) -> None:
    """Reject invalid geography, inferred reactor facts, status overclaims and unsafe source URLs."""
    fields, rows = read_table(bundle["data"])
    rows[0][field] = value
    write_table(bundle["data"], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "corruption", ["duplicate", "empty_id", "count", "snapshot_count", "snapshot_source"]
)
def test_historical_counts_and_identity_refuse(bundle: dict[str, Path], corruption: str) -> None:
    """Reject changed historical counts, source namespaces and empty or duplicate stable IDs."""
    path = bundle["snapshot" if corruption.startswith("snapshot") else "data"]
    fields, rows = read_table(path)
    if corruption == "duplicate":
        rows[1]["stable_id"] = rows[0]["stable_id"]
    elif corruption == "empty_id":
        rows[0]["stable_id"] = ""
    elif corruption.endswith("count"):
        rows.pop()
    else:
        rows[0]["source"] = "unknown"
    write_table(path, fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle))
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("which", "field", "value", "diagnostic"),
    [
        ("manifest", "source", "unknown", "two official sources"),
        ("manifest", "sha256", "short", "invalid SHA-256"),
        ("manifest", "sha256", "g" * 64, "invalid SHA-256"),
        ("manifest", "retrieved", "2026-09-30", "wrong retrieval date"),
        ("manifest", "selected_rows", "wrong", "count mismatch"),
        ("manifest", "selected_rows", "1", "count mismatch"),
        ("manifest", "bytes", "0", "count mismatch"),
        ("manifest", "url", "http://source.example", "invalid HTTPS"),
        ("registry", "retrieved", "2026-09-30", "invalid record"),
        ("registry", "url", "http://source.example", "invalid record"),
        ("registry", "source_id", "", "nonempty and unique"),
        ("registry", "license", "", "missing provenance"),
    ],
)
def test_source_provenance_refuses(
    bundle: dict[str, Path], which: str, field: str, value: str, diagnostic: str
) -> None:
    """Reject invalid source identities, hashes, dates, counts and missing provenance fields."""
    fields, rows = read_table(bundle[which])
    rows[0][field] = value
    write_table(bundle[which], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout
    assert "Traceback" not in result.stderr


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


def test_registry_cardinality_and_duplicate_ids_refuse(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Reject duplicate registry IDs and incomplete registry or manifest membership through public main."""
    fields, rows = read_table(bundle["registry"])
    rows[1]["source_id"] = rows[0]["source_id"]
    write_table(bundle["registry"], fields, rows)
    assert validator.main(arguments(bundle)) == 1
    rows.pop()
    write_table(bundle["registry"], fields, rows)
    assert validator.main(arguments(bundle)) == 1
    fields, manifest = read_table(bundle["manifest"])
    manifest.pop()
    write_table(bundle["manifest"], fields, manifest)
    assert validator.main(arguments(bundle)) == 1


def test_real_producer_mismatch_and_failure_leave_data_intact(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Reject actual rebuild mismatches, invalid snapshots and time limits while preserving candidate bytes."""
    fields, rows = read_table(bundle["data"])
    rows[0]["facility_name"] += " changed"
    write_table(bundle["data"], fields, rows)
    before = bundle["data"].read_bytes()
    result = run_cli(SCRIPT, *arguments(bundle))
    assert result.returncode == 1 and "not deterministic" in result.stdout
    assert bundle["data"].read_bytes() == before
    assert not validator.verify_rebuild(bundle["data"], bundle["snapshot"])
    fields, rows = read_table(bundle["snapshot"])
    rows[0]["process_code"] = "99"
    write_table(bundle["snapshot"], fields, rows)
    assert not validator.verify_rebuild(bundle["data"], bundle["snapshot"])
    assert bundle["data"].read_bytes() == before
    assert not validator.verify_rebuild(
        bundle["data"], DIRECTORY / NAMES["snapshot"], timeout=0.000001
    )
    for timeout in [0, float("inf")]:
        assert validator.main([*arguments(bundle), "--timeout", str(timeout)]) == 1


def test_public_record_schema_refusal_and_sensitive_header(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Reject non-string or incomplete record schemas and an unexpected sensitive snapshot column."""
    tables = [read_table(bundle[k])[1] for k in NAMES]
    assert validator.validate_records(*tables) == []
    broken = json.loads(json.dumps(tables))
    broken[0][0]["facility_name"] = None
    assert validator.validate_records(*broken) == ["record differs from its required string schema"]
    tables[1][0].pop("datum")
    assert "string schema" in validator.validate_records(*tables)[0]
    fields, rows = read_table(bundle["snapshot"])
    fields[fields.index("datum")] = "street_address"
    for row in rows:
        row["street_address"] = row.pop("datum")
    write_table(bundle["snapshot"], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle))
    assert result.returncode == 1 and "unexpected header" in result.stdout
