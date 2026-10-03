# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — real capture-bound bundle conformance
"""Exercise native complete source conversion, rights binding and exact offline reproduction."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from ._catalogue_inputs import run_cli
from ._industrial7_sources import (
    PREFIX,
    SCRIPTS,
    copy_custody,
    revise_json,
    tls_source,
)
from ._industrial7_sources import source_custody as source_custody

ARTIFACTS = importlib.import_module(PREFIX + ".artifacts")
BUNDLE = importlib.import_module(PREFIX + ".bundle")
PROVENANCE = importlib.import_module(PREFIX + ".provenance")
ACQUISITION = importlib.import_module(PREFIX + ".acquisition")
VALIDATION = importlib.import_module(PREFIX + ".validate")
CONTRACTS = importlib.import_module(PREFIX + ".contracts")
BUILD = importlib.import_module(PREFIX + ".build_dataset")


@pytest.fixture
def frozen_bundle(tmp_path: Path, source_custody: Path) -> Path:
    """Create all seven artifacts from complete original publisher custody."""
    output = tmp_path / "bundle"
    assert BUNDLE.create_bundle(source_custody, output) == 421
    return output


@pytest.mark.parametrize("optimize", [False, True])
def test_native_complete_bundle_and_original_custody_verification(
    tmp_path: Path, source_custody: Path, optimize: bool
) -> None:
    output = tmp_path / "native"
    inputs = {path: path.read_bytes() for path in source_custody.iterdir() if path.is_file()}
    created = run_cli(
        SCRIPTS / "bundle.py",
        "--capture-directory",
        str(source_custody),
        "--output-directory",
        str(output),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    assert "421 source-derived discovery records" in created.stdout
    verified = run_cli(
        SCRIPTS / "validate.py",
        "--directory",
        str(output),
        "--capture-directory",
        str(source_custody),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert VALIDATION.validate_bundle(output, capture_directory=source_custody) == 421
    assert {path: path.read_bytes() for path in inputs} == inputs
    names = {path.name for path in output.iterdir()}
    assert names == {
        ARTIFACTS.SNAPSHOT_NAME,
        ARTIFACTS.DATASET_NAME,
        ARTIFACTS.SOURCE_MANIFEST,
        ARTIFACTS.BUNDLE_MANIFEST,
        "RIGHTS.md",
        "source_registry.tsv",
        "source_snapshot_manifest.tsv",
    }
    assert not any(
        name.endswith(".html") or name.endswith(".zip") or name.endswith(".pdf") for name in names
    )
    registry = CONTRACTS.read_table(output / "source_registry.tsv", ARTIFACTS.REGISTRY_FIELDS)
    assert len(registry) == 5
    assert {row["publisher"] for row in registry} == {
        "Swiss Federal Office of Energy (SFOE)",
        "ARPAE Emilia-Romagna",
        "opendata.swiss",
    }
    assert {row["license"] for row in registry} == {
        "LicenseRef-opendata-swiss-terms-by",
        "CC-BY-4.0",
    }
    manifest = json.loads((output / ARTIFACTS.BUNDLE_MANIFEST).read_text())
    for name, metadata in manifest["files"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == metadata["sha256"]
        assert (output / name).stat().st_size == metadata["bytes"]
    assert manifest["files"][ARTIFACTS.DATASET_NAME]["license"] == ARTIFACTS.DATA_LICENSE


@pytest.mark.parametrize("optimize", [False, True])
def test_native_offline_reproduction_needs_only_complete_frozen_artifacts(
    tmp_path: Path, frozen_bundle: Path, optimize: bool
) -> None:
    before = {path.name: path.read_bytes() for path in frozen_bundle.iterdir()}
    output = tmp_path / "reproduced"
    result = run_cli(
        SCRIPTS / "bundle.py",
        "--frozen-directory",
        str(frozen_bundle),
        "--output-directory",
        str(output),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before
    assert {path.name: path.read_bytes() for path in frozen_bundle.iterdir()} == before
    assert VALIDATION.validate_bundle(output) == 421


@pytest.mark.parametrize(
    "artifact",
    [
        "RIGHTS.md",
        "source_registry.tsv",
        "source_snapshot_manifest.tsv",
        "source_manifest.json",
        "bundle_manifest.json",
        "industrial_facilities_round7.tsv",
        "selected_source_snapshot.tsv",
    ],
)
def test_any_artifact_byte_drift_cannot_validate_or_reproduce(
    tmp_path: Path, frozen_bundle: Path, artifact: str
) -> None:
    path = frozen_bundle / artifact
    path.write_bytes(path.read_bytes() + b"altered")
    before = {child.name: child.read_bytes() for child in frozen_bundle.iterdir()}
    with pytest.raises(ValueError):
        VALIDATION.validate_bundle(frozen_bundle)
    output = tmp_path / "must_not_exist"
    with pytest.raises(ValueError):
        BUNDLE.create_bundle(frozen_bundle, output, frozen=True)
    assert not output.exists()
    assert {child.name: child.read_bytes() for child in frozen_bundle.iterdir()} == before


@pytest.mark.parametrize("failure", ["missing", "symlink", "directory", "oversized"])
def test_incomplete_or_nonregular_bundle_is_refused_before_publication(
    tmp_path: Path, frozen_bundle: Path, failure: str
) -> None:
    path = frozen_bundle / "RIGHTS.md"
    original = path.read_bytes()
    path.unlink()
    if failure == "symlink":
        another = tmp_path / "rights-original"
        another.write_bytes(original)
        path.symlink_to(another)
    elif failure == "directory":
        path.mkdir()
    elif failure == "oversized":
        with path.open("wb") as handle:
            handle.truncate(CONTRACTS.MAX_BYTES + 1)
    with pytest.raises(ValueError):
        VALIDATION.validate_bundle(frozen_bundle)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("snapshot_sha256", "0" * 64),
        ("selected_counts", {"ch-sfoe-biogas": 153.0, "it-arpae-biogas": 268}),
        ("raw_counts", {"ch-sfoe-biogas": 153, "it-arpae-biogas": 331}),
        ("swiss_annual_rows", 974.0),
        ("swiss_annual_rows", 975),
        ("page_size", True),
        ("page_size", 0),
        ("page_size", 1001),
        ("swiss_reference_date", "2021-01-01"),
        ("captures", []),
        ("grants", {}),
    ],
)
def test_reviewed_source_profile_and_grants_are_mandatory(
    frozen_bundle: Path, field: str, value: object
) -> None:
    path = frozen_bundle / ARTIFACTS.SOURCE_MANIFEST
    manifest = json.loads(path.read_text())
    manifest[field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        VALIDATION.validate_bundle(frozen_bundle)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", None),
        ("sha256", None),
        ("sha256", "F" * 64),
        ("bytes", True),
        ("bytes", 0),
        ("bytes", CONTRACTS.MAX_BYTES + 1),
        ("http_status", True),
        ("http_status", 503),
        ("tls_verified", False),
        ("origin_url", "https://example.invalid/unrelated"),
        ("retrieved_utc", None),
        ("retrieved_utc", "invalid"),
        ("retrieved_utc", "2026-09-30T00:00:00"),
        ("retrieved_utc", "2999-01-01T00:00:00+00:00"),
    ],
)
def test_manifest_receipts_cannot_lose_type_hash_origin_or_acquisition_date(
    frozen_bundle: Path, field: str, value: object
) -> None:
    path = frozen_bundle / ARTIFACTS.SOURCE_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["captures"][0][field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        VALIDATION.validate_bundle(frozen_bundle)


@pytest.mark.parametrize(
    "failure", ["duplicate", "missing", "unknown", "extra_member", "terms", "date"]
)
def test_complete_resource_set_exact_terms_and_utc_dates_are_bound(
    frozen_bundle: Path, failure: str
) -> None:
    path = frozen_bundle / ARTIFACTS.SOURCE_MANIFEST
    manifest = json.loads(path.read_text())
    captures = manifest["captures"]
    if failure == "duplicate":
        captures.append(copy.deepcopy(captures[0]))
    elif failure == "missing":
        captures.pop()
    elif failure == "unknown":
        captures[0]["name"] = "unrelated.json"
    elif failure == "extra_member":
        captures[0]["unexpected"] = True
    elif failure == "terms":
        next(row for row in captures if row["name"] == "SFOE_TERMS.html")["sha256"] = "0" * 64
    else:
        next(row for row in captures if row["name"] == "SFOE_ORIGINAL.csv.zip")["retrieved_utc"] = (
            "2026-09-29T23:30:00+02:00"
        )
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        VALIDATION.validate_bundle(frozen_bundle)


def test_self_consistent_offline_edit_cannot_pass_original_raw_custody(
    tmp_path: Path, frozen_bundle: Path, source_custody: Path
) -> None:
    snapshot, manifest, observations = ARTIFACTS.read_bundle(frozen_bundle)
    changed = copy.deepcopy(observations)
    changed[0]["facility_name"] += " changed"
    snapshot = BUILD.table_bytes(CONTRACTS.SNAPSHOT_FIELDS, changed)
    manifest["snapshot_sha256"] = hashlib.sha256(snapshot).hexdigest()
    changed_bundle = tmp_path / "self-consistent"
    changed_bundle.mkdir()
    for name, body in ARTIFACTS.expected_artifacts(snapshot, manifest, changed).items():
        (changed_bundle / name).write_bytes(body)
    assert VALIDATION.validate_bundle(changed_bundle) == 421
    with pytest.raises(ValueError, match="original raw custody"):
        VALIDATION.validate_bundle(changed_bundle, capture_directory=source_custody)


def test_noncanonical_snapshot_cannot_be_relabelled_with_a_matching_digest(
    frozen_bundle: Path,
) -> None:
    snapshot = frozen_bundle / ARTIFACTS.SNAPSHOT_NAME
    body = snapshot.read_bytes().replace(b"\n", b"\r\n")
    snapshot.write_bytes(body)
    path = frozen_bundle / ARTIFACTS.SOURCE_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["snapshot_sha256"] = hashlib.sha256(body).hexdigest()
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="byte binding"):
        VALIDATION.validate_bundle(frozen_bundle)


@pytest.mark.parametrize("failure", ["source", "nested", "existing", "repository"])
def test_bundle_outputs_preserve_source_trees_and_existing_state(
    tmp_path: Path, source_custody: Path, failure: str
) -> None:
    source = tmp_path / "copied"
    copy_custody(source, source_custody)
    output = tmp_path / "output"
    if failure == "source":
        output = source
    elif failure == "nested":
        output = source / "nested"
    elif failure == "existing":
        output.mkdir()
        (output / "existing").write_text("preserve")
    else:
        output = SCRIPTS / "must_not_exist"
    before = {path.name: path.read_bytes() for path in source.iterdir()}
    with pytest.raises(ValueError):
        BUNDLE.create_bundle(source, output)
    assert {path.name: path.read_bytes() for path in source.iterdir()} == before
    if failure == "existing":
        assert (output / "existing").read_text() == "preserve"


@pytest.mark.parametrize("optimize", [False, True])
def test_native_bundle_and_validation_refuse_invalid_sources_and_artifacts(
    tmp_path: Path, frozen_bundle: Path, optimize: bool
) -> None:
    result = run_cli(
        SCRIPTS / "bundle.py",
        "--capture-directory",
        str(tmp_path / "missing"),
        "--output-directory",
        str(tmp_path / "not-created"),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 1
    assert not (tmp_path / "not-created").exists()
    (frozen_bundle / ARTIFACTS.DATASET_NAME).write_text("wrong\n")
    result = run_cli(
        SCRIPTS / "validate.py",
        "--directory",
        str(frozen_bundle),
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 1
    assert "INDUSTRIAL VALIDATION FAILED" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ["--snapshot", "source"],
        ["--snapshot", "source", "--dataset", "data", "--capture-directory", "raw"],
        ["--directory", "bundle", "--dataset", "data"],
    ],
)
def test_native_validation_refuses_ambiguous_modes(tmp_path: Path, args: list[str]) -> None:
    result = run_cli(SCRIPTS / "validate.py", *args, cwd=tmp_path)
    assert result.returncode == 2


def test_verified_pagination_retains_all_page_receipts(
    tmp_path: Path, source_custody: Path
) -> None:
    layer = json.loads((source_custody / "ARPAE_LAYER.json").read_text())
    layer["maxRecordCount"] = 100
    page = json.loads((source_custody / "ARPAE_COMPLETE.json").read_text())
    overrides = {"ARPAE_LAYER.json": json.dumps(layer).encode()}
    for index, offset in enumerate(range(0, 330, 100)):
        current = {**page, "features": page["features"][offset : offset + 100]}
        current["exceededTransferLimit"] = offset + 100 < 330
        overrides[f"ARPAE_PAGE_{index:04d}.json"] = json.dumps(current).encode()
    tls = tmp_path / "tls"
    tls.mkdir()
    with tls_source(tls, source_custody, overrides) as (
        url,
        ca,
    ):
        capture = tmp_path / "paginated"
        rows, _ = ACQUISITION.acquire(capture, mirror_base=url, ca_file=ca)
        assert len(rows) == 421
    output = tmp_path / "pages-bundle"
    assert BUNDLE.create_bundle(capture, output) == 421
    assert VALIDATION.validate_bundle(output, capture_directory=capture) == 421
    manifest = json.loads((output / ARTIFACTS.SOURCE_MANIFEST).read_text())
    names = {receipt["name"] for receipt in manifest["captures"]}
    assert {f"ARPAE_PAGE_{index:04d}.json" for index in range(4)} <= names
    assert "ARPAE_COMPLETE.json" not in names


def test_new_unselected_native_feature_requires_review_of_the_complete_source_count(
    tmp_path: Path, source_custody: Path
) -> None:
    source = tmp_path / "changed-native-source"
    copy_custody(source, source_custody)
    page = json.loads((source / "ARPAE_COMPLETE.json").read_text())
    ids = json.loads((source / "ARPAE_IDS.json").read_text())
    feature = copy.deepcopy(page["features"][0])
    feature["attributes"]["OBJECTID"] = max(ids["objectIds"]) + 1
    feature["attributes"]["COD_OE"] = "NEW-NONBIOGAS"
    feature["attributes"]["TIPO_COMB"] = "Biomasse solide"
    page["features"].append(feature)
    ids["objectIds"].append(feature["attributes"]["OBJECTID"])
    revise_json(source, "ARPAE_COMPLETE.json", page)
    revise_json(source, "ARPAE_IDS.json", ids)
    revise_json(source, "ARPAE_COUNT.json", {"count": 331})
    output = tmp_path / "must_not_exist"
    with pytest.raises(ValueError, match="reviewed source"):
        BUNDLE.create_bundle(source, output)
    assert not output.exists()
