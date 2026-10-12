# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — group map builder against the accepted snapshot and page

"""Exercise the group map builder through its real command line.

Every case runs the actual script against the accepted source snapshot, the
retained portfolio citations and the accepted page, or against a copy of the
snapshot with exactly one value changed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ._catalogue_inputs import ROOT, run_cli
from .conftest import load_module

SCRIPT = ROOT / "metadata/group_map/build_group_map.py"
SNAPSHOT = SCRIPT.with_name("source_snapshot.json")
DATA = SCRIPT.with_name("ecosystem_projects.json")
PAGE = ROOT / "docs/ecosystem.md"
CITATIONS = ROOT / "metadata/reactor_portfolio/links.v1.json"

Change = Callable[[dict[str, Any]], None]


def _record(snapshot: dict[str, Any], project: str) -> dict[str, Any]:
    """Return the snapshot record of one project."""
    found: dict[str, Any] = next(r for r in snapshot["records"] if r["project"] == project)
    return found


def _changed(tmp_path: Path, change: Change, source: Path = SNAPSHOT) -> Path:
    """Write a copy of an accepted JSON source with one change applied."""
    document: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
    change(document)
    path = tmp_path / source.name
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _digests() -> list[str]:
    """Return the digests of the accepted snapshot, data and page."""
    return [hashlib.sha256(p.read_bytes()).hexdigest() for p in (SNAPSHOT, DATA, PAGE)]


def test_accepted_data_and_page_equal_the_rendered_snapshot() -> None:
    """Pass the check normally and under -O for all 55 projects, leaving accepted bytes unchanged."""
    before = _digests()
    for optimized in (False, True):
        result = run_cli(SCRIPT, "--check", optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout == "CHECK PASSED\tprojects\t55\n"
    assert before == _digests()


def test_candidate_bundle_reproduces_the_accepted_bytes(tmp_path: Path) -> None:
    """Write a bundle outside the repository whose two files equal the accepted ones."""
    result = run_cli(SCRIPT, "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / DATA.name).read_bytes() == DATA.read_bytes()
    assert (tmp_path / PAGE.name).read_bytes() == PAGE.read_bytes()
    assert sorted(p.name for p in tmp_path.iterdir()) == [PAGE.name, DATA.name]


def test_public_render_returns_the_accepted_bytes_without_writing() -> None:
    """Return exactly the accepted data and page from the importable render function."""
    module = load_module("metadata/group_map/build_group_map.py", "group_map_builder")
    before = _digests()
    rendered = module.render(SNAPSHOT, CITATIONS)
    assert rendered == {
        "data": DATA.read_text(encoding="utf-8"),
        "page": PAGE.read_text(encoding="utf-8"),
    }
    assert before == _digests()


def test_accepted_data_bind_the_snapshot_and_every_cited_project() -> None:
    """Bind the data to the exact snapshot bytes and to the 54 cited projects plus the atlas."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cited = {r["project_id"] for r in json.loads(CITATIONS.read_text(encoding="utf-8"))["records"]}
    assert data["source_snapshot"]["sha256"] == hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
    assert {p["name"] for p in data["projects"]} == cited | {"ATLAS-REACTORUM"}
    assert all(p["owning_groups"] == ["SCPN-REACTOR-SYSTEMS"] for p in data["projects"])
    released = {p["name"] for p in data["projects"] if p["status"] == "released"}
    assert released == {p["name"] for p in data["projects"] if p["packages"]}
    assert data["format"] == "ecosystem-projects/1.0"
    page = PAGE.read_text(encoding="utf-8")
    assert all(p["name"] in page for p in data["projects"])
    assert "SCPN-PHWR-CORE exclusively owns heavy-water pressure tubes" in page
    assert "belongs to SCPN-CHANNEL-CORE." in page and " F3 " not in page and "F13" not in page


def _drop(snapshot: dict[str, Any]) -> None:
    """Remove the last record and keep the count consistent."""
    snapshot["records"].pop()
    snapshot["count"] -= 1


def _rename(snapshot: dict[str, Any]) -> None:
    """Give the last record an identity no citation knows."""
    snapshot["records"][-1]["project"] = "SCPN-ZZ-UNCITED-CORE"


def _licences(packaging: str | None, readme: str | None) -> Change:
    """Return a change of both licence statements of the tokamak core."""

    def change(snapshot: dict[str, Any]) -> None:
        licence = _record(snapshot, "SCPN-TOKAMAK-CORE")["licence"]
        licence["packaging"], licence["readme_spdx"] = packaging, readme

    return change


def _manifest(project: str, key: str, value: object) -> Change:
    """Return a change of one manifest value of one project."""

    def change(snapshot: dict[str, Any]) -> None:
        _record(snapshot, project)["manifest"][key] = value

    return change


def _top(key: str, value: object) -> Change:
    """Return a change of one envelope value."""

    def change(snapshot: dict[str, Any]) -> None:
        snapshot[key] = value

    return change


def _unpublished_prototype(snapshot: dict[str, Any]) -> None:
    """Withdraw the public repository of a core that declares a prototype."""
    _record(snapshot, "SCPN-TOKAMAK-CORE")["hosting"] = {"slug": None, "visibility": None}


def _private(snapshot: dict[str, Any]) -> None:
    """Mark a public repository as private."""
    _record(snapshot, "SCPN-TOKAMAK-CORE")["hosting"]["visibility"] = "private"


