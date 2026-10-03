# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_evidence_profiles_browser.py

"""Follow actual detail, keyboard, mobile and file-download paths in native Chrome."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, cast

import pytest

from .conftest import load_module
from .test_browser_checks import BrowserEndpoints
from .test_browser_checks import native_browser as native_browser


class Browser(Protocol):
    """Public native Chrome session methods used by these application checks."""

    def evaluate(self, expression: str, *, timeout: float | None = None) -> object: ...
    def command(
        self, method: str, params: dict[str, object] | None = None, *, timeout: float | None = None
    ) -> dict[str, object]: ...
    def wait_ready(self, *, timeout: float = 15) -> None: ...


@pytest.fixture
def browser(native_browser: BrowserEndpoints) -> Iterator[Browser]:
    """Connect to the actual application using the maintained public CDP interface."""
    module = load_module("04_interactive_presentation/browser-check.py", "atlas_profile_browser")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as session:
        session.command("Page.reload")
        session.wait_ready()
        yield cast(Browser, session)


def press(browser: Browser, key: str, code: str, number: int, text: str = "") -> None:
    for kind in ("keyDown", "keyUp"):
        browser.command(
            "Input.dispatchKeyEvent",
            {
                "type": kind,
                "key": key,
                "code": code,
                "windowsVirtualKeyCode": number,
                "text": text if kind == "keyDown" else "",
            },
        )


def test_actual_all135_dialogs_keep_claim_text_locators_and_capture_scope(browser: Browser) -> None:
    result = browser.evaluate("""(() => {
      const doc = window.REACTOR_TAXONOMY_EVIDENCE_PROFILES;
      let entries = 0, claims = 0;
      for (const button of document.querySelectorAll('#reactorGrid .reactor-card')) {
        button.click();
        const row = reactors.find(row => row.name === button.dataset.name);
        const profile = doc.records.find(profile => profile.entry_id === row.id);
        const dialog = document.querySelector('#reactorDialog');
        const nodes = [...dialog.querySelectorAll('.claim-citations li')];
        if (!dialog.open || nodes.length !== profile.claims.length) throw Error('Detail count');
        for (const [i, node] of nodes.entries()) {
          const citation = profile.claims[i].citation;
          if (node.querySelector('p').textContent !== citation.statement ||
              !node.textContent.includes(citation.scope)) throw Error('Claim text or scope');
          const source = doc.sources.find(source => source.id === citation.source_id);
          const link = node.querySelector('a');
          if (!link.href.startsWith(source.url)) throw Error('Source locator');
          if (source.captured_at === null && !node.textContent.includes('original retrieval date unknown'))
            throw Error('Unknown capture time');
        }
        entries++; claims += nodes.length;
        dialog.close();
      }
      return {entries, claims};
    })()""")
    assert result == {"entries": 135, "claims": 599}


def test_keyboard_mobile_expansion_close_and_actual_json_download(
    browser: Browser, tmp_path: Path
) -> None:
    browser.command(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": 375,
            "height": 812,
            "deviceScaleFactor": 1,
            "mobile": True,
        },
    )
    try:
        browser.evaluate("""
          document.querySelector('#taxonomy').scrollIntoView();
          document.querySelector('#reactorGrid .reactor-card').focus();
        """)
        press(browser, "Enter", "Enter", 13, "\r")
        assert browser.evaluate("document.querySelector('#reactorDialog').open") is True
        browser.evaluate("""
          document.querySelector('#reactorDialog .profile-questions summary').scrollIntoView();
          document.querySelector('#reactorDialog .profile-questions summary').focus();
        """)
        press(browser, " ", "Space", 32, " ")
        assert (
            browser.evaluate("document.querySelector('#reactorDialog .profile-questions').open")
            is True
        )
        assert (
            browser.evaluate("""
          document.querySelector('#reactorDialog').scrollWidth <=
          document.querySelector('#reactorDialog').clientWidth + 1
        """)
            is True
        )
        browser.command(
            "Browser.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": str(tmp_path),
            },
        )
        browser.evaluate("""
          document.querySelector('#reactorDialog .profile-download').scrollIntoView();
          document.querySelector('#reactorDialog .profile-download').focus();
        """)
        press(browser, "Enter", "Enter", 13, "\r")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            downloads = list(tmp_path.glob("*-evidence-profile.json"))
            if len(downloads) == 1:
                break
            time.sleep(0.05)
        else:
            pytest.fail("Native profile download was not created")
        exported = json.loads(downloads[0].read_text())
        assert exported["schema_version"] == "atlas-entry-evidence-1.0.0"
        expected = browser.evaluate("""JSON.parse(AtlasTaxonomyEvidenceProfiles.exportProfile(
          window.REACTOR_TAXONOMY_EVIDENCE_PROFILES,
          window.REACTOR_TAXONOMY_EVIDENCE_PROFILES.inputs.taxonomy_sha256,
          window.REACTOR_TAXONOMY_EVIDENCE_PROFILES.records[0].entry_id))""")
        assert exported == expected
        assert exported["source_rights"] == "catalogue-only; original not redistributed"
        press(browser, "Escape", "Escape", 27)
        assert browser.evaluate("document.querySelector('#reactorDialog').open") is False
    finally:
        browser.command("Emulation.clearDeviceMetricsOverride")
        browser.command("Browser.setDownloadBehavior", {"behavior": "default"})


def test_reload_uses_identical_profile_snapshot_without_invented_review(browser: Browser) -> None:
    before = browser.evaluate("JSON.stringify(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES)")
    browser.command("Page.reload")
    browser.wait_ready()
    assert browser.evaluate("JSON.stringify(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES)") == before
    assert (
        browser.evaluate("""window.REACTOR_TAXONOMY_EVIDENCE_PROFILES.records.every(
      record => record.review_disposition.complete_entry_review === false &&
                record.review_disposition.independent_review === null)""")
        is True
    )
