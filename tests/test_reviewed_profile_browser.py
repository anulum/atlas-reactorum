# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual reviewed-profile producer/Chrome consumer integration.

"""Exercise genuine emitted original/current profiles through the real loaded page."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest

from ._native_browser_ranges import browser_ranges
from .browser_checks_runtime import BrowserEndpoints
from .test_author_review_contract import PROFILE, ROOT, read
from .test_author_review_contract import candidate as candidate
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser
from .test_reviewed_profile_products import PRODUCT
from .test_reviewed_profile_products import emitted as emitted
from .test_reviewed_profile_products import genuine_products as genuine_products


@pytest.fixture(scope="module")
def browser(
    native_browser: BrowserEndpoints, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[Browser]:
    """Collect the actual registered reader source and native execution ranges.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned real Chrome serving the complete current candidate.
    tmp_path_factory : pytest.TempPathFactory
        Owned Samsung allocation for native source and range receipts.

    Yields
    ------
    Browser
        Source-exact real page session with the actual profile API registered.
    """
    with browser_ranges(
        native_browser,
        tmp_path_factory.mktemp("native-reviewed-profile-ranges"),
        [ROOT / "04_interactive_presentation/taxonomy-reviewed-profiles.js"],
        "reviewed-profile",
    ) as connected:
        yield connected


def test_actual_producer_and_chrome_keep_both_full_contexts(
    browser: Browser, emitted: Path
) -> None:
    """Select revised and original records through the real page's complete reader.

    Parameters
    ----------
    browser : Browser
        Actual loaded source-exact Chrome API session.
    emitted : pathlib.Path
        Actual Node-generated whole original/current reviewed product.
    """
    script_paths = browser.evaluate(
        "[...document.scripts].filter(script=>script.src)"
        ".map(script=>new URL(script.src).pathname)"
        ".filter(path=>path.endsWith('/taxonomy-reviewed-profiles.js'))"
    )
    assert script_paths == [
        "/data/taxonomy-reviewed-profiles.js",
        "/taxonomy-reviewed-profiles.js",
    ]
    document = read(emitted / PRODUCT)
    baseline = read(emitted / PROFILE)
    result = browser.evaluate(
        "((doc,baseline)=>{const before=JSON.stringify({doc,baseline});const selected=AtlasTaxonomyReviewedProfiles.readProfile(doc,doc.inputs,baseline,'phwr-candu');const result={count:doc.records.length,claims:doc.original_profiles.records.reduce((n,row)=>n+row.claims.length,0),original:selected.original_profile.taxonomy_record.name,current:selected.taxonomy_record.name,scope:selected.author_review.fields.name.assessment};selected.author_review.fields.name.assessment='caller mutation';result.unchanged=JSON.stringify({doc,baseline})===before;return result;})("
        + json.dumps(document)
        + ","
        + json.dumps(baseline)
        + ")",
        timeout=30,
    )
    assert isinstance(result, dict)
    assert result["count"] == 135 and result["claims"] == 599
    assert result["original"] == "PHWR / CANDU"
    assert result["current"] == "Pressure-tube PHWR including CANDU"
    assert result["unchanged"] is True
    assert "pressure-vessel" in str(result["scope"])
    damaged = read(emitted / PRODUCT)
    cast(list[dict[str, object]], damaged["records"])[-1]["name"] = "unassessed last caption"
    assert (
        browser.evaluate(
            "((doc,baseline)=>{try{AtlasTaxonomyReviewedProfiles.readProfile(doc,doc.inputs,baseline,'pwr');return false;}catch{return true;}})("
            + json.dumps(damaged)
            + ","
            + json.dumps(baseline)
            + ")",
            timeout=30,
        )
        is True
    )
