# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual navigation and source-exact native controller execution.
"""Exercise original page controls and every actual native navigation region."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

import pytest
import requests

from .conftest import load_module
from .test_browser_checks import BrowserEndpoints
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser, press
from .test_taxonomy_comparison_browser import NativeScript, native_count, reload_page

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "04_interactive_presentation/page-navigation.js"


def position(browser: Browser, index: int) -> None:
    """Move the actual original section into the measured viewport without synthetic geometry."""
    browser.evaluate(
        "(index=>{const section=document.querySelectorAll('main>section')[index];"
        "section.scrollIntoView({behavior:'instant'});pageNavigation.update();})("
        + str(index)
        + ")"
    )


def ready_position(browser: Browser, index: int) -> None:
    """Wait for the expected original section and a settled actual scroll position."""
    prefix = str(index + 1).zfill(2) + " / 10"
    deadline = time.monotonic() + 10
    stable_since = time.monotonic()
    previous: object = None
    while True:
        actual = browser.evaluate("[slideStatus.textContent,window.scrollY]")
        if actual != previous:
            stable_since = time.monotonic()
            previous = actual
        if isinstance(actual, list) and actual[0] == prefix:
            if time.monotonic() - stable_since >= 0.3:
                return
        assert time.monotonic() < deadline
        time.sleep(0.05)


def test_actual_navigation_buttons_mobile_menu_and_boundary_clamps(browser: Browser) -> None:
    """Use original desktop/mobile controls and preserve first/last section clamps."""
    assert browser.evaluate("document.querySelectorAll('#mobileNav .nav-dot').length") == 10
    position(browser, 0)
    browser.evaluate("prevSlide.click()")
    ready_position(browser, 0)
    browser.evaluate("nextSlide.click()")
    ready_position(browser, 1)
    browser.evaluate("document.querySelectorAll('.topnav .nav-dot')[4].click()")
    ready_position(browser, 4)
    browser.evaluate("menuToggle.click()")
    assert browser.evaluate("mobileNav.hidden") is False
    browser.evaluate("menuToggle.click()")
    assert browser.evaluate("mobileNav.hidden") is True
    browser.evaluate(
        "menuToggle.click();document.querySelectorAll('#mobileNav .nav-dot')[9].click()"
    )
    ready_position(browser, 9)
    assert browser.evaluate("mobileNav.hidden") is True
    assert browser.evaluate("menuToggle.getAttribute('aria-expanded')") == "false"
    browser.evaluate("nextSlide.click()")
    ready_position(browser, 9)
    browser.evaluate("document.querySelector('[data-jump]').click()")
    ready_position(browser, 1)


def test_actual_keyboard_retains_editable_focus_and_all_original_keys(browser: Browser) -> None:
    """Use native keyboard events for page navigation and preserve focused form editing."""
    position(browser, 2)
    browser.evaluate(
        "document.body.focus();document.activeElement.blur();window.navKeyResults=[];"
        "window.addEventListener('keydown',event=>navKeyResults.push([event.key,event.defaultPrevented]))"
    )
    for key, code, number, expected in [
        ("ArrowRight", "ArrowRight", 39, 3),
        ("PageDown", "PageDown", 34, 4),
        ("ArrowLeft", "ArrowLeft", 37, 3),
        ("PageUp", "PageUp", 33, 2),
        ("Home", "Home", 36, 0),
        ("End", "End", 35, 9),
    ]:
        press(browser, key, code, number)
        ready_position(browser, expected)
        assert browser.evaluate("navKeyResults.at(-1)") == [key, True]
    position(browser, 3)
    browser.evaluate("reactorSearch.focus()")
    press(browser, "ArrowRight", "ArrowRight", 39)
    assert browser.evaluate("slideStatus.textContent") == "04 / 10"
    assert browser.evaluate("navKeyResults.at(-1)") == ["ArrowRight", False]
    browser.evaluate("document.activeElement.blur()")
    press(browser, "x", "KeyX", 88, "x")
    assert browser.evaluate("slideStatus.textContent") == "04 / 10"
    assert browser.evaluate("navKeyResults.at(-1)") == ["x", False]


def test_actual_dialog_close_button_content_click_and_backdrop(browser: Browser) -> None:
    """Keep original dismissal while an actual content click leaves the dialog open."""
    browser.evaluate("openFacility(REACTOR_FACILITIES[0].id)")
    assert browser.evaluate("reactorDialog.open") is True
    browser.evaluate("dialogBody.click()")
    assert browser.evaluate("reactorDialog.open") is True
    browser.evaluate("document.querySelector('.dialog-close').click()")
    assert browser.evaluate("reactorDialog.open") is False
    browser.evaluate("openFacility(REACTOR_FACILITIES[0].id);reactorDialog.click()")
    assert browser.evaluate("reactorDialog.open") is False


def test_actual_missing_window_invalid_index_and_missing_section_refuse(browser: Browser) -> None:
    """Refuse actual detached-document and removed-section inputs through public APIs."""
    result = browser.evaluate(
        "(()=>{try{AtlasPageNavigation.start(document.implementation.createHTMLDocument('detached'));}"
        "catch(error){return error.message;}})()"
    )
    assert result == "Atlas navigation window is unavailable"
    for expression in ["NaN", "1.5"]:
        result = browser.evaluate(
            "(()=>{try{pageNavigation.goTo("
            + expression
            + ");}catch(error){return error.message;}})()"
        )
        assert result == "Atlas section target is unavailable"
    result = browser.evaluate(
        "(()=>{const main=document.getElementById('main'),sections=[...main.children];"
        "try{sections.forEach(section=>section.remove());pageNavigation.goTo(0);}"
        "catch(error){return error.message;}finally{sections.forEach(section=>main.append(section));}})()"
    )
    assert result == "Atlas section target is unavailable"


def test_actual_empty_jump_and_null_focus_refuse_without_invented_targets(browser: Browser) -> None:
    """Observe genuine event refusal and absent active-element handling in real DOM states."""
    result = browser.evaluate(
        "(()=>{const button=document.querySelector('[data-jump]'),original=button.getAttribute('data-jump');"
        "let message;const listener=event=>{message=event.message;event.preventDefault();};"
        "window.addEventListener('error',listener);try{button.setAttribute('data-jump','');button.click();return message;}"
        "finally{button.setAttribute('data-jump',original);window.removeEventListener('error',listener);}})()"
    )
    assert isinstance(result, str) and "Atlas section target is unavailable" in result
    result = browser.evaluate(
        "(()=>{const body=document.body;try{body.remove();const absent=document.activeElement===null;"
        "window.dispatchEvent(new KeyboardEvent('keydown',{key:'Unused'}));return absent;}"
        "finally{document.documentElement.append(body);pageNavigation.update();}})()"
    )
    assert result is True


def test_actual_viewport_without_scroll_range_has_zero_progress(browser: Browser) -> None:
    """Remove actual page content to measure a genuine native zero-scroll-range state."""
    result = browser.evaluate(
        "(()=>{const body=document.body,progress=document.getElementById('progressBar');"
        "try{body.remove();pageNavigation.update();return "
        "[document.documentElement.scrollHeight,innerHeight,progress.style.width];}"
        "finally{document.documentElement.append(body);pageNavigation.update();}})()"
    )
    assert isinstance(result, list)
    assert result[0] == result[1]
    assert result[2] == "0%"


@pytest.fixture(scope="module")
def evidence_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Require execution of every original native controller region and function."""
    configured = os.environ.get("ATLAS_NAVIGATION_BROWSER_EVIDENCE")
    directory = (
        Path(configured) if configured else tmp_path_factory.mktemp("navigation-native-ranges")
    )
    directory.mkdir(exist_ok=True)
    yield directory
    scripts: list[NativeScript] = []
    expected_hash = hashlib.sha256(CONTROLLER.read_bytes()).hexdigest()
    for path in directory.glob("*.json"):
        report: object = json.loads(path.read_text())
        assert isinstance(report, dict)
        assert report["controller_sha256"] == expected_hash
        assert report["native_source_equal"] is True
        native = report["raw_native_script_coverage"]
        assert isinstance(native, list)
        for script in native:
            assert isinstance(script, dict)
            assert str(script["url"]).endswith("/page-navigation.js")
            scripts.append(cast(NativeScript, script))
    assert scripts
    boundaries = sorted(
        {
            offset
            for script in scripts
            for function in script["functions"]
            for region in function["ranges"]
            for offset in (region["startOffset"], region["endOffset"])
        }
    )
    assert boundaries[0] == 0
    assert boundaries[-1] == len(CONTROLLER.read_text().encode("utf-16-le")) // 2
    for start, end in pairwise(boundaries):
        assert max(native_count(script, (start + end) / 2) for script in scripts) > 0, (start, end)
    counts: dict[tuple[str, int, int], int] = {}
    for script in scripts:
        for function in script["functions"]:
            outer = function["ranges"][0]
            key = (function["functionName"], outer["startOffset"], outer["endOffset"])
            counts[key] = counts.get(key, 0) + outer["count"]
    assert all(count > 0 for count in counts.values())


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, request: pytest.FixtureRequest, evidence_directory: Path
) -> Iterator[Browser]:
    """Capture source-exact CDP coverage while exercising the actual navigation page."""
    module = load_module("04_interactive_presentation/browser-check.py", "atlas_navigation_browser")
    with requests.get(native_browser["endpoint"] + "/json/list", timeout=5) as response:
        response.raise_for_status()
        targets: object = response.json()
    assert isinstance(targets, list)
    baseline = urlsplit(native_browser["page"])
    pages = [
        target["url"]
        for target in targets
        if isinstance(target, dict)
        and target.get("type") == "page"
        and isinstance(target.get("url"), str)
        and urlsplit(target["url"])[:3] == baseline[:3]
    ]
    assert len(pages) == 1, targets
    with module.BrowserSession(native_browser["endpoint"], pages[0]) as session:
        active = cast(Browser, session)
        active.wait_ready()
        active.command("Debugger.enable")
        active.command("Profiler.enable")
        active.command("Profiler.startPreciseCoverage", {"callCount": True, "detailed": True})
        active.evaluate(
            "history.replaceState(null, '', " + json.dumps(native_browser["page"]) + ")"
        )
        reload_page(active)
        active.wait_ready()
        try:
            yield active
        finally:
            results = active.command("Profiler.takePreciseCoverage")["result"]
            assert isinstance(results, list)
            owned = []
            for script in results:
                if isinstance(script, dict) and str(script.get("url", "")).endswith(
                    "/page-navigation.js"
                ):
                    source = active.command(
                        "Debugger.getScriptSource", {"scriptId": script["scriptId"]}
                    )
                    assert source["scriptSource"] == CONTROLLER.read_text()
                    owned.append(script)
            assert owned
            report = {
                "controller_path": str(CONTROLLER),
                "controller_sha256": hashlib.sha256(CONTROLLER.read_bytes()).hexdigest(),
                "case": request.node.name,
                "raw_native_script_coverage": owned,
                "native_source_equal": True,
            }
            with (evidence_directory / (request.node.name + ".json")).open("x") as handle:
                handle.write(json.dumps(report, indent=2) + "\n")
            active.command("Profiler.stopPreciseCoverage")
            active.command("Profiler.disable")
            active.command("Debugger.disable")
            active.evaluate(
                "history.replaceState(null, '', " + json.dumps(native_browser["page"]) + ")"
            )
