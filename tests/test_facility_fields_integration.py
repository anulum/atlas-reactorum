# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — frozen facility-field runtime integration

"""Exercise complete frozen source bindings through real release records and native CLI."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from metadata.facility_fields.inputs import mapping, original_rows
from metadata.facility_fields.runtime import MEMBERS, apply_fields
from tools.rebuild import copy_source

from ._facility_field_sources import PINS, ROOT, document
from ._facility_field_sources import original_source as original_source


def release_projection(root: Path) -> list[dict[str, object]]:
    """Supply complete accepted frozen bytes and actual public facility records.

    Parameters
    ----------
    root : Path
        Owned source-copy directory receiving the frozen projection members.

    Returns
    -------
    list of dict
        Complete current public facility rows without converting source field values.

    Raises
    ------
    OSError
        An owned source or output member cannot be read or written.
    """
    for member in MEMBERS[:2]:
        shutil.copy2(ROOT / member, root / member)
    return original_rows(
        document(ROOT / "04_interactive_presentation/data/global_reactors.sample.json")["records"]
    )


def replace_projection(root: Path, body: dict[str, object]) -> None:
    """Change a complete owned projection for a negative structural conformance case.

    Parameters
    ----------
    root : Path
        Owned source-copy directory receiving the frozen projection members.
    body : dict[str, object]
        Complete negative-control JSON document whose structure or source bindings were changed.

    Raises
    ------
    OSError
        An owned source or output member cannot be read or written.
    """
    data = (json.dumps(body, ensure_ascii=False, indent=2) + "\n").encode()
    (root / MEMBERS[0]).write_bytes(data)
    (root / MEMBERS[1]).write_text(hashlib.sha256(data).hexdigest() + "\n")


def test_all_frozen_assertions_apply_idempotently_to_actual_records(original_source: Path) -> None:
    """Replay all 1,631 frozen assertions twice and preserve independent primary research additions.

    Parameters
    ----------
    original_source : Path
        Owned copy of original frozen inputs and their recorded source bindings.
    """
    rows = release_projection(original_source)
    assert apply_fields(original_source, rows) == 1631
    once = copy.deepcopy(rows)
    assert apply_fields(original_source, rows) == 1631
    assert rows == once
    assert sum(bool(row.get("purpose")) for row in rows) == 1443
    assert sum(bool(row.get("fuel_or_feed")) for row in rows) == 533
    assert (
        sum(
            len(original_rows(row["field_observations"]))
            for row in rows
            if "field_observations" in row
        )
        == 1631
    )


@pytest.mark.parametrize(
    "failure",
    [
        "version",
        "count_type",
        "count",
        "row_count",
        "pins_binding",
        "fields",
        "shape",
        "source_binding",
        "target_binding",
        "purpose_basis",
        "fuel_basis",
        "duplicate",
        "blank_value",
        "different_dataset",
        "original_value",
        "pins_version",
        "pins_bool",
        "source_scope",
        "target_scope",
        "target_bytes",
    ],
)
def test_structural_and_source_binding_refusals_leave_all_actual_records_unchanged(
    original_source: Path, failure: str
) -> None:
    """Inject bound-source and contract faults and require refusal before any record is mutated.

    Parameters
    ----------
    original_source : Path
        Owned copy of original frozen inputs and their recorded source bindings.
    failure : str
        Specific source or structural fault injected into the owned input copy.
    """
    rows = release_projection(original_source)
    body = document(original_source / MEMBERS[0])
    records = original_rows(body["records"])
    body["records"] = records
    if failure == "version":
        body["schema_version"] = "unsupported"
    elif failure == "count_type":
        body["record_count"] = True
    elif failure == "count":
        body["record_count"] = 1630
    elif failure == "row_count":
        records.pop()
    elif failure == "pins_binding":
        body["source_pins_sha256"] = "changed"
    elif failure == "fields":
        records[0]["field"] = "unreviewed"
    elif failure == "shape":
        records[0]["extra"] = "unreviewed"
    elif failure in {"source_binding", "target_binding"}:
        records[0]["source_sha256" if failure == "source_binding" else "target_sha256"] = "changed"
    elif failure in {"purpose_basis", "fuel_basis"}:
        next(
            row
            for row in records
            if row["field"] == ("purpose" if failure == "purpose_basis" else "fuel_or_feed")
        )["basis"] = "physical-verification"
    elif failure == "duplicate":
        records[1] = dict(records[0])
    elif failure == "blank_value":
        records[0]["value"] = " "
    elif failure in {"different_dataset", "original_value"}:
        selected = next(
            row for row in rows if row.get("stable_id", row["id"]) == records[0]["target_id"]
        )
        selected[
            "dataset_source" if failure == "different_dataset" else str(records[0]["field"])
        ] = "owner original that must be preserved"
    elif failure == "target_bytes":
        path = original_source / str(records[0]["target_dataset"])
        path.write_bytes(path.read_bytes() + b"\n")
    else:
        pins = document(original_source / PINS)
        if failure in {"pins_version", "pins_bool"}:
            pins["schema_version"] = True if failure == "pins_bool" else 2
        else:
            mapping(pins["sources" if failure == "source_scope" else "target_datasets"]).pop(
                "industrial6-snapshot" if failure == "source_scope" else "industrial7"
            )
        (original_source / PINS).write_text(json.dumps(pins))
    replace_projection(original_source, body)
    before = copy.deepcopy(rows)
    with pytest.raises(ValueError):
        apply_fields(original_source, rows)
    assert rows == before


@pytest.mark.parametrize("member", MEMBERS)
def test_incomplete_frozen_member_refuses_runtime(original_source: Path, member: str) -> None:
    """Remove one frozen input and forbid acceptance of a partial source-bound projection.

    Parameters
    ----------
    original_source : Path
        Owned copy of original frozen inputs and their recorded source bindings.
    member : str
        Original bundle member made unavailable or aliased for this case.
    """
    rows = release_projection(original_source)
    path = original_source / member
    path.rename(path.with_suffix(path.suffix + ".unavailable"))
    with pytest.raises(ValueError):
        apply_fields(original_source, rows)


def test_complete_absence_and_optional_layer_absence_have_explicit_scope(
    original_source: Path,
) -> None:
    """Distinguish an absent optional industrial layer from a partly installed frozen bundle.

    Parameters
    ----------
    original_source : Path
        Owned copy of original frozen inputs and their recorded source bindings.
    """
    rows = release_projection(original_source)
    path = (
        original_source
        / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/industrial_facilities_round7.tsv"
    )
    path.rename(path.with_suffix(".unavailable"))
    remaining = [
        row for row in rows if row["dataset_source"] != str(path.relative_to(original_source))
    ]
    assert apply_fields(original_source, remaining) == 1210
    for member in MEMBERS:
        path = original_source / member
        path.rename(path.with_suffix(path.suffix + ".unavailable"))
    assert apply_fields(original_source, remaining) == 0


@pytest.mark.parametrize("optimize", [False, True])
def test_real_consumer_runs_without_any_original_preparation_fixture(
    tmp_path: Path, optimize: bool
) -> None:
    """Build without test helpers under normal and optimised Python, then verify native serialisers.

    Parameters
    ----------
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    optimize : bool
        Whether the real interpreter removes assertions with its -O option.
    """
    source = tmp_path / "release"
    copy_source(ROOT, source)
    (source / "tests").rename(tmp_path / "original-research-fixtures")
    data = source / "04_interactive_presentation/data"
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimize else []),
            str(ROOT / "04_interactive_presentation/scripts/build_datasets.py"),
            "--source-root",
            str(source),
            "--data-dir",
            str(data),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (source / "tests").exists()
    dataset = document(data / "global_reactors.sample.json")
    assert dataset["schema_version"] == "1.3.0"
    assert dataset["record_count"] == 13459
    inventory = document(data / "dataset-inventory.json")
    assert inventory["facility_field_assertions"] == 1631
    for member in MEMBERS:
        assert (
            mapping(inventory["inputs"])[member]
            == hashlib.sha256((source / member).read_bytes()).hexdigest()
        )
    rows = original_rows(dataset["records"])
    assert sum(bool(row.get("purpose")) for row in rows) == 1443
    assert sum(bool(row.get("fuel_or_feed")) for row in rows) == 533

    node_script = r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const data = process.argv[1], application = process.argv[2];
const context = {window: {}, URL};
for (const [file, key] of [['global_reactors.sample','REACTOR_FACILITIES'],['fusion_companies.sample','FUSION_COMPANIES']]) {
  vm.runInNewContext(fs.readFileSync(data + '/' + file + '.js', 'utf8'), context);
  assert.deepEqual(JSON.parse(JSON.stringify(context.window[key])), JSON.parse(fs.readFileSync(data + '/' + file + '.json','utf8')));
}
const declarations = fs.readFileSync(application, 'utf8').split('document.addEventListener("DOMContentLoaded"')[0];
vm.runInNewContext(declarations, context);
for (const record of context.window.REACTOR_FACILITIES) {
  const html = context.facilityFieldSources(record);
  if (!record.field_observations) { assert.equal(html, ''); continue; }
  assert.ok(html.includes('Source field assertions'));
  for (const row of record.field_observations) {
    assert.ok(html.includes(row.checked));
    assert.ok(html.includes(row.license));
    assert.ok(html.includes(row.source_field));
  }
}
const original = context.window.REACTOR_FACILITIES.find(r => r.field_observations);
const damaged = JSON.parse(JSON.stringify(original));
damaged.field_observations[0].value += '<script>alert(1)</script>';
assert.ok(!context.facilityFieldSources(damaged).includes('<script>'));
process.stdout.write('complete JSON/JavaScript parity and public field HTML serialization; no browser acceptance claimed');
"""
    native = subprocess.run(
        [
            shutil.which("node") or "node",
            "-e",
            node_script,
            str(data),
            str(ROOT / "04_interactive_presentation/app.js"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert native.returncode == 0, native.stderr
    assert "complete JSON/JavaScript parity" in native.stdout
