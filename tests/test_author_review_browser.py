# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_author_review_browser.py

"""Exercise the loaded native Chrome author-review reader with actual source input."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from ._native_browser_ranges import browser_ranges
from .browser_checks_runtime import BrowserEndpoints
from .test_author_review_contract import REVIEW, ROOT, read
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser


@pytest.fixture(scope="module")
def browser(
    native_browser: BrowserEndpoints, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[Browser]:
    """Retain both actual loaded modules and their native execution regions.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Real isolated Chrome endpoint serving the complete candidate.
    tmp_path_factory : pytest.TempPathFactory
        Owned Samsung receipt allocation for original native source and ranges.

    Yields
    ------
    Browser
        Actual application session with precise source coverage enabled.
    """
    sources = [
        ROOT / "04_interactive_presentation" / name
        for name in [
            "author-review-values.js",
            "author-review-dimensions.js",
            "author-review-revisions.js",
            "taxonomy-author-review.js",
        ]
    ]
    with browser_ranges(
        native_browser,
        tmp_path_factory.mktemp("native-author-review-ranges"),
        sources,
        "author-review",
    ) as connected:
        yield connected


def test_loaded_actual_whole_input_keeps_values_and_forecasts(browser: Browser) -> None:
    """Admit every original entry through the page's registered production reader.

    Parameters
    ----------
    browser : Browser
        Real Chrome session whose original script bytes and dataset were verified.
    """
    input_path = Path(os.environ.get("ATLAS_AUTHOR_REVIEW_INPUT", str(ROOT / REVIEW)))
    doc = read(input_path)
    result = browser.evaluate(
        "(input => {const before=JSON.stringify(input); const admitted=AtlasTaxonomyAuthorReview.read(input,window.REACTOR_TAXONOMY_EVIDENCE_PROFILES); return {entries:admitted.records.length,fields:admitted.records.reduce((n,row)=>n+Object.keys(row.fields).length,0),observations:admitted.records.reduce((n,row)=>n+row.observations.length,0),facets:admitted.records.reduce((n,row)=>n+row.facets.length,0),attained:admitted.records.reduce((n,row)=>n+row.development_assessments.length,0),unchanged:JSON.stringify(input)===before,unknown:admitted.records.every(row=>row.current_activity==='unknown' && row.complete_entry_review===true && row.independent_review===null),forecast:admitted.records.flatMap(row=>row.observations).filter(item=>item.temporal_role==='forecast').map(item=>item.event_date)};})("
        + json.dumps(doc)
        + ")",
        timeout=30,
    )
    assert result == {
        "entries": 135,
        "fields": 2835,
        "observations": 31,
        "facets": 138,
        "attained": 21,
        "unchanged": True,
        "unknown": True,
        "forecast": [
            {"value": "2024", "precision": "year"},
            {"value": "2026", "precision": "year"},
            {"value": "2029", "precision": "year"},
        ],
    }
    for fault in [
        "source",
        "future-event",
        "completion",
        "scope",
        "basis",
        "independent",
        "stage-forecast",
        "industrial-experiment",
    ]:
        changed = read(input_path)
        rows = changed["records"]
        assert isinstance(rows, list) and isinstance(rows[0], dict)
        first = rows[0]
        if fault == "source":
            fields = first["fields"]
            assert isinstance(fields, dict) and isinstance(fields["principle"], dict)
            fields["principle"]["source_ids"] = ["absent-source"]
        elif fault == "future-event":
            observations = first["observations"]
            assert isinstance(observations, list) and isinstance(observations[0], dict)
            observations[0]["event_date"] = {"value": "2030-01-01", "precision": "day"}
        elif fault == "stage-forecast":
            target = next(
                row
                for row in rows
                if isinstance(row, dict)
                and row["entry_id"] == "nuclear-heat-coupled-to-hydrogen-production"
            )
            assert isinstance(target, dict)
            stages = target["development_assessments"]
            assert isinstance(stages, list) and isinstance(stages[0], dict)
            stages[0]["observation_ids"] = ["httr-hydrogen-future-project-schedule"]
        elif fault == "industrial-experiment":
            target = next(
                row
                for row in rows
                if isinstance(row, dict) and row["entry_id"] == "muon-catalysed-fusion"
            )
            assert isinstance(target, dict)
            stages = target["development_assessments"]
            assert isinstance(stages, list) and isinstance(stages[0], dict)
            stages[0]["stage"] = "industrial"
        elif fault == "scope":
            first["review_scope"] = "all-hardware-qualified"
        elif fault == "basis":
            first["review_basis"] = "independent-review"
        elif fault == "independent":
            first["independent_review"] = {"accepted": True}
        else:
            first["complete_entry_review"] = False
        assert (
            browser.evaluate(
                "(input => {try {AtlasTaxonomyAuthorReview.read(input,window.REACTOR_TAXONOMY_EVIDENCE_PROFILES);return false;} catch {return true;}})("
                + json.dumps(changed)
                + ")",
                timeout=30,
            )
            is True
        )


def test_loaded_projection_keeps_original_snapshot_and_stable_identity(browser: Browser) -> None:
    """Project every actual entry in Chrome without rewriting original context.

    Parameters
    ----------
    browser : Browser
        Actual source-exact loaded page containing the registered projection API.
    """
    input_path = Path(os.environ.get("ATLAS_AUTHOR_REVIEW_INPUT", str(ROOT / REVIEW)))
    document = read(input_path)
    result = browser.evaluate(
        "(input=>{const baseline=window.REACTOR_TAXONOMY_EVIDENCE_PROFILES;const before=JSON.stringify({input,baseline});const rows=AtlasTaxonomyAuthorReview.project(input,baseline);const changed=[];for(let i=0;i<rows.length;i++)for(const key of Object.keys(rows[i]))if(JSON.stringify(rows[i][key])!==JSON.stringify(baseline.records[i].taxonomy_record[key]))changed.push([rows[i].id,key,rows[i][key]]);rows[0].source_ids.push('caller-mutation');return {count:rows.length,fields:rows.reduce((n,row)=>n+Object.keys(row).length,0),changed,originalsUnchanged:JSON.stringify({input,baseline})===before};})("
        + json.dumps(document)
        + ")",
        timeout=30,
    )
    assert result == {
        "count": 135,
        "fields": 2835,
        "changed": [
            ["integral-pwr", "maturity", "deployed"],
            ["phwr-candu", "name", "Pressure-tube PHWR including CANDU"],
            ["heavy-water-pressure-vessel-reactor", "maturity", "deployed"],
            ["magnox-gas-cooled-reactor", "maturity", "deployed"],
            ["prismatic-htgr", "maturity", "deployed"],
            ["lead-bismuth-fast-reactor", "maturity", "deployed"],
            [
                "nuclear-heat-coupled-to-hydrogen-production",
                "name",
                "Nuclear energy coupled to hydrogen production",
            ],
        ],
        "originalsUnchanged": True,
    }


def test_actual_historical_deployment_does_not_promote_past_forecasts(browser: Browser) -> None:
    """Read dated source-attributed deployment and preserve historical forecast roles.

    Parameters
    ----------
    browser : Browser
        Actual complete page with the latest owning-produced source proposal.
    """
    result = browser.evaluate(
        """(() => {
          const doc=REACTOR_TAXONOMY_REVIEWED_PROFILES;
          const entry=doc.author_reviews.records.find(row=>row.entry_id==='integral-pwr');
          const original=doc.original_profiles.records.find(row=>row.entry_id==='integral-pwr');
          const current=doc.records.find(row=>row.id==='integral-pwr');
          openReactor(current.name);
          return {original:original.taxonomy_record.maturity,current:current.maturity,
                  label:dialogBody.textContent.includes('deployment in a stated application'),
                  forecasts:entry.observations.filter(row=>row.temporal_role==='forecast').map(row=>row.event_date.value),
                  attained:entry.development_assessments.flatMap(row=>row.observation_ids),
                  sourceAttribution:dialogBody.textContent.includes('Manufacturer-attributed'),
                  independent:entry.independent_review,complete:entry.complete_entry_review};
        })()"""
    )
    assert result == {
        "original": "demonstrated",
        "current": "deployed",
        "label": True,
        "forecasts": ["2024", "2026"],
        "attained": ["ritm-arktika-commissioned-2020"],
        "sourceAttribution": True,
        "independent": None,
        "complete": True,
    }
    browser.evaluate("reactorDialog.close()")
