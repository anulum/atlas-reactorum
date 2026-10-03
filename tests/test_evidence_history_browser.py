# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual original claim history and pending correction downloads

"""Exercise retained original claim history and proposals through the real Chrome application."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
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
CONTROLLER = ROOT / "04_interactive_presentation/evidence-history-controller.js"


@pytest.fixture(scope="module")
def evidence_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Require execution of every original native controller region and function."""
    configured = os.environ.get("ATLAS_HISTORY_BROWSER_EVIDENCE")
    directory = Path(configured) if configured else tmp_path_factory.mktemp("history-native-ranges")
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
            assert str(script["url"]).endswith("/evidence-history-controller.js")
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


def settle(browser: Browser, prefix: str = "History ready.") -> None:
    """Wait for the real asynchronous learning state within a finite deadline."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        value = browser.evaluate("document.querySelector('#historyStatus').textContent")
        if isinstance(value, str) and value.startswith(prefix):
            return
        time.sleep(0.05)
    pytest.fail("Actual history view did not reach its declared state")


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, request: pytest.FixtureRequest, evidence_directory: Path
) -> Iterator[Browser]:
    """Capture source-exact CDP coverage while exercising the actual history page."""
    module = load_module("04_interactive_presentation/browser-check.py", "atlas_history_browser")
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
                    "/evidence-history-controller.js"
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


def download_value(browser: Browser, link: str = "historyDownload") -> dict[str, object]:
    """Read the JSON offered by an actual application download control."""
    value = browser.evaluate(
        "JSON.parse(decodeURIComponent(document.getElementById("
        + json.dumps(link)
        + ").getAttribute('href').split(',').slice(1).join(',')))"
    )
    assert isinstance(value, dict)
    return value


def change(browser: Browser, control: str, value: str) -> None:
    """Change a real stable identity selection and dispatch its public DOM event."""
    browser.evaluate(
        "(([id,value]) => {const select=document.getElementById(id); select.value=value; "
        "select.dispatchEvent(new Event('change'));})(" + json.dumps([control, value]) + ")"
    )


def reload_with(browser: Browser, expression: str) -> None:
    """Supply actual journal input before startup without changing controller source."""
    browser.command("Page.enable")
    installed = browser.command(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "document.addEventListener('DOMContentLoaded', () => {" + expression + "});"},
    )
    try:
        reload_page(browser)
    finally:
        browser.command(
            "Page.removeScriptToEvaluateOnNewDocument", {"identifier": installed["identifier"]}
        )


def fill_proposal(
    browser: Browser,
    source_url: str = "https://example.test/original",
    next_entry: str | None = None,
) -> None:
    """Fill and submit the actual contributor form with a source and locator."""
    browser.evaluate(
        "(([source,nextEntry]) => {const form=document.getElementById('correctionForm'); "
        "const values={proposed_statement:'Source-backed replacement proposed for curator review.', "
        "source_url:source, locator:'Section 2.1.3, page 4', reason:'Clarify the bounded classification statement.', "
        "submitted_by:'Native browser contributor'}; for(const [name,value] of Object.entries(values)) "
        "form.elements.namedItem(name).value=value; form.requestSubmit(); "
        "if(nextEntry){historyEntry.value=nextEntry; historyEntry.dispatchEvent(new Event('change'));}})("
        + json.dumps([source_url, next_entry])
        + ")"
    )


def proposal_settle(
    browser: Browser, prefix: str = "Correction proposal prepared locally."
) -> None:
    """Wait for the real local proposal result within a finite deadline."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        value = browser.evaluate("correctionStatus.textContent")
        if isinstance(value, str) and value.startswith(prefix):
            return
        time.sleep(0.05)
    pytest.fail("Actual correction form did not reach its declared state")


