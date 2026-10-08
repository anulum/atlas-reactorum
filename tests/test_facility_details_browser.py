# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility-detail-controller.js actual public browser surface.
"""Exercise the complete actual owning module through the real Atlas Chrome page."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from ._native_browser_ranges import browser_ranges, verify_ranges
from .browser_checks_runtime import BrowserEndpoints
from .browser_checks_runtime import native_browser as native_browser
from .test_evidence_profiles_browser import Browser

ROOT = Path(__file__).resolve().parents[1]
MODULES = (ROOT / "04_interactive_presentation/facility-detail-controller.js",)


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
    directory = tmp_path_factory.mktemp("test_facility_details_browser-native")
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


def test_original_source_layers_detail_cells_and_missing_identity(browser: Browser) -> None:
    """Inspect original records from every source layer and keep absent identities unopened."""
    result = browser.evaluate(
        "(()=>{const selected=new Map();for(const row of REACTOR_FACILITIES){if(!selected.has(row.dataset_source))selected.set(row.dataset_source,row);}let count=0;for(const row of selected.values()){openFacility(row.id);if(dialogTitle.textContent!==row.name)throw Error('original identity changed');if(!reactorDialog.open)throw Error('native dialog unopened');reactorDialog.close();count++;}openFacility('not an original facility');return {count,open:reactorDialog.open};})()",
        timeout=60,
    )
    assert isinstance(result, dict) and result["count"] == 12 and result["open"] is False
    browser.evaluate(
        "openFacility(REACTOR_FACILITIES.find(row=>row.field_observations?.length).id)"
    )
    assert browser.evaluate("dialogBody.textContent.includes('Source field assertions')") is True
    browser.evaluate("reactorDialog.close()")


def test_omitted_dataset_context_stays_absent_in_actual_detail(browser: Browser) -> None:
    """Omit optional original dataset labels and require the real detail to retain their absence."""
    result = browser.evaluate(
        "(()=>{const original=REACTOR_FACILITIES[0];const rows=AtlasApplicationData.facilities([{...original,dataset:undefined,dataset_source:undefined}]);AtlasFacilityDetails.create(document,rows).open(original.id);const keys=[...dialogBody.querySelectorAll('dt')].map(node=>node.textContent);const value={name:dialogTitle.textContent,expected:original.name,hasDataset:keys.includes('Dataset')};reactorDialog.close();return value;})()"
    )
    assert (
        isinstance(result, dict)
        and result["name"] == result["expected"]
        and result["hasDataset"] is False
    )
