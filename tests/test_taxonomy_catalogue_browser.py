# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — taxonomy-catalogue-controller.js actual public browser surface.
"""Exercise the complete actual owning module through the real Atlas Chrome page."""

from __future__ import annotations

from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from ._native_browser_ranges import browser_ranges, verify_ranges
from .browser_checks_runtime import BrowserEndpoints
from .browser_checks_runtime import native_browser as native_browser
from .test_application_data_browser import FallbackHandler
from .test_evidence_profiles_browser import Browser

ROOT = Path(__file__).resolve().parents[1]
MODULES = (ROOT / "04_interactive_presentation/taxonomy-catalogue-controller.js",)


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
    directory = tmp_path_factory.mktemp("test_taxonomy_catalogue_browser-native")
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


def test_actual_facets_cards_detail_and_absent_selection(browser: Browser) -> None:
    """Filter actual source facets, inspect a source-bound card and clear every selection."""
    assert browser.evaluate("document.querySelectorAll('.reactor-card').length") == 135
    browser.evaluate("document.querySelector('.reactor-card').click()")
    assert browser.evaluate("reactorDialog.open") is True
    assert browser.evaluate("dialogBody.textContent.includes('Taxonomy audit')") is True
    browser.evaluate("reactorDialog.close();openReactor('not an original source entry')")
    assert browser.evaluate("reactorDialog.open") is False
    for index in range(5):
        browser.evaluate(f"document.querySelectorAll('#domainFilters .chip')[{index}].click()")
        assert (
            browser.evaluate("document.querySelector('#activeFilterText').textContent.length>0")
            is True
        )
    browser.evaluate("document.querySelector('#domainFilters .chip').click()")
    for identity in ("maturityFilter", "familyFilter", "kindFilter"):
        browser.evaluate(
            "(()=>{const control=document.getElementById('"
            + identity
            + "');control.selectedIndex=1;control.dispatchEvent(new Event('change'));})()"
        )
        assert browser.evaluate("document.querySelectorAll('.reactor-card').length<135") is True
        browser.evaluate(
            "document.getElementById('"
            + identity
            + "').value='all';document.getElementById('"
            + identity
            + "').dispatchEvent(new Event('change'))"
        )
    browser.evaluate(
        "reactorSearch.value='no original taxonomy entry has this exact phrase';reactorSearch.dispatchEvent(new Event('input'))"
    )
    assert browser.evaluate("reactorGrid.textContent") == "No matching systems."


def test_missing_actual_filter_label_refuses(browser: Browser) -> None:
    """Detach the genuine select from its label and require the public start refusal."""
    result = browser.evaluate(
        "(()=>{document.body.append(maturityFilter);try{taxonomyCatalogue.start();}catch(error){return error.message;}})()"
    )
    assert result == "Required Atlas filter label is unavailable"


def test_actual_missing_source_retains_families_without_inventing_parent_identity(
    browser: Browser, native_browser: BrowserEndpoints
) -> None:
    """Use the actual missing-script route and retain all authored fallback rows without a PWR parent."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), FallbackHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        browser.command(
            "Page.navigate", {"url": f"http://127.0.0.1:{server.server_port}/index.html"}
        )
        browser.wait_ready()
        assert browser.evaluate("reactors.length") == 31
        browser.evaluate("openReactor('LENR / cold fusion')")
        assert (
            browser.evaluate("dialogBody.querySelector('.hierarchy').textContent")
            == "Contested claim → LENR / cold fusion"
        )
        assert browser.evaluate("dialogBody.querySelector('.profile-download')===null") is True
        browser.evaluate("reactorDialog.close()")
        result = browser.evaluate(
            "(()=>{const original=AtlasFallbackTaxonomy;try{AtlasFallbackTaxonomy=original.map((row,index)=>index===0?{...row,domain:'unclassified source domain',maturity:'unclassified source maturity',evidence:'unclassified source evidence',strength:''}:row);const owner=AtlasTaxonomyCatalogue.create(document,[],[]);owner.start();owner.open(original[0].name);return {text:dialogBody.textContent,profile:dialogBody.querySelector('.evidence-profile')===null};}finally{AtlasFallbackTaxonomy=original;reactorDialog.close();}})()"
        )
        assert isinstance(result, dict) and result["profile"] is True
        assert (
            "unclassified source domain" in str(result["text"])
            and "unclassified source maturity" in str(result["text"])
            and "unclassified source evidence" in str(result["text"])
        )
        assert "Not specified" in str(result["text"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()
