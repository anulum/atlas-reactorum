# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — primary research producer and release consumer conformance
"""Exercise the actual projection and release CLI with complete original inputs.

Software citation fixtures below confer no scientific acceptance. A complete
production review is still required before publishing the real source ledger.
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.rebuild import repository_files

from .test_research_primary_projection import ROOT, citation, inputs, ledger
from .test_research_primary_projection import baseline as baseline

PRIMARY = importlib.import_module(
    "05_global_reactor_map.imports.research_reactors.official_source_enrichment.primary_integration"
)
LAYER = "05_global_reactor_map/imports/research_reactors/official_source_enrichment"


@pytest.fixture
def primary_bundle(tmp_path: Path, baseline: dict[str, dict[str, str]]) -> Path:
    """Produce a real full-cohort bundle, with distinct selected and held fixture roles.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.

    Returns
    -------
    pathlib.Path
        Directory containing the three complete producer-bound fixture members.
    """
    directory = tmp_path / "bundle"
    directory.mkdir()
    original, fields = inputs(directory, baseline)
    original.rename(directory / PRIMARY.MEMBERS[0])
    fields.rename(directory / PRIMARY.MEMBERS[1])
    decisions = ledger(baseline)
    for field, decision, value in (
        ("purpose", "selected", "Exact contract fixture purpose <&>"),
        ("operator", "held", "Unresolved contract fixture operator"),
        ("first_criticality", "selected", "1957-08"),
    ):
        row = next(row for row in decisions if row["field"] == field)
        citation(row)
        row.update(selection=decision, value=value)
        if field == "first_criticality":
            row["date_precision"] = "month"
    with (directory / PRIMARY.MEMBERS[1]).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=decisions[0], delimiter="\t")
        writer.writeheader()
        writer.writerows(decisions)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / LAYER / "build_projection.py"),
            "--baseline",
            str(directory / PRIMARY.MEMBERS[0]),
            "--assertions",
            str(directory / PRIMARY.MEMBERS[1]),
            "--output",
            str(directory / PRIMARY.MEMBERS[2]),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["selected_fields"] == 2
    return directory


def test_producer_output_consumer_preserves_all_original_cells_and_decisions(
    primary_bundle: Path, baseline: dict[str, dict[str, str]]
) -> None:
    """Consume a complete producer bundle and retain every original nonempty cell and no-fill decision.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    """
    projection = PRIMARY.load_projection(baseline, primary_bundle)
    assert projection is not None
    assert len(projection.rows) == 172 and len(projection.assertions) == 358
    for assertion in projection.assertions:
        value = projection.rows[assertion["stable_id"]][assertion["field"]]
        assert value == (assertion["value"] if assertion["selection"] == "selected" else "")
    for identity, original in baseline.items():
        for field, value in original.items():
            if value:
                assert projection.rows[identity][field] == value


def test_historical_build_requires_no_primary_overlay(
    tmp_path: Path, baseline: dict[str, dict[str, str]]
) -> None:
    """Keep historical builds unchanged when the whole optional primary bundle is absent.

    Parameters
    ----------
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    """
    assert PRIMARY.load_projection(baseline, tmp_path) is None


@pytest.mark.parametrize("member", PRIMARY.MEMBERS)
def test_missing_bundle_member_refuses_instead_of_silently_using_partial_data(
    primary_bundle: Path, baseline: dict[str, dict[str, str]], member: str
) -> None:
    """Remove each member in turn and require refusal of a partially installed primary review.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    member : str
        Original bundle member made unavailable or aliased for this case.
    """
    (primary_bundle / member).rename(primary_bundle / "retained-original")
    with pytest.raises(ValueError, match="complete original"):
        PRIMARY.load_projection(baseline, primary_bundle)


@pytest.mark.parametrize("member", PRIMARY.MEMBERS)
def test_source_alias_refuses_the_public_consumer(
    primary_bundle: Path, baseline: dict[str, dict[str, str]], member: str
) -> None:
    """Refuse each aliased bundle member through the same consumer used by the release builder.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    member : str
        Original bundle member made unavailable or aliased for this case.
    """
    path = primary_bundle / member
    original = primary_bundle / "retained-original"
    path.rename(original)
    path.symlink_to(original)
    with pytest.raises(ValueError, match="complete original"):
        PRIMARY.load_projection(baseline, primary_bundle)


def test_original_baseline_drift_is_not_approved_by_a_matching_stable_identity(
    primary_bundle: Path, baseline: dict[str, dict[str, str]]
) -> None:
    """Bind complete original row contents rather than accepting identity-only baseline agreement.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    """
    changed = {identity: dict(row) for identity, row in baseline.items()}
    next(iter(changed.values()))["name"] += "changed original source"
    with pytest.raises(ValueError, match="original merged sources"):
        PRIMARY.load_projection(changed, primary_bundle)


def test_a_directory_cannot_replace_an_original_projection_member(
    primary_bundle: Path, baseline: dict[str, dict[str, str]]
) -> None:
    """Refuse a non-file projection member instead of accepting an apparently complete directory.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    """
    path = primary_bundle / PRIMARY.MEMBERS[2]
    path.rename(primary_bundle / "retained-original")
    path.mkdir()
    with pytest.raises(ValueError, match="complete original"):
        PRIMARY.load_projection(baseline, primary_bundle)


@pytest.mark.parametrize(
    "document", [[], None, {"record_count": True}, {"record_count": 172, "selected_fields": False}]
)
def test_projection_counts_require_integers_and_an_object(
    primary_bundle: Path, baseline: dict[str, dict[str, str]], document: object
) -> None:
    """Reject malformed projection wrappers and boolean counts despite Python integer compatibility.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    document : object
        Malformed wrapper or count value passed to the real consumer.
    """
    (primary_bundle / PRIMARY.MEMBERS[2]).write_text(json.dumps(document))
    with pytest.raises(ValueError, match="complete producer inputs"):
        PRIMARY.load_projection(baseline, primary_bundle)


@pytest.mark.parametrize(
    "key",
    [
        "rows",
        "assertions",
        "baseline_sha256",
        "ledger_sha256",
        "selected_fields",
        "schema_version",
        "record_count",
    ],
)
def test_changed_projection_refuses_without_changing_the_original_bundle(
    primary_bundle: Path, baseline: dict[str, dict[str, str]], key: str
) -> None:
    """Mutate each producer-bound component and require public consumer reconstruction to reject it.

    Parameters
    ----------
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    baseline : dict[str, dict[str, str]]
        All 172 original merged rows with their exact string-valued source cells.
    key : str
        Producer-bound component changed in the owned projection.
    """
    path = primary_bundle / PRIMARY.MEMBERS[2]
    document = json.loads(path.read_text())
    document[key] = "unbound projection change"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="complete producer inputs"):
        PRIMARY.load_projection(baseline, primary_bundle)


@pytest.fixture
def primary_source_tree(tmp_path: Path, primary_bundle: Path) -> Path:
    """Build the actual application through its release CLI in an owned source copy.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    primary_bundle : Path
        Producer-created software contract bundle; its citations do not approve scientific facts.

    Returns
    -------
    pathlib.Path
        Complete source tree with real release outputs generated from the fixture bundle.
    """
    destination = tmp_path / "native-primary-consumer"
    destination.mkdir()
    for source in repository_files(ROOT):
        output = destination / source.relative_to(ROOT)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
    for member in PRIMARY.MEMBERS:
        shutil.copy2(primary_bundle / member, destination / LAYER / member)
    data = destination / "04_interactive_presentation/data"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "04_interactive_presentation/scripts/build_datasets.py"),
            "--source-root",
            str(destination),
            "--data-dir",
            str(data),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return destination


def test_actual_release_cli_and_schema_keep_primary_decisions_and_legacy_sources(
    primary_source_tree: Path, primary_bundle: Path
) -> None:
    """Follow producer bytes into the full release and retain original field evidence and input hashes.

    Parameters
    ----------
    primary_source_tree : Path
        Complete source tree rebuilt by the real release CLI from a fixture bundle.
    primary_bundle : Path
        Complete producer-created bundle; fixture citations confer no scientific approval.
    """
    data = primary_source_tree / "04_interactive_presentation/data"
    document = json.loads((data / "global_reactors.sample.json").read_text())
    schema = json.loads((data / "global_reactors.schema.json").read_text())
    Draft202012Validator(schema).validate(document)
    assert document["schema_version"] == "1.3.0"
    projection = json.loads((primary_bundle / PRIMARY.MEMBERS[2]).read_text())
    by_id = {row["id"]: row for row in document["records"]}
    for original in projection["rows"]:
        record = by_id[original["stable_id"]]
        assert record.get("research_primary_assertions", []) == [
            row for row in projection["assertions"] if row["stable_id"] == record["id"]
        ]
        for field in ("operator", "purpose", "first_criticality"):
            assert record[field] == original[field]
        for assertion in record.get("research_primary_assertions", []):
            if assertion["source_url"]:
                assert assertion["source_url"] in record["source_urls"]
    published = json.loads(
        (ROOT / "04_interactive_presentation/data/global_reactors.sample.json").read_text()
    )
    for original in published["records"]:
        assert by_id[original["id"]].get("research_field_origins") == original.get(
            "research_field_origins"
        )
        assert by_id[original["id"]].get("field_observations") == original.get("field_observations")
    inventory = json.loads((data / "dataset-inventory.json").read_text())
    assert inventory["research_primary_decisions"]["selected"] == 2
    assert inventory["research_primary_decisions"]["held"] == 1
    assert sum(inventory["research_primary_decisions"].values()) == 358
    for member in PRIMARY.MEMBERS:
        assert (
            inventory["inputs"][LAYER + "/" + member]
            == hashlib.sha256((primary_source_tree / LAYER / member).read_bytes()).hexdigest()
        )
    assert document["record_count"] == 13459


@pytest.mark.parametrize("damage", ["partial", "unreviewed"])
def test_release_cli_refuses_partial_or_unreviewed_inputs_before_any_product_is_emitted(
    primary_source_tree: Path, tmp_path: Path, damage: str
) -> None:
    """Reject missing or unreviewed primary inputs before creating any release output.

    Parameters
    ----------
    primary_source_tree : Path
        Complete source tree rebuilt by the real release CLI from a fixture bundle.
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    damage : str
        Selected incomplete or unreviewed input condition.
    """
    directory = primary_source_tree / LAYER
    if damage == "partial":
        (directory / PRIMARY.MEMBERS[2]).rename(directory / "retained-original")
    else:
        path = directory / PRIMARY.MEMBERS[1]
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            columns = reader.fieldnames
            rows = list(reader)
        rows[-1]["selection"] = "unreviewed"
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns or [], delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    output = tmp_path / "refused-products"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "04_interactive_presentation/scripts/build_datasets.py"),
            "--source-root",
            str(primary_source_tree),
            "--data-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "Primary research inputs refused; check original sources and complete field review.\n"
    )
    assert not output.exists()
