# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native map engine pointer gesture regression

"""Retain complete evidence while fitting the real facility dialog to its viewport."""

from __future__ import annotations

import json

import pytest

from .browser_checks_runtime import ASSETS, NAVIGATION_CHECKER, BrowserEndpoints, wait_for_page
from .browser_checks_runtime import native_browser as native_browser


@pytest.mark.parametrize("mode", ("http", "file"))
@pytest.mark.parametrize("width", (1440, 390, 320))
def test_original_source_evidence_wraps_without_altering_provenance(
    native_browser: BrowserEndpoints, mode: str, width: int
) -> None:
    """Expand actual Tunney's Pasture decisions without horizontal source overflow.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned native Chrome serving the complete canonical Atlas catalogue.
    mode : str
        Actual HTTP presentation or identical direct-file page.
    width : int
        Desktop or narrow mobile viewport width in CSS pixels.

    Raises
    ------
    AssertionError
        A real original hash or link changes, a source panel overflows, or
        the native negative control no longer reproduces the reported defect.
    """
    endpoint, initial = native_browser["endpoint"], native_browser["page"]
    page = initial if mode == "http" else (ASSETS / "index.html").as_uri()
    with NAVIGATION_CHECKER.BrowserSession(endpoint, initial, timeout=30) as browser:
        browser.wait_ready(timeout=30)
        if page != initial:
            browser.command("Page.navigate", {"url": page})
            wait_for_page(endpoint, page, timeout=30)
            browser.wait_ready(timeout=30)
        try:
            browser.command(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
            )
            result = browser.evaluate("""(() => {
                openFacility("cnsc-ca-slowpoke-tunneys-pasture");
                const section = document.querySelector(".primary-research-sources");
                if (!section) throw new Error("Actual original decision panel absent");
                const details = [...section.querySelectorAll("details")];
                details.forEach(item => { item.open = true; });
                const summaries = details.map(item => item.querySelector("summary").textContent);
                const original = {
                    text: section.textContent,
                    links: [...section.querySelectorAll("a")].map(a => a.getAttribute("href"))
                };
                const measure = () => {
                    const panel = document.querySelector("#dialogBody");
                    return {scroll: panel.scrollWidth, client: panel.clientWidth};
                };
                const fixed = measure();
                section.style.overflowWrap = "normal";
                const negative = measure();
                section.style.removeProperty("overflow-wrap");
                const restored = measure();
                const retained = original.text === section.textContent &&
                    JSON.stringify(original.links) === JSON.stringify(
                        [...section.querySelectorAll("a")].map(a => a.getAttribute("href")));
                const record = window.REACTOR_FACILITIES.find(
                    item => item.id === "cnsc-ca-slowpoke-tunneys-pasture");
                const sourcePreserved = record.research_primary_assertions.every(assertion =>
                    (!assertion.source_sha256 || original.text.includes(assertion.source_sha256)) &&
                    (!assertion.source_url || original.links.includes(assertion.source_url)));
                const overflow = [...document.querySelectorAll("#dialogBody *")].filter(
                    el => el.clientWidth && el.scrollWidth > el.clientWidth).map(
                    el => ({tag: el.tagName, cls: el.className, text: el.textContent.slice(0,80),
                        scroll: el.scrollWidth, client: el.clientWidth}));
                return {fixed, negative, restored, retained, sourcePreserved, summaries, overflow};
            })()""")
            assert isinstance(result, dict)
            print(json.dumps({"width": width, "mode": mode, "observation": result}, sort_keys=True))
            for key in ("fixed", "restored"):
                dimensions = result[key]
                assert isinstance(dimensions, dict)
                assert dimensions["scroll"] == dimensions["client"], result
            negative = result["negative"]
            assert isinstance(negative, dict)
            assert negative["scroll"] > negative["client"], result
            assert result["retained"] is True and result["sourcePreserved"] is True
            assert result["summaries"] == [
                "Operator: Unresolved claim",
                "First criticality: Selected value · 1971-05",
            ], result
        finally:
            browser.evaluate("document.querySelector('#reactorDialog').close()")
            browser.command("Emulation.clearDeviceMetricsOverride")
            if page != initial:
                browser.command("Page.navigate", {"url": initial})
                wait_for_page(endpoint, initial, timeout=30)
                browser.wait_ready(timeout=30)
