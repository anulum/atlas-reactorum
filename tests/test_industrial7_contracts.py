# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — observation contract conformance
"""Check complete real observations and fail closed on source and snapshot mutations."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli, write_table

PREFIX = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"
CONTRACTS = importlib.import_module(PREFIX + ".contracts")
SWISS = importlib.import_module(PREFIX + ".swiss")
ITALIAN = importlib.import_module(PREFIX + ".italian")
SCRIPT = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/contracts.py"
FIXTURES = ROOT / "tests/data/industrial_round7"


@pytest.fixture
def observations() -> list[dict[str, str]]:
    """Read both complete native sources, never substituting miniature records."""
    rows: list[dict[str, str]] = SWISS.read_swiss(
        FIXTURES / "SFOE_ORIGINAL.csv.zip", retrieved="2026-09-30", source_date="2020-12-31"
    )
    rows.extend(
        ITALIAN.read_italian(
            FIXTURES / "ARPAE_LAYER.json",
            FIXTURES / "ARPAE_COUNT.json",
            FIXTURES / "ARPAE_IDS.json",
            [FIXTURES / "ARPAE_COMPLETE.json"],
            retrieved="2026-09-30",
        )
    )
    return rows


def test_complete_source_observations_are_valid(observations: list[dict[str, str]]) -> None:
    assert len(observations) == 421
    CONTRACTS.check_observations(observations)
    assert CONTRACTS.object_fields({"source": "actual"}) == {"source": "actual"}
    assert CONTRACTS.object_rows([{"source": "actual"}]) == [{"source": "actual"}]
    assert CONTRACTS.quantity(0, minimum=0, maximum=1) == 0
    assert CONTRACTS.quantity("1", minimum=0, maximum=1) == 1


@pytest.mark.parametrize("value", [None, [], "not an object", {1: "nonstring key"}])
def test_nonobjects_are_refused(value: object) -> None:
    with pytest.raises(ValueError, match="object"):
        CONTRACTS.object_fields(value)


@pytest.mark.parametrize("value", [None, [], "not an array", [None]])
def test_nonarrays_and_nonobject_rows_are_refused(value: object) -> None:
    with pytest.raises(ValueError):
        CONTRACTS.object_rows(value)


@pytest.mark.parametrize(
    "value", [True, None, [], "", "not numeric", float("nan"), float("inf"), -1, 2, 10**1000]
)
def test_quantities_are_not_coerced_or_filled(value: object) -> None:
    with pytest.raises(ValueError, match="quantity"):
        CONTRACTS.quantity(value, minimum=0, maximum=1)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", "unknown"),
        ("country", "wrong"),
        ("license", "AGPL-3.0-or-later"),
        ("source_record_id", ""),
        ("facility_name", " "),
        ("retrieved", "invalid"),
        ("retrieved", "9999-12-31"),
        ("source_date", ""),
        ("lat", "nan"),
        ("lon", "181"),
        ("capacity_chp_kw", "-1"),
        ("capacity_electrical_mw", "1"),
        ("capacity_thermal_mw", "1"),
    ],
)
def test_complete_set_preserves_source_contract(
    observations: list[dict[str, str]], field: str, value: str
) -> None:
    changed = copy.deepcopy(observations)
    changed[0][field] = value
    with pytest.raises(ValueError):
        CONTRACTS.check_observations(changed)


@pytest.mark.parametrize(
    "mutation", ["empty", "schema", "duplicate", "italian_chp", "italian_upgrade"]
)
def test_missing_sets_duplicate_ids_and_source_only_fields(
    observations: list[dict[str, str]], mutation: str
) -> None:
    changed = copy.deepcopy(observations)
    if mutation == "empty":
        changed = []
    elif mutation == "schema":
        changed[0].pop("license")
    elif mutation == "duplicate":
        changed[1]["source_record_id"] = changed[0]["source_record_id"].upper()
    else:
        row = next(record for record in changed if record["source"] == "it-arpae-biogas")
        row["capacity_chp_kw" if mutation == "italian_chp" else "upgrading_capacity_m3_hour"] = "1"
    with pytest.raises(ValueError):
        CONTRACTS.check_observations(changed)


@pytest.mark.parametrize(
    "failure",
    [
        "missing",
        "symlink",
        "oversized",
        "encoding",
        "syntax",
        "constant",
        "huge_integer",
        "nonobject",
    ],
)
def test_bounded_native_json_reader(tmp_path: Path, failure: str) -> None:
    path = tmp_path / "capture.json"
    if failure == "symlink":
        path.symlink_to(FIXTURES / "ARPAE_COUNT.json")
    elif failure == "oversized":
        with path.open("wb") as handle:
            handle.truncate(CONTRACTS.MAX_BYTES + 1)
    elif failure == "encoding":
        path.write_bytes(b"\xff")
    elif failure == "syntax":
        path.write_text("{invalid")
    elif failure == "constant":
        path.write_text('{"value": NaN}')
    elif failure == "huge_integer":
        path.write_text('{"value": ' + "1" * 10000 + "}")
    elif failure == "nonobject":
        path.write_text("[]")
    with pytest.raises(ValueError):
        CONTRACTS.read_json(path)


def test_real_source_json_reader() -> None:
    assert CONTRACTS.read_json(FIXTURES / "ARPAE_COUNT.json")["count"] == 330


@pytest.mark.parametrize(
    "failure",
    ["missing", "symlink", "oversized", "encoding", "header", "empty", "width", "quoting"],
)
def test_complete_table_schema_is_required(
    tmp_path: Path, observations: list[dict[str, str]], failure: str
) -> None:
    path = tmp_path / "snapshot.tsv"
    if failure == "symlink":
        path.symlink_to(FIXTURES / "ARPAE_IDS.json")
    elif failure == "oversized":
        with path.open("wb") as handle:
            handle.truncate(CONTRACTS.MAX_BYTES + 1)
    elif failure == "encoding":
        path.write_bytes(b"\xff")
    elif failure == "header":
        path.write_text("wrong\n")
    elif failure == "empty":
        write_table(path, CONTRACTS.SNAPSHOT_FIELDS, [])
    elif failure in {"width", "quoting"}:
        write_table(path, CONTRACTS.SNAPSHOT_FIELDS, observations)
        with path.open("a") as handle:
            handle.write('"unterminated' if failure == "quoting" else "too\tfew\n")
    with pytest.raises(ValueError):
        CONTRACTS.read_table(path, CONTRACTS.SNAPSHOT_FIELDS)


@pytest.mark.parametrize("optimize", [False, True])
def test_complete_round_trip_and_native_readonly_cli(
    tmp_path: Path, observations: list[dict[str, str]], optimize: bool
) -> None:
    path = tmp_path / "snapshot.tsv"
    write_table(path, CONTRACTS.SNAPSHOT_FIELDS, observations)
    before = path.read_bytes()
    assert CONTRACTS.read_table(path, CONTRACTS.SNAPSHOT_FIELDS) == observations
    result = run_cli(SCRIPT, "--snapshot", str(path), cwd=tmp_path, optimize=optimize)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "421 source observations" in result.stdout
    assert path.read_bytes() == before
    bad = copy.deepcopy(observations)
    bad[0]["license"] = "incorrect"
    write_table(path, CONTRACTS.SNAPSHOT_FIELDS, bad)
    failure = run_cli(SCRIPT, "--snapshot", str(path), cwd=tmp_path, optimize=optimize)
    assert failure.returncode == 1
    assert "OBSERVATION CHECK FAILED" in failure.stdout
    assert "Traceback" not in failure.stderr
    assert json.loads((FIXTURES / "ARPAE_COUNT.json").read_text())["count"] == 330
