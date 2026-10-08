# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — process-specific industrial validator conformance

"""Validate all process-specific facilities, source provenance and actual prior import layers."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round6"
SCRIPT = DIRECTORY / "validate.py"
NAMES = {
    "data": "industrial_facilities_round6.tsv",
    "snapshot": "selected_source_snapshot.tsv",
    "manifest": "source_snapshot_manifest.tsv",
    "registry": "source_registry.tsv",
    "matrix": "source_gap_matrix.tsv",
}
PRIOR = DIRECTORY.parent / "industrial_facilities.tsv"


@pytest.fixture
def validator() -> ModuleType:
    """Load the process-specific industrial validator through its repository module path.

    Returns
    -------
    ModuleType
        Validator exposing native read-only validation entry points.
    """
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round6_validator")


@pytest.fixture
def bundle(tmp_path: Path) -> dict[str, Path]:
    """Copy all five accepted process-specific tables into owned test storage.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for data, snapshot, manifest, registry and source-gap matrix.

    Returns
    -------
    dict[str, Path]
        Complete table paths indexed by their native CLI option names.
    """
    paths = {key: tmp_path / name for key, name in NAMES.items()}
    for key, path in paths.items():
        path.write_bytes((DIRECTORY / NAMES[key]).read_bytes())
    return paths


def arguments(bundle: dict[str, Path]) -> list[str]:
    """Construct native CLI arguments for the complete five-table bundle.

    Parameters
    ----------
    bundle : dict[str, Path]
        Data, snapshot, manifest, registry and source-gap matrix paths.

    Returns
    -------
    list[str]
        Alternating native option names and paths for read-only validation.
    """
    return [value for key, path in bundle.items() for value in ("--" + key, str(path))]


def test_native_complete_validation_preserves_all_layers(
    bundle: dict[str, Path], validator: ModuleType
) -> None:
    """Validate all 1,131 facilities in both CLI modes while preserving current and prior table bytes."""
    before = {key: path.read_bytes() for key, path in bundle.items()}
    prior = {p: p.read_bytes() for p in validator.OTHER_LAYERS}
    for optimize in (False, True):
        result = run_cli(SCRIPT, *arguments(bundle), optimize=optimize)
        assert result.returncode == 0 and result.stdout.startswith("PASS: 1,131"), (
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
    """Reject blank required observations in optimized mode without changing candidate bytes."""
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
        ("lat", "unknown", "invalid coordinate"),
        ("country", "unknown", "EPE country/licence mismatch"),
        (
            "reactor_type_if_explicit",
            "inferred stirred tank",
            "reactor field must remain blank",
        ),
        ("capacity", "inferred1MW", "not deterministic"),
        ("retrieved", "2026-09-30", "invalid source/date"),
        ("status", "operating", "status caveat missing"),
        ("source_url", "http://source.example/data", "invalid source/date"),
        ("source_url", "https:///data", "invalid source/date"),
        ("source_url", "https://u:p@source.example/data", "invalid source/date"),
        ("source_url", "https://source.example:0/data", "invalid source/date"),
        ("source_url", "https://source.example:99999/data", "invalid source/date"),
        ("source_url", "https://[invalid/data", "invalid source/date"),
        ("source_url", "https://source.example/white space", "invalid source/date"),
    ],
)
def test_full_data_fact_refusals(
    bundle: dict[str, Path], field: str, value: str, diagnostic: str
) -> None:
    """Reject invalid coordinates, invented reactor facts, status overclaims and unsafe provenance URLs."""
    fields, rows = read_table(bundle["data"])
    rows[0][field] = value
    write_table(bundle["data"], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and diagnostic in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("which", "field", "value", "diagnostic"),
    [
        ("snapshot", "source", "unknown", "unexpected source counts"),
        ("snapshot", "source_record_id", "", "snapshot source keys must be non-empty"),
        ("snapshot", "country", "unknown", "unexpected country"),
        ("snapshot", "coordinate_basis", "unknown", "EPE coordinate provenance missing"),
        ("manifest", "source", "unknown", "exactly four imported sources"),
        ("manifest", "sha256", "short", "invalid manifest hash"),
        ("manifest", "sha256", "g" * 64, "invalid manifest hash"),
        ("manifest", "retrieved", "2026-09-30", "count/date mismatch"),
        ("manifest", "selected_rows", "wrong", "count/date mismatch"),
        ("manifest", "selected_rows", "1", "count/date mismatch"),
        ("manifest", "raw_rows", "1", "count/date mismatch"),
        ("manifest", "bytes", "0", "count/date mismatch"),
        ("manifest", "url", "http://source.example", "anonymous HTTPS"),
        ("registry", "retrieved", "2026-09-30", "invalid source registry row"),
        ("registry", "url", "http://source.example", "invalid source registry row"),
        ("registry", "source_id", "", "nonempty and unique"),
        ("registry", "license", "", "missing provenance"),
    ],
)
def test_source_identity_and_provenance_refuse(
    bundle: dict[str, Path], which: str, field: str, value: str, diagnostic: str
) -> None:
    """Reject changed source identities, counts, hashes, dates and missing provenance observations."""
    fields, rows = read_table(bundle[which])
    rows[0][field] = value
    write_table(bundle[which], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert (
        result.returncode == 1 and diagnostic in result.stdout and "Traceback" not in result.stderr
    )


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
    """Reject altered accepted counts and empty or duplicate identities without tracebacks."""
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


@pytest.mark.parametrize("which", ["data", "snapshot", "manifest", "registry", "matrix"])
@pytest.mark.parametrize(
    "corruption", ["header", "empty", "extra", "short", "quote", "utf8", "missing"]
)
def test_all_table_boundaries_refuse(bundle: dict[str, Path], which: str, corruption: str) -> None:
    """Reject malformed or missing input for each of the five native table roles."""
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
    """Reject unreadable, malformed or overlapping prior layers without modifying their bytes."""
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
    rows[0]["country"] = "unknown"
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


@pytest.mark.parametrize("corruption", ["duplicate", "empty_id", "imports", "theme", "date", "url"])
def test_complete_process_gap_matrix_refusals(bundle: dict[str, Path], corruption: str) -> None:
    """Reject changed matrix identities, import decisions, themes, dates and unsafe source URLs."""
    fields, rows = read_table(bundle["matrix"])
    if corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "empty_id":
        rows[0]["source_id"] = ""
    elif corruption == "imports":
        rows[0]["import_decision"] = "DEFER"
    elif corruption == "theme":
        for row in rows:
            row["process_theme"] = "unknown"
    elif corruption == "date":
        rows[0]["retrieved"] = "2026-09-30"
    else:
        rows[0]["official_url"] = "http://source.example"
    write_table(bundle["matrix"], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle))
    assert result.returncode == 1 and "FAIL" in result.stdout and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("which", "source", "field", "value"),
    [
        ("data", "br-epe-", "lat", "0"),
        ("data", "br-epe-", "license", "unknown"),
        ("data", "br-epe-", "verification_notes", "no supporting caveat"),
        ("data", "us-epa-lmop:", "lat", "0"),
        ("data", "us-epa-lmop:", "country", "unknown"),
        ("data", "us-epa-lmop:", "license", "unknown"),
        ("data", "us-epa-lmop:", "verification_notes", "no supporting caveat"),
        ("data", "us-epa-lmop:", "stable_id", "unknown:record"),
        ("snapshot", "br-epe-ethanol", "source", "us-epa-lmop"),
        ("snapshot", "br-epe-ethanol", "facility_name", ""),
        ("snapshot", "br-epe-ethanol", "lat", "NaN"),
        ("snapshot", "br-epe-ethanol", "lon", "not numeric"),
        ("snapshot", "us-epa-lmop", "source", "br-epe-ethanol"),
        ("snapshot", "us-epa-lmop", "source_status", "planned"),
        ("snapshot", "us-epa-lmop", "coordinate_basis", "unknown"),
        ("matrix", "br-epe-ethanol", "rights_status", ""),
        ("matrix", "br-epe-ethanol", "import_decision", ""),
    ],
)
def test_actual_specific_layer_policy(
    bundle: dict[str, Path], which: str, source: str, field: str, value: str
) -> None:
    """Reject source-specific changes to geography, rights, identity and status caveats."""
    fields, rows = read_table(bundle[which])
    key = "stable_id" if which == "data" else "source" if which == "snapshot" else "source_id"
    next(r for r in rows if r[key].startswith(source))[field] = value
    write_table(bundle[which], fields, rows)
    result = run_cli(SCRIPT, *arguments(bundle), optimize=True)
    assert result.returncode == 1 and "FAIL" in result.stdout and "Traceback" not in result.stderr


def test_rights_document_and_service_row_identity(
    bundle: dict[str, Path], validator: ModuleType, tmp_path: Path
) -> None:
    """Require accepted rights-review phrases and distinct service-row IDs through the native validator."""
    rights = tmp_path / "RIGHTS.md"
    rights.write_bytes((DIRECTORY / "RIGHTS.md").read_bytes())
    assert validator.validate_rights(rights.read_text()) == []
    for phrase in [
        "Creative Commons Attribution 4.0 International",
        "CC0 1.0",
        "Boundary of this rights review",
    ]:
        rights.write_text((DIRECTORY / "RIGHTS.md").read_text().replace(phrase, "removed"))
        result = run_cli(SCRIPT, *arguments(bundle), "--rights", str(rights))
        assert result.returncode == 1 and "RIGHTS.md lacks" in result.stdout
    rights.unlink()
    assert run_cli(SCRIPT, *arguments(bundle), "--rights", str(rights)).returncode == 1
    fields, rows = read_table(bundle["snapshot"])
    rows[1]["source_row_id"] = rows[0]["source_row_id"]
    write_table(bundle["snapshot"], fields, rows)
    assert "service row IDs" in run_cli(SCRIPT, *arguments(bundle)).stdout
