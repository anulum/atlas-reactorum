# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual learning navigation, source checks and downloads

"""Exercise complete source-bound learning paths through the real Chrome application."""

from __future__ import annotations

import base64
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
CONTROLLER = ROOT / "04_interactive_presentation/learning-path-controller.js"
PATHS = (
    "water-loops",
    "magnetic-confinement",
    "chemical-flow",
    "wastewater-configurations",
    "electrochemical-processes",
    "neutrons-and-energy",
)


@pytest.fixture(scope="module")
def evidence_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Require execution of every original native controller region and function."""
    configured = os.environ.get("ATLAS_LEARNING_BROWSER_EVIDENCE")
    directory = (
        Path(configured) if configured else tmp_path_factory.mktemp("learning-native-ranges")
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
            assert str(script["url"]).endswith("/learning-path-controller.js")
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


def settle(browser: Browser, prefix: str = "Learning path ready.") -> None:
    """Wait for the real asynchronous learning state within a finite deadline."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        value = browser.evaluate("document.querySelector('#learningStatus').textContent")
        if isinstance(value, str) and value.startswith(prefix):
            return
        time.sleep(0.05)
    pytest.fail("Actual learning path did not reach its declared state")


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, request: pytest.FixtureRequest, evidence_directory: Path
) -> Iterator[Browser]:
    """Capture source-exact CDP coverage while exercising the actual learning page."""
    module = load_module("04_interactive_presentation/browser-check.py", "atlas_learning_browser")
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
        settle(active)
        try:
            yield active
        finally:
            results = active.command("Profiler.takePreciseCoverage")["result"]
            assert isinstance(results, list)
            owned = []
            for script in results:
                if isinstance(script, dict) and str(script.get("url", "")).endswith(
                    "/learning-path-controller.js"
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


def select(browser: Browser, path: str, depth: str = "overview") -> None:
    """Use the real stable-path and reading-depth controls with their change event."""
    browser.evaluate(
        """(([path, depth]) => {
          learningPath.value = path; learningDepth.value = depth;
          learningPath.dispatchEvent(new Event('change'));
        })("""
        + json.dumps([path, depth])
        + ")"
    )


def bundle(browser: Browser) -> dict[str, object]:
    """Read the actual application download without substituting another producer."""
    value = browser.evaluate("""JSON.parse(decodeURIComponent(
      learningDownload.getAttribute('href').split(',').slice(1).join(',')))""")
    assert isinstance(value, dict)
    return value


def answer(browser: Browser, entry_id: str, prefix: str) -> None:
    """Submit an actual radio choice and wait for its source-bound visible feedback."""
    browser.evaluate(
        "document.querySelector("
        + json.dumps('#learningCheck input[value="' + entry_id + '"]')
        + ").checked = true; document.querySelector('#learningCheck').requestSubmit()"
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        value = browser.evaluate("learningFeedback.textContent")
        if isinstance(value, str) and value.startswith(prefix):
            return
        time.sleep(0.05)
    pytest.fail("Actual source-bound answer feedback was unavailable")


@pytest.mark.parametrize("path", PATHS)
def test_every_path_same_original_profiles_citations_and_source_check_in_both_depths(
    browser: Browser, path: str
) -> None:
    """Follow each authored question and verify unchanged evidence in both depths."""
    select(browser, path)
    settle(browser)
    original = bundle(browser)
    learning = original["path"]
    assert isinstance(learning, dict)
    expected = browser.evaluate(
        """(() => {
          const data = window.REACTOR_TAXONOMY_EVIDENCE_PROFILES;
          return """
        + json.dumps(learning["entry_ids"])
        + """.map(id => data.records.find(profile => profile.entry_id === id));
        })()"""
    )
    assert original["profiles"] == expected
    assert original["source_rights"] == "catalogue-only; original not redistributed"
    assert (
        browser.evaluate(
            "learningView.textContent.includes(" + json.dumps(learning["objective"]) + ")"
        )
        is True
    )
    answer(browser, "not-established", "Re-read the cited statement")
    answer(browser, str(learning["answer_entry_id"]), "Your choice matches")
    assert (
        browser.evaluate(
            "learningFeedback.textContent.includes("
            + json.dumps(learning["answer_statement"])
            + ")"
        )
        is True
    )
    select(browser, path, "research")
    settle(browser)
    assert bundle(browser) == original
    assert (
        browser.evaluate("learningView.querySelectorAll('.learning-example > details').length") == 0
    )


def test_share_reload_history_and_comparison_retain_whole_snapshot(browser: Browser) -> None:
    """Restore a shared lesson and compare the same original ordered examples."""
    select(browser, "chemical-flow", "research")
    settle(browser)
    original = bundle(browser)
    assert browser.evaluate("location.href === learningShare.href") is True
    reload_page(browser)
    settle(browser)
    assert bundle(browser) == original
    select(browser, "neutrons-and-energy")
    settle(browser)
    browser.evaluate("history.back()")
    deadline = time.monotonic() + 15
    while browser.evaluate("learningPath.value") != "chemical-flow":
        assert time.monotonic() < deadline
        time.sleep(0.05)
    settle(browser)
    assert bundle(browser) == original
    browser.evaluate("learningCompare.click()")
    deadline = time.monotonic() + 15
    while not str(browser.evaluate("compareStatus.textContent")).startswith("Comparison ready."):
        assert time.monotonic() < deadline
        time.sleep(0.05)
    comparison = browser.evaluate(
        """JSON.parse(decodeURIComponent(compareDownload.href.split(',').slice(1).join(',')))"""
    )
    assert isinstance(comparison, dict)
    assert comparison["profiles"] == original["profiles"]
    assert comparison["sources"] == original["sources"]
    assert bundle(browser) == original


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile", "0" * 64),
        ("lesson", "0" * 64),
        ("path", "unknown"),
        ("view", "future"),
        ("version", "2"),
        ("extra", "true"),
    ],
)
def test_bad_link_refuses_visible_export_and_available_selection_recovers(
    browser: Browser, field: str, value: str
) -> None:
    """Refuse unavailable linked state without exporting a replacement version."""
    linked = browser.evaluate(
        """(([field, value]) => {
          const url = new URL(learningShare.href), query = new URLSearchParams(url.hash.slice(7));
          query.set(field, value); url.hash = 'learn?' + query; return url.href;
        })("""
        + json.dumps([field, value])
        + ")"
    )
    assert isinstance(linked, str)
    browser.evaluate("location.href = " + json.dumps(linked))
    settle(browser, "This learning path could not be restored.")
    assert browser.evaluate("learningView.children.length") == 0
    assert (
        browser.evaluate(
            "[learningShare, learningDownload, learningCompare].every(link => !link.hasAttribute('href') && link.getAttribute('aria-disabled') === 'true')"
        )
        is True
    )
    assert browser.evaluate("location.href") == linked
    select(browser, "water-loops")
    settle(browser)
    assert bundle(browser)["path"] == browser.evaluate("AtlasLearningPaths.listPaths()[0]")


