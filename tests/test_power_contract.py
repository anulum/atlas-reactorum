# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — power source and projection refusal conformance
"""Damage real documentary inputs and require the owning APIs to refuse them."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from typing import cast

import pytest

from .test_power_bundle import BUNDLE, DIRECTORY, ROOT, SOURCE

CONTRACT = importlib.import_module("power_contract")
PROJECT = importlib.import_module("power_projection")
CASES = json.loads((ROOT / "tests/power_mutations.json").read_text())["cases"]


def original_packet() -> dict[str, object]:
    """Select actual units while retaining their complete original blank target sets."""
    ledger = BUNDLE.read_document(DIRECTORY / "primary-fields.json")["fields"]
    sources = BUNDLE.read_document(DIRECTORY / "primary-sources.json")["sources"]
    qualified = next(
        row for row in ledger if row["disposition"] == "qualified" and row["field"] == "operator"
    )
    return {
        "baseline": [
            row for row in BUNDLE.read_source(SOURCE) if row["stable_id"] == qualified["stable_id"]
        ],
        "ledger": [
            qualified,
            *[
                row
                for row in ledger
                if row["stable_id"] == qualified["stable_id"] and row is not qualified
            ],
        ],
        "sources": [
            next(
                row for row in sources if row["source_id"] == qualified["citations"][0]["source_id"]
            ),
            *[row for row in sources if row["source_id"] != qualified["citations"][0]["source_id"]],
        ],
    }


def damage(packet: dict[str, object], case: dict[str, object]) -> None:
    """Apply one explicit source-cell change to a fresh original packet."""
    target: object = packet[str(case["root"])]
    path = cast(list[str | int], case["path"])
    for key in path[:-1]:
        target = target[key] if isinstance(target, dict) else cast(list[object], target)[int(key)]
    if isinstance(target, dict):
        if case["op"] == "delete":
            del target[path[-1]]
        else:
            target[path[-1]] = case["value"]
    else:
        cast(list[object], target)[int(path[-1])] = case["value"]


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_real_source_mutations(case: dict[str, object]) -> None:
    """Share the exact accepted/refused mutations with the actual Node counterpart."""
    packet = original_packet()
    before = copy.deepcopy(packet)
    damage(packet, case)
    if case["accepted"]:
        PROJECT.project_fields(packet["baseline"], packet["ledger"], packet["sources"])
    else:
        with pytest.raises(ValueError):
            PROJECT.project_fields(packet["baseline"], packet["ledger"], packet["sources"])
    assert before == original_packet()


@pytest.mark.parametrize(
    "precision,value",
    [
        ("unknown", ""),
        ("year", "2020"),
        ("month", "2020-02"),
        ("day", "2020-02-29"),
        ("month_range", "2020-01/2020-12"),
    ],
)
def test_documentary_precision_is_not_event_time(precision: str, value: str) -> None:
    """Retain valid documentary date meanings independently of capture and generation."""
    CONTRACT.document_date(
        {"date_precision": precision, "document_date": value, "date_basis": "report_period"}
    )


@pytest.mark.parametrize(
    "precision,value",
    [
        ("unknown", "2020"),
        ("year", "0000"),
        ("month", "2020-13"),
        ("day", "2021-02-29"),
        ("month_range", "2020"),
        ("month_range", "2020-13/2021-01"),
        ("month_range", "2021-01/2020-12"),
    ],
)
def test_documentary_dates_refuse_normalisation(precision: str, value: str) -> None:
    """Refuse impossible, reversed and precision-mismatched documentary dates."""
    with pytest.raises(ValueError):
        CONTRACT.document_date(
            {"date_precision": precision, "document_date": value, "date_basis": "report_period"}
        )


def test_original_scope_roles_attempts_and_complete_target_set() -> None:
    """Refuse duplicate/partial targets, known cells, role drift and non-document support."""
    packet = original_packet()
    baseline = CONTRACT.sequence(packet["baseline"])
    ledger = CONTRACT.sequence(packet["ledger"])
    sources = CONTRACT.sequence(packet["sources"])
    for rows, fields in [
        ([], ledger),
        (baseline * 2, ledger),
        (baseline, []),
        (baseline, ledger * 2),
    ]:
        with pytest.raises(ValueError):
            PROJECT.project_fields(rows, fields, sources)
    with pytest.raises(ValueError):
        CONTRACT.mapping({1: "not a JSON key"})
    with pytest.raises(ValueError):
        CONTRACT.mapping([])
    for bad in (None, "scalar"):
        with pytest.raises(ValueError):
            CONTRACT.sequence(bad)
    for value in (False, 1.2, float("inf"), float("nan"), -1):
        assert not CONTRACT.integer(value, 0, 100)
    assert CONTRACT.integer(20, 0, 100) and CONTRACT.integer(20.0, 0, 100)
    with pytest.raises(ValueError):
        CONTRACT.admit_sources(sources * 2)
    admitted = CONTRACT.admit_sources(sources)
    decision = copy.deepcopy(ledger[0])
    original = baseline[0]
    decision["stable_id"] = "different-unit"
    with pytest.raises(ValueError):
        PROJECT.admit_decision(decision, original, admitted)
    decision = copy.deepcopy(ledger[0])
    original = {**original, "operator": "originally known"}
    with pytest.raises(ValueError):
        PROJECT.admit_decision(decision, original, admitted)
    citation = decision["citations"][0]
    for identity in (
        next(key for key, row in admitted.items() if row["body_state"] == "capture_attempt"),
        next(key for key, row in admitted.items() if row["body_state"] == "context_only"),
    ):
        with pytest.raises(ValueError):
            CONTRACT.admit_citations([{**citation, "source_id": identity}], admitted, selected=True)
    with pytest.raises(ValueError):
        CONTRACT.admit_citations([citation, citation], admitted, selected=True)
    with pytest.raises(ValueError):
        CONTRACT.admit_citations([], admitted, selected=True)
    assert CONTRACT.admit_citations([], admitted, selected=False) == []
    attempt = next(key for key, row in admitted.items() if row["body_state"] == "capture_attempt")
    observation = {
        "basis": "capture refusal",
        "scope": "No factual support admitted",
        "candidate_value": "",
        "citations": [],
        "capture_attempts": [attempt],
    }
    PROJECT.admit_observations([observation], admitted)
    for attempts in ([attempt, attempt], [citation["source_id"]], [None]):
        with pytest.raises(ValueError):
            PROJECT.admit_observations([{**observation, "capture_attempts": attempts}], admitted)
    ledger = BUNDLE.read_document(DIRECTORY / "primary-fields.json")["fields"]
    originals = {row["stable_id"]: row for row in BUNDLE.read_source(SOURCE)}
    held = copy.deepcopy(next(row for row in ledger if row["disposition"] == "held"))
    for changes in ({"value": "invented"}, {"role": "actual_operator"}, {"citations": [citation]}):
        with pytest.raises(ValueError):
            PROJECT.admit_decision({**held, **changes}, originals[held["stable_id"]], admitted)


def test_release_cli_rebuilds_and_refuses_damaged_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run the actual producer API with absent, linked, duplicate, tampered and wrong-bound inputs."""
    cli = importlib.import_module(
        "05_global_reactor_map.imports.power_units.official_source_enrichment.build_power_projection"
    )
    source = tmp_path / "original.tsv"
    source.write_bytes(SOURCE.read_bytes())
    directory = tmp_path / "bundle"
    directory.mkdir()
    assert BUNDLE.load_projection(source, directory) is None
    assert cli.main([str(source), str(directory), "--check"]) == 1
    for name in BUNDLE.MEMBERS[:2]:
        (directory / name).write_bytes((DIRECTORY / name).read_bytes())
    with pytest.raises(ValueError, match="incomplete"):
        BUNDLE.load_projection(source, directory)
    assert cli.main([str(source), str(directory)]) == 0
    assert cli.main([str(source), str(directory), "--check"]) == 0
    product = directory / BUNDLE.MEMBERS[2]
    actual = product.read_bytes()
    for broken in (
        {**json.loads(actual), "record_count": True},
        {**json.loads(actual), "selected_fields": 999},
    ):
        product.write_text(json.dumps(broken))
        assert cli.main([str(source), str(directory), "--check"]) == 1
    product.unlink()
    product.symlink_to(DIRECTORY / BUNDLE.MEMBERS[2])
    assert cli.main([str(source), str(directory)]) == 1
    assert cli.main([str(source), str(directory), "--check"]) == 1
    product.unlink()
    product.write_bytes(actual)
    member = directory / BUNDLE.MEMBERS[0]
    body = member.read_bytes()
    for broken_text in (
        '{"schema_version":"1.0.0","schema_version":"2"}',
        "[]",
        "{",
        '{"schema_version":"2"}',
        '{"schema_version":"1.0.0","source_tsv_sha256":"' + "a" * 64 + '"}',
    ):
        member.write_text(broken_text)
        assert cli.main([str(source), str(directory), "--check"]) == 1
    member.write_bytes(body)
    source.write_text("damaged original")
    assert cli.main([str(source), str(directory), "--check"]) == 1
    source.unlink()
    source.symlink_to(SOURCE)
    with pytest.raises(ValueError):
        BUNDLE.read_source(source)
    with pytest.raises(ValueError):
        BUNDLE.read_source(tmp_path / "missing.tsv")
    assert "POWER PROJECTION REFUSED:" in capsys.readouterr().err


