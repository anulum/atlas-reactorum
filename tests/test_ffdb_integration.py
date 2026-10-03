# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — source-bound FFDB map integration tests

"""Exercise the pinned source through its real consumer, map CLI and Node exports."""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

from metadata.facility_fields.inputs import mapping, original_rows
from tools.rebuild import copy_source

from ._catalogue_inputs import run_cli
from .conftest import ROOT

LAYER = "05_global_reactor_map/imports/fusion/ffdb"
BUILDER = ROOT / "04_interactive_presentation/scripts/build_datasets.py"


@pytest.fixture(scope="module")
def integration() -> ModuleType:
    """Load the actual source consumer with its normal namespace imports."""
    return importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.integration")


@pytest.fixture
def registered_source(tmp_path: Path, integration: ModuleType) -> Path:
    """Copy every complete production input needed by the FFDB consumer."""
    source = tmp_path / "source"
    for member in integration.INPUTS:
        path = source / member
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / member, path)
    return source


def test_public_consumer_retains_all_identities_raw_coordinates_and_absences(
    integration: ModuleType,
    build_datasets: ModuleType,
) -> None:
    rows: list[dict[str, object]] = integration.build_facilities(
        ROOT, build_datasets.normalize_status
    )
    assert len(rows) == 174
    assert len({row["id"] for row in rows}) == 174
    assert all(re.fullmatch(r"iaea-ffdb:[0-9a-f]{64}", str(row["id"])) for row in rows)
    assert sum(row["lat"] is not None and row["lon"] is not None for row in rows) == 137
    assert all(row["lat"] is None and row["lon"] is None for row in rows if row["lat"] is None)
    with (ROOT / LAYER / "fusion_facilities.tsv").open(newline="", encoding="utf-8") as stream:
        source_rows = list(csv.DictReader(stream, delimiter="\t"))
    by_id = {row["stable_id"]: row for row in rows}
    for original in source_rows:
        record = by_id[original["stable_id"]]
        for field, value in original.items():
            if field in {"lat", "lon"}:
                assert record[field] == (float(value) if value else None)
            elif field == "status":
                assert record["source_status"] == value
                assert record[field] == build_datasets.normalize_status(value)
            else:
                assert record[field] == value
        assert record["first_operation"] == record["last_operation"] == ""
        assert record["enrichment_applied"] is False
        assert record["dataset_source"] == f"{LAYER}/fusion_facilities.tsv"
        assert (
            record["id"]
            == "iaea-ffdb:" + hashlib.sha256(original["stable_id"].encode("utf-8")).hexdigest()
        )


@pytest.mark.parametrize("failure", ["missing", "utf8", "json", "header", "rows", "provenance"])
def test_public_consumer_refuses_unreadable_or_changed_source_products(
    registered_source: Path,
    integration: ModuleType,
    build_datasets: ModuleType,
    failure: str,
) -> None:
    table = registered_source / LAYER / "fusion_facilities.tsv"
    provenance = registered_source / LAYER / "field_provenance.json"
    if failure == "missing":
        table.rename(table.with_suffix(".unavailable"))
    elif failure == "utf8":
        table.write_bytes(b"\xff")
    elif failure == "json":
        provenance.write_text("{")
    elif failure == "header":
        table.write_text(table.read_text().replace("stable_id", "different_id", 1))
    elif failure == "rows":
        lines = table.read_text().splitlines(keepends=True)
        table.write_text("".join(lines[:-1]))
    else:
        body = mapping(json.loads(provenance.read_text()))
        body["source_sha256"] = "changed"
        provenance.write_text(json.dumps(body))
    with pytest.raises(integration.DashboardRefused):
        integration.build_facilities(registered_source, build_datasets.normalize_status)


