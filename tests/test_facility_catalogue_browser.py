# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility-catalogue-controller.js actual public browser surface.
"""Exercise the complete actual owning module through the real Atlas Chrome page."""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from ._native_browser_ranges import browser_ranges, verify_ranges
from .browser_checks_runtime import BrowserEndpoints
from .browser_checks_runtime import native_browser as native_browser
from .test_evidence_profiles_browser import Browser

ROOT = Path(__file__).resolve().parents[1]
MODULES = (ROOT / "04_interactive_presentation/facility-catalogue-controller.js",)


@pytest.fixture(scope="module")
def evidence_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Retain exact native cases and require every complete source region/function.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Owner-selected workspace for raw native reports bound to MODULES.

    Yields
    ------
    pathlib.Path
        Exclusive report directory; teardown verifies current source hashes and all execution regions.
    """
    directory = tmp_path_factory.mktemp("test_facility_catalogue_browser-native")
    yield directory
    verify_ranges(directory, MODULES)


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, request: pytest.FixtureRequest, evidence_directory: Path
) -> Iterator[Browser]:
    """Yield the real reloaded Atlas page while recording this complete owner.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual owned Chrome endpoint and exact complete Atlas page URL.
    request : pytest.FixtureRequest
        Registered case identity used for its exclusive native receipt.
    evidence_directory : pathlib.Path
        Owner-selected raw report directory for this module.

    Yields
    ------
    Browser
        Real maintained session with native profiling started before page startup.
    """
    with browser_ranges(native_browser, evidence_directory, MODULES, request.node.name) as active:
        yield active


def test_actual_native_map_filters_and_list_boundaries(browser: Browser) -> None:
    """Select every actual facet, inspect a card and keep the entire original map set."""
    assert browser.evaluate("atlasMap.points.length") == 13357
    for identity in (
        "facilityDomain",
        "facilityKind",
        "facilityDataset",
        "facilityCountry",
        "facilityStatus",
    ):
        browser.evaluate(
            "(()=>{const control=document.getElementById('"
            + identity
            + "');control.selectedIndex=1;control.dispatchEvent(new Event('change'));})()"
        )
        assert browser.evaluate("filteredFacilities().length<13459") is True
        browser.evaluate(
            "document.getElementById('"
            + identity
            + "').value='all';document.getElementById('"
            + identity
            + "').dispatchEvent(new Event('change'))"
        )
    browser.evaluate("document.querySelector('.facility-open').click()")
    assert browser.evaluate("reactorDialog.open") is True
    browser.evaluate(
        "reactorDialog.close();facilitySearch.value='no original facility has this exact phrase';facilitySearch.dispatchEvent(new Event('input'))"
    )
    assert browser.evaluate("document.querySelectorAll('#facilityList article').length") == 0
    assert browser.evaluate("filteredFacilities().length") == 0
    browser.evaluate(
        "facilitySearch.value='';facilitySearch.dispatchEvent(new Event('input'));window.dispatchEvent(new Event('resize'))"
    )
    assert browser.evaluate("atlasMap===facilityCatalogue.map") is True
    assert browser.evaluate("filteredFacilities().length") == 13459


def test_actual_export_controls_and_map_selection_preserve_original_records(
    browser: Browser, tmp_path: Path
) -> None:
    """Download through actual CSV/JSON buttons and open a point emitted by the real map."""
    browser.command(
        "Browser.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": str(tmp_path), "eventsEnabled": True},
    )
    browser.evaluate(
        "facilityExportCsv.click();facilityExportJson.click();atlasMap.emitSelection(atlasMap.points[0])"
    )
    assert browser.evaluate("reactorDialog.open") is True
    browser.evaluate("reactorDialog.close()")
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        csv_files = list(tmp_path.glob("reactor-atlas-filtered-*.csv"))
        json_files = list(tmp_path.glob("reactor-atlas-filtered-*.json"))
        if len(csv_files) == len(json_files) == 1 and not list(tmp_path.glob("*.crdownload")):
            break
        time.sleep(0.05)
    assert len(csv_files) == len(json_files) == 1
    original = json.loads(
        (ROOT / "04_interactive_presentation/data/global_reactors.sample.json").read_text()
    )["records"]
    assert json.loads(json_files[0].read_text()) == original
    with csv_files[0].open(newline="") as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == 13459
    assert [row["id"] for row in records] == [row["id"] for row in original]
    for emitted, record in zip(records, original, strict=True):
        for field in (
            "field_observations",
            "research_field_origins",
            "research_primary_assertions",
            "source_urls",
        ):
            assert json.loads(emitted[field]) == record.get(field, [])
    browser.evaluate("mapViewSummary.remove();atlasMap.draw()")


def test_actual_optional_map_and_missing_controls_keep_explicit_boundaries(
    browser: Browser,
) -> None:
    """Use missing namespace/host/basemap states and preserve the real source list or refusal."""
    result = browser.evaluate(
        "(()=>{const namespace=window.AtlasMap;const outcomes=[];try{for(const altered of [undefined,{...namespace,MapEngine:undefined},{...namespace,coastline:undefined},{...namespace,renderer:undefined}]){window.AtlasMap=altered;const owner=AtlasFacilityCatalogue.create(document,REACTOR_FACILITIES);owner.start();outcomes.push(owner.map===null&&owner.filtered().length===13459);}return outcomes;}finally{window.AtlasMap=namespace;}})()"
    )
    assert result == [True, True, True, True]
    result = browser.evaluate(
        "(()=>{const host=mapHost;host.remove();const owner=AtlasFacilityCatalogue.create(document,REACTOR_FACILITIES);owner.start();return owner.map===null&&owner.filtered().length===13459;})()"
    )
    assert result is True
    result = browser.evaluate(
        "(()=>{document.getElementById('facilityKind').closest('label').remove();document.body.append(facilityStatus);try{facilityCatalogue.start();}catch(error){return error.message;}})()"
    )
    assert result == "Required Atlas filter label is unavailable"


def test_actual_missing_basemap_and_unrecognised_dataset_do_not_invent_labels(
    browser: Browser,
) -> None:
    """Keep original records when the real basemap is absent and show an unknown source path literally."""
    result = browser.evaluate(
        "(()=>{document.querySelector('#worldMap path.land').remove();const owner=AtlasFacilityCatalogue.create(document,REACTOR_FACILITIES);owner.start();return {missing:owner.map===null,text:mapHost.textContent,count:owner.filtered().length};})()"
    )
    assert result == {
        "missing": True,
        "text": "Basemap geometry unavailable; records remain listed below.",
        "count": 13459,
    }
    result = browser.evaluate(
        "(()=>{const rows=AtlasApplicationData.facilities([{...REACTOR_FACILITIES[0],dataset_source:'toString'},{...REACTOR_FACILITIES[1],dataset_source:undefined,record_kind:undefined}]);const owner=AtlasFacilityCatalogue.create(document,rows);owner.start();return document.querySelector('#facilityDataset option[value=toString]').textContent;})()"
    )
    assert result == "toString"


def test_actual_country_lines_follow_projection_zoom_pan_and_preserve_source_rows(
    browser: Browser,
) -> None:
    """Exercise the actual page's original engine and canvas with its complete geographic packet."""
    result = browser.evaluate("""(() => {
      const map = window.atlasMap;
      const canvas = document.querySelector('#mapHost canvas');
      const original = map.borders;
      const row = map.rows[0];
      const results = [];
      for (const projection of ['equal-earth', 'plate-carree']) {
        map.setProjection(projection);
        map.viewport.zoomAbout(2, 400, 200);
        map.viewport.panBy(90, -20);
        map.draw();
        const borders = canvas.toDataURL();
        map.borders = [];
        map.draw();
        results.push(borders !== canvas.toDataURL());
        map.borders = original;
      }
      map.setProjection('equal-earth');
      map.viewport.reset();
      map.draw();
      return {lines: original.length, vertices: original.reduce((n,b) => n+b.points.length,0),
        raster: results, preserved: map.rows[0] === row,
        attribution: document.querySelector('.map-hint').textContent.includes('Natural Earth')};
    })()""")
    assert result == {
        "lines": 393,
        "vertices": 19859,
        "raster": [True, True],
        "preserved": True,
        "attribution": True,
    }


def test_actual_missing_country_packet_keeps_records_and_reports_basemap_failure(
    browser: Browser,
) -> None:
    """Reject missing geographic data in the real viewer while keeping the complete original catalogue."""
    result = browser.evaluate("""(() => {
      const original = window.ATLAS_COUNTRY_BOUNDARIES;
      try {
        window.ATLAS_COUNTRY_BOUNDARIES = null;
        const owner = AtlasFacilityCatalogue.create(document, REACTOR_FACILITIES);
        owner.start();
        return {missing: owner.map === null, count: owner.filtered().length,
          message: mapHost.textContent};
      } finally { window.ATLAS_COUNTRY_BOUNDARIES = original; }
    })()""")
    assert result == {
        "missing": True,
        "count": 13459,
        "message": "Basemap geometry unavailable; records remain listed below.",
    }