@pytest.fixture(scope="module")
def retained_changes(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """Create real import successors with the public native CLI and full source inputs."""
    folder = tmp_path_factory.mktemp("actual-history-imports")
    profiles = json.loads(
        (ROOT / "04_interactive_presentation/data/taxonomy-evidence-profiles.json").read_text()
    )
    journal = ROOT / "metadata/evidence_history/history.json"
    cli = ROOT / "04_interactive_presentation/scripts/evidence_history.cjs"
    node = shutil.which("node")
    assert node is not None
    for index, mode in enumerate(("changed", "removed", "returned"), 4):
        updated = json.loads(json.dumps(profiles))
        if mode == "changed":
            updated["records"][0]["claims"][0]["original_statement"] += (
                " Controlled native import clarification."
            )
            updated["records"][0]["claims"][0]["citation"]["statement"] = updated["records"][0][
                "claims"
            ][0]["original_statement"]
        elif mode == "removed":
            updated["records"].pop(0)
            updated["record_count"] -= 1
        source = folder / (mode + "-profiles.json")
        source.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n")
        successor = folder / (mode + "-journal.json")
        result = subprocess.run(
            [
                node,
                str(cli),
                "--import",
                str(journal),
                str(source),
                f"2026-10-{index:02d}T07:20:00.000Z",
                str(successor),
            ],
            capture_output=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr.decode()
        journal = successor
    value: object = json.loads(journal.read_text())
    assert isinstance(value, dict)
    return value


def test_actual_baseline_original_source_dates_and_all_entry_choices(
    browser: Browser, evidence_directory: Path
) -> None:
    """Inspect the real baseline and select another claim and stable entry."""
    original = download_value(browser)
    profiles = json.loads(
        (ROOT / "04_interactive_presentation/data/taxonomy-evidence-profiles.json").read_text()
    )
    revisions = original["revisions"]
    assert isinstance(revisions, list) and len(revisions) == 1
    assert revisions[0]["claim"] == profiles["records"][0]["claims"][0]
    assert browser.evaluate("historyEntry.options.length") == 135
    assert browser.evaluate("historyView.textContent.includes('Unknown / not recorded')") is True
    assert (
        browser.evaluate("historyView.textContent.includes('first recorded observation')") is True
    )
    change(browser, "historyClaim", "pwr:principle:1")
    settle(browser)
    assert download_value(browser)["claim_id"] == "pwr:principle:1"
    change(browser, "historyEntry", "tokamak")
    settle(browser)
    assert download_value(browser)["entry_id"] == "tokamak"
    assert browser.evaluate("correctionFields.disabled") is False
    browser.evaluate(
        "document.querySelector('#evidence-history').scrollIntoView({behavior:'instant'})"
    )
    screenshot = browser.command("Page.captureScreenshot", {"format": "png"})["data"]
    assert isinstance(screenshot, str)
    with (evidence_directory / "history-desktop.png").open("xb") as handle:
        handle.write(base64.b64decode(screenshot, validate=True))


def test_actual_import_changes_retirement_return_and_exact_revision_navigation(
    browser: Browser, retained_changes: dict[str, object]
) -> None:
    """Follow actual retained imports and restore old dated revisions without substitution."""
    reload_with(browser, "window.REACTOR_EVIDENCE_HISTORY = " + json.dumps(retained_changes) + ";")
    settle(browser)
    original = download_value(browser)
    revisions = original["revisions"]
    assert isinstance(revisions, list) and len(revisions) == 4
    assert [revision["state"] for revision in revisions] == [
        "present",
        "present",
        "not-in-snapshot",
        "present",
    ]
    assert (
        browser.evaluate(
            "historyView.textContent.includes('Controlled native import clarification.')"
        )
        is True
    )
    change(browser, "historyRevision", str(revisions[2]["revision_sha256"]))
    settle(browser)
    assert browser.evaluate("correctionFields.disabled") is True
    assert browser.evaluate("historyRevision.value") == revisions[2]["revision_sha256"]
    absent_url = browser.evaluate("historyShare.href")
    change(browser, "historyRevision", str(revisions[0]["revision_sha256"]))
    settle(browser)
    assert browser.evaluate("correctionFields.disabled") is False
    browser.evaluate("history.back()")
    settle(browser)
    deadline = time.monotonic() + 15
    while browser.evaluate("historyRevision.value") != revisions[2]["revision_sha256"]:
        assert time.monotonic() < deadline
        time.sleep(0.05)
    assert browser.evaluate("location.href") == absent_url
    assert download_value(browser) == original


def test_actual_proposal_preserves_original_and_does_not_mutate_accepted_journal(
    browser: Browser,
) -> None:
    """Prepare an actual pending correction with complete original revision custody."""
    original = download_value(browser)
    before = browser.evaluate("JSON.stringify(window.REACTOR_EVIDENCE_HISTORY)")
    fill_proposal(browser)
    proposal_settle(browser)
    pending = download_value(browser, "correctionDownload")
    revisions = original["revisions"]
    assert isinstance(revisions, list)
    assert pending["state"] == "pending" and pending["review"] is None
    assert pending["original_revision"] == revisions[0]
    assert pending["publication_effect"] == "none; accepted source data remain unchanged"
    assert browser.evaluate("JSON.stringify(window.REACTOR_EVIDENCE_HISTORY)") == before
    assert download_value(browser) == original
    fill_proposal(browser, "http://example.test/unaccepted")
    proposal_settle(browser, "The correction proposal could not be prepared.")
    assert browser.evaluate("correctionDownload.hasAttribute('href')") is False


def test_exact_baseline_link_survives_actual_page_reload(browser: Browser) -> None:
    """Restore the same original claim from a shared exact link after native reload."""
    change(browser, "historyClaim", "pwr:principle:1")
    settle(browser)
    original = download_value(browser)
    url = browser.evaluate("historyShare.href")
    assert isinstance(url, str)
    browser.evaluate("location.href = " + json.dumps(url))
    settle(browser)
    reload_page(browser)
    settle(browser)
    assert browser.evaluate("location.href") == url
    assert browser.evaluate("historyClaim.value") == "pwr:principle:1"
    assert download_value(browser) == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("history", "0" * 64),
        ("revision", "0" * 64),
        ("entry", "unknown"),
        ("claim", "unknown"),
        ("version", "future"),
    ],
)
def test_unavailable_exact_link_refuses_visible_export_and_proposal(
    browser: Browser, field: str, value: str
) -> None:
    """Refuse an unavailable exact target instead of replacing it with current data."""
    browser.evaluate(
        "(([field,value]) => {const url=new URL(historyShare.href); const query=new URLSearchParams(url.hash.slice(9)); "
        "query.set(field,value); location.hash='history?'+query.toString();})("
        + json.dumps([field, value])
        + ")"
    )
    settle(browser, "This historical revision could not be restored.")
    assert browser.evaluate("historyView.children.length") == 0
    assert (
        browser.evaluate(
            "[historyShare,historyDownload,correctionDownload].every(link => !link.hasAttribute('href'))"
        )
        is True
    )
    assert browser.evaluate("correctionFields.disabled") is True
    change(browser, "historyEntry", "tokamak")
    settle(browser)
    assert download_value(browser)["entry_id"] == "tokamak"


