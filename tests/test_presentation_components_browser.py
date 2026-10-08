# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual authored explanation controls and original page wiring.
"""Exercise every authored explanation through the actual complete Chrome page."""

from __future__ import annotations

import json

import pytest

from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser
from .test_evidence_profiles_browser import browser as browser


@pytest.mark.parametrize("topic", ["magnetic", "inertial", "magneto", "alternative"])
def test_actual_fusion_controls_render_complete_original_example_lists(
    browser: Browser, topic: str
) -> None:
    """Render every authored topic through its real bound button and stable DOM control."""
    result = browser.evaluate(
        "(topic => {const control=document.querySelector('[data-fusion='+topic+']');"
        "control.click();return {active:control.classList.contains('active'),"
        "title:fusionDetail.querySelector('h3').textContent,"
        "examples:[...fusionDetail.querySelectorAll('li')].map(node=>node.textContent)};})("
        + json.dumps(topic)
        + ")"
    )
    assert isinstance(result, dict)
    assert result["active"] is True and result["title"]
    assert isinstance(result["examples"], list) and len(result["examples"]) == 6


@pytest.mark.parametrize("flow", ["batch", "cstr", "pfr", "bio"])
def test_actual_flow_controls_render_original_diagrams_and_context(
    browser: Browser, flow: str
) -> None:
    """Render every authored flow through its actual tab and retain all three dimensions."""
    result = browser.evaluate(
        "(flow => {const control=document.querySelector('[data-flow='+flow+']');"
        "control.click();return {active:control.getAttribute('aria-selected'),"
        "diagram:!!flowDemo.querySelector(flow==='pfr'?'.tube':'.vessel'),"
        "dimensions:[...flowDemo.querySelectorAll('dt')].map(node=>node.textContent)};})("
        + json.dumps(flow)
        + ")"
    )
    assert isinstance(result, dict)
    assert result == {
        "active": "true",
        "diagram": True,
        "dimensions": ["Flow", "Typical use", "Watch"],
    }


def test_actual_full_page_counts_and_unbound_fallback_are_preserved(browser: Browser) -> None:
    """Keep the full source catalogue selected and fallback provenance explicitly absent."""
    result = browser.evaluate(
        "({types:reactors.length,facilities:REACTOR_FACILITIES.length,"
        "companies:FUSION_COMPANIES.length,repositories:ANULUM_REACTOR_REPOS.length,"
        "fallback:AtlasFallbackTaxonomy.length,"
        "unbound:AtlasFallbackTaxonomy.every(row=>!Object.hasOwn(row,'id')&&!Object.hasOwn(row,'source_urls'))})"
    )
    assert result == {
        "types": 135,
        "facilities": 13459,
        "companies": 98,
        "repositories": 30,
        "fallback": 31,
        "unbound": True,
    }