@pytest.mark.parametrize("optimize", [False, True])
def test_default_map_cli_and_node_exports_use_only_the_new_fusion_catalogue(
    tmp_path: Path,
    optimize: bool,
) -> None:
    source = tmp_path / "source"
    copy_source(ROOT, source)
    data = source / "04_interactive_presentation/data"
    result = run_cli(
        BUILDER, "--source-root", str(source), "--data-dir", str(data), optimize=optimize
    )
    assert result.returncode == 0, result.stderr
    document = mapping(json.loads((data / "global_reactors.sample.json").read_text()))
    rows = original_rows(document["records"])
    ffdb_rows = [row for row in rows if row["dataset_source"] == f"{LAYER}/fusion_facilities.tsv"]
    assert document["record_count"] == 13459
    assert len(ffdb_rows) == 174
    assert not any(
        str(row["dataset_source"]).endswith("fusion/fusion_facilities.tsv") for row in rows
    )
    assert not any(
        str(row["dataset_source"]).endswith("fusion/enrichment/new_facilities.tsv") for row in rows
    )
    assert all(row["enrichment_applied"] is False for row in ffdb_rows)
    assert sum(row["lat"] is not None for row in ffdb_rows) == 137
    inventory = mapping(json.loads((data / "dataset-inventory.json").read_text()))
    assert inventory["fusion_source"] == "ffdb"
    assert inventory["imported_fusion_facilities"] == 174
    assert all(
        inventory[key] == 0
        for key in (
            "fusion_facility_enrichments",
            "fusion_facility_enrichments_round2",
            "fusion_facility_enrichments_round3",
            "new_fusion_facilities",
        )
    )
    inputs = mapping(inventory["inputs"])
    module = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.integration")
    for member in module.INPUTS:
        assert inputs[member] == hashlib.sha256((source / member).read_bytes()).hexdigest()
    assert "05_global_reactor_map/imports/fusion/fusion_facilities.tsv" not in inputs
    native = subprocess.run(
        [
            shutil.which("node") or "node",
            "-e",
            r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const path = process.argv[1], context = {window: {}};
for (const [name, key] of [['global_reactors.sample', 'REACTOR_FACILITIES'], ['fusion_companies.sample', 'FUSION_COMPANIES']]) {
    vm.runInNewContext(fs.readFileSync(path + '/' + name + '.js', 'utf8'), context);
    assert.deepEqual(JSON.parse(JSON.stringify(context.window[key])), JSON.parse(fs.readFileSync(path + '/' + name + '.json', 'utf8')));
}
process.stdout.write('complete new-source JSON/JavaScript parity');
""",
            str(data),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert native.returncode == 0, native.stderr


@pytest.mark.parametrize("optimize", [False, True])
@pytest.mark.parametrize(
    "member",
    [
        "source_manifest.json",
        "visible_data.frames",
        "fusion_facilities.tsv",
        "field_provenance.json",
    ],
)
def test_map_cli_cannot_fall_back_to_historical_rows_when_ffdb_is_incomplete(
    registered_source: Path,
    tmp_path: Path,
    optimize: bool,
    member: str,
) -> None:
    path = registered_source / LAYER / member
    path.rename(path.with_suffix(path.suffix + ".unavailable"))
    historical = registered_source / "05_global_reactor_map/imports/fusion/fusion_facilities.tsv"
    historical.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / historical.relative_to(registered_source), historical)
    data = tmp_path / "uncreated-output"
    result = run_cli(
        BUILDER, "--source-root", str(registered_source), "--data-dir", str(data), optimize=optimize
    )
    assert result.returncode != 0
    assert not data.exists()


def test_explicit_historical_route_preserves_its_original_records_and_input_scope(
    tmp_path: Path,
) -> None:
    source = tmp_path / "historical"
    copy_source(ROOT, source)
    data = source / "04_interactive_presentation/data"
    result = run_cli(
        BUILDER,
        "--source-root",
        str(source),
        "--data-dir",
        str(data),
        "--fusion-source",
        "historical",
    )
    assert result.returncode == 0, result.stderr
    records = original_rows(
        mapping(json.loads((data / "global_reactors.sample.json").read_text()))["records"]
    )
    assert len(records) == 13438
    assert not any(str(row["dataset_source"]).startswith(LAYER) for row in records)
    inventory = mapping(json.loads((data / "dataset-inventory.json").read_text()))
    assert inventory["fusion_source"] == "historical"
    assert inventory["imported_fusion_facilities"] == 146
    public_input = ROOT / "05_global_reactor_map/imports/fusion/fusion_facilities.tsv"
    assert (
        mapping(inventory["inputs"])["05_global_reactor_map/imports/fusion/fusion_facilities.tsv"]
        == hashlib.sha256(public_input.read_bytes()).hexdigest()
    )
    assert not any(str(row["dataset_source"]).startswith(LAYER) for row in records)
    assert not any(str(key).startswith(LAYER) for key in mapping(inventory["inputs"]))


@pytest.mark.parametrize("optimize", [False, True])
@pytest.mark.parametrize(
    "arguments",
    [
        ("--fusion-source", "historical-full"),
        ("--historical-bundle", "/unavailable/frozen-inputs"),
    ],
)
def test_full_historical_selection_requires_explicit_consistent_arguments(
    tmp_path: Path, optimize: bool, arguments: tuple[str, ...]
) -> None:
    """A missing full input or incompatible selection refuses before output starts."""
    data = tmp_path / "uncreated-output"
    result = run_cli(BUILDER, "--data-dir", str(data), *arguments, optimize=optimize)
    assert result.returncode == 2 and not data.exists()
    assert not result.stdout and "Traceback" not in result.stderr
    assert "requires" in result.stderr