def test_rapid_actual_selections_and_pending_results_cannot_overwrite_new_view(
    browser: Browser,
) -> None:
    """Exercise concurrent success/refusal and proposal completion on real public events."""
    browser.evaluate(
        "historyEntry.value=''; historyEntry.dispatchEvent(new Event('change')); historyEntry.value='tokamak'; historyEntry.dispatchEvent(new Event('change'))"
    )
    settle(browser)
    assert download_value(browser)["entry_id"] == "tokamak"
    browser.evaluate(
        "historyEntry.value='pwr'; historyEntry.dispatchEvent(new Event('change')); historyEntry.value='tokamak'; historyEntry.dispatchEvent(new Event('change'))"
    )
    settle(browser)
    assert download_value(browser)["entry_id"] == "tokamak"
    for url in ("https://example.test/original", "http://example.test/unaccepted"):
        fill_proposal(browser, url, "pwr")
        settle(browser)
        assert browser.evaluate("correctionDownload.hasAttribute('href')") is False
        assert browser.evaluate("correctionStatus.textContent") == ""
        change(browser, "historyEntry", "tokamak")
        settle(browser)


def test_missing_initial_retained_journal_refuses_without_source_substitution(
    browser: Browser,
) -> None:
    """Fail visibly on unavailable initial journal content with exports disabled."""
    reload_with(browser, "window.REACTOR_EVIDENCE_HISTORY = null;")
    settle(browser, "This historical revision could not be restored.")
    assert browser.evaluate("historyView.children.length") == 0
    assert browser.evaluate("historyDownload.hasAttribute('href')") is False


def test_mobile_keyboard_disclosure_and_actual_pending_download(
    browser: Browser, tmp_path: Path, evidence_directory: Path
) -> None:
    """Use real mobile keyboard controls and download the original pending proposal."""
    browser.command(
        "Emulation.setDeviceMetricsOverride",
        {"width": 375, "height": 812, "deviceScaleFactor": 1, "mobile": True},
    )
    browser.command(
        "Emulation.setEmulatedMedia",
        {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
    )
    try:
        browser.evaluate(
            "document.querySelector('#evidence-history').scrollIntoView(); historyEntry.focus()"
        )
        press(browser, "ArrowDown", "ArrowDown", 40)
        press(browser, "Enter", "Enter", 13, "\r")
        settle(browser)
        assert download_value(browser)["entry_id"] == "integral-pwr"
        browser.evaluate("document.querySelector('.history-revision summary').focus()")
        press(browser, " ", "Space", 32, " ")
        assert browser.evaluate("document.querySelector('.history-revision details').open") is True
        assert browser.evaluate("document.documentElement.scrollWidth <= innerWidth + 1") is True
        assert (
            browser.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
        )
        fill_proposal(browser)
        proposal_settle(browser)
        expected = download_value(browser, "correctionDownload")
        browser.command(
            "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(tmp_path)}
        )
        browser.evaluate("correctionDownload.focus()")
        press(browser, "Enter", "Enter", 13, "\r")
        target = tmp_path / "integral-pwr-correction-proposal.json"
        deadline = time.monotonic() + 15
        while not target.exists():
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert json.loads(target.read_text()) == expected
        browser.evaluate(
            "document.querySelector('#evidence-history').scrollIntoView({behavior:'instant'})"
        )
        screenshot = browser.command("Page.captureScreenshot", {"format": "png"})["data"]
        assert isinstance(screenshot, str)
        with (evidence_directory / "history-mobile.png").open("xb") as handle:
            handle.write(base64.b64decode(screenshot, validate=True))
    finally:
        browser.command("Emulation.clearDeviceMetricsOverride")
        browser.command("Emulation.setEmulatedMedia", {"features": []})
        browser.command("Browser.setDownloadBehavior", {"behavior": "default"})
