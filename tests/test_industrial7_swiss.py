# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete native Swiss archive conformance
"""Exercise every source plant, catalogue and annual relation through the public reader."""

from __future__ import annotations

import csv
import hashlib
import importlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli

SWISS = importlib.import_module(
    "05_global_reactor_map.imports.industrial_facilities.expansion_round7.swiss"
)
SCRIPT = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/swiss.py"
FIXTURE = ROOT / "tests/data/industrial_round7/SFOE_ORIGINAL.csv.zip"


def revised_archive(directory: Path, member: str, field: str, value: str) -> Path:
    """Modify one real native cell, preserving every other plant and member."""
    target = directory / "mutated.zip"
    with zipfile.ZipFile(FIXTURE) as original, zipfile.ZipFile(target, "w") as changed:
        for name in original.namelist():
            body = original.read(name)
            if name == member:
                rows = list(csv.reader(io.StringIO(body.decode("latin-1"))))
                rows[1][rows[0].index(field)] = value
                output = io.StringIO()
                csv.writer(output, lineterminator="\n").writerows(rows)
                body = output.getvalue().encode("latin-1")
            changed.writestr(name, body)
    return target


def test_all_original_cells_and_date_semantics_are_retained() -> None:
    rows = SWISS.read_swiss(FIXTURE, retrieved="2026-09-30", source_date="2020-12-31")
    native = SWISS.read_archive(FIXTURE)
    assert len(rows) == len(native["BiogasPlant.csv"]) == 153
    assert len(native["Production.csv"]) == 974
    indexed = {row["source_record_id"]: row for row in rows}
    for plant in native["BiogasPlant.csv"]:
        row = indexed[plant["Number"]]
        for source, target in (
            ("Name", "facility_name"),
            ("Place", "locality"),
            ("Operator", "operator"),
            ("BeginningOfOperation", "source_beginning_operation"),
            ("CombinedHeatAndPower", "capacity_chp_kw"),
            ("UpgradingCapacity", "upgrading_capacity_m3_hour"),
            ("x", "source_east"),
            ("y", "source_north"),
        ):
            assert row[target] == plant[source]
        assert row["source_date"] == "2020-12-31"
        assert row["retrieved"] == "2026-09-30"
        assert not row["capacity_electrical_mw"]
        assert not row["capacity_thermal_mw"]
        assert 45 < float(row["lat"]) < 48
        assert 5 < float(row["lon"]) < 11
        assert "not surveying" in row["coordinate_basis"]
    assert sum(row["operator"] == "-" for row in rows) == 14
    assert sum(bool(row["source_note"]) for row in rows) == 3
    assert not indexed["plant154"]["capacity_chp_kw"]
    provenance = json.loads((FIXTURE.parent / "SOURCE.json").read_text())
    source = next(record for record in provenance["fixtures"] if record["file"] == FIXTURE.name)
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == source["fixture_sha256"]


@pytest.mark.parametrize(
    ("member", "field", "value", "message"),
    [
        ("BiogasPlant.csv", "Number", "plant2", "duplicated"),
        ("BiogasPlant.csv", "Name", "", "required text"),
        ("BiogasPlant.csv", "FacilityKind", "unresolved", "mandatory catalogue"),
        ("BiogasPlant.csv", "ValorizationType", "unresolved", "mandatory catalogue"),
        ("BiogasPlant.csv", "UpgradingTechnology", "unresolved", "upgrading technology"),
        ("BiogasPlant.csv", "BeginningOfOperation", "2001.5", "not integral"),
        ("BiogasPlant.csv", "x", "1", "bounds"),
        ("BiogasPlant.csv", "y", "1", "bounds"),
        ("BiogasPlant.csv", "CombinedHeatAndPower", "-1", "bounds"),
        ("Production.csv", "xtf_id", "", "annual production"),
        ("Production.csv", "BiogasPlantR", "missing", "annual production"),
        ("Production.csv", "Year", "2011.5", "not integral"),
        ("Production.csv", "Electricity", "-1", "bounds"),
        ("FacilityKindCatalogue.csv", "idFacilityKind", "", "catalogue identity"),
        ("FacilityKindCatalogue.csv", "FacilityKind_EN", "", "catalogue identity"),
    ],
)
def test_invalid_native_cells_are_refused(
    tmp_path: Path, member: str, field: str, value: str, message: str
) -> None:
    target = revised_archive(tmp_path, member, field, value)
    with pytest.raises(ValueError, match=message):
        SWISS.read_swiss(target, retrieved="2026-09-30", source_date="2020-12-31")


