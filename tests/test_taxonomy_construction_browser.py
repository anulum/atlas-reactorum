# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_taxonomy_construction_browser.py

"""Preserve authored taxonomy identities through actual Chrome construction."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from ._native_browser_ranges import browser_ranges
from .browser_checks_runtime import BrowserEndpoints
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser


@pytest.fixture(scope="module")
def browser(
    native_browser: BrowserEndpoints, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[Browser]:
    """Retain source-exact native Chrome execution across the constructor cases.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned native Chrome discovery endpoint and complete actual page.
    tmp_path_factory : pytest.TempPathFactory
        Test-owned Samsung directory for the original native coverage receipt.

    Yields
    ------
    Browser
        Real application session with precise source coverage enabled.
    """
    directory = tmp_path_factory.mktemp("native-construction-ranges")
    source = Path(__file__).resolve().parents[1] / (
        "04_interactive_presentation/taxonomy-construction.js"
    )
    with browser_ranges(native_browser, directory, [source], "constructor") as connected:
        yield connected


def test_all135_explicit_identities_and_corrected_caption_keep_original_context(
    browser: Browser,
) -> None:
    """Reconstruct every actual row and change one caption without changing its claims.

    Parameters
    ----------
    browser : Browser
        Native Chrome session serving the complete candidate application and datasets.
    """
    result = browser.evaluate("""(() => {
      const originals = window.REACTOR_TAXONOMY;
      const before = JSON.stringify(originals);
      const construct = corrected => {
        const builder = AtlasTaxonomyConstruction.create(window.REACTOR_TAXONOMY_SOURCES);
        for (const row of originals) {
          const name = corrected && row.id === 'phwr-candu'
            ? 'Pressure-tube PHWR including CANDU' : row.name;
          builder.add(row.domain, row.family, row.source_ids.join(' '), [[
            name, row.parent, row.maturity, row.evidence, row.principle,
            row.strength, row.challenge, row.kind,
            {id: row.id, parent_id: row.parent_id, evidence_scope: row.evidence_scope,
             reviewed_on: row.reviewed_on}
          ]]);
        }
        return builder.complete();
      };
      const same = construct(false);
      if (JSON.stringify(same) !== before) throw Error('Original context changed');
      const corrected = construct(true);
      const changed = corrected.find(row => row.id === 'phwr-candu');
      if (changed.name !== 'Pressure-tube PHWR including CANDU') throw Error('Caption');
      const restored = corrected.map(row => ({...row,
        name: originals.find(original => original.id === row.id).name}));
      if (JSON.stringify(restored) !== before) throw Error('Identity or source context changed');
      const doc = window.REACTOR_TAXONOMY_EVIDENCE_PROFILES;
      for (const row of corrected) {
        const profile = doc.records.find(record => record.entry_id === row.id);
        if (!profile || profile.claims.some(claim => !claim.claim_id.startsWith(row.id + ':')))
          throw Error('Original claim identity');
      }
      if (JSON.stringify(originals) !== before) throw Error('Input mutated');
      return {entries: corrected.length, claims: doc.records.reduce((n, row) => n + row.claims.length, 0),
        identity: changed.id};
    })()""")
    assert result == {"entries": 135, "claims": 599, "identity": "phwr-candu"}


def test_native_identity_refusals_and_failed_locator_reserve_no_row(browser: Browser) -> None:
    """Refuse actual malformed identities, collisions and missing parents in Chrome.

    Parameters
    ----------
    browser : Browser
        Native Chrome session executing the maintained public constructor.
    """
    result = browser.evaluate("""(() => {
      const row = window.REACTOR_TAXONOMY.find(row => row.id === 'pwr');
      const sources = window.REACTOR_TAXONOMY_SOURCES;
      const tuple = overrides => [row.name, null, row.maturity, row.evidence,
        row.principle, row.strength, row.challenge, row.kind, overrides];
      let refused = 0;
      for (const overrides of [{id:''}, {id:null}, {id:4}, {id:'Upper'},
        {id:undefined}, {parent_id:''}, {parent_id:false}, {parent_id:undefined}]) {
        const builder = AtlasTaxonomyConstruction.create(sources);
        try { builder.add(row.domain, row.family, row.source_ids.join(' '), [tuple(overrides)]); }
        catch (error) {
          if (!error.message.includes('identity is invalid')) throw error;
          refused++;
        }
        if (builder.complete().length) throw Error('Rejected row appended');
      }
      const builder = AtlasTaxonomyConstruction.create(sources);
      try { builder.add(row.domain, row.family, 'absent-source', [tuple({id:row.id})]); }
      catch (error) { if (!error.message.includes('source identity is unavailable')) throw error; refused++; }
      builder.add(row.domain, row.family, row.source_ids.join(' '), [tuple({id:row.id})]);
      try { builder.add(row.domain, row.family, row.source_ids.join(' '), [tuple({id:row.id})]); }
      catch (error) { if (error.message !== 'Duplicate ID') throw error; refused++; }
      const dangling = AtlasTaxonomyConstruction.create(sources);
      dangling.add(row.domain, row.family, row.source_ids.join(' '), [tuple({parent_id:'absent-parent'})]);
      try { dangling.complete(); }
      catch (error) { if (error.message !== 'Missing parent') throw error; refused++; }
      return {refused, accepted:builder.complete().length};
    })()""")
    assert result == {"refused": 11, "accepted": 1}