def test_raw_validator_and_actual_builder_refuse_partial_source_bundle(tmp_path: Path) -> None:
    """Damage only one original bundle member in a real source copy and invoke both CLIs."""
    import os
    import subprocess

    rebuild = importlib.import_module("tools.rebuild")
    stage = tmp_path / "source"
    rebuild.copy_source(ROOT, stage)
    relative = DIRECTORY.relative_to(ROOT)
    # The release product is generated from the two original producer members.
    cli = stage / relative / "build_power_projection.py"
    source = stage / SOURCE.relative_to(ROOT)
    result = subprocess.run(
        [
            os.environ.get("ATLAS_PYTHON", str(ROOT / ".venv/bin/python")),
            str(cli),
            str(source),
            str(stage / relative),
        ],
        cwd=stage,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    validator = stage / "05_global_reactor_map/imports/power_units/scripts/validate.py"
    command = [
        os.environ.get("ATLAS_PYTHON", str(ROOT / ".venv/bin/python")),
        str(validator),
        str(source),
    ]
    accepted = subprocess.run(
        command, cwd=stage, capture_output=True, text=True, timeout=60, check=False
    )
    assert accepted.returncode == 0 and "documentary_decisions\t930" in accepted.stdout
    member = stage / relative / "primary-fields.json"
    member.unlink()
    refused = subprocess.run(
        command, cwd=stage, capture_output=True, text=True, timeout=60, check=False
    )
    assert refused.returncode == 1 and "documentary power bundle" in refused.stdout
    builder = stage / "04_interactive_presentation/scripts/build_datasets.py"
    refused = subprocess.run(
        [command[0], str(builder)],
        cwd=stage,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert refused.returncode == 2 and "Primary power inputs refused" in refused.stderr
    assert not (stage / "04_interactive_presentation/data/global_reactors.sample.json").exists()
