# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual current/original profile cards and downloaded files.

"""Exercise reviewed profiles through the genuine Atlas page and native Chrome."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from ._native_browser_ranges import browser_ranges
from .browser_checks_runtime import BrowserEndpoints
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser, press

ROOT = Path(__file__).resolve().parents[1]
MODULES = [
    ROOT / "04_interactive_presentation/taxonomy-reviewed-presentation.js",
    ROOT / "04_interactive_presentation/taxonomy-catalogue-controller.js",
    ROOT / "04_interactive_presentation/app.js",
]


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, tmp_path: Path, request: pytest.FixtureRequest
) -> Iterator[Browser]:
    """Capture the actual registered source while using a fresh real page.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned Chrome process and complete maintained page.
    tmp_path : pathlib.Path
        Samsung-owned case directory for source and execution-range evidence.
    request : pytest.FixtureRequest
        Actual registered case identity, without simulated runtime behaviour.

    Yields
    ------
    Browser
        Real page with current/original profiles loaded by actual script tags.
    """
    with browser_ranges(native_browser, tmp_path, MODULES, request.node.name) as active:
        yield active


def test_all135_actual_cards_preserve_originals_and_select_current_downloads(
    browser: Browser,
) -> None:
    """Click every actual card and inspect complete original/current JSON from real links."""
    result = browser.evaluate(
        """(() => {
          const original = REACTOR_TAXONOMY_EVIDENCE_PROFILES;
          const current = REACTOR_TAXONOMY_REVIEWED_PROFILES;
          const before = JSON.stringify({original,current});
          let count=0, claims=0;
          for (const button of document.querySelectorAll('#reactorGrid .reactor-card')) {
            button.click();
            const row = reactors.find(row=>row.name===button.dataset.name);
            const profile = original.records.find(record=>record.entry_id===row.id);
            const review = current.author_reviews.records.find(record=>record.entry_id===row.id);
            const unsupported=review.fields.maturity.disposition==='unsupported';
            if (unsupported &&
                (!button.querySelector('.maturity').textContent.includes('maturity claim unqualified') ||
                 !dialogBody.querySelector('.dialog-meta').textContent.includes('maturity claim unqualified') ||
                 !dialogBody.querySelector('.author-fields').textContent.includes('maturity: unsupported')))
              throw Error('Unqualified deployment became an accepted maturity label');
            const link = dialogBody.querySelector('.reviewed-profile-download');
            const selected = JSON.parse(decodeURIComponent(link.href.split(',').slice(1).join(',')));
            if (!reactorDialog.open || dialogTitle.textContent!==row.name ||
                dialogBody.querySelectorAll('.author-fields li').length!==21 ||
                JSON.stringify(selected.taxonomy_record)!==JSON.stringify(current.records[count]) ||
                JSON.stringify(selected.original_profile)!==JSON.stringify(profile) ||
                JSON.stringify(selected.author_review)!==JSON.stringify(review) ||
                selected.original_profile.review_disposition.complete_entry_review!==false ||
                selected.author_review.complete_entry_review!==true ||
                selected.author_review.review_scope!=='all-original-fields-and-selected-sources' ||
                selected.author_review.review_basis!=='author-source-inspection' ||
                selected.author_review_context.author!==current.author_reviews.author ||
                selected.author_review_context.reviewed_on!==current.author_reviews.reviewed_on ||
                selected.author_review.independent_review!==null)
              throw Error('Whole current/original detail changed');
            claims += dialogBody.querySelectorAll('.claim-citations li').length;
            count++;
            reactorDialog.close();
          }
          return {count,claims,unchanged:before===JSON.stringify({original,current}),
                  frozen:Object.isFrozen(REACTOR_TAXONOMY_REVIEWED_PROFILE_INPUTS),
                  originalName:REACTOR_TAXONOMY.find(row=>row.id==='phwr-candu').name,
                  currentName:reactors.find(row=>row.id==='phwr-candu').name};
        })()""",
        timeout=60,
    )
    assert isinstance(result, dict)
    assert result["count"] == 135 and result["claims"] == 599
    assert result["unchanged"] is True and result["frozen"] is True
    assert result["originalName"] == "PHWR / CANDU"
    assert result["currentName"] == "Pressure-tube PHWR including CANDU"


def test_keyboard_disclosure_and_actual_current_and_original_files(
    browser: Browser, tmp_path: Path
) -> None:
    """Use native keyboard controls and save both genuine selected downloads.

    Parameters
    ----------
    browser : Browser
        Real maintained detail and native disclosure/download controls.
    tmp_path : pathlib.Path
        Actual Samsung download directory, preserved as test evidence.
    """
    browser.evaluate("openReactor('Pressure-tube PHWR including CANDU')")
    browser.evaluate("dialogBody.querySelector('.author-fields summary').focus()")
    press(browser, " ", "Space", 32, " ")
    assert browser.evaluate("dialogBody.querySelector('.author-fields').open") is True
    browser.command(
        "Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(tmp_path)}
    )
    for selector, filename in [
        (".reviewed-profile-download", "phwr-candu-reviewed-profile.json"),
        (".profile-download", "phwr-candu-evidence-profile.json"),
    ]:
        browser.evaluate("dialogBody.querySelector(" + json.dumps(selector) + ").click()")
        destination = tmp_path / filename
        deadline = time.monotonic() + 15
        while not destination.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        document = json.loads(destination.read_text())
        assert document["selected_entry_id"] == "phwr-candu"
        assert document["source_rights"] == "catalogue-only; original not redistributed"
        if selector == ".reviewed-profile-download":
            assert document["taxonomy_record"]["name"] == "Pressure-tube PHWR including CANDU"
            assert document["original_profile"]["taxonomy_record"]["name"] == "PHWR / CANDU"
            assert document["author_review"]["complete_entry_review"] is True
            assert len(document["inputs"]) == 5
        else:
            assert document["profile"]["taxonomy_record"]["name"] == "PHWR / CANDU"
            assert len(document["inputs"]) == 3


def test_actual_observation_scope_dates_and_mobile_disclosures(browser: Browser) -> None:
    """Keep actual source-specific chronology and evidence boundaries readable on mobile."""
    browser.command(
        "Emulation.setDeviceMetricsOverride",
        {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
    )
    try:
        text = browser.evaluate(
            """(() => {
              const record=REACTOR_TAXONOMY_REVIEWED_PROFILES.author_reviews.records.find(
                row=>row.observations.some(item=>item.event_date.value==='1956'));
              openReactor(reactors.find(row=>row.id===record.entry_id).name);
              return dialogBody.querySelector('.author-observations').textContent;
            })()"""
        )
        assert isinstance(text, str) and "1956 (year)" in text
        assert "PDF page(s)" in text and "experiment" in text
        assert "Scope:" in text and "Publication:" in text and "Source capture:" in text
        assert (
            browser.evaluate(
                "dialogBody.querySelector('.author-assessment').scrollWidth<=reactorDialog.clientWidth"
            )
            is True
        )
    finally:
        browser.command("Emulation.clearDeviceMetricsOverride")


def test_damaged_actual_last_profile_refuses_early_detail_without_partial_output(
    browser: Browser,
) -> None:
    """Refuse a whole damaged product before replacing an early selected detail."""
    result = browser.evaluate(
        """(() => {
          const original=REACTOR_TAXONOMY_REVIEWED_PROFILES;
          const before=dialogBody.innerHTML;
          REACTOR_TAXONOMY_REVIEWED_PROFILES=structuredClone(original);
          REACTOR_TAXONOMY_REVIEWED_PROFILES.records.at(-1).name='Unassessed last caption';
          try {openReactor(reactors[0].name);return false;}
          catch {return dialogBody.innerHTML===before && !reactorDialog.open;}
          finally {REACTOR_TAXONOMY_REVIEWED_PROFILES=original;}
        })()"""
    )
    assert result is True


def test_altered_actual_selected_row_and_unknown_identity_refuse(browser: Browser) -> None:
    """Refuse caller-supplied detail cells that differ from the admitted current profile."""
    for change in ["row.principle='Changed physical principle'", "row.id='absent-source-entry'"]:
        result = browser.evaluate(
            "(()=>{const row=structuredClone(taxonomyRows[0]);"
            + change
            + ";const before=dialogBody.innerHTML;"
            + "const owner=AtlasTaxonomyCatalogue.create(document,[row],taxonomyAuditRows);"
            + "try{owner.open(row.name);return false;}"
            + "catch{return before===dialogBody.innerHTML && !reactorDialog.open;}})()"
        )
        assert result is True
