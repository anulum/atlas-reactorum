# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native comparison navigation, controls and file downloads

"""Exercise complete Atlas comparison URLs, exports and refusals in native Chrome."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import urlsplit

import pytest
import requests

from .conftest import load_module
from .test_browser_checks import BrowserEndpoints
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser, press

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "04_interactive_presentation/taxonomy-comparison-controller.js"


class NativeRange(TypedDict):
    """Original UTF-16 source interval and its native execution count."""

    startOffset: int
    endOffset: int
    count: int


class NativeFunction(TypedDict):
    """Actual Chrome function identity with its nested block ranges."""

    functionName: str
    ranges: list[NativeRange]


class NativeScript(TypedDict):
    """Native script source URL and original unmodified coverage records."""

    functions: list[NativeFunction]
    url: str


def native_count(script: NativeScript, point: float) -> int:
    """Read the deepest native function/block count at an original source offset."""
    functions = [
        function
        for function in script["functions"]
        if function["ranges"][0]["startOffset"] <= point < function["ranges"][0]["endOffset"]
    ]
    if not functions:
        return 0
    function = min(
        functions,
        key=lambda function: (
            function["ranges"][0]["endOffset"] - function["ranges"][0]["startOffset"]
        ),
    )
    ranges = [
        region
        for region in function["ranges"]
        if region["startOffset"] <= point < region["endOffset"]
    ]
    return min(ranges, key=lambda region: region["endOffset"] - region["startOffset"])["count"]


@pytest.fixture(scope="module")
def evidence_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Enforce complete original native controller range/function execution at teardown."""
    configured = os.environ.get("ATLAS_COMPARISON_BROWSER_EVIDENCE")
    directory = (
        Path(configured) if configured else tmp_path_factory.mktemp("comparison-native-ranges")
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
            assert str(script["url"]).endswith("/taxonomy-comparison-controller.js")
            functions = script["functions"]
            assert isinstance(functions, list)
            for function in functions:
                assert isinstance(function, dict)
                assert isinstance(function["functionName"], str)
                regions = function["ranges"]
                assert isinstance(regions, list) and regions
                for region in regions:
                    assert isinstance(region, dict)
                    assert all(
                        isinstance(region[key], int)
                        for key in ("startOffset", "endOffset", "count")
                    )
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
    source = CONTROLLER.read_text()
    assert boundaries[0] == 0 and boundaries[-1] == len(source.encode("utf-16-le")) // 2
    for start, end in pairwise(boundaries):
        assert max(native_count(script, (start + end) / 2) for script in scripts) > 0, (start, end)
    counts: dict[tuple[str, int, int], int] = {}
    for script in scripts:
        for function in script["functions"]:
            outer = function["ranges"][0]
            key = (function["functionName"], outer["startOffset"], outer["endOffset"])
            counts[key] = counts.get(key, 0) + outer["count"]
    assert all(count > 0 for count in counts.values())


def settle(browser: Browser, prefix: str = "Comparison ready.") -> None:
    """Wait for the actual asynchronous rendering state with a bounded deadline."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status = browser.evaluate("document.querySelector('#compareStatus').textContent")
        if isinstance(status, str) and status.startswith(prefix):
            return
        time.sleep(0.05)
    pytest.fail("Actual comparison did not reach its declared rendering state")


def loader_id(browser: Browser) -> object:
    """Observe the actual native main-frame loader identity during navigation."""
    tree = browser.command("Page.getFrameTree")["frameTree"]
    assert isinstance(tree, dict)
    frame = tree["frame"]
    assert isinstance(frame, dict)
    return frame["loaderId"]


def reload_page(browser: Browser) -> None:
    """Wait for a new native loader before inspecting the reloaded document."""
    previous = loader_id(browser)
    browser.command("Page.reload")
    deadline = time.monotonic() + 15
    while loader_id(browser) == previous:
        assert time.monotonic() < deadline
        time.sleep(0.05)
    browser.wait_ready()


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, request: pytest.FixtureRequest, evidence_directory: Path
) -> Iterator[Browser]:
    """Track source-bound native controller execution during actual application use."""
    module = load_module("04_interactive_presentation/browser-check.py", "atlas_comparison_browser")
    with requests.get(native_browser["endpoint"] + "/json/list", timeout=5) as response:
        response.raise_for_status()
        targets: object = response.json()
    assert isinstance(targets, list)
    baseline = urlsplit(native_browser["page"])
    owned_pages = [
        target["url"]
        for target in targets
        if isinstance(target, dict)
        and target.get("type") == "page"
        and isinstance(target.get("url"), str)
        and urlsplit(target["url"])[:3] == baseline[:3]
    ]
    assert len(owned_pages) == 1, targets
    with module.BrowserSession(native_browser["endpoint"], owned_pages[0]) as session:
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
            coverage = active.command("Profiler.takePreciseCoverage")
            owned = []
            results = coverage["result"]
            if not isinstance(results, list):
                pytest.fail("Native coverage did not return actual scripts")
            for script in results:
                if isinstance(script, dict) and str(script.get("url", "")).endswith(
                    "/taxonomy-comparison-controller.js"
                ):
                    source = active.command(
                        "Debugger.getScriptSource", {"scriptId": script["scriptId"]}
                    )
                    assert source["scriptSource"] == CONTROLLER.read_text()
                    owned.append(script)
            assert owned
            directory = evidence_directory
            report = {
                "controller_path": str(CONTROLLER),
                "controller_sha256": hashlib.sha256(CONTROLLER.read_bytes()).hexdigest(),
                "case": request.node.name,
                "raw_native_script_coverage": owned,
                "native_source_equal": True,
            }
            with (directory / (request.node.name + ".json")).open("x") as handle:
                handle.write(json.dumps(report, indent=2) + "\n")
            active.command("Profiler.stopPreciseCoverage")
            active.command("Profiler.disable")
            active.command("Debugger.disable")
            active.evaluate(
                "history.replaceState(null, '', " + json.dumps(native_browser["page"]) + ")"
            )
            assert active.evaluate("location.href") == native_browser["page"]


def select(browser: Browser, first: str, second: str, third: str = "") -> None:
    """Change real stable-ID select controls and dispatch their normal DOM event."""
    browser.evaluate(
        """(([first, second, third]) => {
          for (const [id, value] of [['compareA', first], ['compareB', second], ['compareC', third]])
            document.getElementById(id).value = value;
          document.querySelector('#compareC').dispatchEvent(new Event('change'));
        })("""
        + json.dumps([first, second, third])
        + ")"
    )


def bundle(browser: Browser) -> dict[str, object]:
    """Read the actual downloadable JSON representation from its public link."""
    value = browser.evaluate("""JSON.parse(decodeURIComponent(
      document.querySelector('#compareDownload').getAttribute('href').split(',').slice(1).join(',')))""")
    assert isinstance(value, dict)
    return value


def test_actual_three_entry_share_reload_and_all_claims_preserve_snapshot(browser: Browser) -> None:
    """Restore a three-entry shared comparison with exact snapshot, source claims and export equality."""
    select(browser, "tokamak", "pwr", "bwr")
    settle(browser)
    before = bundle(browser)
    assert before["selection"] == {"entry_ids": ["tokamak", "pwr", "bwr"]}
    source_json = browser.evaluate("JSON.stringify(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES)")
    assert isinstance(source_json, str)
    snapshot = before["snapshot"]
    assert isinstance(snapshot, dict)
    assert snapshot["profile_sha256"] == hashlib.sha256(source_json.encode()).hexdigest()
    assert browser.evaluate("document.querySelectorAll('.comparison-sources').length") == 3
    profiles = before["profiles"]
    assert isinstance(profiles, list)
    expected = sum(len(profile["claims"]) for profile in profiles)
    assert (
        browser.evaluate(
            "document.querySelectorAll('.comparison-sources .claim-citations li').length"
        )
        == expected
    )
    shared = browser.evaluate("document.querySelector('#compareShare').href")
    assert browser.evaluate("window.location.href") == shared
    reload_page(browser)
    settle(browser)
    assert bundle(browser) == before
    assert browser.evaluate("[compareA.value, compareB.value, compareC.value]") == [
        "tokamak",
        "pwr",
        "bwr",
    ]


def test_native_browser_history_restores_each_selection_and_default(browser: Browser) -> None:
    """Restore each previous comparison and the default selection through native browser history."""
    default = bundle(browser)
    select(browser, "pwr", "bwr")
    settle(browser)
    first = bundle(browser)
    select(browser, "tokamak", "stellarator")
    settle(browser)
    browser.evaluate("history.back()")
    deadline = time.monotonic() + 15
    while (
        browser.evaluate("document.querySelector('#compareDownload').getAttribute('href')") is None
        or bundle(browser) != first
    ):
        assert time.monotonic() < deadline
        time.sleep(0.05)
    assert bundle(browser) == first
    browser.evaluate("history.back()")
    deadline = time.monotonic() + 15
    while (
        browser.evaluate("document.querySelector('#compareDownload').getAttribute('href')") is None
        or bundle(browser) != default
    ):
        assert time.monotonic() < deadline
        time.sleep(0.05)
    assert bundle(browser) == default
    assert browser.evaluate("[compareA.value, compareB.value, compareC.value]") == [
        "pwr",
        "tokamak",
        "",
    ]


@pytest.mark.parametrize("state", ["stale", "unknown", "future", "duplicate"])
def test_shared_link_refuses_bad_snapshot_or_identity_and_can_recover(
    browser: Browser, state: str
) -> None:
    """Refuse invalid shared state without stale links and recover through valid UI selection."""
    shared = browser.evaluate("document.querySelector('#compareShare').href")
    assert isinstance(shared, str)
    if state == "stale":
        linked = browser.evaluate("""(() => {
          const url = new URL(document.querySelector('#compareShare').href);
          const query = new URLSearchParams(url.hash.slice(9));
          query.set('snapshot', '0'.repeat(64)); url.hash = 'compare?' + query; return url.href;
        })()""")
    elif state == "unknown":
        linked = shared.replace("entry=tokamak", "entry=unknown")
    elif state == "future":
        linked = shared.replace("version=1", "version=2")
    else:
        linked = shared.replace("entry=tokamak", "entry=pwr")
    assert isinstance(linked, str)
    browser.command("Page.navigate", {"url": linked})
    deadline = time.monotonic() + 15
    while browser.evaluate("location.href") != linked:
        assert time.monotonic() < deadline
        time.sleep(0.05)
    reload_page(browser)
    settle(browser, "This comparison could not be restored.")
    assert browser.evaluate("document.querySelector('#compareView').children.length") == 0
    assert (
        browser.evaluate("document.querySelector('#compareDownload').hasAttribute('href')") is False
    )
    assert browser.evaluate("document.querySelector('#compareShare').hasAttribute('href')") is False
    assert browser.evaluate("window.location.href") == linked
    select(browser, "bwr", "tokamak")
    settle(browser)
    assert bundle(browser)["selection"] == {"entry_ids": ["bwr", "tokamak"]}


def test_hash_navigation_and_duplicate_choices_never_export_stale_result(browser: Browser) -> None:
    """Refuse duplicate or unsupported state and restore the default after taxonomy navigation."""
    select(browser, "pwr", "pwr")
    settle(browser, "This comparison could not be restored.")
    assert (
        browser.evaluate("document.querySelector('#compareDownload').hasAttribute('href')") is False
    )
    select(browser, "pwr", "bwr")
    settle(browser)
    browser.evaluate("location.hash = 'compare?version=unsupported'")
    settle(browser, "This comparison could not be restored.")
    assert browser.evaluate("document.querySelector('#compareView').children.length") == 0
    browser.evaluate("location.hash = 'taxonomy'")
    settle(browser)
    assert bundle(browser)["selection"] == {"entry_ids": ["pwr", "tokamak"]}


def test_rapid_valid_and_invalid_selections_keep_only_final_render(browser: Browser) -> None:
    """Render and export only the final valid comparison after rapid asynchronous state changes."""
    browser.evaluate("""(() => {
      const change = () => compareB.dispatchEvent(new Event('change'));
      compareA.value = 'pwr'; compareB.value = 'bwr'; change();
      compareB.value = 'pwr'; change();
      compareA.value = 'tokamak'; compareB.value = 'stellarator'; change();
    })()""")
    settle(browser)
    assert bundle(browser)["selection"] == {"entry_ids": ["tokamak", "stellarator"]}
    assert browser.evaluate(
        "[...document.querySelectorAll('.comparison thead th')].map(node => node.textContent)"
    ) == ["Dimension", "Tokamak", "Stellarator"]


def test_unavailable_actual_profile_document_has_visible_initial_refusal(browser: Browser) -> None:
    """Show initial refusal and remove the download link when the profile document is unavailable."""
    browser.evaluate("window.REACTOR_TAXONOMY_EVIDENCE_PROFILES = null")
    browser.evaluate("AtlasTaxonomyComparisonController.start(reactors)")
    settle(browser, "This comparison could not be restored.")
    assert (
        browser.evaluate("document.querySelector('#compareDownload').hasAttribute('href')") is False
    )


@pytest.mark.parametrize("wrong_tag", [False, True])
def test_actual_comparison_controller_refuses_damaged_template_controls(
    browser: Browser, wrong_tag: bool
) -> None:
    """Refuse actual missing or incorrectly tagged controls before binding navigation."""
    original = bundle(browser)
    result = browser.evaluate(
        "(async wrongTag => {const original=document.getElementById('compareA');"
        "const replacement=document.createElement('p');"
        "if(wrongTag) replacement.id='compareA'; original.replaceWith(replacement);"
        "try {await AtlasTaxonomyComparisonController.start(reactors); return 'unexpected success';}"
        "catch(error) {return error.message;}"
        "finally {replacement.replaceWith(original);}})(" + json.dumps(wrong_tag) + ")"
    )
    assert result == "Required Atlas control is unavailable: compareA"
    assert bundle(browser) == original


@pytest.mark.parametrize("domain", ["fission", "fusion"])
def test_actual_comparison_defaults_require_original_domain_rows(
    browser: Browser, domain: str
) -> None:
    """Refuse a real source-row selection missing a required comparison domain."""
    before = browser.evaluate("JSON.stringify(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES)")
    result = browser.evaluate(
        "(async domain => {try {await AtlasTaxonomyComparisonController.start("
        "reactors.filter(row => row.domain!==domain)); return 'unexpected success';}"
        "catch(error) {return error.message;}})(" + json.dumps(domain) + ")"
    )
    assert result == "Original comparison domain is unavailable: " + domain
    assert browser.evaluate("JSON.stringify(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES)") == before


def test_mobile_keyboard_source_disclosure_and_real_comparison_download(
    browser: Browser, tmp_path: Path
) -> None:
    """Open sources by native mobile keyboard and download the exact current comparison bundle."""
    browser.command(
        "Emulation.setDeviceMetricsOverride",
        {"width": 375, "height": 812, "deviceScaleFactor": 1, "mobile": True},
    )
    try:
        select(browser, "pwr", "tokamak", "bwr")
        settle(browser)
        expected = bundle(browser)
        browser.evaluate("""
          document.querySelector('#compare').scrollIntoView();
          document.querySelector('.comparison-sources summary').focus();
        """)
        press(browser, " ", "Space", 32, " ")
        assert browser.evaluate("document.querySelector('.comparison-sources').open") is True
        assert browser.evaluate("document.documentElement.scrollWidth <= innerWidth + 1") is True
        browser.command(
            "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(tmp_path)}
        )
        browser.evaluate("document.querySelector('#compareDownload').focus()")
        press(browser, "Enter", "Enter", 13, "\r")
        deadline = time.monotonic() + 15
        target = tmp_path / "atlas-reactorum-comparison.json"
        while not target.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert target.exists()
        assert json.loads(target.read_text()) == expected
    finally:
        browser.command("Emulation.clearDeviceMetricsOverride")
        browser.command("Browser.setDownloadBehavior", {"behavior": "default"})
