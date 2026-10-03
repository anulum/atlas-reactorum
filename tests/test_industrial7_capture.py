# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — original full-capture native conformance
"""Exercise public custody CLI and full positive source rights using complete original bytes."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from ._industrial7_sources import CAPTURE, copy_custody, receipt_change, revise_json, run_cli
from ._industrial7_sources import source_custody as source_custody


def test_complete_original_source_and_unchanged_custody(
    source_custody: Path,
) -> None:
    paths = [path for path in source_custody.iterdir() if path.is_file()]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    rows, receipts = CAPTURE.read_captures(source_custody)
    assert len(rows) == 421 and len(receipts) == 8
    assert sum(row["source"] == "ch-sfoe-biogas" for row in rows) == 153
    assert sum(bool(row["source_position_warning"]) for row in rows) == 23
    assert rows == sorted(rows, key=lambda row: (row["source"], row["source_record_id"].casefold()))
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths} == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "unrelated"),
        ("bytes", 1),
        ("bytes", "19723"),
        ("sha256", "wrong"),
        ("tls_verified", False),
        ("http_status", 301),
        ("http_status", 200.0),
        ("retrieved_utc", "invalid"),
        ("retrieved_utc", "2026-09-30T20:00:00"),
        ("retrieved_utc", "9999-01-01T00:00:00+00:00"),
        ("url", None),
        ("url", "http://untrusted.invalid"),
        ("url", "https://unrelated.invalid/data"),
        ("origin_url", "https://unrelated.invalid/data"),
    ],
)
def test_original_receipt_binding(
    source_custody: Path, tmp_path: Path, field: str, value: object
) -> None:
    copy_custody(tmp_path / "copy", source_custody)
    directory = tmp_path / "copy"
    receipt_change(directory, "SFOE_ORIGINAL.csv.zip", field, value)
    with pytest.raises(ValueError):
        CAPTURE.read_captures(directory)


@pytest.mark.parametrize("kind", ["missing", "symlink", "oversized", "unsafe_name"])
def test_original_body_file_bounds(source_custody: Path, tmp_path: Path, kind: str) -> None:
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    name = "SFOE_ORIGINAL.csv.zip"
    path = directory / name
    if kind == "unsafe_name":
        name = "../SFOE_ORIGINAL.csv.zip"
    else:
        path.unlink()
        if kind == "symlink":
            path.symlink_to(source_custody / name)
        elif kind == "oversized":
            with path.open("wb") as stream:
                stream.truncate(CAPTURE.MAX_BYTES + 1)
    with pytest.raises(ValueError):
        CAPTURE.verified_receipt(directory, name, expected_url=CAPTURE.SFOE_URL)


@pytest.mark.parametrize(
    ("name", "field", "value"),
    [
        ("ARPAE_COUNT.json", "count", 0),
        ("ARPAE_COUNT.json", "count", True),
        ("ARPAE_COUNT.json", "count", 100001),
        ("ARPAE_LAYER.json", "maxRecordCount", 0),
        ("ARPAE_LAYER.json", "maxRecordCount", True),
        ("ARPAE_LAYER.json", "maxRecordCount", 100001),
    ],
)
def test_native_source_page_plan_limits(
    source_custody: Path, tmp_path: Path, name: str, field: str, value: object
) -> None:
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    data = json.loads((directory / name).read_text())
    data[field] = value
    revise_json(directory, name, data)
    with pytest.raises(ValueError, match="outside its bound"):
        CAPTURE.read_captures(directory)


@pytest.mark.parametrize(
    "kind",
    [
        "swiss_failure",
        "italian_failure",
        "swiss_missing",
        "swiss_duplicate",
        "swiss_url",
        "swiss_rights",
        "swiss_license",
        "italian_missing",
        "italian_duplicate",
        "italian_url",
        "italian_license",
        "terms_changed",
    ],
)
def test_full_native_exact_resource_rights(source_custody: Path, tmp_path: Path, kind: str) -> None:
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    if kind == "terms_changed":
        path = directory / "SFOE_TERMS.html"
        path.write_bytes(path.read_bytes() + b" ")
        receipt_change(directory, path.name, "bytes", path.stat().st_size)
        receipt_change(
            directory, path.name, "sha256", hashlib.sha256(path.read_bytes()).hexdigest()
        )
    else:
        swiss = kind.startswith("swiss")
        name = "SFOE_METADATA.json" if swiss else "ARPAE_METADATA.json"
        data = json.loads((directory / name).read_text())
        if kind.endswith("failure"):
            data["success"] = False
        else:
            meta = data["result"]
            identity = (
                "6a31d549-be3e-4727-a4f8-05d7d2ab5c54"
                if swiss
                else "1af54eda-b778-4b21-a8dc-e4710600d25d"
            )
            exact = next(resource for resource in meta["resources"] if resource["id"] == identity)
            if kind.endswith("missing"):
                exact["id"] = "unverified-resource"
            elif kind.endswith("duplicate"):
                meta["resources"].append(exact.copy())
            elif not swiss and kind.endswith("license"):
                meta["license_id"] = "unverified"
            else:
                exact[kind.rsplit("_", 1)[1]] = "unrelated"
        revise_json(directory, name, data)
    with pytest.raises(ValueError):
        CAPTURE.read_captures(directory)


@pytest.mark.parametrize("kind", ["empty", "ambiguous", "page_filename"])
def test_complete_page_membership(source_custody: Path, tmp_path: Path, kind: str) -> None:
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    if kind != "ambiguous":
        (directory / "ARPAE_COMPLETE.json").unlink()
    if kind != "empty":
        shutil.copy2(source_custody / "ARPAE_COMPLETE.json", directory / "ARPAE_PAGE_0001.json")
    with pytest.raises(ValueError):
        CAPTURE.read_captures(directory)


def test_receipt_mirror_origin_and_actual_utc_date(source_custody: Path, tmp_path: Path) -> None:
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    name = "SFOE_ORIGINAL.csv.zip"
    receipt_change(directory, name, "origin_url", CAPTURE.SFOE_URL)
    receipt_change(directory, name, "mirror_base", "https://trusted.institution.invalid/corpus")
    receipt_change(directory, name, "url", "https://trusted.institution.invalid/corpus/" + name)
    receipt_change(directory, name, "retrieved_utc", "2026-09-29T23:30:00-01:00")
    rows, _ = CAPTURE.read_captures(directory)
    assert (
        next(row for row in rows if row["source"] == "ch-sfoe-biogas")["retrieved"] == "2026-09-30"
    )


@pytest.mark.parametrize(
    "mirror", [None, "", True, "http://host", "https://host?query=1", "https://host/wrong"]
)
def test_mirror_declaration_is_bound_to_the_actual_resource(
    source_custody: Path, tmp_path: Path, mirror: object
) -> None:
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    name = "SFOE_ORIGINAL.csv.zip"
    receipt_change(directory, name, "origin_url", CAPTURE.SFOE_URL)
    receipt_change(directory, name, "url", "https://host/corpus/" + name)
    receipt_change(directory, name, "mirror_base", mirror)
    with pytest.raises(ValueError):
        CAPTURE.read_captures(directory)


@pytest.mark.parametrize("optimize", [False, True])
def test_native_public_cli_and_optimized_refusals(
    source_custody: Path, tmp_path: Path, optimize: bool
) -> None:
    success = run_cli("capture", source_custody, optimize=optimize)
    assert success.returncode == 0, success.stdout + success.stderr
    assert json.loads(success.stdout)["observations"] == 421
    directory = tmp_path / "copy"
    copy_custody(directory, source_custody)
    receipt_change(directory, "ARPAE_IDS.json", "url", "https://unrelated.invalid/")
    failure = run_cli("capture", directory, optimize=optimize)
    assert failure.returncode == 1 and "CAPTURE CHECK FAILED" in failure.stdout
    assert "Traceback" not in failure.stderr
