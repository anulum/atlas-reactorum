# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — app.js actual public browser surface.
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
MODULES = (ROOT / "04_interactive_presentation/app.js",)


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
    directory = tmp_path_factory.mktemp("test_application_browser-native")
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


def test_actual_startup_and_every_authored_panel_control(browser: Browser) -> None:
    """Use the loaded application, original public aliases and every real panel click."""
    assert browser.evaluate(
        "[reactors.length,REACTOR_FACILITIES.length,FUSION_COMPANIES.length,ANULUM_REACTOR_REPOS.length]"
    ) == [135, 13459, 98, 30]
    assert browser.evaluate("atlasMap===facilityCatalogue.map") is True
    for topic in ("magnetic", "inertial", "magneto", "alternative"):
        browser.evaluate("document.querySelector('[data-fusion=\"" + topic + "\"]').click()")
        assert (
            browser.evaluate("document.querySelector('#fusionDetail h3').textContent.length>0")
            is True
        )
    for flow in ("batch", "cstr", "pfr", "bio"):
        browser.evaluate("document.querySelector('[data-flow=\"" + flow + "\"]').click()")
        assert (
            browser.evaluate(
                "document.querySelector('[data-flow=\""
                + flow
                + "\"]').getAttribute('aria-selected')"
            )
            == "true"
        )
    assert (
        browser.evaluate(
            "[typeof openReactor,typeof openFacility,typeof filteredFacilities,typeof downloadFacilityData]"
        )
        == ["function"] * 4
    )
    assert browser.evaluate("filteredFacilities().length") == 13459