def _no_function(snapshot: dict[str, Any]) -> None:
    """Remove the only function source of an architecture-only device core."""
    _record(snapshot, "SCPN-MUON-FUSION-CORE")["manifest"]["device_family"] = None


def _atlas_duplicate(snapshot: dict[str, Any]) -> None:
    """Repeat the first record."""
    snapshot["records"].insert(0, snapshot["records"][0])
    snapshot["count"] += 1


@pytest.mark.parametrize(
    ("change", "diagnostic"),
    [
        (_top("schema", "scpn.other.v1"), "schema is not recognised"),
        (_top("group", "SCPN-OTHER"), "belongs to another group"),
        (_top("captured", "2026-02-30"), "full ISO date"),
        (_top("captured", None), "full ISO date"),
        (_top("count", 54), "count differs"),
        (_top("records", {}), "count differs"),
        (_atlas_duplicate, "duplicated or unordered"),
        (_drop, "name different projects"),
        (_rename, "no retained portfolio citation"),
        (_licences(None, None), "states no single licence"),
        (_licences("MIT", "AGPL-3.0-or-later"), "states no single licence"),
        (
            _manifest("SCPN-PWR-CORE", "category", "chemical_device"),
            "differs from its retained citation",
        ),
        (_manifest("SCPN-PWR-CORE", "category", "invented"), "declares no known family"),
        (_manifest("SCPN-PWR-CORE", "category", "evidence_library"), "declares no known family"),
        (_manifest("SCPN-PWR-CORE", "evidence_maturity", "validated"), "unknown evidence maturity"),
        (_manifest("SCPN-PWR-CORE", "boundary", None), "states no function"),
        (_no_function, "states no function"),
        (_unpublished_prototype, "matches no status rule"),
        (_private, "neither public nor unpublished"),
    ],
)
def test_changed_snapshot_refuses_with_its_reason(
    tmp_path: Path, change: Change, diagnostic: str
) -> None:
    """Refuse one changed snapshot value under -O, naming the reason and writing nothing."""
    source = _changed(tmp_path, change)
    before = source.read_bytes()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = run_cli(SCRIPT, "--source", str(source), "--output-dir", str(bundle), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stderr and "Traceback" not in result.stderr
    assert list(bundle.iterdir()) == [] and source.read_bytes() == before


def test_unreadable_sources_and_foreign_citations_refuse(tmp_path: Path) -> None:
    """Refuse a missing snapshot, malformed JSON and citations owned by another group."""
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    foreign = _changed(tmp_path, _top("owner_group", "SCPN-OTHER"), CITATIONS)
    for arguments in (
        ("--source", str(tmp_path / "absent.json")),
        ("--source", str(broken)),
        ("--citations", str(foreign)),
    ):
        result = run_cli(SCRIPT, *arguments, "--check")
        assert result.returncode == 1 and result.stderr.startswith("REFUSED: ")
        assert "Traceback" not in result.stderr
    assert "another group" in run_cli(SCRIPT, "--citations", str(foreign), "--check").stderr


def test_check_names_accepted_outputs_that_differ_from_another_snapshot(tmp_path: Path) -> None:
    """Report both accepted outputs when a later capture date is rendered against them."""
    source = _changed(tmp_path, _top("captured", "2026-10-13"))
    result = run_cli(SCRIPT, "--source", str(source), "--check")
    assert result.returncode == 1
    assert "metadata/group_map/ecosystem_projects.json, docs/ecosystem.md" in result.stderr


@pytest.mark.parametrize("destination", [ROOT, ROOT / "docs", ROOT / "absent-directory"])
def test_bundle_destination_inside_the_repository_or_absent_refuses(destination: Path) -> None:
    """Refuse the repository, a directory inside it and a missing directory, creating nothing."""
    before = _digests()
    result = run_cli(SCRIPT, "--output-dir", str(destination))
    assert result.returncode == 1 and "outside the accepted repository" in result.stderr
    assert before == _digests() and not (ROOT / "absent-directory").exists()
    assert not (ROOT / "docs" / DATA.name).exists()


def _unclassified_release(snapshot: dict[str, Any]) -> None:
    """Remove the classifier and the commercial line of the released fusion library."""
    record = _record(snapshot, "SCPN-FUSION-CORE")
    record["classifier"] = None
    record["licence"]["commercial_line"] = None


def test_release_without_classifier_or_commercial_line_is_stated_as_such(tmp_path: Path) -> None:
    """Render a release without a maturity word and drop the commercial sentence for all."""
    source = _changed(tmp_path, _unclassified_release)
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = run_cli(SCRIPT, "--source", str(source), "--output-dir", str(bundle))
    assert result.returncode == 0, result.stdout + result.stderr
    page = (bundle / PAGE.name).read_text(encoding="utf-8")
    assert "| PyPI scpn-fusion 4.0.0 |" in page and "PyPI scpn-mif-core 0.1.1 (pre-alpha)" in page
    assert "Every project states AGPL-3.0-or-later.\n" in page
    data = json.loads((bundle / DATA.name).read_text(encoding="utf-8"))
    fusion = next(p for p in data["projects"] if p["name"] == "SCPN-FUSION-CORE")
    assert fusion["maturity"] == {"value": None, "source": None}
    assert fusion["commercial_licence_available"] is False
