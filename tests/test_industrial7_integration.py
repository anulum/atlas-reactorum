# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_industrial7_integration.py
"""Exercise complete round-seven custody through the actual map build and Node assets."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.rebuild import copy_source

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "04_interactive_presentation/scripts/build_datasets.py"
LAYER = Path("05_global_reactor_map/imports/industrial_facilities/expansion_round7")
MEMBERS = (
    "selected_source_snapshot.tsv",
    "industrial_facilities_round7.tsv",
    "source_manifest.json",
    "source_registry.tsv",
    "source_snapshot_manifest.tsv",
    "RIGHTS.md",
    "bundle_manifest.json",
)
NODE = shutil.which("node") or "node"


@pytest.fixture
def complete_source(tmp_path: Path) -> Path:
    """Copy every actual release input into a new source tree.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Session-owned external directory for a complete source copy.

    Returns
    -------
    pathlib.Path
        New source tree with generated products and private records omitted.
    """
    source = tmp_path / "source"
    copy_source(ROOT, source)
    return source


def run_build(source: Path, optimized: bool) -> subprocess.CompletedProcess[str]:
    """Run the actual map builder from another directory using complete real sources.

    Parameters
    ----------
    source : pathlib.Path
        Newly owned copy of all repository source inputs.
    optimized : bool
        Whether the real interpreter runs with assertions disabled.

    Returns
    -------
    subprocess.CompletedProcess of str
        Native CLI result, including diagnostics on a refused source bundle.
    """
    return subprocess.run(
        [
            sys.executable,
            *(("-O",) if optimized else ()),
            str(BUILDER),
            "--source-root",
            str(source),
            "--data-dir",
            str(source / "04_interactive_presentation/data"),
        ],
        cwd=source.parent,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize("optimized", [False, True])
def test_all_original_cells_and_full_node_assets_reach_the_map(
    complete_source: Path, optimized: bool
) -> None:
    result = run_build(complete_source, optimized)
    assert result.returncode == 0, result.stderr
    data = complete_source / "04_interactive_presentation/data"
    document = json.loads((data / "global_reactors.sample.json").read_text())
    selected = [
        row for row in document["records"] if row.get("dataset_source") == str(LAYER / MEMBERS[1])
    ]
    with (complete_source / LAYER / MEMBERS[1]).open(newline="", encoding="utf-8") as handle:
        source = list(csv.DictReader(handle, delimiter="\t"))
    assert document["record_count"] == 13459
    assert len(source) == len(selected) == 421
    assert len({row["id"] for row in document["records"]}) == 13459
    assert {row["country"] for row in selected} == {"Switzerland", "Italy"}
    by_id = {row["stable_id"]: row for row in selected}
    for row in source:
        record = by_id[row["stable_id"]]
        for field, value in row.items():
            if field in {"lat", "lon"}:
                assert record[field] == float(value), (row["stable_id"], field)
            elif field == "status":
                assert record["source_status"] == value
            else:
                assert record[field] == value, (row["stable_id"], field)
        assert record["reactor_type_if_explicit"] == ""
        assert record["operator"] == row["operator"]
        assert record["capacity"] == row["capacity"]
    inventory = json.loads((data / "dataset-inventory.json").read_text())
    assert inventory["imported_industrial_facilities_round7"] == 421
    assert inventory["facility_domains"]["chemical"] == 11086
    supplemental = json.loads((data / "facilities-supplemental.json").read_text())
    assert inventory["supplemental_facilities"] == len(supplemental["records"]) == 10
    for name in MEMBERS:
        path = complete_source / LAYER / name
        assert (
            inventory["inputs"][str(LAYER / name)] == hashlib.sha256(path.read_bytes()).hexdigest()
        )

    script = """
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const folder = process.argv[1];
for (const [file, key] of [
  ['global_reactors.sample', 'REACTOR_FACILITIES'],
  ['fusion_companies.sample', 'FUSION_COMPANIES']
]) {
  const context = {window: {}};
  vm.runInNewContext(fs.readFileSync(folder + '/' + file + '.js', 'utf8'), context);
  const actual = JSON.parse(JSON.stringify(context.window[key]));
  assert.deepEqual(actual, JSON.parse(fs.readFileSync(folder + '/' + file + '.json', 'utf8')));
}
process.stdout.write('complete JavaScript/JSON parity');
"""
    node = subprocess.run(
        [NODE, "-e", script, str(data)], capture_output=True, text=True, timeout=30, check=False
    )
    assert node.returncode == 0, node.stderr
    assert node.stdout == "complete JavaScript/JSON parity"


@pytest.mark.parametrize("optimized", [False, True])
def test_absent_round_preserves_every_other_published_record(
    complete_source: Path, optimized: bool
) -> None:
    for name in MEMBERS:
        (complete_source / LAYER / name).unlink()
    result = run_build(complete_source, optimized)
    assert result.returncode == 0, result.stderr
    data = complete_source / "04_interactive_presentation/data"
    records = json.loads((data / "global_reactors.sample.json").read_text())["records"]
    published = json.loads(
        (ROOT / "04_interactive_presentation/data/global_reactors.sample.json").read_text()
    )["records"]
    expected = [row for row in published if row.get("dataset_source") != str(LAYER / MEMBERS[1])]
    assert records == expected
    assert len(records) == 13038
    inventory = json.loads((data / "dataset-inventory.json").read_text())
    assert inventory["imported_industrial_facilities_round7"] == 0
    assert not any(path.startswith(str(LAYER)) for path in inventory["inputs"])


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("missing", MEMBERS)
def test_any_incomplete_bundle_refuses_map_outputs(
    complete_source: Path, optimized: bool, missing: str
) -> None:
    (complete_source / LAYER / missing).unlink()
    result = run_build(complete_source, optimized)
    assert result.returncode != 0
    data = complete_source / "04_interactive_presentation/data"
    assert not (data / "global_reactors.sample.json").exists()
    assert not (data / "global_reactors.sample.js").exists()
    assert not (data / "fusion_companies.sample.json").exists()
    assert not (data / "dataset-inventory.json").exists()


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("changed", [MEMBERS[0], MEMBERS[1], MEMBERS[2]])
def test_changed_source_cells_or_resource_grant_refuse_map_outputs(
    complete_source: Path, optimized: bool, changed: str
) -> None:
    path = complete_source / LAYER / changed
    if changed == MEMBERS[2]:
        manifest = json.loads(path.read_text())
        manifest["grants"]["ch-sfoe-biogas"]["resource_id"] = "another-resource"
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    else:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fields = list(reader.fieldnames or ())
            rows = list(reader)
        field = "operator" if changed == MEMBERS[0] else "capacity"
        rows[0][field] = "altered source value"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    result = run_build(complete_source, optimized)
    assert result.returncode != 0
    assert not (
        complete_source / "04_interactive_presentation/data/global_reactors.sample.json"
    ).exists()


def test_dangling_completion_inventory_is_not_an_absent_round(complete_source: Path) -> None:
    for name in MEMBERS:
        (complete_source / LAYER / name).unlink()
    (complete_source / LAYER / MEMBERS[-1]).symlink_to("missing-inventory.json")
    result = run_build(complete_source, True)
    assert result.returncode != 0
    assert not (
        complete_source / "04_interactive_presentation/data/global_reactors.sample.json"
    ).exists()


def test_complete_round_can_build_without_absent_earlier_industrial_layers(
    complete_source: Path,
) -> None:
    parent = complete_source / LAYER.parent
    (parent / "industrial_facilities.tsv").unlink()
    for number in range(2, 7):
        (parent / f"expansion_round{number}/industrial_facilities_round{number}.tsv").unlink()
    result = run_build(complete_source, True)
    assert result.returncode == 0, result.stderr
    data = complete_source / "04_interactive_presentation/data"
    document = json.loads((data / "global_reactors.sample.json").read_text())
    assert document["record_count"] == 2794
    assert (
        len(
            [
                row
                for row in document["records"]
                if row.get("dataset_source") == str(LAYER / MEMBERS[1])
            ]
        )
        == 421
    )