def test_rapid_valid_invalid_paths_and_obsolete_answers_keep_latest_view(browser: Browser) -> None:
    """Keep the latest real selection while earlier renders and answers settle."""
    browser.evaluate("""(() => {
      const change = () => learningPath.dispatchEvent(new Event('change'));
      learningPath.value = 'chemical-flow'; change();
      learningDepth.value = 'unavailable'; change();
      learningPath.value = 'neutrons-and-energy'; learningDepth.value = 'overview'; change();
    })()""")
    settle(browser)
    assert (
        browser.evaluate("learningPathTitle.textContent")
        == "What does a neutron-source description establish?"
    )
    browser.evaluate("""(() => {
      document.querySelector('#learningCheck input').checked = true;
      learningCheck.requestSubmit(); learningPath.value = 'water-loops';
      learningPath.dispatchEvent(new Event('change'));
    })()""")
    settle(browser)
    assert browser.evaluate("learningFeedback.textContent") == ""
    browser.evaluate("""(() => {
      const choice = document.querySelector('#learningCheck input');
      choice.value = 'unavailable'; choice.checked = true; learningCheck.requestSubmit();
      learningPath.value = 'magnetic-confinement'; learningPath.dispatchEvent(new Event('change'));
    })()""")
    settle(browser)
    assert browser.evaluate("learningFeedback.textContent") == ""


def test_invalid_submitted_choice_and_missing_initial_document_refuse(browser: Browser) -> None:
    """Expose source/choice refusal without retaining a downloadable stale result."""
    browser.evaluate("""(() => {
      const choice = document.querySelector('#learningCheck input');
      choice.value = 'unavailable'; choice.checked = true; learningCheck.requestSubmit();
    })()""")
    settle(browser, "This learning path could not be restored.")
    browser.evaluate(
        "window.REACTOR_TAXONOMY_EVIDENCE_PROFILES = null; AtlasLearningPathController.start(reactors)"
    )
    settle(browser, "This learning path could not be restored.")
    assert browser.evaluate("learningDownload.hasAttribute('href')") is False


@pytest.mark.parametrize("damage", ["missing", "wrong-tag", "wrong-namespace"])
def test_actual_learning_controller_refuses_damaged_template_control(
    browser: Browser, damage: str
) -> None:
    """Refuse missing, mistagged or foreign-namespace controls in the actual page."""
    original = bundle(browser)
    result = browser.evaluate(
        "(async damage => {const original=document.getElementById('learningPath');"
        "const replacement=damage==='wrong-namespace' ? "
        "document.createElementNS('http://www.w3.org/2000/svg','select') : document.createElement('p');"
        "if(damage!=='missing') replacement.id='learningPath'; original.replaceWith(replacement);"
        "try {await AtlasLearningPathController.start(reactors); return 'unexpected success';}"
        "catch(error) {return error.message;}"
        "finally {replacement.replaceWith(original);}})(" + json.dumps(damage) + ")"
    )
    assert result == "Required Atlas control is unavailable: learningPath"
    assert bundle(browser) == original


