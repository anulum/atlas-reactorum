# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native versioned industrial provenance conformance
"""Verify exact legacy reproduction and explicit provenance migration on original sources."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

from ._catalogue_inputs import run_cli
from ._industrial7_sources import PREFIX, SCRIPTS
from ._industrial7_sources import source_custody as source_custody

ARTIFACTS = importlib.import_module(PREFIX + ".artifacts")
BUNDLE = importlib.import_module(PREFIX + ".bundle")
VALIDATION = importlib.import_module(PREFIX + ".validate")


def bundle_bytes(directory: Path) -> dict[str, bytes]:
    """Read every artifact without rewriting a frozen source or its inventory."""
    return {path.name: path.read_bytes() for path in directory.iterdir()}


@pytest.fixture(params=[1, 2])
def versioned_bundle(tmp_path: Path, source_custody: Path, request: pytest.FixtureRequest) -> Path:
    """Create both exact report contracts from the same complete original custody."""
    output = tmp_path / "bundle"
    assert BUNDLE.create_bundle(source_custody, output) == 421
    if request.param == 1:
        snapshot, manifest, observations = ARTIFACTS.read_bundle(output)
        for name, body in ARTIFACTS.expected_artifacts(
            snapshot, manifest, observations, schema_version=1
        ).items():
            (output / name).write_bytes(body)
    assert VALIDATION.validate_bundle(output, capture_directory=source_custody) == 421
    return output


@pytest.mark.parametrize("optimised", [False, True])
def test_native_frozen_reproduction_retains_version_and_all_original_bytes(
    tmp_path: Path, versioned_bundle: Path, optimised: bool
) -> None:
    before = bundle_bytes(versioned_bundle)
    output = tmp_path / "reproduced"
    result = run_cli(
        SCRIPTS / "bundle.py",
        "--frozen-directory",
        str(versioned_bundle),
        "--output-directory",
        str(output),
        cwd=tmp_path,
        optimize=optimised,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert bundle_bytes(output) == before
    assert bundle_bytes(versioned_bundle) == before
    assert VALIDATION.validate_bundle(output) == 421


@pytest.mark.parametrize("optimised", [False, True])
def test_explicit_native_upgrade_changes_only_report_and_inventory(
    tmp_path: Path, versioned_bundle: Path, source_custody: Path, optimised: bool
) -> None:
    before = bundle_bytes(versioned_bundle)
    version = json.loads(before[ARTIFACTS.BUNDLE_MANIFEST])["schema_version"]
    output = tmp_path / "upgraded"
    result = run_cli(
        SCRIPTS / "bundle.py",
        "--frozen-directory",
        str(versioned_bundle),
        "--upgrade-provenance",
        "--output-directory",
        str(output),
        cwd=tmp_path,
        optimize=optimised,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    after = bundle_bytes(output)
    assert after.keys() == before.keys()
    expected_changes = {"RIGHTS.md", ARTIFACTS.BUNDLE_MANIFEST} if version == 1 else set()
    assert {name for name in before if before[name] != after[name]} == expected_changes
    inventory = json.loads(after[ARTIFACTS.BUNDLE_MANIFEST])
    original_inventory = json.loads(before[ARTIFACTS.BUNDLE_MANIFEST])
    assert inventory["schema_version"] == 2
    assert inventory["selected_counts"] == original_inventory["selected_counts"]
    for name, metadata in inventory["files"].items():
        assert metadata["license"] == original_inventory["files"][name]["license"]
        assert metadata["sha256"] == hashlib.sha256(after[name]).hexdigest()
        assert metadata["bytes"] == len(after[name])
    report = after["RIGHTS.md"].decode()
    assert report.startswith("<!--\n")
    hidden, prose = report.split("-->", 1)
    assert len(hidden.removeprefix("<!--\n").splitlines()) == 7
    assert prose.startswith("\n\n# Industrial round 7 source rights and attribution\n")
    if version == 1:
        assert prose.removeprefix("\n\n").encode() == before["RIGHTS.md"]
    assert VALIDATION.validate_bundle(output, capture_directory=source_custody) == 421
    assert bundle_bytes(versioned_bundle) == before


@pytest.mark.parametrize("value", [True, False, 1.0, 2.0, 0, 3, None, "2"])
def test_unsupported_inventory_version_is_refused_before_output(
    tmp_path: Path, versioned_bundle: Path, value: object
) -> None:
    path = versioned_bundle / ARTIFACTS.BUNDLE_MANIFEST
    inventory = json.loads(path.read_text())
    inventory["schema_version"] = value
    path.write_text(json.dumps(inventory))
    before = bundle_bytes(versioned_bundle)
    output = tmp_path / "must-not-exist"
    result = run_cli(
        SCRIPTS / "bundle.py",
        "--frozen-directory",
        str(versioned_bundle),
        "--upgrade-provenance",
        "--output-directory",
        str(output),
        cwd=tmp_path,
        optimize=True,
    )
    assert result.returncode == 1
    assert not output.exists()
    assert bundle_bytes(versioned_bundle) == before


@pytest.mark.parametrize("mutation", ["version", "report", "rebound_report"])
@pytest.mark.parametrize("optimised", [False, True])
def test_cross_version_or_self_rebound_report_never_validates(
    tmp_path: Path, versioned_bundle: Path, mutation: str, optimised: bool
) -> None:
    inventory_path = versioned_bundle / ARTIFACTS.BUNDLE_MANIFEST
    inventory = json.loads(inventory_path.read_text())
    rights = versioned_bundle / "RIGHTS.md"
    if mutation == "version":
        inventory["schema_version"] = 3 - inventory["schema_version"]
    else:
        rights.write_bytes(rights.read_bytes() + b"altered report\n")
        if mutation == "rebound_report":
            inventory["files"]["RIGHTS.md"]["bytes"] = rights.stat().st_size
            inventory["files"]["RIGHTS.md"]["sha256"] = hashlib.sha256(
                rights.read_bytes()
            ).hexdigest()
    inventory_path.write_text(json.dumps(inventory, sort_keys=True, indent=2) + "\n")
    before = bundle_bytes(versioned_bundle)
    result = run_cli(
        SCRIPTS / "validate.py",
        "--directory",
        str(versioned_bundle),
        cwd=tmp_path,
        optimize=optimised,
    )
    assert result.returncode == 1
    assert bundle_bytes(versioned_bundle) == before


@pytest.mark.parametrize("value", [True, 1.0, 0, 3])
def test_public_renderer_refuses_unsupported_bundle_contract(
    versioned_bundle: Path, value: object
) -> None:
    snapshot, manifest, observations = ARTIFACTS.read_bundle(versioned_bundle)
    with pytest.raises(ValueError, match="version"):
        ARTIFACTS.expected_artifacts(snapshot, manifest, observations, schema_version=value)


@pytest.mark.parametrize("optimised", [False, True])
def test_upgrade_requires_frozen_input_and_preserves_capture_custody(
    tmp_path: Path, source_custody: Path, optimised: bool
) -> None:
    before = bundle_bytes(source_custody)
    output = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="frozen"):
        BUNDLE.create_bundle(source_custody, output, upgrade_provenance=True)
    result = run_cli(
        SCRIPTS / "bundle.py",
        "--capture-directory",
        str(source_custody),
        "--upgrade-provenance",
        "--output-directory",
        str(output),
        cwd=tmp_path,
        optimize=optimised,
    )
    assert result.returncode == 2
    assert not output.exists()
    assert bundle_bytes(source_custody) == before