def test_documented_nonblank_upgrading_catalogue_join(tmp_path: Path) -> None:
    archive = SWISS.read_archive(FIXTURE)
    key = archive["UpgradingTechnologyCatalogue.csv"][0]["idTechnology"]
    target = revised_archive(tmp_path, "BiogasPlant.csv", "UpgradingTechnology", key)
    rows = SWISS.read_swiss(target, retrieved="2026-09-30", source_date="2020-12-31")
    assert (
        rows[0]["source_upgrading_technology"]
        == archive["UpgradingTechnologyCatalogue.csv"][0]["Technology_EN"]
    )


@pytest.mark.parametrize("date", ["invalid", "2020-99-31"])
def test_reference_dates_are_not_relabelled(date: str) -> None:
    with pytest.raises(ValueError, match="reference date"):
        SWISS.read_swiss(FIXTURE, retrieved="2026-09-30", source_date=date)


@pytest.mark.parametrize("failure", ["missing", "symlink", "oversized", "invalid_zip"])
def test_archive_file_boundaries(tmp_path: Path, failure: str) -> None:
    target = tmp_path / "archive.zip"
    if failure == "symlink":
        target.symlink_to(FIXTURE)
    elif failure == "oversized":
        with target.open("wb") as handle:
            handle.truncate(SWISS.MAX_BYTES + 1)
    elif failure == "invalid_zip":
        target.write_bytes(b"not an archive")
    with pytest.raises(ValueError):
        SWISS.read_archive(target)


@pytest.mark.parametrize(
    "failure",
    [
        "missing_member",
        "extra_member",
        "duplicate_member",
        "expanded",
        "header",
        "empty",
        "width",
        "quoting",
        "duplicate_annual",
        "duplicate_pair",
        "duplicate_catalogue",
    ],
)
def test_complete_archive_relations_are_checked(tmp_path: Path, failure: str) -> None:
    target = tmp_path / "broken.zip"
    with zipfile.ZipFile(FIXTURE) as original, zipfile.ZipFile(target, "w") as changed:
        for name in original.namelist():
            if failure == "missing_member" and name == "Production.csv":
                continue
            body = original.read(name)
            if name == "Production.csv":
                rows = list(csv.reader(io.StringIO(body.decode("latin-1"))))
                if failure == "header":
                    rows[0][0] = "unexpected"
                elif failure == "empty":
                    rows = rows[:1]
                elif failure == "width":
                    rows[1].pop()
                elif failure == "duplicate_annual":
                    rows[2][0] = rows[1][0]
                elif failure == "duplicate_pair":
                    for index in (1, 6):
                        rows[2][index] = rows[1][index]
                output = io.StringIO()
                csv.writer(output, lineterminator="\n").writerows(rows)
                body = output.getvalue().encode("latin-1")
                if failure == "expanded":
                    body += b" " * (5 * 1024 * 1024)
                elif failure == "quoting":
                    body += b'"unterminated'
            elif failure == "duplicate_catalogue" and name == "FacilityKindCatalogue.csv":
                rows = list(csv.reader(io.StringIO(body.decode("latin-1"))))
                rows[2][0] = rows[1][0]
                output = io.StringIO()
                csv.writer(output, lineterminator="\n").writerows(rows)
                body = output.getvalue().encode("latin-1")
            changed.writestr(name, body)
        if failure == "extra_member":
            changed.writestr("extra.csv", b"unexpected")
        elif failure == "duplicate_member":
            with pytest.warns(UserWarning, match="Duplicate name"):
                changed.writestr("Production.csv", b"unexpected")
    with pytest.raises(ValueError):
        SWISS.read_swiss(target, retrieved="2026-09-30", source_date="2020-12-31")


@pytest.mark.parametrize("optimize", [False, True])
def test_native_cli_other_working_directory(tmp_path: Path, optimize: bool) -> None:
    result = run_cli(
        SCRIPT,
        "--archive",
        str(FIXTURE),
        "--retrieved",
        "2026-09-30",
        "--source-date",
        "2020-12-31",
        cwd=tmp_path,
        optimize=optimize,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["plant_observations"] == 153
    failure = run_cli(
        SCRIPT,
        "--archive",
        str(tmp_path / "missing"),
        "--retrieved",
        "2026-09-30",
        "--source-date",
        "2020-12-31",
        cwd=tmp_path,
        optimize=optimize,
    )
    assert failure.returncode == 1
    assert "SWISS CHECK FAILED" in failure.stdout
    assert "Traceback" not in failure.stderr