def test_actual_missing_form_answer_cannot_produce_source_feedback(browser: Browser) -> None:
    """Refuse a real submitted form with no selected answer and disable stale exports."""
    browser.evaluate("learningCheck.dispatchEvent(new Event('submit', {cancelable:true}))")
    settle(browser, "This learning path could not be restored.")
    assert browser.evaluate("learningView.children.length") == 0
    assert browser.evaluate("learningDownload.hasAttribute('href')") is False


def test_mobile_keyboard_check_source_disclosure_reduced_motion_and_real_download(
    browser: Browser, tmp_path: Path, evidence_directory: Path
) -> None:
    """Use native mobile keyboard controls and download the actual evidence bundle."""
    browser.command(
        "Emulation.setDeviceMetricsOverride",
        {"width": 375, "height": 812, "deviceScaleFactor": 1, "mobile": True},
    )
    browser.command(
        "Emulation.setEmulatedMedia",
        {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
    )
    try:
        browser.evaluate("document.querySelector('#learn').scrollIntoView(); learningPath.focus()")
        press(browser, "ArrowDown", "ArrowDown", 40)
        press(browser, "Enter", "Enter", 13, "\r")
        settle(browser)
        assert browser.evaluate("learningPath.value") == "magnetic-confinement"
        expected = bundle(browser)
        browser.evaluate("learningDepth.focus()")
        press(browser, "ArrowDown", "ArrowDown", 40)
        press(browser, "Enter", "Enter", 13, "\r")
        settle(browser)
        assert browser.evaluate("learningDepth.value") == "research"
        assert bundle(browser) == expected
        browser.evaluate(
            "learningDepth.value = 'overview'; learningDepth.dispatchEvent(new Event('change'))"
        )
        settle(browser)
        browser.evaluate("document.querySelector('.learning-example > details > summary').focus()")
        press(browser, " ", "Space", 32, " ")
        assert (
            browser.evaluate("document.querySelector('.learning-example > details').open") is True
        )
        browser.evaluate(
            "document.querySelector('#learningCheck input[value=stellarator]').focus()"
        )
        press(browser, " ", "Space", 32, " ")
        browser.evaluate("document.querySelector('#learningCheck button').focus()")
        press(browser, "Enter", "Enter", 13, "\r")
        deadline = time.monotonic() + 15
        while not str(browser.evaluate("learningFeedback.textContent")).startswith(
            "Your choice matches"
        ):
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert browser.evaluate("document.documentElement.scrollWidth <= innerWidth + 1") is True
        browser.evaluate("document.querySelector('#learn').scrollIntoView()")
        screenshot = browser.command("Page.captureScreenshot", {"format": "png"})["data"]
        assert isinstance(screenshot, str)
        with (evidence_directory / "learning-mobile.png").open("xb") as handle:
            handle.write(base64.b64decode(screenshot, validate=True))
        assert (
            browser.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
        )
        browser.command(
            "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(tmp_path)}
        )
        browser.evaluate("learningDownload.focus()")
        press(browser, "Enter", "Enter", 13, "\r")
        target = tmp_path / "magnetic-confinement-learning-session.json"
        deadline = time.monotonic() + 15
        while not target.exists():
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert json.loads(target.read_text()) == expected
    finally:
        browser.command("Emulation.clearDeviceMetricsOverride")
        browser.command("Emulation.setEmulatedMedia", {"features": []})
        browser.command("Browser.setDownloadBehavior", {"behavior": "default"})


def test_desktop_opening_routes_and_all_navigation_sections_are_reachable(
    browser: Browser, evidence_directory: Path
) -> None:
    """Verify the actual opening routes and capture the desktop learning layout."""
    routes = browser.evaluate(
        "[...document.querySelectorAll('.hero-actions > a')].map(link => link.hash)"
    )
    assert routes == ["#learn", "#compare", "#global-map"]
    assert browser.evaluate("document.querySelectorAll('.topnav .nav-dot').length") == 10
    assert browser.evaluate("document.querySelectorAll('main > section').length") == 10
    assert (
        browser.evaluate(
            "[...document.querySelectorAll('main > section')].filter(section => !['intro','learn'].includes(section.id)).every(section => section.querySelector('.section-head .kicker').textContent.startsWith(section.dataset.section + ' /'))"
        )
        is True
    )
    assert browser.evaluate(
        "[...document.querySelectorAll('#sources article > span')].map(span => span.textContent)"
    ) == ["01", "02", "03"]
    assert browser.evaluate(
        "[...document.querySelectorAll('.topnav .nav-dot')].map(button => button.dataset.target)"
    ) == browser.evaluate(
        "[...document.querySelectorAll('main > section')].map(section => section.id)"
    )
    browser.evaluate("document.querySelector('.hero-actions > a').click()")
    settle(browser)
    assert browser.evaluate("location.hash") == "#learn"
    browser.evaluate("document.querySelector('#learn').scrollIntoView({behavior:'instant'})")
    screenshot = browser.command("Page.captureScreenshot", {"format": "png"})["data"]
    assert isinstance(screenshot, str)
    with (evidence_directory / "learning-desktop.png").open("xb") as handle:
        handle.write(base64.b64decode(screenshot, validate=True))
